# FAZ 7C — VERCEL + SUPABASE DEPLOY CHECKLIST

**Tarih:** 2026-09-23 · **MOD:** analiz + checklist (kod YOK, migration YOK)
**Mimari:** GitHub → Vercel (Django/Vue) → Supabase PostgreSQL

## 1. DEPLOY DURUMU

**DÜZELTME GEREKLİ** — kod hazır (check OK, makemigrations temiz, pytest 386,
E2E GO); düzeltmeler yalnızca deploy-günü config + manuel kurulum (§10).
Repo/migration değişikliği yapılmadı.

## 2. VERCEL AYARLARI (kesin gerekli)

- Backend proje: root `manage.py` + `requirements.txt` (saf PyPI pinleri, yerel
  bağımlılık yok) + `config/wsgi.py::application` → otomatik Django detection
  (Vercel docs 2026). `vercel.json` zorunlu değil; tek opsiyonel:
  `{"functions": {"config/wsgi.py": {"maxDuration": 60}}}`.
- Frontend proje (`frontend/`): Build `npm ci && npm run build` (vue-tsc + vite),
  output `frontend/dist`. `DJANGO_SETTINGS_MODULE=config.settings.prod` ENV'i şart
  (`wsgi.py` default'u dev'e düşer).
- Routing: frontend `baseURL '/api/v1'` (relative, `apiClient.ts:100`) → aynı
  domainde `/api/*` backend'e rewrite; `createWebHistory()` (`router/index.ts:9`)
  → SPA fallback rewrite (`/((?!api).*)` → `/index.html`) ŞART.
- Health erişimi (kökte `/health` YOK — tam yollar): `GET /api/v1/health/`
  (liveness, DB sorgusuz) + `GET /api/v1/health/ready/` (DB + bekleyen-migration
  sayacı; `SECURE_REDIRECT_EXEMPT` muaf, `prod.py:46`).

## 3. SUPABASE AYARLARI (kesin gerekli)

- **DIRECT connection, port 5432** (pooler yasak): 28 tabloda RLS + her istekte
  session-seviyesi `set_config('app.current_tenant')` (`TenantBaglamMiddleware`) →
  transaction-mode pooler GUC'u sıfırlar (fail-closed boş sonuç). `CONN_MAX_AGE`
  tanımsız (=0): her istek yeni bağlantı, serverless-safe. Ek pooling gerekmez.
- **SSL:** `DATABASE_URL=...?sslmode=require` → `OPTIONS {'sslmode':'require'}`
  (doğrulandı); araçlara `PGSSLMODE=require` ENV'i (`_run_db_tool` ortamı kopyalar).
- Supabase Auth kullanılmaz; JWT (`TenantTokenObtainPairView`) + `Is*Editor` +
  tenant claim aynen korunur. Refresh rotation DB yazar (blacklist tabloları
  zincirde) — direct bağlantıda sorunsuz.

## 4. ENV LİSTESİ

