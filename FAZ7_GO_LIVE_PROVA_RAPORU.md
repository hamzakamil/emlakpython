# FAZ 7 — GO-LIVE DEPLOYMENT PROVASI RAPORU

**Tarih:** 2026-09-23 · **MOD:** operasyon + test · **Ortam:** dev (Docker DB, port 5433)
**KARAR: DÜZELTME GEREKLİ** (kod davranışı sağlam; eksikler prod ENV + posta kararı + zamanlayıcı aktivasyonu — tamamı kod dışı)

## 1. ENV durumu

Prod'da zorunlu (koddan — `config/settings/prod.py` + `base.py`):

| ENV | Durum | Not |
|---|---|---|
| `DJANGO_SECRET_KEY` | fail-closed doğrulandı | ENV yoksa startup `ImproperlyConfigured` ile patlar (prova edildi) |
| `DATABASE_URL` | fail-closed doğrulandı | yoksa startup patlar |
| `DJANGO_ALLOWED_HOSTS` | prod'da değer ŞART | `env.list` default'suz — eksikse startup patlar |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | prod değerleri ŞART (manuel madde) | default `[]` = kapalı; JWT API CSRF gerektirmez |
| `BACKUP_ENCRYPTION_KEY` | **EKSİK (dev boş)** | boşsa şifresiz yedek + `event=yedek_sifresiz` uyarısı (prova logunda görüldü) |
| `BACKUP_OFFSITE_DIR` | **EKSİK (dev boş)** | boşsa off-site kopya yok + `event=yedek_offsite_yok` (prova logunda görüldü) |
| `PG_DUMP_PATH` / `PSQL_PATH` | opsiyonel | otomatik keşif çalıştı (PATH + `C:/Program Files/PostgreSQL` + ayar) |
| `BACKUP_SAKLAMA_GUN=30`, `BACKUP_MAX_YAS_SAAT=26` | default'lar devrede | ENV ile ezilebilir |

Dev `.env` anahtarları: `DJANGO_SETTINGS_MODULE`, `DJANGO_SECRET_KEY`,
`DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`, `CORS_ALLOWED_ORIGINS`
(değerler rapora yazılmadı).

## 2. HTTPS / proxy durumu

- Repoda nginx/Docker(prod)/Dockerfile yok; `docker-compose.yml`yalnızca dev DB.
- `SECURE_PROXY_SSL_HEADER` **tanımlı değil** — bilinçli (FAZ 6F-1 §2.3: proxy
  yokken tanımlamak spoof riski). **EKLENMEDİ** (görev kuralı + kod notu aynı yönde).
- `prod.py`: `SECURE_SSL_REDIRECT=True` + HSTS (1 yıl, subdomains, preload) +
  `SECURE_REDIRECT_EXEMPT=["^api/v1/health/"]` (prob muafiyeti kodda).
- Sonuç: TLS sonlandırma reverse proxy/nginx'de yapılacak (manuel madde).
  Proxy kurulduğunda header sözleşmesi (`X-Forwarded-Proto`) o gün netleşip
  tek satırla eklenir; bugün eklenmemesi doğru karardır.

## 3. Backup / restore (prova edildi)

- `db_yedekle --etiket faz7-prova` → **OK**: `emlak_erp_20260923_133058_faz7-prova.sql`
  (466.121 bayt) + `.manifest.json` (`sifreli:false`, `offsite:""`).
- Manifest sha256 bağımsız doğrulandı (`Get-FileHash`): birebir eşleşti.
- `db_restore --dosya=... --hedef-db-adi=emlak_erp --onay=EVET-EMINIM` →
  **RESTORE TAMAM** (round-trip; `transaction_timeout` uyumluluk ayıklama yolu da çalıştı).
- Fernet şifreleme round-trip bağımsız doğrulandı (eşit hash).
- Şifreli yedek + off-site kopya **dev'de doğrulanamadı** (ENV boş) — prod'da
  ilk `db_yedekle` sonrası `sistem_kontrol` YEDEK-satırı ile doğrulanacak.
