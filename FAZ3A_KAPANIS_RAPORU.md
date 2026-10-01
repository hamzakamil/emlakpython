# FAZ 3A KAPANIŞ RAPORU

> **FAZ 6G TARİHSEL NOTU (2026-09-23, salt-dokümantasyon — kod değişikliği YOK):**
> Bu raporun gövdesi, yazıldığı andaki (FAZ 3B taslağının `purchasing/models.py`
> dosyasını bozduğu) durumu anlatır ve **tarihsel olarak korunur**. Altında
> anlatılan kırık durum **çözülmüştür** — kod ağacından doğrulandı:
> `purchasing/models.py` içe aktarılıyor; purchasing migration zinciri
> 0001→0004 mevcut; `manage.py check` OK; `makemigrations --check` temiz;
> `pytest --ignore=frontend` 386 passed/exit 0. Harici taslak için öngörülen
> `Depo/MalKabul/MalKabulKalemi/StokHareketi` modelleri artık resmi zincirin
> parçasıdır (0002 + 0003 `StokHesapEsleme` + 0004 KDV). Güncel durum için:
> `memory-bank/` + `FAZ6G_SENKRON_RAPORU.md`.

**Kapanış türü:** KOŞULLU — FAZ 3A kodu doğrulandı, ancak doğrulama penceresi içinde harici bir FAZ 3B müdahalesi tespit edildi (detay: "FAZ 3A Değişiklik Durumu"). Bu görevde **kod değiştirilmedi, migration üretilmedi, refactor/temizlik yapılmadı.**

## Migration Durumu

- `purchasing/migrations/0001_initial.py` **değiştirilmedi** (mtime 22.09 02:35:17, boyut 12415 — FAZ 3A bitim değeriyle aynı).
- Yeni migration üretilmedi; `purchasing/migrations/` içinde 0001 dışında dosya yok.
- `0027_reconcile_missing_tables` ve sonrası zincire dokunulmadı.
- Dev DB `showmigrations purchasing`: `[X] 0001_initial` (FAZ 3A oturumunda normal `migrate` ile uygulanmıştı).
- **Güncel uyarı:** `purchasing/models.py` içine haricen eklenen `Depo/MalKabul/MalKabulKalemi/StokHareketi` modellerinin migration'ı yoktur. Dosya içe aktarılamadığı için (`NameError`, aşağıya bak) `makemigrations --check` şu an çalışmıyor; engel kalkınca ilk `makemigrations` bu 4 model için 0002 üretecektir (bu görevde üretilmedi).

## Backend Testleri

Pristine (FAZ 3A bitim durumu) ağaç üzerinde, bu oturumda alındı:

- `python manage.py check` → **System check identified no issues (0 silenced).**
- `python manage.py makemigrations --check --dry-run` → **No changes detected.**
- `python manage.py test --noinput` → **toplam 208, passed 208, failed 0, skipped 0 — OK** (193 mevcut + 15 purchasing; skip/xfail yok). Koşu öncesi test DB sıfırdan 0001→0028+purchasing 0001 ile kuruldu, koşu sonu yok edildi.
- `pytest --ignore=frontend` → **pristine ağaçta tamamlanamadı**: koşu anında `purchasing/models.py` harici ekleme nedeniyle önce `IndentationError` (satır 512), ardından tamamlanan ekleme nedeniyle `NameError` verdi. Önceki FAZ 3A oturumunda pytest 209 test, failure/error yok idi.
- Güncel ağaçta Django komutlarının tamamı (`check/test/migrate/pytest`) aynı `NameError` ile düşüyor; bu, FAZ 3A kodunun değil harici ekin kusurudur.

## Frontend Testleri

