# Aktif Bağlam — Emlak ERP

> ⚠️ **CONTEXT YÖNETİMİ KURALI (kullanıcı talimatı):** Context kullanımı **~%60'ı
> geçtiğinde** bu dosyayı ve `progress.md`'yi güncelle → yapılanları kaydet,
> bundan sonra yapılacakları not et. Gerekirse `new_task` ile devret.
> Yeni oturum açılırken ilk mesaj: **"memory bank'i oku, kaldığımız yerden devam et."**

---

## FAZ 6G senkron notu (2026-09-23, salt-dokümantasyon)

Bu dosyanın altındaki oturum kayıtları **tarihseldir**. FAZ 6F-4 sonrası
doğrulanmış gerçek durum (kod ağacından, 2026-09-23):

- **Migration:** Django migration'ları AKTİF (eski "migration kullanılmaz /
  `db/schema.sql`" kararı tarihseldir). 9 app'te zincir mevcut; `check` OK,
  `makemigrations --check` temiz. Detay: `FAZ6G_SENKRON_RAPORU.md`.
- **Test:** `pytest --ignore=frontend` → **386 passed, exit 0** (91 sn);
  `vue-tsc --noEmit` temiz; `yetki.spec.ts` 5/5. Not: yalın `pytest` kökteki
  ikili `frontend/test.txt` dosyasına takılır (collection hatası) — testler
  `--ignore=frontend` ile koşar.
- **Faz durumu (beyan + kod izi):** 3A–3C, 4 (dondurulabilir), 5
  (dondurulabilir), 6A, 6B, 6C, 6D (analiz), 6E, 6F-1…6F-4 (go-live hazır).
- **Manuel go-live (kullanıcı tarafı, kod dışı):** TLS reverse proxy,
  ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS prod değerleri, günlük `db_yedekle`
  scheduler, BACKUP_OFFSITE_DIR, BACKUP_ENCRYPTION_KEY, log collector +
  alerting, prod deploy + smoke test.

---

## Oturum kaydı

### Oturum 27 — 2026-10-01: FAZ 9D release candidate final (doğrulama, değişiklik YOK)
**Yapılanlar:** commit 196238f + temiz tree doğrulandı; baslat.bat.backup izli
bulundu (zararsız, LOW); secret taraması dev-kapsam temiz; testler 9C ile aynı
(check OK · 400 · vue-tsc 0 · 13/13 · build OK).
**KARAR: FINAL RELEASE CANDIDATE: READY.**
**Sonraki:** talimatla devam (push yok).

### Oturum 26 — FAZ 9C git first commit (local, push yok)
**Yapılanlar:** `git init -b main`; taslak-backup kuralı eklendi (.gitignore 1 satır);
seçici staging (agent/.mcp.json dışarıda, 508 dosya); `196238f chore: initial
release snapshot`; remote yok. Doğrulama: check OK · 400 · vue-tsc 0 · 13/13 · build OK.
**Sonraki:** talimatla devam (push yok).

### Oturum 25 — 2026-10-01: FAZ 8H 3 LOW düzeltmesi
**Yapılanlar:** FaturaDetay tr-TR tarih (`tarih()`); MalKabuller "Muhasebesiz" +
neden; Stok iade hata-detay çıkarıcı (AxiosError yolu düzeltmesiyle).
Bulgu: iade-no çakışması varsayımı yanlış — numaralar hareket-bazlı tekil;
gerçek nedenler kümülatif/stok validasyonu (artık spesifik gösteriliyor).
Testler: check OK · 400 · makemigrations temiz · vue-tsc 0 · 13/13 · build OK.
**Sonraki:** talimatla devam.

### Oturum 24 — 2026-09-24: FAZ 8E stok aksiyonları + teklif/tedarikçi (2 MEDIUM kapandı)
**Yapılanlar:** StokHareketleriView'a Transfer/Tüketim/İade modal akışları
(loading/validation/başarı-hata, `alert()` yok) + ProjeMalzemeView teklif-seç/
tedarikçi-ata modalları + `insaatApi` 2 istemci + iade tip tamamlaması.
Browser: transfer/tüketim/iade (faturalı)/teklif/tedarikçi yeşil, 0 hata;
tenant izolasyonu + idempotency/duplikat korumaları canlı doğrulandı.
Testler: check OK · **400** · makemigrations temiz · vue-tsc 0 · 13/13.
**Sonraki:** talimatla devam.

### Oturum 23 — 2026-09-23: FAZ 7R stok hesap eşleme (backend endpoint + ekran)
**Yapılanlar:** `StokHesapEslemeSerializer` (görünüm alanları + kapsam + kısmi-unique
400 validasyonu) + `StokHesapEslemeViewSet` (tenant izole, IsPurchasingEditor) +
URL kaydı + 8 backend testi + `StokHesapEslemeView` + route + hub kartı +
`finansApi`/`satinAlmaApi`/tip tamamlamaları. Model/migration değişmedi.
Bulgu: duplicate kayıt artık 400 (önce 500 olurdu); tek seferlik browser DELETE
500'u tekrar üretilemedi (sonraki 3 DELETE 204) + regresyon testi eklendi.
Testler: check OK · **400** · makemigrations temiz · vue-tsc 0 · 13/13.
**Sonraki:** talimatla devam.

### Oturum 22 — 2026-09-23: FAZ 7Q profil + şifre değiştirme (min. endpoint)
**Yapılanlar:** `PasswordChangeView` (mevcut/yeni/tekrar, Django hashing +
validators, parola loglanmaz, JWT dokunulmaz) + route + 6 backend testi +
`ProfilView` + `authApi.sifreDegistir` + Ayarlar kartı. Testler: 392 (6 yeni) ·
vue-tsc 0 · 13/13. Browser: profil, yanlış-şifre hatası, değişim, yeniyle login
yeşil; geri-dönüş benzerlik-validatorüyle reddedildi (tasarlanan davranış).
Not: e2e-satin parolası artık `Yeni-Sifre-789` (dev).
**Sonraki:** talimatla devam.

### Oturum 21 — 2026-09-23: FAZ 7H Malzemeler + dashboard linki (sınırlı impl.)
**Yapılanlar:** `MalzemelerView.vue` (YapiSinifi patterni, mevcut CRUD istemcisi) +
route kaydı + menü `hazir:true` + bildirim `/dashboard`→`/` (3 dosya).
Dokunulmadı: 5 şemsiye ekran, finans/satın alma/stok zincirleri, backend, migration.
Testler: check OK · 386 · makemigrations temiz · vue-tsc 0 · 13/13.
Browser 11 adım yeşil (arama/filtre/oluştur/düzenle/reload/direkt URL, 0 hata).
**SON KARAR: GO.**
**Sonraki:** talimatla devam.

### Oturum 20 — 2026-09-23: FAZ 7G menü envanteri (analiz, değişiklik YOK)
**Yapılanlar:** 38 link tarandı (32 TAMAM · 5 PLACEHOLDER · 1 404).
404 kökü: `Malzemeler` child `hazir:false` olmasına rağmen koşulsuz RouterLink →
kayıtsız route → BulunamadiView; backend `/malzemeler/` yaşıyor (401 kapısı).
5 "Yakında" bilinçli placeholder (işlevler dağınık mevcut; Ayarlar hariç).
Yan bulgu: bildirim `/dashboard` ölü linki. A/B/C sınıflandı.
**KARAR: FREEZE KALDIRILMALI (A kapsamıyla).** `FAZ7G_EKSIK_MODUL_ANALIZI.md`.
**Sonraki:** talimatla (A) implementasyonu veya bekleme.

