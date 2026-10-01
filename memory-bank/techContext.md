# Teknik Bağlam — Emlak ERP
> FAZ 6G (2026-09-23) senkron notu: bu dosya güncel gerçekle eşitlendi.
> Tarihsel kararlar ("migration kullanılmaz" vb.) üzeri çizili / "tarihsel"
> etiketiyle korunur. Doğrulama kanıtları: `FAZ6G_SENKRON_RAPORU.md`.

## Stack (kaynak: docs/proje-kurallari/00-TEKNOLOJI-STACK.md + kod ağacı)
- **Backend:** Python 3.12 + Django 6.1.1 + Django REST Framework 3.18
- **Frontend:** Vue 3 + TypeScript + Pinia + Tailwind (Composition API);
  `vite.config.ts` prod `sourcemap: false`; `.vue` dosyalarında `console.*` yok
- **DB:** PostgreSQL (dev/yerel + test izole DB); shared DB + tenant_id +
  `TenantBaglamMiddleware` (`app.current_tenant` GUC) + `TenantScopedViewSet`
- **Auth:** JWT (simplejwt; dev 8 sa / prod 15 dk / test 5-10 dk; refresh 7 gün +
  rotation + blacklist) + `users.LoginDenemesi` kilidi (5 deneme / 900 sn) +
  RBAC (DRF permission_classes; `IsSuperUser` database_admin'de)
- **API dokümantasyonu:** drf-spectacular (OpenAPI/Swagger/Redoc)
- **Test:** pytest (backend, `--ignore=frontend` ile 386 passed) + Vitest
  (`yetki.spec.ts` 5/5) + `vue-tsc --noEmit`
- **Deploy:** Docker + Ubuntu VPS + Nginx + Let's Encrypt; CI/CD GitHub Actions
  (hedef; manuel go-live 7 maddesi açık — activeContext'e bak)

## Kurulu paketler (venv — requirements.txt, FAZ 6G güncel)
Django 6.1.1 · djangorestframework 3.18.1 · djangorestframework-simplejwt 5.5.1 ·
psycopg 3.3.5 (+binary) · drf-spectacular 0.30.0 · django-filter 26.1 ·
django-environ 0.14.0 · python-dotenv 1.0.1 · django-cors-headers 4.9.0 ·
openpyxl 3.1.5 · cryptography 50.0.1 · pytest 9.1.1 · pytest-django 4.14.0

## Veritabanı (FAZ 6G güncel)
- Ayarlar: `DATABASE_URL` (ENV) + `config/settings/{base,dev,prod,test}.py`;
  `.env.example` dev örneği; `.env.test` izole test DB'si (2026-09-23'te pytest
  386 passed — eski "5434 erişilemiyor" notu tarihseldir).
- ~~Migration'lar kullanılmaz; şema `db/schema.sql` (pg_dump) ile elle yönetilir;
  test DB'si pytest `--no-migrations` ile modellerden oluşturulur~~ (tarihsel —
  2026-09-14 kararı; FAZ 6 öncesi Django migration zincirine dönüldü, zincir
  aşağıda; `db/schema.sql`, `db/rls.sql`, `db/tablo_olustur.py` otorite değildir).
- **Migration zinciri (kodda doğrulandı):** tenants 1 · users 2 · real_estate 1 ·
  construction 0001→0031 (+0027 reconcile, 0028 merge) · cari 7 · finance 17 ·
  accounting 8 · audit 2 · purchasing 4. Akış: `makemigrations` → `migrate` →
  test (`check` + `makemigrations --check` + pytest).
- **RLS zemini:** `TenantBaglamMiddleware` her istekte `app.current_tenant`
  ayarlar (session auth → `request.user`; JWT → access token; süper adminde
  `X-Tenant-Id` kapsamı; anonim/geçersiz → boş = güvenli varsayılan).
  Tasarım notu: docs/rls-plani.md (tarihsel §5 `emlak_app`+FORCE maddesi manuel
  go-live kapsamına taşındı).

## Mevcut dosya yapısı
```
c:\proje\emlakpython\
├── .venv\                       # sanal ortam (gitignore)
├── config\
│   ├── settings\                # base.py / dev.py / prod.py
│   ├── urls.py                  # api/v1/ — health, auth/token, schema, docs
│   └── tests.py                 # smoke testler (3)
├── tenants\                     # Tenant, TenantAwareModel
├── users\                       # User (AUTH_USER_MODEL) + rolleri
├── real_estate\ cari\ finance\ accounting\   # kapsam: roadmap Faz 1+
├── construction\                # Faz 1+2 — Poz, Malzeme, Yapı Sınıfı, Proje, PozPlan + API
│   └── services.py              # maliyet motoru + s_egrisi_raporu (PV/AV/sapma)
├── docs\proje-kurallari\        # 00-STACK .. 06-ILHAM (bağlayıcı)
├── docs\kurulum.md              # kurulum adımları (§4.1 şema değişikliği, §5 uçlar)
├── memory-bank\                 # bu klasör
├── db\schema.sql                # şema (pg_dump, elle şema yönetimi — migration YOK)
├── db\rls.sql                   # RLS policy'leri (idempotent, 10 tablo)
├── db\tablo_olustur.py          # eksik tabloyu şema oluşturucuyla açan yardımcı
├── docker-compose.yml           # PostgreSQL 16 (5433)
├── requirements.txt, pytest.ini, .env, .env.example, .gitignore
├── site-specification.json      # düzeltildi (tasarım rehberi)
├── roadmap.md                   # (.cline\tasks\roadmap.md ile senkron)
├── frontend\                      # config + src/ (Faz 0 scaffold tamam)
│   ├── src\router\                # /giris, / (panel), /insaat/*, /gayrimenkul/* + guard
│   ├── src\stores\auth.ts         # Pinia JWT store (+ auth.spec.ts)
│   ├── src\services\              # apiClient (Bearer+401 refresh+zarf), zarf, authApi, insaatApi
│   ├── src\views\ src\layouts\    # Giris, Dashboard, Bulunamadi; insaat/ (4 ekran), gayrimenkul/
│   └── src\types\ src\utils\      # api + insaat/gayrimenkul tipleri, rol etiketleri/yetki
```

