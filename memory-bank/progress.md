# İlerleme — Emlak ERP
> FAZ 6G (2026-09-23) senkron notu: aşağıdaki oturum kayıtları tarihseldir.
> Doğrulanmış güncel durum: migration'lar AKTİF · pytest `--ignore=frontend`
> **386 passed/exit 0** · `check` OK · `makemigrations --check` temiz ·
> `vue-tsc` temiz · Vitest `yetki.spec.ts` 5/5 · FAZ 3A–6F-4 tamam/go-live hazır
> (manuel go-live 7 maddesi kod dışı, kullanıcı tarafında). Detay:
> `FAZ6G_SENKRON_RAPORU.md`.
## Oturum geçmişi
### 2026-09-14 — Oturum 1: dokümantasyon okuma + memory-bank + envanter
### 2026-09-14 — Oturum 2: backend iskeleti
### 2026-09-14 — Oturum 2 devamı: migration iptali + İnşaat Faz 1
### 2026-09-15 — Oturum 3: ÇŞİDB poz parser + IV-A import (Faz 1 tamam)
### 2026-09-15 — Oturum 4: Faz 2 poz maliyet planı (metraj) + S-eğrisi raporu
### 2026-09-16 — Oturum 5: Tüm Inşaat Modüllerinin CRUD iskeleti tamamlandı (Tedarikçi, Hakediş, etc.)
### 2026-09-16 — Oturum 6: Tenant izolasyonu (RLS/Middleware) ve Süper Admin Mekanizmaları tamamlandı.
### 2026-09-16 — Oturum 7: Yapılandırma ve Süreç Dokümantasyonu (`CONTRIBUTING.md`, `schema.sql` finalizasyonu) tamamlandı.
### 2026-09-18 — Oturum 8: Finans çekirdeği ve fatura/rapor ekranları tamamlandı.
### 2026-09-18 — Oturum 9: Kullanıcı deneyimi ve operasyon paneli yenilendi.

## Tamamlandı ✅
- **Finans / Cari / Muhasebe / Fatura / Raporlar:** Cari hareket ve özet action'ları,
  fatura CRUD + iptal deseni, finans özeti/cari özeti/mizan rapor endpoint'leri,
  muhasebe route alias'ları ve tenant RLS listesi tamamlandı.
- **Frontend:** Cari hareketler, faturalar, mizan ve raporlar route/menu/servisleri;
  fatura formu, arama/filtre/istatistikler ve finans rapor ekranı eklendi.
- **Doğrulama:** `manage.py check` temiz; frontend type-check temiz, production build
  başarılı, Vitest **11/11**; geliştirme DB'sinde fatura/cari raporu/finans özeti/mizan
  smoke başarılı. Yeni `finance_fatura`, `finance_rapor`, `finance_ayar` tabloları açıldı.
- Eski servis taslakları (`cari/services.py`, `accounting/services.py`, `finance/utils.py`)
  mevcut model alanlarıyla uyumlu hale getirildi; güncel RLS script'i geliştirme DB'sine uygulandı.
- Dashboard, readme/site-spec beklentisine göre statik modül kartlarından gerçek finans
  KPI'ları, cari bakiye görünümünü ve hızlı işlemleri kullanan operasyon paneline dönüştürüldü.
- AppLayout responsive, daraltılabilir sidebar; aktif sayfa bağlamı, tenant bilgisi,
  arama yer tutucusu ve bildirim alanı ile yenilendi.
- Veritabanı yönetimindeki Django 6 `timezone.utc` kaynaklı 500 düzeltildi; database API
  hataları artık loglanıyor ve frontend `detail/errors` mesajlarını kullanıcıya gösteriyor.
- Frontend doğrulama: `vue-tsc`, production build ve Vitest **11/11** başarılı.
- **Admin/yetki:** Superuser JWT ve `/auth/me` içinde `super_admin`; finans/muhasebe
  rollerinde yazma yetkisi görünür ve backend’de kabul edilir. Admin tenant seçimiyle
  cari, hesap, ayar ve fatura oluşturma smoke testi `201` döndü.
- **Ayarlar:** `/finance/ayarlar/` CRUD ve `/finans/ayarlar` Vue ekranı eklendi;
  ayar benzersizliği tenant + anahtar olarak düzeltildi.