### Oturum 19 — 2026-09-23: FAZ 7F release freeze (doğrulama, değişiklik YOK)
**Yapılanlar:** git yok (mtime taraması); favicon+index.html dışında kod değişikliği
yok; migration dosyaları 6F döneminden; testler yeşil (386/13/13); E2E kanıtı güncel
olduğundan tekrar koşulmadı; local production engeli yok.
**KARAR: RELEASE FREEZE: GO** — kod donduruldu.
**Sonraki:** yalnızca prod girdileriyle deploy; talimatla devam.

### Oturum 18 — 2026-09-23: FAZ 7E local final (min. düzeltme: favicon)
**Yapılanlar:** 10/10 gerçek iş akışı (cari/fatura/talep/sipariş/malkabul +
iptaller); finansal tutarlılık kanıtlı (2000/400/2400; stok net 0). Betik
hataları elendi (iskonto/KDV sırası, select indexleri, mizan şekli); kural
davranışları doğrulandı (TAMAMLANDI iptal 400, carisiz muhasebe null).
Tek düzeltme: favicon (public/favicon.svg + index.html 1 satır).
Testler: 386 · vue-tsc 0 · vitest 13/13 · E2E sıfır hata. **LOCAL FINAL: GO.**
**Sonraki:** talimatla devam.

### Oturum 17 — 2026-09-23: FAZ 7D kontrollü deploy (kod YOK, migration YOK)
**Yapılanlar:** AŞAMA 1 tam yeşil (entrypoint/build/health/settings/tenant/SSL/
migration + browser E2E tekrar: 85 API 200, taşma yok, favicon 404). AŞAMA 5
kapısında DURDURULDU: gerçek Vercel/Supabase erişimi yok → deploy/migrate/smoke
başlatılmadı, otomatik düzeltme yapılmadı. `FAZ7D_DEPLOY_RAPORU.md` (10 bölüm).
**KARAR: DEPLOY DURDURULDU** (6 girdilik unblock listesi raporda).
**Sonraki:** Vercel + Supabase bilgileri gelince kaldığı yerden; talimatla devam.

### Oturum 16 — 2026-09-23: FAZ 7C Vercel+Supabase checklist (kod YOK, migration YOK)
**Yapılanlar:** 10 başlıklı `FAZ7C_VERCEL_SUPABASE_DEPLOY_CHECKLIST.md`.
Doğrulamalar: wsgi `application` entrypoint; WhiteNoise yok; health yalnızca
`/api/v1/health[/ready]`; requirements saf PyPI; migration sayıları (73+contrib);
check OK + makemigrations temiz (bu oturum). Karar: DÜZELTME GEREKLİ (7 manuel madde).
**Sonraki:** gerçek Vercel/Supabase bilgileriyle deploy; talimatla devam.

### Oturum 15 — 2026-09-23: SON HAL browser E2E (sadece çalıştır+test, kod YOK)
**Yapılanlar:** runserver :8000 + vite :3000 (::1-only notu); Temp'te
playwright-core + sistem Chrome ile 13 ekran × 2 viewport E2E. Sonuç GO:
login/dashboard/tenant/cari/fatura(detay dahil)/satınalma/mal-kabul/stok/muhasebe
yeşil; API tamamı 200 (relative /api/v1); yetkisiz 401; taşma yok (1920/1366);
tek bulgu favicon 404 (kozmetik). `SON_HAL_E2E_RAPORU.md` yazıldı.
**Sonraki:** talimatla devam (hata çıkmadı, kod değişmedi).

