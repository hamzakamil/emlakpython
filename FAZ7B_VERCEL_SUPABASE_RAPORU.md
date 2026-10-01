# FAZ 7B — VERCEL + SUPABASE PRODUCTION RAPORU

**Tarih:** 2026-09-23 · **MOD:** analiz (+ minimum düzeltme yetkisi)
**KARAR: DÜZELTME GEREKLİ** — kodda hata yok, repo değişikliği YOK;
düzeltmeler deploy-config + manuel kurulum (aşağıda 7 madde, uygulanabilir içerikle)

## 1. Vercel uyumluluğu (Vercel docs 2026 ile doğrulandı)

- Backend otomatik tanınır: kökte `manage.py` + `requirements.txt` içinde Django +
  `config/wsgi.py` içinde `application` (`WSGI_APPLICATION`) → sıfır-config deploy,
  tek Function (Fluid compute). `vercel.json` zorunlu değil; yalnızca süre ayarı
  için deploy günü eklenir: `{"functions": {"config/wsgi.py": {"maxDuration": 60}}}`.
- ASGI (`config/asgi.py`) de mevcut; WSGI önerilir (soket/uzun-bağlantı yok).
- `CONN_MAX_AGE` tanımsız → default 0 (istek-başı yeni bağlantı): serverless-safe. ✔
- Frontend: `npm run build` → `frontend/dist`, API tabanı relative `/api/v1` → aynı
  domain altında rewrite ile birleşir. Router `createWebHistory()` kullanıyor
  (`router/index.ts:9`) → **SPA rewrite şart**: `rewrites: [{source: "/((?!api).*)",
  destination: "/index.html"}]` (veya dashboard routing rules). Eklenmedi — deploy
  günü 5 satır (gereksiz config yasağına uygun: yalnızca zorunlu olan).
- Static: WhiteNoise YOK, `collectstatic` → `staticfiles/`. Admin arayüzü prod'da
  stilsiz açılır; karar deploy'da: (a) WhiteNoise ekle (tek dep + 1 middleware —
  minimum düzeltme adayı, bugün eklenmedi), veya (b) `staticfiles/` Vercel static
  route'una bağla. İşlevsellik etkilenmez.
- Dosya yüklemeleri (`FileField`: `construction/ifc/%Y/%m/`, `kabul_teminati/`,
  `risk_taniklik/`) `MEDIA_ROOT`'a yazar → Vercel ephemeral FS'de istekler arası
  KAYBOLUR. IFC işleri (`job.file.open`) aynı invocation içinde çalışırsa okunur,
  sonra silinir. Kalıcı belge gerekiyorsa Supabase Storage'a taşınması bir
  özellik işidir (yapılmadı); bugün karar: geçici dosya akışları çalışır, kalıcı
  arşiv beklenmez.

## 2. Supabase PostgreSQL (kod-kanıtlı)

- `DATABASE_URL=postgres://...?sslmode=require` → `env.db()` OPTIONS'a
  `{'sslmode': 'require'}` yazar (doğrulandı) → psycopg SSL zorlar. Kod değişikliği YOK.
- `pg_dump`/`psql` için `PGSSLMODE=require` ENV'i yeter (`_run_db_tool` ortamı
  kopyalar). Kod değişikliği YOK.
- **Bağlantı tipi: DIRECT (5432) zorunlu.** Neden (kritik): dev DB'de 28 tabloda
  RLS policy aktif ve `TenantBaglamMiddleware` her istekte session-seviyesi
  `set_config('app.current_tenant', ...)` yazar. Transaction-mode pooler'da
  session SET'leri işlem sonunda sıfırlanır → RLS bağlamı düşer (fail-closed:
  boş sonuç). Pooler gerekiyorsa yalnızca session-mode; default transaction-mode
  (6543) YASAK. Yeni `purchasing_*`/bildirim/audit tablolarında RLS yok —
  izolasyon orada app katmanında (`TenantScopedViewSet`, testli).
- Supabase Auth'a geçilmedi; mevcut JWT + `Is*Editor` + tenant claim yapısı aynen korunur.

## 3. ENV (Vercel dashboard + migrate çalıştıran makine; değer uydurulmadı)