- Dokümantasyon okundu; teknoloji stack, veri modeli, API/rol kararları net.
- Frontend config dosyaları mevcut (vue/vuex/router).
- `site-specification.json` JSON düzeltmesi (surfaceHover tırnak) + doğrulama.
- Backend iskeleti:
  - venv + `requirements.txt`; Django 6.1.1 / DRF / simplejwt / psycopg3 / spectacular vd.
  - Docker Compose PostgreSQL 16 (host 5433, volume `emlakpython_pgdata`)
  - `config/settings/` paketi (base/dev/prod), tr-TR, Europe/Istanbul, `MAILERS`
  - 6 modül app + Türkçe AppConfig verbose_name
  - Tenant, TenantAwareModel, User (rol enum) + admin
  - JWT + Swagger/Redoc + `api/v1/health/`
  - **Şema yönetimi (FAZ 6G güncel — migration'lar AKTİF):** tenants 1 · users 2 ·
    real_estate 1 · construction 0001→0031 (+0027 reconcile, 0028 merge) · cari 7 ·
    finance 17 · accounting 8 · audit 2 · purchasing 4. `makemigrations --check`
    temiz (2026-09-23 doğrulandı).
    (Tarihsel: 2026-09-14'te "migration kullanılmaz → `db/schema.sql`" kararı
    vardı; aşağıdaki 2 satır o dönemin kaydıdır — otorite değildir.)
  - ~~6 app'in `migrations/` klasörleri silindi; `schema.sql` `django_migrations`~~
  - ~~tablo olmadan yeniden üretildi; pytest --no-migrations~~
- AGENTS yol düzeltmeleri (`.cline/rules/aAGENTS.md`)

- Sunucu başlatma sorunu çözüldü: port 8000 temizlendi ve DJANGO_SETTINGS_MODULE ayarlandı.
- construction/admin.py dosyasında HakedisAdmin sınıfının list_display, list_filter ve search_fields alanları güncellendi (donem_baslangic/donem_bitis yerine donem, hakedis_no search'ten kaldırıldı).
## İnşaat Modülü (Faz 1 & 2) ☑
- **Inşaat Faz 1 (çekirdek):** 7 model (`PozGrubu`, `Poz`, `Malzeme`, `PozMalzemeIliskisi`, `PozFiyat`, `YapiSinifiBirimMaliyet`, `Proje`) — Decimal, DB check/unique constraint.
- **Servisler:** `services.py` maliyet motoru; roller: `SANTIYE_SEFI`, `MALIYET_MUHENDISI`.
- **API:** 11 ViewSet `/api/v1/construction/...` (7 Faz 1 + 4 Faz 2) + `IsConstructionEditor` rolo.
- **Frontend:** Pozlar, Projeler, Malzemeler, etc. CRUD ekranları ve router entegrasyonları hazır.
- **Schema:** Tüm şemalar `db/schema.sql` içine toplandı (1024 satır).

## Yapılacaklar / Devam Edilen ◐ (FAZ 6G güncel)
**Kod işi kalmadı — manuel go-live (kod dışı, kullanıcı tarafı):**
1. TLS sonlandıran reverse proxy/nginx
2. ALLOWED_HOSTS ve CSRF_TRUSTED_ORIGINS production değerleri
3. Günlük `db_yedekle` scheduler
4. BACKUP_OFFSITE_DIR
5. BACKUP_ENCRYPTION_KEY
6. Log collector + alerting
7. Gerçek production deployment ve smoke test
**(Tarihsel — tamamlandığı doğrulanan eski sıradakiler:** Cari/Finans/Muhasebe
ekranları, şantiye günlüğü, taşeron hakediş, İSG/kalite listeleri, RLS FORCE /
`emlak_app` geçişi yerine geçen TenantBaglamMiddleware + migration zinciri,
ÇŞİDB PDF parser / import API upload — faz kapsamlarında kapandı veya
bilinçli olarak backlogda bırakıldı. Eski metin aşağıda tarihsel olarak korunur.)
**Faza 3: Çekirdek Finans/Muhasebe Modülleri (Cari, Hesap, Finans) - SCALFOLDING TAMAMLANDI.**
1. **Cari (Bireysel/Kurumsal):** `Cari` (bireysel/kurumsal); `CariHareket` (borç/alacak, iptal deseni); `CariOzet` (Ana veri akışı).
2. **Muhasebe:** `HesapPlani` + `MuhasebeFisi` (borç==alacak `clean()`); `FisSatiri` (satır tutarı > 0, hem borç hem alacak olamaz); `Mizan` (Rapor).
3. **Finans:** `KasaBankaHesabi` + `FinansalIslem` (gelir/gider/transfer, iptal deseni); `PozPlan` ile entegrasyon (Gantt/S-eğrisi).
4. **Frontend (UI/UX):** Cari Hareketler, Genel Muhasebe Defteri, Mizan Raporu gibi arayüzler tasarlanacak ve entegre edilecek.

## Sırada ☐ (FAZ 6G: yukardaki 7 manuel go-live maddesi; kod sırasında iş yok.
Eski liste tarihsel olarak aşağıda korunur.)
1. **Cari/Finans/Muhasebe frontend ekranları:** (Bu adımı tamamladık - Scaffolded).
2. **roadmap Faz 2 kalanlar:** şantiye günlüğü, **taşeron hakediş ✅**, iş güvenliği/kalite listeleri (çekirdek ekran/API kapsamı)
3. **Prod Hazırlığı:** RLS FORCE geçişi: emlak_app rolü + komutlara tenant_baglam helper'ı.
4. **Operasyonel:** ÇŞİDB doğrudan PDF parser; import API upload endpoint'i.
### 2026-09-22 — Oturum 9: Migrasyon uzlaştırması (0021‑0026)
- Oluşturulan uyumlu migrasyon `0027_reconcile_missing_tables.py`.
- 0021‑0026 migrasyonları doğrudan `django_migrations` tablosuna kaydedildi.
- 0028 merge migrasyonu uygulandı.
- `showmigrations`, `check`, `makemigrations --check` temiz.
- Geliştirme DB şeması model ile senkron.
### 2026-09-23 — Oturum 10 (FAZ 6G): proje hafızası senkronu, salt-dokümantasyon
- Kod değişikliği YOK, migration YOK; yalnızca `memory-bank/`, `FAZ3A_KAPANIS_RAPORU.md`
  (tarihsel not) ve `FAZ6G_SENKRON_RAPORU.md` güncellendi.
- Doğrulama: `check` OK · `makemigrations --check` temiz · pytest
  `--ignore=frontend` 386 passed/exit 0 · `vue-tsc` temiz · Vitest yetki 5/5.
- Eski/yanlış kayıtlar (migration-YOK kararı, erişilemiyor denilen test DB,
  FAZ3A kırık-models.py, ara test sayıları) tarihsel olarak işaretlendi.
### 2026-09-23 — Oturum 11 (FAZ 7): go-live deployment provası — DÜZELTME GEREKLİ
- Operasyon (dev): 15 bekleyen migration uygulandı; db_yedekle + manifest/sha256 +
  db_restore round-trip + sistem_kontrol/smoke TAMAM; collectstatic 157 dosya.
- Bulgu: dev finance_fatura 10 kolon gerideydi → sqlmigrate çıktısıyla onarıldı
  (migration dosyası değişmedi); fatura smoke 500 → 200.
- HTTP smoke 8/8 yeşil; regression pytest 386 · vue-tsc 0 · vitest 13/13.
- Açık (kod dışı): prod ENV değerleri, BACKUP_OFFSITE_DIR/ENCRYPTION_KEY,
  prod MAILERS (mail.E001), scheduler aktivasyonu, TLS proxy, prod smoke.
- Rapor: `FAZ7_GO_LIVE_PROVA_RAPORU.md`. Kod değişikliği YOK, migration YOK.
### 2026-09-23 — Oturum 12 (FAZ 7A): production ENV finali — MANUEL KURULUM GEREKLİ
- ENV tablosu (fail-closed 3 + manuel 3); şifreli+off-site backup zinciri uçtan uca
  prova edildi (restore TAMAM, artefaktlar temizlendi).
- mail.E001: console MAILERS kaynağı, app e-posta göndermiyor → SMTP eklenmedi.
- Drift nedeni: toplu kayıt + V2 construction-only karşılaştırma; runbook yazıldı.
- Testler: check OK · deploy tek ERROR mail.E001 (security 0) · makemigrations temiz ·
  pytest 386 · vue-tsc 0 · vitest 13/13. Kod değişikliği YOK, migration YOK.
### 2026-09-23 — Oturum 13 (FAZ 7B): production runbook yazıldı (kod değişikliği YOK)
- `docs/PRODUCTION_RUNBOOK.md`: 10 bölüm + son kabul checklisti; placeholder'lı,
  secretsız, ek servisiz (Redis/PgBouncer yok).
### 2026-09-23 — Oturum 14 (FAZ 7B): Vercel + Supabase analizi — DÜZELTME GEREKLİ
- Vercel sıfır-config detection (docs 2026); CONN_MAX_AGE yok (=0, uygun).
- Kritik: 28 tabloda RLS + session GUC → Supabase DIRECT zorunlu, pooler yasak.
- sslmode OPTIONS kanıtlı; yedek harici koşucuya; Vercel Cron elendi; rewrite deploy günü.
- Testler: pytest 386 · vue-tsc 0 · vitest 13/13. Kod değişikliği YOK, migration YOK.
### 2026-09-23 — Oturum 15 (SON HAL E2E): GO (kod değişikliği YOK)
- runserver :8000 + vite :3000; 13 ekran × 2 viewport yeşil; API 200; yetkisiz 401;
  taşma yok; tek bulgu favicon 404 (kozmetik). Rapor: `SON_HAL_E2E_RAPORU.md`.
### 2026-09-23 — Oturum 16 (FAZ 7C): Vercel+Supabase checklist — DÜZELTME GEREKLİ
- 10 başlıklı `FAZ7C_VERCEL_SUPABASE_DEPLOY_CHECKLIST.md`; wsgi entrypoint,
  WhiteNoise yok, health yolları, 73 migration sayımı doğrulandı.
- check OK + makemigrations temiz (bu oturum). Kod YOK, migration YOK.
### 2026-09-23 — Oturum 17 (FAZ 7D): kontrollü deploy — DEPLOY DURDURULDU
- AŞAMA 1 yeşil (build exit 0, E2E tekrar: 85 API 200, taşma yok).
- AŞAMA 5 kapısı: Vercel/Supabase erişimi yok → deploy başlatılmadı.
- Rapor: `FAZ7D_DEPLOY_RAPORU.md` (10 bölüm + 6 unblock maddesi).
### 2026-09-23 — Oturum 18 (FAZ 7E): local final — GO
- 10/10 iş akışı + finansal tutarlılık (2000/400/2400, stok net 0).
- Tek düzeltme: favicon. Testler: 386 · vue-tsc 0 · 13/13 · E2E sıfır hata.
### 2026-09-23 — Oturum 19 (FAZ 7F): release freeze — GO
- Git yok (mtime ile doğrulandı); favicon dışı kod değişikliği yok; migration 6F'den.
- Testler: check OK · 386 · makemigrations temiz · vue-tsc 0 · 13/13. E2E tekrarlanmadı (kanıt güncel).
### 2026-09-23 — Oturum 20 (FAZ 7G): menü envanteri — FREEZE KALDIRILMALI (A kapsamı)
- 38 link: 32 TAMAM · 5 PLACEHOLDER · 1 404 (Malzemeler: route/component yok, API var).
- 5 Yakında bilinçli placeholder; /dashboard ölü linki yan bulgu. Kod değişmedi.
### 2026-09-23 — Oturum 21 (FAZ 7H): A maddesi tamam — GO
- MalzemelerView + route + hazir:true + /dashboard→/ (3 dosya).
- Testler: check OK · 386 · makemigrations temiz · vue-tsc 0 · 13/13.
- Browser 11 adım yeşil, 0 hata. Backend/migration değişmedi.
### 2026-09-23 — Oturum 22 (FAZ 7Q): profil + şifre değiştirme
- `PasswordChangeView` + route + 6 test + ProfilView + hub kartı.
- Testler: check OK · 392 · makemigrations temiz · vue-tsc 0 · 13/13.
- Browser yeşil; e2e-satin parolası `Yeni-Sifre-789` (dev). Migration YOK.
### 2026-09-23 — Oturum 23 (FAZ 7R): stok hesap eşleme tamam
- Serializer + ViewSet + URL + 8 test + ekran + route + hub kartı.
- Duplicate 400 validasyonu; tekil browser DELETE 500 tekrarlanamadı (3×204).
- Testler: check OK · 400 · makemigrations temiz · vue-tsc 0 · 13/13.
### 2026-09-24 — Oturum 24 (FAZ 8E): 2 MEDIUM kapandı
- Stok Transfer/Tüketim/İade UI + ProjeMalzeme teklif/tedarikçi modalları.
- Browser 5 akış yeşil, 0 hata. Backend/migration değişmedi.
### 2026-10-01 — Oturum 25 (FAZ 8H): 3 LOW düzeltmesi
- Fatura tr-TR tarih; Muhasebesiz açıklaması; iade spesifik hata mesajı.
- Testler: check OK · 400 · makemigrations temiz · vue-tsc 0 · 13/13 · build OK.