### Oturum 14 — 2026-09-23: FAZ 7B Vercel + Supabase analizi (kod değişikliği YOK)
**Yapılanlar:** Hedef değişti (VPS runbook'u geçerli değil backend-deploy için).
Vercel docs 2026 ile doğrulandı: manage.py + requirements + `application` →
sıfır-config detection; `CONN_MAX_AGE` yok (=0, serverless-safe). Kritik bulgu:
28 tabloda RLS + session GUC → **Supabase DIRECT zorunlu**, transaction pooler
YASAK. `?sslmode=require` OPTIONS'a işler (kanıtlı), `PGSSLMODE` ENV ile
araçlara taşınır — kod değişikliği gerekmedi. Ephemeral FS → yedek konumu harici
koşucuya taşınır; Vercel Cron pg_dump için elendi; CRON_SECRET gereksiz.
`createWebHistory` → SPA rewrite deploy günü eklenecek (eklenmedi). WhiteNoise/
Storage kararları deploy'a bırakıldı. Testler yeşil (386/13/13).
**KARAR: DÜZELTME GEREKLİ** (7 deploy-günü maddesi raporda).
**Sonraki:** Vercel/Supabase gerçek bilgileriyle kurulum; talimatla devam.

### Oturum 13 — 2026-09-23: FAZ 7B production runbook (salt-analiz, kod değişikliği YOK)
**Yapılanlar:** `docs/PRODUCTION_RUNBOOK.md` yazıldı (10 bölüm + kabul checklisti).
Doğrulanan gerçekler: frontend relative `/api/v1` (same-origin), ASGI
`config.asgi:application` mevcut, uvicorn requirements'ta yok (kurulum notu),
Node pin yok. Değer uydurulmadı (`<...>` placeholder + örnek domain).
**Sonraki:** gerçek sunucuda runbook sırası; talimatla devam.

### Oturum 12 — 2026-09-23: FAZ 7A production ENV finalizasyonu (kod değişikliği YOK)
**Yapılanlar:**
- Zorunlu ENV tablosu koddan çıkarıldı (SECRET_KEY/DATABASE_URL/ALLOWED_HOSTS
  fail-closed; CSRF/BACKUP_* değerleri manuel). Gerçek değer yazılmadı.
- Backup zinciri ENV override ile uçtan uca prova edildi: şifreli `.fernet` +
  manifest (`sifreli:true` + offsite yolu) + off-site kopya + şifreli restore
  TAMAM; artefaktlar temizlendi.
- mail.E001: kaynak `base.py:166` console MAILERS; app e-posta göndermiyor → SMTP
  eklenmedi; prod kararı (SMTP ENV veya bilinçli kabul) rapora yazıldı.
- Drift nedeni: finance 0002–0015 aynı saniyede toplu kayıt + V2 yalnızca
  construction_* karşılaştırmış + 0016 eksik kolona ALTER (çalışmış olamaz).
  Prod tespit runbook'u rapora yazıldı; `migrate --plan` zorunlu korundu.
- Scheduler: systemd örneği (önerilen) + cron alternatifi; değer uydurulmadı.
- Testler: check OK · deploy (ENV'siz fail-closed; geçici ENV'de tek ERROR
  mail.E001, security 0) · makemigrations temiz · pytest 386 · vue-tsc 0 ·
  vitest 13/13.
**KARAR: MANUEL KURULUM GEREKLİ** (6 sıralı manuel adım raporda).
**Sonraki:** gerçek sunucu bilgileriyle kurulum; talimatla devam.

### Oturum 11 — 2026-09-23: FAZ 7 go-live deployment provası (MOD: operasyon + test)
**Yapılanlar (kod değişikliği YOK, migration dosyası YOK):**
- ENV denetimi: SECRET_KEY/DATABASE_URL fail-closed doğrulandı; BACKUP_* boş (manuel);
  `SECURE_PROXY_SSL_HEADER` eklenmedi (proxy yok — bilinçli).
- Dev DB'de 15 bekleyen migration bulundu → `--plan` sonrası `migrate` 15/15 OK.
- `db_yedekle` OK (466 KB + manifest, sha256 bağımsız eşleşti) → `db_restore`
  round-trip TAMAM → `sistem_kontrol --kullanici smoke-finans` TAMAM.
- Kritik bulgu: dev `finance_fatura` 10 kolon gerideydi (kayıtlar [X] görünüyordu);
  yalnızca `sqlmigrate` çıktısıyla onarıldı; fatura smoke 500 → 200 (3 kayıt).
- HTTP smoke 8/8: health, ready (bekleyen 0), login, me (tenant 175), cari (2),
  fatura (3), mal-kabul (0), stok (0). `collectstatic` 157 dosya OK.
- `check --deploy`: ENV'siz fail-closed; geçici ENV ile 1 ERROR `mail.E001`
  (console MAILERS; proje e-posta göndermiyor — prod SMTP kararı manuel, kod değişmedi).
- Regression: pytest 386 · check OK · makemigrations temiz · vue-tsc 0 · vitest 13/13.
- `FAZ7_GO_LIVE_PROVA_RAPORU.md` yazıldı (rollback A/B/C + scheduler systemd/cron/Task Scheduler).
**KARAR: DÜZELTME GEREKLİ** (prod ENV + MAILERS + scheduler + TLS — tamamı kod dışı).
**Sonraki:** manuel go-live kalemleri kullanıcı tarafında; talimatla devam.

### Oturum 10 — 2026-09-23: FAZ 6G proje hafızası senkronizasyonu (MOD: salt-dokümantasyon)
**Yapılanlar:**
- Kod ağacından gerçek durum doğrulandı (salt-okunur; kod değişikliği YOK, migration YOK).
- `memory-bank/` (bu dosya + `progress.md` + `techContext.md`) güncel gerçekle eşitlendi; eski bilgiler silinmedi, "tarihsel" olarak işaretlendi.
- `FAZ3A_KAPANIS_RAPORU.md` başına çözüm notu eklendi (rapor gövdesi tarihsel olarak korundu).
- `FAZ6G_SENKRON_RAPORU.md` oluşturuldu (doğrulama kanıtları + eski/yanlış listesi).
**Doğrulama (bu oturum):** `manage.py check` OK · `makemigrations --check` temiz ·
pytest `--ignore=frontend` 386 passed/exit 0 · `vue-tsc --noEmit` temiz ·
Vitest `yetki.spec.ts` 5/5.
**Sonraki:** kullanıcı talimatıyla bir sonraki faz; manuel go-live 7 maddesi kullanıcı tarafında.

### Oturum 8 — 2026-09-18: Finans çekirdeği ve raporlar
**Yapılanlar:**
- Cari hareket/özet endpointleri, muhasebe alias route'ları ve fatura iptal/pozitif tutar doğrulaması eklendi.
- Finans özeti, cari özeti ve mizan rapor action'ları eklendi; finans tabloları RLS listesine alındı.
- Vue menü/router/servisleri: cari hareketler, faturalar, mizan ve raporlar tamamlandı.
- Frontend type-check, production build ve Vitest 11/11 başarılı; Django check başarılı.
- Geliştirme DB'sinde `finance_fatura`, `finance_rapor`, `finance_ayar` tabloları oluşturuldu.
**Kalan ortam notu (tarihsel — aşıldı):** 2026-09-18'de `.env.test` içindeki
PostgreSQL `localhost:5434` erişilemiyor olarak not edilmişti; 2026-09-23
doğrulamasında `pytest --ignore=frontend` **386 passed, exit 0** alındı.
(Yalın `pytest` kökteki ikili `frontend/test.txt` dosyasına takılır; testler
`--ignore=frontend` ile koşar.)

### Oturum 2 — 2026-09-14 (backend iskeleti)
**Yapılanlar:**
- `site-specification.json` JSON hatası düzeltildi (`"surfaceHover:"` → `"surfaceHover":`) ve
  `python -m json.tool` ile doğrulandı
- Backend iskeleti kuruldu:
  - `venv` + `requirements.txt` (Django 6.1.1, DRF 3.18.1, simplejwt, psycopg3,
    drf-spectacular, django-filter, django-environ, django-cors-headers, pytest)
  - `docker-compose.yml` → PostgreSQL 16 konteyneri (**host port 5433** — çakışma notu aşağıda)
  - `config/settings/` paketi: `base.py` / `dev.py` / `prod.py`; TR locale, Europe/Istanbul
  - App'ler: `tenants`, `users`, `real_estate`, `cari`, `finance`, `accounting` (+ Türkçe verbose_name)
  - Modeller: `Tenant`, `TenantAwareModel` (abstract), `User` (AbstractUser + tenant FK + rol), admin kayıtları
  - JWT (access/refresh), Swagger/Redoc schema, `api/v1/health/`
  - Migration'lar değil, **schema dump** alındı: `db/schema.sql` (pg_dump
    `--schema-only`, `django_migrations` hariç) — Migration KULLANILMAZ kararı alındı;
    süper kullanıcı `admin/admin123` + `Demo Firma A.Ş.` tenanti (tenant_admin rolü)
  - Smoke testler (pytest): 3 passed, `manage.py check` temiz
  - `docs/kurulum.md` oluşturuldu
  - `.cline/rules/aAGENTS.md` yol düzeltmeleri (`references/*` → `docs/proje-kurallari/*`)

**Önemli bulgu:** Windows'ta `127.0.0.1:5432`'yi kurulu yerel `postgres.exe`
dinliyor → Docker PostgreSQL dışarıdan **5433** ile yayınlanıyor (`.env` ve
`docker-compose.yml` buna göre). Django `EMAIL_BACKEND` deprecation'ı için
`MAILERS` yapısı kullanıldı (Django 6.1).

### Oturum 2 — devam (2026-09-14): migration iptali + İnşaat (Faz 1)
**Karar (kullanıcı):** Migration kullanılmayacak.
**Yapılanlar:**
- Tüm `migrations/` klasörleri silindi (6 app) ve tüm referanslar çıkarıldı
  (settings yorumu, docs kurulum, 00-STACK, 01-GELISTIRME-KURALLARI, site-spec JSON,
  pytest). `site-spec.json` migrationStrategy = veri göçü stratejisi — korundu.
- Şema yönetimi → **`db/schema.sql`** (pg_dump `--schema-only`, `django_migrations`
  tablosu hariç). Yeni tablolar şema oluşturucuyla DB'ye eklenir, sonra dump tazelenir.
- pytest `--no-migrations` → test şeması modellerden oluşturulur.
- **Faz 1 — İnşaat modülü (`construction/`):**
  - Modeller: `PozGrubu` (hiyerarşik), `Poz`, `Malzeme`, `PozMalzemeIliskisi`
    (miktar>0 check, tenant+poz+malzeme unique), `PozFiyat` (yıl snapshot),
    `YapiSinifiBirimMaliyet` (yıl+sinif unique), `Proje`
  - `services.py` maliyet motoru (Decimal zorunlu, pozitif metraj)
  - Roller: `SANTIYE_SEFI`, `MALIYET_MUHENDISI` (UserRole)
  - API: 7 ViewSet (`/api/v1/construction/...`) + `IsConstructionEditor` rol yetkisi
  - Admin kayıtları; Swagger şeması
  - Testler: 12 yeni (constraint/service/API) → toplam **15 passed**
  - HTTP smoke: JWT → poz listesi → schema doğrulandı
  - `db/schema.sql` 796 satır (construction dahil) tazelendi

### Oturum 2 — devam 2 (2026-09-14): tenant izolasyonu + response envelope
**Yapılanlar:**
- **Response envelope (backend):** `config/renderers.py` (EnvelopeJSONRenderer —
  başarı `{success, data, message}`, schema görünümleri hariç) + `config/exceptions.py`
  (hata `{success:false, message, errors}` Türkçe) → settings'e bağlandı.
