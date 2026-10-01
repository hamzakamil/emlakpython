# FAZ 3A — SATIN ALMA ÇEKİRDEĞİ İMPLEMENTASYON RAPORU

**Tarih:** 2026-09-22
**Kapsam:** SatınAlmaTalebi / SatınAlmaTalebiKalemi / SatınAlmaSiparisi / SatınAlmaSiparisiKalemi
**Kapsam dışı (yazılmadı):** MalKabul, StokHareketi, depo, malzeme tüketimi, gerçek maliyet, stok değerleme, yeni fatura/cari/muhasebe modeli, FAZ 3B kodu.

---

## 1. MİMARİ UYUM

- Yeni `purchasing` uygulaması; desenler birebir kopyalandı: `TenantScopedViewSet` (tenants/api.py), `TenantAwareModelSerializer`, `IsConstructionEditor` kalıbında `IsPurchasingEditor`, `@action` + `transaction.atomic` + `select_for_update` (kazanan-sec / hakedis_onayla), destroy→iptal/arşiv (Hakedis/TedarikciTeklifi), `toplam_tutar` save() hesabı, `CheckConstraint`/`UniqueConstraint`, zarf renderer (otomatik).
- Durum makineleri `finance/services/state_machine.py` `fatura_durum_gecis` kalıbında (geçiş haritası + satır kilidi + ValidationError).
- Mevcut muhasebe/cari/fatura/banka/kasa koduna dokunulmadı; sipariş onayı muhasebe fişi üretmez.
- Yeni model icadı yok: Proje, Poz, Malzeme, Mahal, Tedarikci, TedarikciTeklifi, users.User, tenant yapısı kullanıldı.
- Frontend: Vue 3 + TS + Pinia(auth) + vue-router + axios + crudFactory + useKayitListesi + VeriTablosu/Sayfalama/KayitModal + Tailwind ortak sınıflar. Yeni framework/state eklenmedi.

## 2. DEĞİŞTİRİLEN DOSYALAR

**Yeni (backend):**
- `purchasing/__init__.py`, `purchasing/apps.py`, `purchasing/models.py`, `purchasing/services.py`, `purchasing/serializers.py`, `purchasing/views.py`, `purchasing/urls.py`, `purchasing/permissions.py`, `purchasing/admin.py`, `purchasing/tests.py`, `purchasing/migrations/__init__.py`
- `purchasing/migrations/0001_initial.py` (oluşturulan migration — aşağıya bak)

**Düzenlenen (backend, minimal):**
- `config/settings/base.py` — INSTALLED_APPS'e `purchasing` eklendi
- `config/urls.py` — `/api/v1/purchase-requests/` + `/api/v1/purchase-orders/` route kaydı
- `tenants/middleware.py` — AUDIT_MODELS'e `purchasing.SatinAlmaTalebi`, `purchasing.SatinAlmaSiparisi` eklendi (Kural 36)

**Yeni (frontend):**
- `frontend/src/types/satinAlma.ts`, `frontend/src/services/satinAlmaApi.ts`
- `frontend/src/views/satinalma/TaleplerView.vue` (liste + oluşturma/düzenleme + onay/red/iptal + dönüşüm)
- `frontend/src/views/satinalma/TalepDetay.vue` (detay + kalemler + teklif seçimi + onay)
- `frontend/src/views/satinalma/SiparislerView.vue` (liste + oluşturma/düzenleme + onay)
- `frontend/src/views/satinalma/SiparisDetay.vue` (detay + sabit fiyatlı kalemler)

**Düzenlenen (frontend, minimal):**
- `frontend/src/router/index.ts` — 4 route (`talepler`, `talep-detay`, `siparisler`, `siparis-detay`)
- `frontend/src/layouts/AppLayout.vue` — SATIN ALMA menü grubu
- `frontend/src/config/menuHelp.ts` — 2 yardım kaydı

## 3. OLUŞTURULAN MIGRATION