## Zorunlu 8 kural (özet)
1. Para: Decimal/NUMERIC, float yasak
2. Çift taraflı muhasebe: borç == alacak, kayıt öncesi kontrol
3. Fiziksel DELETE yok — iptal deseni (is_cancelled/cancel())
4. Türkçe karakterler asla ASCII'ye çevrilmez
5. Multi-tenant izolasyonu her katmanda (middleware + RLS)
6. Çoklu tablo işlemi → transaction.atomic()
7. Yetki backend'de zorunlu (DRF permission_classes)
8. Kişisel veri minimize + maskeleme (TCKN, IBAN, telefon)

## Doğrulanan alt-sistemler (FAZ 6F, kodda — 2026-09-23)
- **Güvenlik:** `prod.py` fail-closed (SECRET_KEY + DATABASE_URL yoksa startup
  patlar); `SECURE_SSL_REDIRECT` + HSTS (1 yıl, subdomains, preload) + secure
  session/CSRF cookie; JWT dev 8 sa / prod 15 dk; `token_blacklist` + rotation;
  login kilidi (`users/tokens.py` + `LoginDenemesi`, eşik 5 / 900 sn,
  `users/test_guvenlik.py` 19 test).
- **Yedekleme:** `db_yedekle` (pg_dump + sha256 manifest + Fernet şifreleme +
  30 gün retention + off-site kopya) · `db_restore` (hedef-DB eşleşme + sha256
  kontrolü) · API `/database/backups|create|download|restore` (yalnızca süper
  admin; restore öncesi otomatik güvenlik yedeği) · `sistem_kontrol`
  (db/migration/yedek-yaşı/disk/smoke). ENV: `BACKUP_SAKLAMA_GUN=30`,
  `BACKUP_MAX_YAS_SAAT=26`, `BACKUP_OFFSITE_DIR=""`, `BACKUP_ENCRYPTION_KEY=""`
  (son ikisi manuel go-live kalemi). Excel: template/import/export
  (`event=export` + `event=export_hata` logları; 10.000 satır/sayfa, 100 MB).
- **Audit/logging:** `TenantAuditMiddleware` (mutating metodlar, best-effort,
  `KAYNAK_MODEL` eşlemesi) · `AuditLog.correlation_id` · `IstekBaglamMiddleware`
  (korelasyon ID + `X-Correlation-ID` yanıt başlığı + `SLOW_REQUEST_MS=1000` /
  `SLOW_DB_MS=500` WARNING eşiği) · `LOGGING` console/`erp` formatter (secret
  loglanmaz).
- **Health/readiness:** `GET /api/v1/health/` (liveness, DB sorgusuz) +
  `/health/ready/` (DB + bekleyen-migration sayacı; 503'te sebep sızdırmaz) +
  prod `SECURE_REDIRECT_EXEMPT = ["^api/v1/health/"]` (prob muafiyeti).
- **Yetki matrisi (backend otorite; frontend yalnızca UX maskesi):**
  construction/purchasing yazma = super/tenant/firma admin + maliyet_mühendisi +
  proje_yöneticisi (6C SoD: finans/muhasebe satın almada yazamaz/onaylayamaz);
  cari/finance yazma += muhasebe + finans; muhasebe yazma = adminler + muhasebe
  (finans yazamaz); database_admin = yalnızca süper admin. Frontend:
  `satinAlmaYazabilirMi` backend ile birebir senkron (5/5 test); genel
  `yazabilirMi` inşaat/muhasebe ekranlarında backend'den gevşektir (muhasebe/
  finans butonu görür, backend 403 verir — fail-closed, kritik değil).
- **Prod readiness (kod tarafı):** `check` OK · `check --deploy` güvenlik 0
  (beyan; ENV'li prod ortamında) · `makemigrations --check` temiz ·
  sourcemap kapalı · `console.*` yok · `cariApi` üst-seviye kullanılmayan
  `hareketler` nesnesi yok. Açık (kod dışı): TLS proxy, prod ENV değerleri,
  scheduler, OFFSITE/ENCRYPTION_KEY, log collector+alerting, prod smoke.

## Ortam
- Windows 11 (win32), VS Code; çalışma dizini: c:\proje\emlakpython
- PowerShell; `.venv\Scripts\python.exe` ( collective komutlarda `head` yok —
  `Select-Object -Last` kullanılır)
- Test komutu: `python -m pytest --ignore=frontend` (kökteki ikili
  `frontend/test.txt` yalın `pytest` collection'ını bozar — kod dışı not)
- Dev JWT: access 8 saat (dev.py); prod 15 dk (prod.py); test 5/10 dk (test.py)