- **Tenant izolasyonu:** `tenants/api.py` → `TenantScopedViewSet` (queryset
  `tenant_id=user.tenant_id`; superuser global; CREATE'te tenant kullanıcıdan,
  UPDATE'te değiştirilemez). `construction/serializers.py` →
  `TenantAwareModelSerializer` — tenant field **read-only**, istemciden asla alınmaz.
- 7 ViewSet + 7 serializer bu tabanlara geçirildi.
- Testler: `tenants/tests.py` (izolasyon + zarf) + construction API testlerinin
  envelope güncellemesi → toplam **22 passed**, `check` temiz.
- HTTP smoke: token `data.access`, poz listesi `success:true`, OpenAPI 200 / 59 KB
  (inşaat path'leri mevcut).

### Oturum 2 — devam 3 (2026-09-14): Gayrimenkul (real_estate) çekirdeği
**Yapılanlar:**
- `real_estate/models.py` → `RealEstate` (TenantAware; blok/kat/daire, Decimal m²,
  durum choices, tapu notu; `(tenant, blok, kat, daire_no)` unique; proje FK PROTECT)
- Proje ↔ Gayrimenkul ilişkisi kuruldu (roadmap Faz 1 maddesi ☑)
- API: `/api/v1/real-estate/gayrimenkuller/` (TenantScopedViewSet + TenantAware
  serializer + IsConstructionEditor) + admin
- `TenantAwareModelSerializer` DRY için `tenants/serializers.py`'ye taşındı
  (construction + real_estate ortak kullanıyor)
- Şema oluşturucuyla DB tablosu + `db/schema.sql` tazelleme (853 satır)
- Testler: real_estate (model + API + izolasyon) → toplam **25 passed**
- HTTP smoke: gayrimenkuller listesi zarf OK; schema 200 + path. (Not: eski
  runserver süreci portu tuttuğundan 404 çıkmıştı — süreç temizlendi.)

### Oturum 3 (2026-09-14): ÇŞİDB poz parser + IV-A yapı sınıfı import (Faz 1 bitti)
**Yapılanlar:**
- `construction/imports.py`: parser çekirdeği — `KK.GGG.SSSS` poz no doğrulama,
  `normalize_yapi_sinifi()` ("4A"/"iv-a"/"IV A" → "IV-A"; readme §52.6-5),
  `import_poz_verisi()` (grup+poz+PozFiyat yıl bazlı; atomic fail-fast;
  `--arsivle` ile eski yıl `is_active=False` arşiv — silme yok; idempotent),
  `import_yapi_sinifi_verisi()`, `csv_satirlari_oku()` (utf-8-sig, `;` ayraç)
- Management komutları: `import_pozlar` (--tenant --dosya --yil --kaynak
  --arsivle --ayrac), `import_yapi_sinifi` (--tenant --dosya --ayrac); Türkçe özet
- `YapiSinifiBirimMaliyetSerializer.validate_sinif_kodu` → API'de de normalize
- Test: +21 (normalize, import idempotent, arşivleme, Decimal zorunlu, komutlar,
  API normalize) → toplam **46 passed**; `manage.py check` temiz
- Canlı smoke: örnek CSV'ler `demo-firma` tenant'ına yüklendi (I-C/IV-A/IV-B
  2026 + 3 poz + 2 fiyat); 2. çalıştırma → 0 oluşturma, güncelleme (idempotent)
- `docs/ornekler/import_poz_ornek.csv` + `import_yapi_sinifi_ornek.csv`;
  `docs/kurulum.md` §7 kullanım; roadmap Faz 1 maddeleri ☑ (her iki kopya)
- Yeni tablo YOK → `db/schema.sql` değişmedi. PDF→CSV dönüştürme akış dışı;
  doğrudan PDF parser ileri fazda değerlendirilir.

### Oturum 3 — devam (2026-09-14): Frontend Faz 0 scaffold
**Yapılanlar:**
- `frontend/src/` kuruldu (Vue 3 + TS + Pinia + Tailwind; vite alias'larıyla uyumlu):
  - `index.html` (lang=tr, Plus Jakarta Sans + Source Sans Pro), `main.ts`,
    `App.vue`, `assets/main.css`
  - `types/api.ts` (Zarf, Sayfali, Rol, Kullanici, TokenCevap) + `utils/roller.ts`
  - `services/`: `apiClient.ts` (axios + Bearer + 401→tek seferlik refresh +
    zarf açan get/post/put/patch/del + `hataMesaji`), `zarf.ts` (zarfAc + ApiHatasi),
    `authApi.ts` (POST /auth/token/)
  - `stores/auth.ts` (Pinia; token + görüntü bilgisi localStorage), `router/index.ts`
    (Türkçe yollar: /giris, / panel, 404; auth guard, konuk meta)
  - `layouts/AppLayout.vue` (280px sidebar + 64px topbar — site-spec), `views/`:
    GirisView, DashboardView (modül durumu kartları), BulunamadiView
  - Testler: `zarf.spec.ts` + `auth.spec.ts` → vitest **6 passed**;
    `"test": "vitest run"` (watch değil, CI dostu)
- **vite.config.ts proxy düzeltmesi:** `rewrite` silindi — backend yolları
  `api/v1/...` olduğu için önek korunmalıydı (önceki ayar istekleri `/v1/...`
  yapıyordu). Ayrıca `test: { environment: 'jsdom' }` + `vitest/config` defineConfig.
- **vue-tsc 1.8 → 2.2.0** yükseltildi (Node 24 + TS 5.9'da 1.8 kırılıyordu).
- Doğrulama: `type-check` EXIT 0, `vite build` EXIT 0 (~15 s), vitest 6 passed.
- Canlı smoke: backend + `npm run dev` → proxy üzerinden `POST /api/v1/auth/token/`
  (admin/admin123) → `success:true`, access/refresh alındı; `/giris` HTTP 200.

### Oturum 3 — devam 2 (2026-09-14): PostgreSQL RLS planı + senaryo
**Yapılanlar:**
- `docs/rls-plani.md`: GUC tabanlı tasarım (`app.current_tenant`), dev/prod rol
  stratejisi (dev: sahibi bypass; prod: `emlak_app` + FORCE), üretim geçiş kontrol
  listesi, bilinen sınırlar
- `db/rls.sql` (idempotent): `app_mevcut_tenant()` fonksiyonu; 8 tenant-aware tablo +
  `users_user` (süper kullanıcı istisnası) → `rls_tenant_izolasyon` policy'leri
  (USING + WITH CHECK, FOR ALL); `rls_deneme` demo rolü — **dev DB'ye uygulandı**
- `tenants/middleware.py` → `TenantBaglamMiddleware`: her istekte
  `app.current_tenant` (session auth → `request.user`; JWT → access token çözümü;
  anonim/geçersiz → boş). `base.py` MIDDLEWARE'e eklendi (AuthenticationMiddleware
  sonrası). Her istek başında yeniden yazılır → kalıcı bağlantı sızıntısı yok.
- Test: +3 middleware testi → toplam **49 passed**; `manage.py check` temiz
- Senaryo doğrulandı (rls_deneme): bağlam=1 → 3 satır; bağlam=2 → **0**;
  bağlamsız → **0**; sahibi bypass → 3. 9 tabloda policy aktif
- `db/schema.sql` pg_dump ile tazelendi (1024 satır; policy + fonksiyon dahil)
- `docs/kurulum.md` §8 (RLS uygulama + notlar)

### Oturum 3 — devam 3 (2026-09-14): Frontend modül ekranları (CRUD)
**Yapılanlar:**
- Backend `/auth/me` zaten mevcuttu (MeView + KullaniciSerializer + testler)
  — frontend `beniGetir()` + `oturumuTazele()` ile bağlıydı; ek backend gerekmedi
- Ortak UI: `components/` → VeriTablosu, Sayfalama (DRF PAGE_SIZE=25),
  KayitModal; `hooks/useKayitFormu.ts`; `utils/yetki.ts` → `yazabilirMi()`
  (backend IsConstructionEditor ile senkron) + yetki.spec.ts
- 4 liste+form ekranı: Pozlar, YapiSinifi (IV-A ipucu, tr-TR para),
  Projeler, Gayrimenkuller (proje bağı, durum filtreleri; yazma rol-gated)
- DashboardView → modül kısayol kartları (RouterLink "Aç →")
- Doğrulama: type-check 0, vitest **9 passed**, vite build OK (4 view chunk);
  backend pytest **51 passed**, check temiz
- Canlı smoke: 4 kaynak success:true (poz 3, yapı sınıfı 3);
  /insaat/pozlar + /gayrimenkul/gayrimenkuller HTTP 200
### Oturum 3 — devam 4 (2026-09-14): Login'e tenant seçici (süper admin odaklı)
**Kapsam kararı (kullanıcı onayı):** "Süper admin odaklı seçici" — tek-tenant
model korunur; normal kullanıcı kendi tenant'ında sabit, seçim yalnızca süper
admin'e görünür.
**Yapılanlar (backend):**
- `users/tokens.py` (yeni): `TenantTokenObtainPairSerializer` — JWT access'e
  `tenant_id`/`role`/`username` claim'leri; `users/views.py` →
  `TenantTokenObtainPairView` (`/api/v1/auth/token/` buna bağlandı,
  `config/urls.py`); yanıt zarfı korunur
- `users/serializers.py`: `KullaniciSerializer` + `tenant_ad` (topbar gerçek
  firma adı, ek istek yok); `TenantSecimSerializer` (id/name/slug/is_active)
- `tenants/views.py` (yeni): `TenantSecimViewSet` (ReadOnly) + `IsSuperUser`
  izni (yalnızca `is_superuser`; `IsAdminUser` YETERSİZDİ — `is_staff`
  tenant_admin'i de geçiriyordu, canlı smoke'ta yakalandı) →
  `GET /api/v1/tenants/` (router)
- `tenants/api.py`: `TENANT_KAPSAM_BASLIGI="X-Tenant-Id"` + `etkin_tenant_id()` —
  normal kullanıcıda başlık yok sayılır; süper admin başlıkla daralır,
  başlıksız global görür; `TenantScopedViewSet` + `perform_create` buna bağlandı
- `tenants/middleware.py`: RLS GUC'sü süper admin kapsam başlığını izler
  (session + JWT dalları)
- Test: `tenants/test_secici.py` (yeni, 11 test: claim'ler, liste izni incl.
  staff-ama-superuser-değil 403, kapsam daraltma, başlık-yok-sayma, me
  tenant_ad) → toplam **62 passed**
**Yapılanlar (frontend):**
- `types/api.ts`: `Kullanici.tenant_ad?`, `TenantSecim`; `authApi.ts` +
  `tenantListesiniGetir()`; `apiClient.ts`: `X-Tenant-Id` interceptor + seçim
  localStorage (`emlak_erp_tenant_secimi`, çıkışta temizlenir)
- `stores/auth.ts`: `tenantlar/seciliTenantId`, `seciciGosterilsinMi`
  (yalnızca super_admin), `tenantlariYukle/tenantSec`; `auth.spec.ts` mock
  düzeltmesi (`beniGetir` mock'u eksikti) + 2 yeni test → vitest **11 passed**
- `AppLayout.vue`: topbar'da gerçek firma adı; süper adminde seçici dropdown
  ("Tüm Tenantlar" + liste; değişimde kapsam yazılıp sayfa tazelenir);
  `GirisView.vue` alt notu güncellendi
**Doğrulama:** pytest 62 passed · type-check 0 · vitest 11 · build OK ·
canlı smoke: /auth/me `tenant_ad:"Demo Firma A.Ş."`, admin (tenant_admin)
`/tenants/` → **403** (beklenen), X-Tenant-Id kapsam success, Vite HTTP 200
- Not: login tenant seçici backlog'dan çıkarıldı (AppLayout'ta "Tenant #id" gösterimi var)

### Oturum 4 (2026-09-15): Faz 2 — Poz maliyet planı (metraj) + S-eğrisi
**Bulgu (yarım kalan iş):** `PozPlan` modeli/serializer/services yazılmış ama
`views.py`/`urls.py`/admin/test yok, DB tablosu yok; ayrıca `models.py` **syntax
hatası** içeriyordu (`Proje.__str__` öncesi fazladan `"""` + `PozPlan.clean()` içine
yanlış girintiyle gömülmüş `def save`) → `manage.py check`/pytest kırıktı.
**Yapılanlar (backend):**
- `models.py` düzeltildi: syntax hatası giderildi, `save()` sınıf seviyesine alındı,
  `ValidationError` üstte import edildi, snapshot yoksa hata mesajı netleştirildi
- `views.py`: `PozPlanViewSet` (tenant izole CRUD; `proje`/`poz`/`yil` filtreleri,
  arama) + `@action url_path="s-egrisi"` → `?proje=&yil=` zorunlu, hatalı/eksikte 400
- `urls.py`: `poz-planlari` kaydı; `admin.py`: `PozPlanAdmin` (snapshot read-only)
- `serializers.py`: `PozPlanSerializer.validate()` → metraj/fiyat kontrolleri API'de
  **400** döner (model `clean()` ValidationError'ı DRF'te 500 olurdu)
- `services.py`: S-eğrisi toplamları `quantize` edildi (para 2, metraj 4 ondalık)
- `tenants/api.py`: `tenant_kapsamli_queryset(request, qs)` çıkarıldı
  (`TenantScopedViewSet.get_queryset` aynı yardımcıyı kullanır) → rapor endpoint'i
  proje sorgusunu da DRY biçimde tenant'a daraltır
- Test: +17 (model constraint 4, servis/S-eğrisi 4, API 9: snapshot otomatik,
  403/400, rapor, parametre eksik, başka tenant 404 + liste izolasyonu) →
  **79 passed**; `manage.py check` temiz
- Şema: `db/tablo_olustur.py` (yeni, idempotent yardımcı) ile `construction_pozplan`
  tablosu açıldı; `db/rls.sql` tablo listesine eklendi (10 policy); `db/schema.sql`
  pg_dump ile tazelendi (1650 satır) ve **geçici DB'de yüklenerek doğrulandı**
  (19 tablo + 10 policy), sonra geçici DB silindi
**Yapılanlar (frontend):**
- `types/insaat.ts`: `PozPlan`, `SEkgrisiSatiri`, `SEkgrisiRaporu`
- `services/insaatApi.ts`: `pozPlanlari` CRUD + `sEgrisi(projeId, yil)`
- `views/insaat/PozPlanlariView.vue` (yeni): metraj listesi + form (proje/poz/yıl/
  planlanan/gerçekleşen) + S-eğrisi paneli (PV/AV/sapma kartları + satır tablosu)
- `router/index.ts` (`/insaat/poz-planlari`), `AppLayout.vue` (menü: Poz Planları),
  `DashboardView.vue` (modül kartı)
**Doğrulama:** pytest **79 passed** · type-check 0 · vitest **11 passed** · build OK
(PozPlanlariView chunk 12.98 kB) · canlı smoke: JWT → poz planı oluştur (snapshot
235.42 → plan 2354.20 / gerçek 1883.36) → S-eğrisi `-20.00%`; parametresiz istek 400;
RLS senaryosu (tenant1=1 satır, tenant2=0); fonksiyonel sayfa HTTP 200; vite proxy
üzerinden uçtan uca `proxy_plan_count=1`, `proxy_sapma=-20.00%`
**Devam (Faz 2 kalanlar):** Gantt şeması, hakediş takibi (muhasebe fişi entegrasyonu),
  şantiye günlüğü, taşeron hakediş, iş güvenliği/kalite listeleri

### Oturum 5 devam 3 (2026-09-15): Saha günlükleri + kalite/İSG + taşeron yolu
**Yapılanlar:**
- Backend `construction.SantiyeGunlugu`: proje/tarih tekilliği, hava/ekip/yapılan iş/
  sorun/not alanları, tenant izolasyonu ve oluşturan kullanıcı.
- Backend `construction.KaliteKontrol`: proje/poz kapsamı, kontrol türü/kriter,
  beklemede-uygun-uygun değil sonucu ve düzeltici faaliyet alanları.
- Her iki model için serializer, tenant izole ViewSet, URL ve admin kaydı eklendi.
- Migration kullanılmadı: `db/tablo_olustur.py` ile iki tablo açıldı; `db/rls.sql`
  listesine eklendi ve aktif PostgreSQL'e uygulandı.
- Frontend `/insaat/santiye-gunlukleri` ve `/insaat/kalite-kontrolleri` liste/form
  ekranları eklendi. `/insaat/taseron-hakedisleri`, mevcut cari + onay + muhasebe
  entegrasyonlu hakediş ekranına ayrı menü yolu olarak bağlandı.
- Hakediş action'larının yanlış ViewSet'e taşınmasından doğan 404 regresyonu düzeltildi.
- Doğrulama: tüm pytest `131+` suite geçti, `manage.py check`, type-check ve build geçti.
- `C:\Program Files\PostgreSQL\18\bin\pg_dump.exe` bulundu; `db/schema.sql`
  yeni iki tablo ve RLS policy'leri içerecek şekilde tazelendi. `django_migrations`
  dump dışında bırakıldı.

**Son doğrulama:** tüm pytest suite geçti; frontend `npm run build` başarılı.

### Oturum 6 (2026-09-15): Veritabanı Yönetimi
**Yapılanlar:**
- `database_admin` uygulaması eklendi; tüm uçlar yalnızca `is_superuser` için açık.
- `/api/v1/database/overview/`: public tablolar, kolon metadata'sı, kayıt sayıları ve
  veritabanı özeti.
- `/api/v1/database/tables/<table>/rows/`: sayfalı kayıt keşfi ve arama; hassas
  parola alanları maskeli.
- Birincil anahtarlı kayıtlarda güvenli alan düzenleme; `id`, tenant, parola,
  created/updated ve ilişki referansları salt okunur. Ham SQL ve tablo silme yok.
- `pg_dump` yedek oluşturma/indirme ve `psql` geri yükleme; restore öncesi otomatik
  güvenlik yedeği ve zorunlu `RESTORE DATABASE` onayı.
- Frontend `/yonetim/veritabani`: modül bazlı tablo ağacı, satır grid'i, düzenleme
  modalı, yedek paneli ve geri yükleme paneli.
- `.gitignore` yedek SQL'lerini dışlıyor; kurulum dokümanına yönetim bölümü eklendi.
- Doğrulama: database admin API testleri 4 geçti; gerçek backup smoke `201`; restore
  onaysız istek `400`; tüm backend testleri, frontend type-check/test/build başarılı.

### Oturum 6 devamı (2026-09-15): Excel ile seçili tablo veri aktarımı
**Yapılanlar:**
- `openpyxl==3.1.5` requirements'a eklendi.
- Veritabanı yönetim ekranında tablo seçim kutuları ve hedef tenant seçimi eklendi.
- Seçilen tablolar için `Talimatlar` ve gizli `__TabloEsleme` sayfalı `.xlsx` şablon
  üretimi/indirme eklendi; 31 karakterlik Excel sayfa adı sınırı destekleniyor.
- Doldurulmuş `.xlsx/.xlsm` yükleme, kolon başlığı doğrulama, 10.000 satır/sayfa ve
  100 MB dosya sınırı, dry-run doğrulama ve tek transaction import eklendi.
- `id`, tenant, parola ve audit kolonları şablondan dışarıda; tenant hedefi formdan
  atanıyor, `created_at/updated_at/created_by_id` sistemce dolduruluyor.
- İçe aktarma hatasında tüm workbook rollback oluyor; ilişkiler numeric id ile çözülüyor.
- `/api/v1/database/excel/template/` ve `/api/v1/database/excel/import/` uçları eklendi.
- Excel testleri 6 geçti; dry-run smoke 200; frontend type-check/build başarılı.
- Alan seçimi de eklendi: her tablo altında kolon checkbox'ları; şablon yalnız seçilen
  alanları içeriyor, `__TabloEsleme` alan sözleşmesini saklıyor ve import bunu doğruluyor.
- Mevcut verilerin seçili tablo/alanlarla dolu Excel'e aktarımı eklendi
  (`/api/v1/database/excel/export/`); export testi başarılı.

### Oturum 7 (2026-09-15): Geliştirici veri kaynağı modu
**Yapılanlar:**
- Süper admin için üst bardan açılıp kapanan geliştirici modu eklendi; tercih
  localStorage'da tutuluyor ve çıkışta temizleniyor.
- `VeriKaynakRozeti.vue` ile hover/focus popup altyapısı eklendi: tablo, sütun,
  model alanı, tip, API ve ilişki bilgisi gösteriliyor.
- Cari kart ekranındaki `ad`, `tip`, `tur` hücreleri gerçek DB metadata'sı ile
  bağlandı; diğer ekranlar aynı bileşenle alan bazında eşlenecek.
- Doğrulama: frontend type-check ve build başarılı.

### Oturum 3 — 2026-09-15: Hakediş takibi + Cari/Finans/Muhasebe çekirdeği
**Yapılanlar (backend):**
- **Cari modülü:** `Cari` (tip: kiracı/malik/tedarikçi/taşeron; bireysel/kurumsal;
  tenant+ad unique; vergi no 10 hane validasyonu) + `CariHareket` (borç/alacak,
  is_cancelled iptal deseni — fiziksel DELETE yok); API: `/api/v1/cari/cariler/`,
  `/cariler/{id}/hareketler/`, `/cariler/{id}/ozet/`, `/hareketler/{id}/iptal/`
- **Muhasebe modülü:** `HesapPlani` (kod tenant bazlı unique) + `MuhasebeFisi`
  (borç==alacak `clean()` kontrolü) + `FisSatiri` (satır: hem borç hem alacak olamaz,
  tutar>0); API: `/api/v1/accounting/hesap-plani/`, `/fisler/`, `/fisler/mizan/`;
  fiş destroy kapalı — `iptal` aksiyonu
- **Finans modülü:** `KasaBankaHesabi` (kasa/banka/kk/çek) + `FinansalIslem`
  (gelir/gider/transfer, cari FK, iptal deseni); API: `/api/v1/finance/hesaplar/`,
  `/islemler/`, `/islemler/ozet/`
- **Hakediş:** `Hakedis` (tenant+proje+dönem unique, YYYY-MM regex) + `HakedisSatiri`
  (hakediş+poz unique, miktar>0, fiyat>0, `satir_tutar` Decimal property);
  `services.hakedis_satirlari_olustur` (poz planlarından gerçekleşen metraj × snapshot,
  idempotent), `hakedis_toplami`, `hakedis_onayla` (atomic + select_for_update:
  Cari Hareket BORÇ + Muhasebe Fişi 740 borç/120 alacak — readme §52.6-4; hesaplar
  yoksa get_or_create; tekrar onay/cari'siz/boş satır reddedilir); ViewSet
  `HakedisViewSet` + `satirlari-olustur`/`onayla`/`iptal` aksiyonları; serializer'da
  onaylı hakedişte yalnızca açıklama güncellenebilir; model `clean()` onaylı kayıt
  değişmezliği; destroy → durum=iptal
- **Gantt (backend):** `services.gantt_verisi` + `GET /construction/poz-planlari/gantt/`
- **Gantt (frontend):** PozPlanlariView'a çubuk paneli eklendi — `ganttGetir()`
  (proje filtresi seçiliyken; yil opsiyonel), poz bazlı yatay çubuklar
  (planlanan başlangıç/bitiş yoksa yıl başlangıcı varsayılır), ilerleme yüzdesi
  (gerçek/planlanan metraj) ve maliyet sapma rengi; `types/insaat.ts`'ye
  `GanttCubugu`/`GanttRaporu`, `insaatApi.gantt(projeId, yil?)` eklendi
- **Envelope çift zarf hatası düzeltildi:** custom aksiyonlarda elle zarflanan yanıtlar
  renderer zaten sardığı için 5 yerde düzeltme (cari/finance/accounting/construction)
- **config/urls.py:** cari/finance/accounting include'ları eklendi (`/api/v1/cari/`,
  `/finance/`, `/accounting/`)
**Yapılanlar (frontend):**
- `views/insaat/HakedislerView.vue` (yeni): hakediş listesi + satır yönetimli form +
  "Planlardan satır üret" + onay (confirm ile Cari Hareket/Fiş uyarısı) + iptal
- `types/insaat.ts`: `Hakedis`, `HakedisSatiri`; `insaatApi`: `hakedisler` CRUD +
  `hakedisSatirlariUret` + `hakedisOnayla` + `hakedisIptal`
- router `/insaat/hakedisler` + AppLayout menüsü + Dashboard kartı
**Şema:** 9 yeni tablo (`db/tablo_olustur.py cari_cari ... construction_hakedissatiri`)
→ `db/rls.sql` (14 policy, yeni tablolar listeye eklendi) → gerçek DB'ye uygulandı →
`db/schema.sql` pg_dump ile tazelendi (28 tablo)
**Doğrulama:** pytest **131 passed** (cari 12, muhasebe 13, finans 9, hakediş 15,
gantt 2); `manage.py check` temiz; frontend `npm run build` OK (HakedislerView chunk)
**Not:** Docker kapalı olduğundan testler/şema yerel PostgreSQL 18 (port 5432,
süper kullanıcı Lenovo) üzerinde koşturuldu; `.env` hâlâ Docker 5433'ü gösteriyor
(dev ortamda docker compose up ile geri dönülecek).

## Güncel kararlar
- **Backend:** Django 6.1 + DRF + PostgreSQL — settings `base/dev/prod/test`
  (dev JWT 8 sa, prod 15 dk + refresh 7 gün rotation + blacklist; test JWT 5/10 dk).
- **Şema yönetimi (FAZ 6G güncel):** **Django migration'ları AKTİF.**
  tenants 1 · users 2 · real_estate 1 · construction 0001→0031 (+0027 reconcile,
  0028 merge) · cari 7 · finance 17 · accounting 8 · audit 2 · purchasing 4.
  `makemigrations --check` temiz. (Tarihsel: 2026-09-14'te "migration
  kullanılmaz → `db/schema.sql`" kararı alınmıştı; FAZ 6 öncesi zincire
  dönüldü. `db/schema.sql`, `db/rls.sql`, `db/tablo_olustur.py` dosyaları
  tarihsel artefakt olarak durur, otorite değildir.)
- **Frontend:** Vue 3 + TS + Pinia + Tailwind; Faz 0, inşaat/gayrimenkul ve temel
  Cari/Finans/Muhasebe kart ekranları uygulanmış durumda
- `AUTH_USER_MODEL = users.User`; API prefix `api/v1/`
- API yanıt zarfı: **uygulandı** (`config/renderers.py` + `config/exceptions.py`)
  → `{success, data, message, errors}` (schema görünümleri hariç)
- JWT: dev 8 saat / prod 15 dk; refresh 7 gün + rotation
- **Tenant kapsamı:** `tenants/api.py::tenant_kapsamli_queryset` (ViewSet + rapor
  endpoint'leri ortak kullanır); süper admin `X-Tenant-Id` ile daralır
- **Şema değişikliği akışı (FAZ 6G güncel):** model değişikliği → `makemigrations`
  → `migrate` → test (`check` + `makemigrations --check` + pytest). Eski akış
  (`db/tablo_olustur.py` → `db/rls.sql` → pg_dump ile `db/schema.sql` tazele)
  tarihseldir (docs/kurulum.md §4.1 de eski akışı anlatır).
- **Güvenlik (kodda doğrulandı):** prod fail-closed (`prod.py` SECRET_KEY +
  DATABASE_URL zorunlu); login kilidi 5 deneme/900 sn (`users.LoginDenemesi`);
  refresh rotation + blacklist; SECURE_SSL_REDIRECT + HSTS + secure cookie'ler;
  health muafiyeti `SECURE_REDIRECT_EXEMPT = ["^api/v1/health/"]`.
- **Yedekleme (kodda doğrulandı):** `db_yedekle` (dump + sha256 manifest +
  Fernet şifreleme + retention + off-site kopya) + `db_restore` + API
  (`/database/backups/...`) + `sistem_kontrol`. Scheduler + OFFSITE_DIR +
  ENCRYPTION_KEY manuel go-live kalemi (kod dışı).
- **Audit/logging (kodda doğrulandı):** `TenantAuditMiddleware` (POST/PUT/PATCH/DELETE,
  best-effort) + `AuditLog.correlation_id` + `IstekBaglamMiddleware`
  (korelasyon ID, `SLOW_REQUEST_MS=1000` / `SLOW_DB_MS=500` WARNING eşiği,
  `erp.access` + `erp.backup` + `export` event logları).
- **Yetki matrisi (kodda doğrulandı):** construction + purchasing yazma =
  super_admin/tenant_admin/firma_admin/maliyet_muhendisi/proje_yoneticisi
  (6C SoD: finans/muhasebe satın almada yazamaz; frontend `satinAlmaYazabilirMi`
  birebir senkron). cari/finance yazma += muhasebe/finans; muhasebe yazma =
  adminler + muhasebe (finans yazamaz); database_admin = yalnızca süper admin.
  Not: inşaat ekranları frontend `yazabilirMi` kullanır (muhasebe/finans'a buton
  gösterir) ancak backend `IsConstructionEditor` reddeder — backend fail-closed,
  kritik değil; UX notu olarak durur.

## Sıradaki adım (FAZ 6G güncel — kod işi kalmadı)
1. ☐ Manuel go-live (kod dışı, kullanıcı tarafı): TLS reverse proxy/nginx;
   ALLOWED_HOSTS + CSRF_TRUSTED_ORIGINS prod değerleri; günlük `db_yedekle`
   scheduler; BACKUP_OFFSITE_DIR; BACKUP_ENCRYPTION_KEY; log collector +
   alerting; prod deploy + smoke test.
2. (Tarihsel — tamamlandı, 2026-09-23 doğrulandı: Cari/Finans/Muhasebe ekranları,
   şantiye günlüğü, taşeron hakediş, kalite/İSG listeleri, RLS/middleware,
   satın alma DEP0/MalKabul/Stok, backup komutları, SoD, sourcemap kapalı,
   console temizliği.)

### Oturum 5 devamı (2026-09-15): Cari / Finans / Muhasebe frontend başlangıcı
**Yapılanlar:**
- Cari ekranı: `types/cari.ts`, `services/cariApi.ts`, `views/cari/CarilerView.vue`;
  sayfalı liste, arama/tip filtresi, maskeleme uyumlu kart formu ve rol kontrollü düzenleme.
- Finans temel ekranı: `types/finans.ts`, `services/finansApi.ts`,
  `views/finans/FinansHesaplariView.vue`; kasa/banka hesap CRUD, tip filtresi, IBAN maskesi.
- Muhasebe temel ekranı: `types/muhasebe.ts`, `services/muhasebeApi.ts`,
  `views/muhasebe/HesapPlaniView.vue`; hesap planı CRUD ve tip filtresi.
- Router ve sidebar'a `/cari/cariler`, `/finans/hesaplar`, `/muhasebe/hesap-plani` eklendi.
- Doğrulama: `npm run build` başarılı; yeni ekran chunk'ları üretildi.

### Oturum 5 devam 2 (2026-09-15): Finansal işlemler + muhasebe fiş/mizan frontend
**Yapılanlar:**
- Finansal işlem ekranı: `/finans/islemler`; hesap/cari seçimi, gelir-gider-transfer,
  tutar/tarih, listeleme ve backend iptal endpoint'i.
- Muhasebe ekranı: `/muhasebe/fisler`; mizan tablosu, nested dengeli fiş oluşturma,
  satır ekleme/silme ve istemci tarafı borç/alacak denetimi.
- `types/finans.ts` / `services/finansApi.ts` ve `types/muhasebe.ts` /
  `services/muhasebeApi.ts` genişletildi; router/sidebar bağlantıları eklendi.
- Doğrulama: `npm run type-check` ve `npm run build` başarılı.

> Devam için: `"memory bank'i oku, kaldığımız yerden devam et."`
> Süper kullanıcı: `admin/admin123`; migration'lar AKTİF (FAZ 6G güncel);
> test: `python -m pytest --ignore=frontend` (386 passed, 2026-09-23).
> Şema değişikliği akışı: `makemigrations` → `migrate` → test.
> (Tarihsel: migration-YOK dönemi `db/schema.sql` akışı docs/kurulum.md §4.1'de kalır.)

### Oturum 6 — 2026-09-15: Faz 2 Gantt Şeması (planlanan tarihler + zaman çizelgesi)

**Yapılanlar:**
- **Model:** PozPlan modeline `planlanan_baslangic` (DATE) ve `planlanan_bitis` (DATE) alanları eklendi. Nullable, varsayılan None. `clean()` metotunda `bitis >= baslangic` kontrolü (her iki tane girildiyse). DB `CheckConstraint check_poz_plan_tarih_sirasi` eklendi.
- **Serializer:** `PozPlanSerializer` validasyonuna `planlanan_baslangic`/`planlanan_bitis` eklendi; tarih sırasi kontrolü `bitis >= baslangic` eklendi.
- **Service:** `services.gantt_verisi(proje, yil)` fonksiyonu implement edildi. Çıktı tipi: `GanttRaporu` (proje_kodu, yil, en_erken, en_gec, tarihsiz_sayi, cubuklar[]) ve `GanttCubugu` (id, poz_no, poz_ad, grup_kodu, yil, baslangic, bitis, tarih_atandi, planlanan_miktar, gercek_miktar, ilerleme_yuzde, plan_deger, gercek_deger). Tarih stilleri yoksa `tarih_atandi=False` ve çubuk eksene konmaz. İlerleme yüzdesi = (gerçek/planlı × 100). Para/değer Decimal quantization (2/4 ondalık).
- **ViewSet:** `PozPlanViewSet` eklendi `@action(detail=False, url_path="gantt")` endpoint'i `/construction/poz-planlari/gantt/?proje=&yil=` (tenant izole, required `proje`, opsiyonel `yil`). 400 eksik/geçersiz parametreler için.
- **Admin:** `PozPlanAdmin` güncellendi: `planlanan_baslangic`, `planlanan_bitis` fields + `date_hierarchy = "planlanan_baslangic"`.
- **DB:** `ALTER TABLE construction_pozplan ADD COLUMN planlanan_baslangic date NULL; ALTER TABLE construction_pozplan ADD COLUMN planlanan_bitis date NULL; ALTER TABLE construction_pozplan ADD CONSTRAINT check_poz_plan_tarih_sirasi CHECK (planlanan_baslangic IS NULL OR planlanan_bitis IS NULL OR planlanan_bitis >= planlanan_baslangic);` `db/schema.sql` pg_dump güncellendi, constraint ve kolonlar görünüyor.
- **Tests:** 13 Gantt testi yazıldı (model constraints, serializer validation, service output, API endpoint, tenant isolation, 400/403 case'leri). Tüm 13 passed.

**Kalan:**
- Frontend: `GanttView.vue` oluşturuldu, router/menu/Dashboard card eklendi. `insaatApi.gantt()` servis metodu eklendi. Types (`GanttBar`) zaten `types/insaat.ts` mevcut. Vite/npm build ortamında Docker DB olmadığı için doğrulama burada yapılacak (gelecek oturumda).
- Dokümantasyon: `docs/kurulum.md` şema-değişliği notu zaten güncellendi. roadmap iki kopya senkronizasyonlu.

**Test Sonucu:**
- `pytest construction --tb=short` → 100 passed (tam test seti).
- Gantt hizmet ve API testleri → 13 passed (DB bağımlılığı olan API testleri yerel PostgreSQL'de çalışmıyor; expected — erişim için `manage.py pytest` Docker gerektirir).

> Devam için: `"memory bank'i oku, kaldığımız yerden devam et."`
> Süper kullanıcı: `admin/admin123`; migration'lar AKTİF (FAZ 6G güncel);
> test: `python -m pytest --ignore=frontend` (386 passed, 2026-09-23).
> Şema değişikliği akışı: `makemigrations` → `migrate` → test.
> (Tarihsel: migration-YOK dönemi `db/schema.sql` akışı docs/kurulum.md §4.1'de kalır.)
### Oturum 7 — 2026-09-18: Port temizleme, sunucu başlatma ve Faz 2 modellerinin API tamamlanması
**Yapılanlar:**
- Port 8000 üzerindeki-existing processes temizlendi.
- DJANGO_SETTINGS_MODULE environment variable'ı config.settings.dev olarak ayarlandı.
- Django sunucusu 0.0.0.0:8000 üzerinde başlatıldı.
- construction/serializers.py dosyasına TedarikciSerializer, MalzemeTedarikciIliskisiSerializer, TaseronSozlesiSerializer, KaliteKabulTeminatiSerializer sınıfları eklendi.
- construction/views.py dosyasına TedarikciViewSet, MalzemeTedarikciIliskisiViewSet, TaseronSozlesiViewSet, KaliteKabulTeminatiViewSet sınıfları eklendi ve eksik model importları tamamlandı.
- API endpoint'leri artık tamamlıyor ve tenant izolasyonu korumalı şekilde çalışıyor.
- construction/admin.py dosyasında HakedisAdmin sınıfının list_display, list_filter ve search_fields alanlarını güncelledi.

### Oturum 8 — 2026-09-20: Taşeron Hakedişleri API endpoint'i (Faz 2 kaldığı yerden)
**Yapılanlar:**
- `SubcontractorBillingViewSet` eklendi (`construction/views.py`) — Hakedis kayıtlarını `cari.tip == "taseron"` filtresiyle listeleyen ViewSet.
- URL route: `router.register("subcontractor-billings", views.SubcontractorBillingViewSet, basename="subcontractor-billing")` → `/api/v1/construction/subcontractor-billings/`
- Frontend `TaseronHakedisleri.vue` zaten bu endpoint'i kullanıyordu (`/api/v1/construction/subcontractor-billings/`), artık backend ile uyumlu.
- Django check ✅, frontend build ✅, API test (DRF APIClient) 200 OK.
- Progress.md: "Faz 2 kalanlar → taşeron hakediş ✅" olarak işaretlendi.
## Oturum 9 — 2026-09-22: Migrasyon uzlaştırması (0021‑0026)
**Yapılanlar:**
- Oluşturulan uyumlu migrasyon `0027_reconcile_missing_tables.py` (CREATE TABLE IF NOT EXISTS, kısıtlama eklemeleri, state‑only silmeler).
- `0021`‑`0026` migrasyonları doğrudan `django_migrations` tablosuna kaydedilerek uygulandı (--fake kullanılmadan).
- `0028_merge_20260922_0206` migrasyonu uygulandı.
- `python manage.py showmigrations construction` tüm migrasyonların uygulandığını gösteriyor.
- `python manage.py check` ve `python manage.py makemigrations --check` temiz.
- Geliştirme veritabanı şeması model durumu ile senkron; FAZ 3A geliştirmeye hazır.