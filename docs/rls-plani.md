# RLS Planı — Tenant İzolasyonunun DB Katmanında Garantisi

> Kural 5 (01-GELISTIRME-KURALLARI.md): "Multi-tenant izolasyonu her katmanda
> korunur." Bugüne dek izolasyon **uygulama katmanında** sağlanıyordu
> (`TenantScopedViewSet` queryset filtresi + `TenantAwareModelSerializer`
> read-only tenant). Bu plan, aynı garantinin **PostgreSQL Row Level Security
> (RLS)** ile DB katmanına taşınma yolunu tanımlar. Script: `db/rls.sql`.

---

## 1. Mevcut durum

| Katman | Mekanizma | Durum |
|---|---|---|
| API | `TenantScopedViewSet` (queryset `tenant_id = user.tenant_id`; superuser global) | ✅ aktif |
| Serializer | `TenantAwareModelSerializer` (tenant read-only; istemciden asla alınmaz) | ✅ aktif |
| **DB** | **RLS policy'leri (`app.current_tenant` GUC'süne bağlı)** | ✅ dev'de etkin, FORCE üretim aşamasında |

## 2. Tasarım

- **Bağlam değişkeni:** Her DB oturumunda `app.current_tenant` özel ayarı (GUC)
  tenant pk'sını taşır. Boş/ayarlanmamışsa `app_mevcut_tenant()` `NULL` döner ve
  hiçbir tenant satırı görünmez (**güvenli varsayılan**).
- **Yardımcı fonksiyon:** `app_mevcut_tenant()` —
  `NULLIF(current_setting('app.current_tenant', true), '')::bigint`
- **Policy:** `tenant_id` kolonlu 8 tabloda tek policy:
  `USING (tenant_id = app_mevcut_tenant()) WITH CHECK (tenant_id = app_mevcut_tenant())`
  — hem okuma hem yazma korumalı (`FOR ALL` varsayılan).
- **users_user istisnası:** Süper kullanıcı satırları (`tenant_id IS NULL`) her
  bağlamda görünür; normal kullanıcılar yalnız kendi tenant'ının kullanıcılarını görür.
- **Middleware:** `tenants.middleware.TenantBaglamMiddleware` her istekte GUC'yi
  ayarlar: (1) session auth (Django admin) → `request.user.tenant_id`;
  (2) JWT (DRF API) → `Authorization` başlığındaki access token çözülür,
  `user_id` → `tenant_id`. Anonim/geçersiz istekte GUC boş bırakılır.
- **Oturum düzeyi ayar:** `set_config(..., false)` ile oturum değişkeni yazılır ve
  **her istek başında yeniden yazılır**; böylece kalıcı bağlantılarda
  (`CONN_MAX_AGE > 0`) önceki isteğin tenant'ı sızamaz (anonim istek de
  bağlamı boşaltır).

## 3. Kapsam: tablolar

`db/rls.sql` şu tablolara policy ekler (idempotent — tekrar çalıştırılabilir):
`construction_pozgrubu`, `construction_poz`, `construction_malzeme`,
`construction_pozmalzemeiliskisi`, `construction_pozfiyat`,
`construction_yapisinifibirimmaliyet`, `construction_proje`,
`real_estate_realestate`, `users_user` (özel policy).
`tenants_tenant` kapsam dışıdır (kök tablo; kendi listesi Yetki/RBAC ile yönetilir).
Yeni tenant-aware model eklendiğinde tablo adı `db/rls.sql`'deki diziye yazılmalıdır.

## 4. Rollar — dev ve prod ayrımı

| Ortam | Bağlantı rolü | FORCE | Sonuç |
|---|---|---|---|
| **Dev** | `emlak` (tablo sahibi) | kapalı | Sahip RLS'den muaftır → Django ve management komutları etkilenmez; policy'ler DB'de hazır bekler. Doğrulama `rls_deneme` rolüyle yapılır. |
| **Prod** | `emlak_app` (sahibi **değil**) | açık | RLS tüm sorgulara uygulanır; GUC'süz bağlam boş veri görür. |

## 5. Üretim geçiş kontrol listesi (FORCE aşaması)

1. `CREATE ROLE emlak_app LOGIN PASSWORD '<gizli>';`
2. `GRANT USAGE ON SCHEMA public TO emlak_app; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES ... ;` (+ sequence hakları, `app_mevcut_tenant()` EXECUTE)
3. Django `DATABASE_URL` → `emlak_app` kullanıcısına geçirilir
4. Her kapsam tablosu için: `ALTER TABLE ... FORCE ROW LEVEL SECURITY;`
5. Management komutları (import_pozlar vb.) istek döngüsü dışında çalışır →
   komut koduna `tenant_baglam(tenant)` context manager'ı eklenmelidir
   (`connection.cursor().execute("SELECT set_config('app.current_tenant', %s, false)")`)
6. `django_migrations`/yönetimsel işler sahibi rol (`emlak`) ile yürütülür
7. Senaryo tekrarı: `rls_deneme` yerine `emlak_app` ile §6 doğrulaması

## 6. Doğrulama senaryosu (`db/rls.sql` uygulandıktan sonra)

```sql
SET ROLE rls_deneme;
SELECT set_config('app.current_tenant', '1', false);
SELECT count(*) FROM construction_poz;   -- yalnız tenant 1 satırları
SELECT set_config('app.current_tenant', '2', false);
SELECT count(*) FROM construction_poz;   -- 0 (başka tenantın verisi görünmez)
SELECT set_config('app.current_tenant', '', false);
SELECT count(*) FROM construction_poz;   -- 0 (bağlamsız erişim yok)
RESET ROLE;
SELECT count(*) FROM construction_poz;   -- sahip (emlak) bypass: tüm satırlar
```

Django tarafı testler: `tenants/tests.py::TenantBaglamMiddlewareTests` — JWT'li
istekte GUC'nin tenant pk'ya, anonim/geçersiz token'da boşa ayarlandığını doğrular.

## 7. Bilinen sınırlar ve notlar

- **pytest:** `--no-migrations` ile test şeması modellerden üretilir; test DB'sinde
  policy'ler yoktur. RLS doğrulaması DB senaryosuyla (§6) yapılır — testler
  uygulama katmanı izolasyonunu kapsar.
- **Şema yönetimi:** RLS policy'leri `db/rls.sql`'de sürüm kontrolündedir; dev DB'ye
  uygulandıktan sonra `db/schema.sql` pg_dump ile tazelendiğinde policy'ler de
  dump'a düşer (çift kaynak yok: değişiklikler `rls.sql` üzerinden yapılır).
- **Süper kullanıcılar (tenant NULL):** Django süper admin hesapları RLS'de her
  bağlamda görünür (users_user policy'si); veri tablolarında superuser için
  bağlam, ileride gelecek "tenant seçici" ile verilir (plan madde 2 — frontend).
- **Django admin:** session auth ile GUC doğru ayarlanır; dev'de sahibi rolü
  bypass sağladığından admin işlemleri etkilenmez.
- **Performans:** Policy per-satırlık `app_mevcut_tenant()` çağrısı `STABLE`
  işaretlidir; planner satır başına bir kez değerlendirir.