```
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<50+ (secrets.token_urlsafe(50))>
DATABASE_URL=postgres://<kullanici>:<parola>@<direct-host>:5432/<db>?sslmode=require
PGSSLMODE=require
DJANGO_ALLOWED_HOSTS=<vercel-domain>,<ozel-domain>
DJANGO_CSRF_TRUSTED_ORIGINS=https://<...>
CORS_ALLOWED_ORIGINS=https://<...>
BACKUP_ENCRYPTION_KEY=<Fernet anahtarı>
BACKUP_OFFSITE_DIR=<harici-storage yansitan yol>  # §4'e bak
```

## 4. Backup / restore (model değişikliği)

- Vercel FS kalıcı backup alanı olarak KULLANILAMAZ (`backups/`, manifest, `.fernet`
  invocation sonunda silinir). `db_yedekle`/`db_restore` kodu değişmeden kalır;
  **çalışma yeri değişir:** zamanlanmış yedek, Supabase URL'li harici koşucuda
  (GitHub Actions cron veya mevcut bir makine) çalışır; `BACKUP_OFFSITE_DIR`
  nesne-depolamaya senkronlanan dizin olur.
- Fernet + SHA256 + manifest zinciri aynen korunur (FAZ7'de uçtan uca kanıtlı).
  Restore: aynı koşucudan `db_restore` (çift onay yerleşik) veya Supabase
  dashboard PITR (karar: dosya-tabanlı birincil, PITR ikincil).
- `media/` yüklemeleri bu modele dahil değil (§1 dosya notu).

## 5. Cron / otomasyon

- Vercel Cron + function-içi `pg_dump`: UYGUN DEĞİL (binary yok, süre sınırlı,
  FS ephemeral) — denenmedi, mimari olarak elendi; function'a zorlanmadı.
- Alternatif (servis eklemeden): harici cron (GHA scheduled / mevcut scheduler)
  → `db_yedekle` → manifest kontrolü → başarısızlıkta `erp.backup` ERROR logu +
  alarmlı log takibi. `CRON_SECRET` değerlendirmesi: tetikleyen HTTP uç yok,
  eklenecek uç yok → **gerekmez** (ileride eklenirse o gün korunur).

## 6. Health / monitoring (Vercel + Supabase)

- Liveness `/api/v1/health/`, readiness `/api/v1/health/ready/` (DB + migration
  sayacı) aynen; uptime kontrolü readiness'e bağlanır.
- 5xx + slow request/db (`SLOW_REQUEST_MS=1000`, `SLOW_DB_MS=500`) + correlation
  ID (`X-Correlation-ID` yanıt başlığı) `erp.access` console loglarında → Vercel
  Logs / Log Drain'e akar; ek ajan yok.
- Backup failure: koşucu logu (`erp.backup` ERROR) + `sistem_kontrol` YEDEK-ESKI.
- Disk: serverless'ta yok → DB boyutu Supabase dashboard; yedek dizini koşucuda.

## 7. Deployment sırası

ENV (Vercel + koşucu) → Supabase (direct URL, SSL) → harici makineden
`migrate --plan` → `migrate` → Vercel deploy (backend + frontend, rewrite'larla) →
health/readiness → kullanıcı smoke (login/me) → finansal smoke (cari/fatura/stok okuma).

## 8. Rollback (ayrı)

- **Vercel:** dashboard instant rollback (önceki deployment).
- **Migration:** `migrate <app> <önceki>` (kopya DB'de önce dene); kod rollback'iyle eşzamanlı yapma.
- **Supabase DB:** dosya yedeğinden `db_restore` (birincil) / dashboard PITR (ikincil);
  restore öncesi güncel `db_yedekle` güvenlik ağı. Üç yöntem birbirine karıştırılmaz.

## 9. Testler (bu oturum; kod değişmedi)

`check` OK · `makemigrations --check` temiz · `pytest --ignore=frontend`
**386 passed** · `vue-tsc` 0 · `vitest` **13/13**. `check --deploy`: FAZ7A sonucu
geçerli (tek ERROR `mail.E001`, security 0) — kod aynı.

## Değişen dosyalar / migration / manuel kalanlar

- **Repo:** DEĞİŞİKLİK YOK. **Migration:** YOK. **Yeni doküman:** bu dosya.
- **7 düzeltme maddesi (deploy günü):** (1) SPA+API rewrite'ları, (2) `maxDuration`
  (gerekirse), (3) ENV seti (§3), (4) Supabase direct URL, (5) admin static kararı
  (WhiteNoise/bagh), (6) harici yedek koşucusu + storage, (7) prod MAILERS kararı.
- Supabase Auth geçişi yapılmadı; finansal davranış aynı; tenant yapısı korundu.