- `purchasing/migrations/0001_initial.py` — 5 model (4 kapsam modeli + `BelgeNumaraSayaci`) + 5 constraint (2 unique belge no, 1 sayaç unique, 2 check). Normal `makemigrations` ile üretildi; dev DB'ye normal `migrate` ile uygulandı (`Applying purchasing.0001_initial... OK`). `--fake` yok.
- Mevcut app'lerde migration değişikliği yok.

## 4. ÖNEMLİ KARARLAR

- **Merkezi belge no:** Projede merkezi servis yoktu; `purchasing/services.belge_numarasi_uret` tek uygulama noktasıdır (tenant+yıl+tip sayaç, `atomic`+`select_for_update`, format `ST-YYYY-NNNN` / `SS-YYYY-NNNN`, unique constraint ikinci güvence). Modellerde ayrı numara mantığı yok.
- **Fiyat snapshot:** `birim_fiyat` dönüşüm anındaki teklif fiyatıdır; test ile kilitlendi (teklif 100→999 değişiminde sipariş kalemi 100.00 kalır). Ek snapshot alanı eklenmedi.
- **Çift dönüşüm engeli:** `durum==ONAYLANDI` zorunluluğu + aktif kaynak kontrolü + `select_for_update` (yarışta ikinci işlem SIPARISE_DONUSTU görür).
- **Soft delete:** destroy→durum IPTAL (talep: siparişe dönüşmüş hariç; sipariş: tamamlanmış hariç); kalem destroy→`is_active=False` (taslak ebeveynde). Fiziksel silme yok.
- **Yetki:** `IsPurchasingEditor` = construction seti + FINANS/MUHASEBE (frontend `yetki.ts` ile uyumlu; istenirse daraltılabilir — risklere bak).
- **Kalemde `proje` yok:** başlıktan alınır; `mahal.proje` ve `secili_teklif` (tenant/proje/malzeme) uyumu model `clean()` + serializer'da çift katmanlı.

## 5. TEST SONUÇLARI

- `python manage.py check` → **no issues (0 silenced)**
- `python manage.py makemigrations --check --dry-run` → **No changes detected**
- `python manage.py test --noinput` → **toplam 208, passed 208, failed 0, skipped 0 — OK** (193 mevcut + 15 yeni purchasing; skip/xfail yok)
- pytest (`--ignore=frontend`, `--no-migrations` yok) → **209 test, failure/error işareti yok**
- `purchasing/tests.py` 15 test kapsar: talep/kalem oluşturma, tenant izolasyonu, tenant-dışı kaynak reddi, teklif seçimi + uyumsuz teklif reddi, onay akışı + geçersiz geçiş, ret, iptal (fiziksel silme yok), okur-yazamaz yetkisi, dönüşüm, ikinci dönüşüm engeli, onaysız dönüşüm engeli, fiyat snapshot korunumu, numara benzersizliği, sipariş oluşturma+onay.
- Frontend `npm run type-check` (`vue-tsc --noEmit`) → **hatasız**.

## 6. RİSKLER / NOTLAR

1. **Yetki genişliği:** FINANS/MUHASEBE yazabilir (construction backend'de yazamaz). Bilinçli seçim; istenirse `purchasing/permissions.py` EDITOR_ROLES daraltılır.
2. **KISMI_TESLIM/TAMAMLANDI geçişleri** tanımlı ama tetikleyen endpoint/aksiyon yok — FAZ 3B (MalKabul) sürükleyecek.
3. **Çift dönüşüm koruması** uygulama-seviyesi kontroldür (`kaynak_talep` nullable olduğundan DB unique yok); `select_for_update` yarışı kapatır.
4. `TalepDetay.vue` içinde iki `onMounted` bloğu var (çalışır, ancak tek blokta birleştirilebilir — kozmetik).
5. `0027_reconcile_missing_tables` zincirde duruyor (zararsız no-op, V2 raporu); FAZ 3A onu değiştirmedi.
6. Stok/depo ekranı yapılmadı (kapsam dışı).