- `npm run type-check` (`vue-tsc --noEmit`) → **hatasız** (bu oturumda, güncel ağaçta alındı; frontend dosyalarına harici dokunuş yok).
- Mevcut ekranlar: `TaleplerView` (liste+oluşturma/düzenleme+onay/red/iptal+dönüşüm), `TalepDetay` (kalemler+teklif seçimi+onay), `SiparislerView`, `SiparisDetay`; tipler `types/satinAlma.ts`, istemci `services/satinAlmaApi.ts`; router'da 4 route, AppLayout'ta SATIN ALMA grubu, menuHelp'te 2 kayıt. Hiçbiri bu görevde değiştirilmedi.

## FAZ 3A Değişiklik Durumu

**Bu görevde FAZ 3A koduna dokunulmadı** (model, migration, endpoint, state kuralı, ekran — tamamı salt-okunur incelendi).

**Tespit (yasak ihlali — dış kaynaklı):** Doğrulama penceresi içinde `purchasing/models.py` dosyasına FAZ 3B taslağı eklendi:

- Kanıt: boyut 13856 → 26416, mtime 02:35:17 → 02:53:17; 402. satırdan itibaren `# FAZ 3B — Mal Kabul + Stok Hareketi` başlığı; `Depo`, `MalKabul`, `MalKabulKalemi`, `StokHareketi` sınıfları; `BelgeTipi`/`BELGE_ONEKLERI` bloklarının dosyada **ikinci kez** tanımlanması (`MAL_KABUL` değeriyle).
- Dosya önce eksik gövdeyle (`IndentationError`), sonra bitmiş ama hatalı haliyle (`MalKabul.Meta` içinde `Durum` görünmediği için `NameError`) bırakıldı. Sonuç: Django import zinciri kırık, proje çalışmıyor.
- Bulaşma tek dosyayla sınırlı (repo genelinde `MalKabul|StokHareketi|class Depo` araması yalnızca bu dosyada eşleşti). Frontend, migration'lar, muhasebe/cari/fatura, tenant/auth dokunulmamış.
- Düzeltme (ekin geri alınması) **bilinçli olarak yapılmadı**: git yok — silme geri alınamaz şekilde чужой çalışmayı yok ederdi; ayrıca yasak metni model değişikliğini açıkça men ediyor. Karar kullanıcıya bırakıldı (Riskler).

## Mevcut Satın Alma Veri Akışı

(Kilitli FAZ 3A davranışı — değişiklik yok.)

- `SatinAlmaTalebi` (talep_no `ST-YYYY-NNNN`, TASLAK→ONAYA_GONDERILDI→ONAYLANDI/REDDEDILDI→SIPARISE_DONUSTU/IPTAL) + `SatinAlmaTalebiKalemi` (proje başlıktan; `secili_teklif` tenant/proje/malzeme uyumlu).
- Onaylı talep → `talepten_siparis_olustur` (atomic + select_for_update; tek seferlik; tedarikçi birliği zorunlu) → `SatinAlmaSiparisi` (siparis_no `SS-YYYY-NNNN`, TASLAK→ONAY_BEKLIYOR→ONAYLANDI→KISMI_TESLIM/TAMAMLANDI/IPTAL) + `SatinAlmaSiparisiKalemi` (`birim_fiyat` snapshot, `toplam_tutar` otomatik).
- Endpointler: `/api/v1/purchase-requests/`, `/api/v1/purchase-request-items/`, `/api/v1/purchase-orders/`, `/api/v1/purchase-order-items/` (+ `onaya-gonder/onayla/reddet/iptal-et`, `talepten-siparis-olustur`).
- Tenant izolasyonu `TenantScopedViewSet`; yetki `IsPurchasingEditor`; destroy→iptal/arşiv (fiziksel silme yok); audit `AUDIT_MODELS` içinde 2 purchasing başlığı; sipariş bu fazda muhasebe fişi üretmez.

## FAZ 3B'ye Devredilen Konular

Kod yazılmadı; yalnızca devir noktaları:

1. `SatinAlmaSiparisi.Durum` içinde `KISMI_TESLIM/TAMAMLANDI` tanımlı ama tetikleyen akış yok — MalKabul onayları sürecek.
2. `SatinAlmaSiparisiKalemi.birim_fiyat/toplam_tutar` kabul maliyetinin kaynağı (snapshot zinciri hazır).
3. `kaynak_talep` izlenebilirliği ve `BelgeNumaraSayaci` altyapısı (`MK-` tipi sayaç için genişletilebilir yapı mevcut — `BelgeTipi`/`BELGE_ONEKLERI` tek nokta).
4. Harici taslakta öngörülen akış (uygulanmadı, yalnızca tespit): `SatinAlmaSiparisi → MalKabul (kabul/red miktarı) → StokHareketi (GİRİŞ, maliyet snapshot) → Stok (türetilmiş bakiye; taslakta ayrı Stok tablosu yok)`.
5. Önkoşul: `purchasing/models.py` dosyasındaki harici ekin akıbeti netleşmeden FAZ 3B başlamamalı (Riskler).

## FAZ 3B Öncesi Mevcut Stok Yapısı

- **Stok modeli yok.** Depo modeli yok. Mal kabul modeli (migration'lı) yok.
- **Stok hareket modeli (lojistik) var:** `construction.MalzemeHareketi` (TenantAwareModel + is_active) — `proje, malzeme, yon (giris/cikis), miktar Decimal(14,4), birim, qr_kodu, gerceklesme_zamani, kaydeden→User, notlar`. Stok bakiyesi modelde tutulmaz; giriş−çıkış toplamıyla türetilir.
- **Malzeme–stok ilişkisi:** `construction.Malzeme` kartında miktar/bakiye alanı yok (`malzeme_kodu, ad, birim, ts_no, qr_kodu` + unique'ler). `PozMalzemeIliskisi` ihtiyaç miktarını (birim başına), `ProjeMalzeme` projeye özel tedarik bağlamını tutar.
- **Birim yapısı:** serbest `CharField(20)`; kalemler boşsa malzemeden devralır (`save()` içinde). Birim dönüşüm tablosu yok.
- **Miktar hesaplama:** `toplam_tutar = miktar × birim_fiyat` (sipariş kalemi, 2 ondalık); miktarlar 4 ondalık, `MinValueValidator` + check constraint korumalı.
- **Proje/depo/malzeme:** depo kavramı yok; hareketler `proje + malzeme` ekseninde. `Mahal.proje` (CASCADE) ve kalemlerdeki `poz/mahal` (PROTECT, opsiyonel) bağlamı mevcut.
- **Audit/tenant:** tüm hareket modelleri `TenantAwareModel` + `is_active`; middleware POST/PUT/PATCH/DELETE'i `AUDIT_MODELS` kapsamında loglar.

## Riskler

1. **Kilitli dosyaya harici yazım (gerçekleşti):** `purchasing/models.py` FAZ 3B taslağıyla bozuldu; proje şu an import edilemiyor. Git yok — geri alma risksiz değil. **Öneri:** ekin sahibi netleştirilmeden FAZ 3B başlatılmasın; ya ek ayrı branch'e taşınsın ya da FAZ 3B resmi başlangıcıyla birlikte dosya onarılıp 0002 migration'ı üretilsin. Bu görevde ikisi de yapılmadı.
2. **Eşzamanlı yazım riski:** ek, doğrulama sırasında tamamlandı — aynı anda başka bir yazıcı aktif olabilir. Kilitli dosyalara yazan süreçler durdurulmadan doğrulama tekrarı anlamsız.
3. **Karar ihtiyacı:** (a) harici ek geri alınsın mı (FAZ 3A pristine kilitlensin), (b) ek FAZ 3B başlangıcı sayılıp onarılsın mı? Karar verilmeden `makemigrations --check`/test/pytest yeşile dönemez.
4. Önceki bilinen notlar geçerli: `IsPurchasingEditor` FINANS/MUHASEBE'yi yazar sayar; çift-dönüşüm koruması uygulama seviyesindedir; `0027` zincirde no-op durur.