- Restore sonrası `sistem_kontrol --kullanici smoke-finans`: DB OK, MIGRATION OK,
  YEDEK OK (0.0 sa), DISK OK, SMOKE OK (tenant=175, fatura=3, stok=0).

## 4. Deployment sırası (prova edilen)

1. Güvenlik ağı: dumpdata (Temp; 204 KB) — pg_dump yedeğinden ÖNCE ek güvence.
2. `db_yedekle` → OK (yukarıda).
3. `migrate --plan` → 15 işlem, tamamı eklemeli (audit kolonu, purchasing KDV,
   token_blacklist 12, LoginDenemesi); yıkıcı işlem yok.
4. `migrate` → **15/15 OK** (dev DB artık güncel).
5. `collectstatic --noinput` → **157 dosya OK** (`staticfiles/` gitignore'lu).
6. Restart → prod'da servis restart (aşağıda runbook); provada dev runserver kullanıldı.
7. `sistem_kontrol` → TAMAM; `sistem_kontrol --kullanici smoke-finans` → TAMAM.

## 5. Smoke (gerçek HTTP, 127.0.0.1:8001)

| Kontrol | Sonuç |
|---|---|
| `GET /api/v1/health/` | 200 `{"success":true,"data":{"status":"ok"}}` |
| `GET /api/v1/health/ready/` | 200 `db:ok, bekleyen_migration:0` |
| `POST /auth/token/` (smoke-finans) | 200, access 311 karakter |
| `GET /auth/me/` | tenant=175, "Smoke Finans" (ilk denemede `tenant_id` alan adı yanlış okundu; API doğru — `tenant` pk döner) |
| `GET /cari/cariler/` | 200, 2 kayıt |
| `GET /finance/faturalar/` | önce **500 ProgrammingError** → dev drift onarımı sonrası **200, 3 kayıt** (tamamı tenant=175) |
| `GET /purchase-mal-kabul/` | 200, 0 kayıt |
| `GET /purchase-stok-hareketleri/` | 200, 0 kayıt |

Prova notu (dev-only, operasyonel): smoke-finans parolası `Prova123!` olarak
ayarlandı; sunucu prova sonrası durduruldu.

## 6. Kritik bulgu: dev finance_fatura şema kayması (ONARILDI, dev-only)

- `finance` 0009–0017 `django_migrations`'ta `[X]` görünmesine rağmen
  `finance_fatura` tablosunda 10 kolon eksikti (0009'un 9'u + 0010 `iade_faturasi_id`).
  `dumpdata` ve fatura listesi bunu düşürdü; test DB'si (sıfırdan kurulum) etkilenmez.
- Nedeni kod dışı (geçmişte kayıtsız şema müdahalesi); migration dosyalarına dokunulmadı.
- Onarım: **yalnızca Django `sqlmigrate` çıktısı** çalıştırıldı (el SQL yok):
  0009 (9 kolon) + 0010 (FK + index). Sonrası fatura 200 + pytest 386 yeşil.
- Prod dersi: `django_migrations` geçmişi her zaman gerçeği yansıtmaz → prod'da
  `migrate --plan` + `sistem_kontrol` + HTTP smoke üçlüsü şart (runbook'a eklendi).

## 7. Rollback senaryoları (birbirinden ayrı; git yok — dosya snapshot şart)

Önkoşul (her deploy öncesi): proje dizini snapshot'ı
(`.venv/`, `node_modules/`, `backups/`, `media/`, `staticfiles/` hariç).

- **A — yalnızca uygulama kodu:** servisi durdur → snapshot'ı geri kopyala →
  `collectstatic --noinput` → servis başlat → `sistem_kontrol` + smoke.
  Migration çalışmadıysa DB'ye dokunulmaz.
- **B — migration geri alma (ayrı senaryo):** yalnızca ilgili app için
  `migrate <app> <önceki>`; geri yönde veri kaybı riski olan işlemler prod'da
  önce kopya DB'de denenir. Kod geri alma ile aynı anda yapılmaz.
- **C — DB restore (ayrı senaryo):** önce güncel `db_yedekle` (güvenlik ağı) →
  `db_restore --dosya=... --hedef-db-adi=<ad> --onay=EVET-EMINIM` (hedef adı +
  sha256 kontrolü yerleşik) → `sistem_kontrol --kullanici ...` + smoke.
- Karıştırma yasağı: kod geri alırken DB'ye dokunma; DB restore ederken kodu
  değiştirne; migration geri alırken yedeksiz ilerleme.

## 8. Scheduler (günlük `db_yedekle`)

Gerçek komut (tüm platformlarda aynı):
`python manage.py db_yedekle [--etiket gece]` (sıfır-dışı çıkış + ERROR log;
parola/anahtar loglanmaz). Başarısızlık `sistem_kontrol` YEDEK-ESKI uyarısına düşer.

- **systemd (önerilen — prod hedefi Ubuntu VPS):** `emlak-erp-backup.service` +
  `emlak-erp-backup.timer` (günlük 03:00). Neden: log journal'da, başarısızlık
  görünür, VPS standardı.
- **cron (alternatif):** `0 3 * * * cd /srv/emlakpython && .venv/bin/python manage.py db_yedekle --etiket gece >> /var/log/emlak-backup.log 2>&1`.
- **Task Scheduler (yalnızca Windows host):** prod hedefi Linux olduğundan
  önerilmez; bu makinedeki prova için kullanılabilir.
- Kod varsayımı yok: prod host OS + servis yöneticisi kullanıcı tarafından
  netleştirilince yukarıdaki üç seçenekten biri aktive edilir (manuel madde).

## 9. Son regression (prova sonrası)

| Kontrol | Sonuç |
|---|---|
| `python -m pytest --ignore=frontend` | **386 passed, exit 0** |
| `manage.py check` | OK |
| `manage.py check --deploy` (ENV'siz prod) | fail-closed `ImproperlyConfigured` (tasarlanan) |
| `manage.py check --deploy` (geçici ENV) | **1 ERROR: mail.E001** (aşağıda) + spectacular uyarıları (şema-only); security-tag 0 |
| `makemigrations --check` | temiz |
| `npm run type-check` | exit 0 |
| `npx vitest run` | **13/13 passed** |

**mail.E001 notu (DÜZELTME maddesi, kod değişmedi):** `base.py:166` `MAILERS`
console backend'i prod'da deploy ERROR'u üretir. Proje kodu hiç e-posta
göndermiyor (send_mail kullanımı yok) — etki sıfır, ancak `check --deploy`
kapısı kırmızı kalır. Çözüm prod SMTP bilgisiyle `MAILERS` prod girdisi
(ENV'den); gerçek SMTP bilgisi bilinmediğinden varsayımla yazılmadı.

## Değişen dosyalar / migration

- **Repo kodu:** DEĞİŞİKLİK YOK. **Migration:** YOK (dosya üretilmedi/değişmedi).
- **Dev DB (operasyonel):** 15 bekleyen migration uygulandı + finance_fatura
  10 kolon onarımı (sqlmigrate çıktısı) + smoke-finans parola reseti.
- **Üretilen artefaktlar:** `backups/emlak_erp_20260923_133058_faz7-prova.sql` +
  manifest (gitignore'lu); `staticfiles/` (gitignore'lu); Temp: dumpdata güvenlik
  ağı + prova betiği (repo dışı).
- **Yeni doküman:** bu dosya (`FAZ7_GO_LIVE_PROVA_RAPORU.md`).

## Manuel kalanlar (kod dışı)

TLS proxy/nginx · prod ENV değerleri (SECRET_KEY, DATABASE_URL, ALLOWED_HOSTS,
CSRF_TRUSTED_ORIGINS) · BACKUP_OFFSITE_DIR + BACKUP_ENCRYPTION_KEY · prod
MAILERS kararı · günlük scheduler aktivasyonu · log collector + alerting ·
gerçek prod deploy + smoke.