Mevcut (kod default'lu): `BACKUP_SAKLAMA_GUN=30`, `BACKUP_MAX_YAS_SAAT=26`,
`IFC_UPLOAD_MAX_BYTES=50MB`, `CORS_ALLOWED_ORIGINS`, `SLOW_*` sabitleri.
Eksik / **MANUEL OLARAK SAĞLANMALI**: `DJANGO_SECRET_KEY` (50+, fail-closed),
`DATABASE_URL` (direct + `?sslmode=require`, fail-closed), `DJANGO_ALLOWED_HOSTS`
(vercel + özel domain, fail-closed), `DJANGO_CSRF_TRUSTED_ORIGINS` (https),
`CORS_ALLOWED_ORIGINS` (https), `BACKUP_ENCRYPTION_KEY` (Fernet),
`BACKUP_OFFSITE_DIR` (harici storage yolu), `PGSSLMODE=require`
(backup koşucusu). Gerçek değer yazılmadı.

## 5. MIGRATION PLANI

Sıra (harici koşucudan, prod URL ile): `migrate --plan` (incele; yıkıcı işlemde
DUR) → `migrate`. Beklenen: proje app'leri 73 dosya (accounting 8 · audit 2 ·
cari 7 · construction 31 · finance 17 · purchasing 4 · real_estate 1 · tenants 1 ·
users 2) + contrib + `token_blacklist` 12. Sıfır Supabase DB'sine tam zincir
temiz uygulanır (test DB'si her koşuda bunu kanıtlıyor: 386 passed). Supabase
mevcut DB varsa önce `migrate --plan` ile fark kapatılır; `--fake`/kayıt-ile-
uzlaştırma yasak (FAZ7 drift dersi). Doğrulama: readiness `bekleyen_migration:0`.

## 6. STATIC / MEDIA DURUMU

- WhiteNoise YOK (doğrulandı) → `collectstatic` çıktısı `staticfiles/`; admin
  static için karar: (a) WhiteNoise ekle (minimum aday, eklenmedi) veya
  (b) Vercel static route. İşlevsellik etkilenmez.
- Media `FileField` (`construction/ifc/%Y/%m/`, `kabul_teminati/`,
  `risk_taniklik/`) `MEDIA_ROOT`'a yazar → ephemeral'da kalıcı değil. Geçici akış
  (IFC içe aktarma) aynı invocation'da çalışır; kalıcı arşiv Storage taşınması
  özellik işidir (yapılmadı, beklenti yok).

## 7. BACKUP / RESTORE PLANI

Vercel FS kullanılmaz. `db_yedekle`/`db_restore` kodu aynı; **çalışma yeri:**
Supabase URL'li harici koşucu (GHA cron veya mevcut makine) + `BACKUP_OFFSITE_DIR`
nesne-depolamaya senkron dizin. Fernet + SHA256 + manifest korunur (FAZ7A uçtan
uca kanıtlı). Restore: koşucudan `db_restore` (birincil) / Supabase PITR (ikincil).
Vercel Cron varsayılan olarak eklenmez (binary/süre/ephemeral nedeniyle elendi).

## 8. DEPLOY SIRASI (uygulanabilir)

1. Supabase projesi → direct URL + SSL testi. 2. Vercel'e 2 proje (backend root,
   frontend `frontend/`). 3. ENV gir (§4). 4. Koşucudan `migrate --plan` →
   `migrate`. 5. Deploy (rewrite'lar §2 ile). 6. `collectstatic` (build adımında).
   7. Health/readiness. 8. Smoke (§9). 9. İlk şifreli+off-site yedek + manifest
   doğrulaması. 10. Yedek zamanlayıcısı + monitoring bağlanır.

## 9. DEPLOY SONRASI SMOKE TEST

Health 200 → readiness (`bekleyen_migration:0`) → login (token) → me (tenant) →
cari liste → fatura liste + detay → satın alma (talep/sipariş) → mal kabul →
stok (hareket/durum) → muhasebe (plan/fiş/mizan) → logout (refresh revoke).
Referans: SON HAL E2E 13/13 ekran GO, API 4xx/5xx=0.

## 10. RİSKLER / MANUEL İŞLEMLER

- Pooler'a kayma (RLS sessiz kırılır) → URL'i direct tut; readiness + smoke yakalar.
- `vercel.json`/rewrite unutulması (SPA 404) → §2 checklist.
- `MAILERS` console → `check --deploy` E001 (app e-posta göndermiyor; SMTP veya
  bilinçli kabul kararı).
- Media kalıcılığı yok (bilinçli kapsam dışı).
- Gerçek Vercel/Supabase bilgisi yok → yukarıdaki 7 deploy-günü maddesi
  (rewrite, maxDuration, ENV, direct URL, static kararı, yedek koşucusu, MAILERS)
  manuel uygulanacak. Ubuntu/VPS çözümü üretilmedi (hedef-dışı).
