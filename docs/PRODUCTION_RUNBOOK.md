# PRODUCTION RUNBOOK — Emlak ERP (Ubuntu VPS)

> Tek dosyalık kurulum + işletim sırası. `<...>` = kurulumda doldurulur (uydurulmadı).
> Örnek domain: `ornek.example.com`. Kod değişikliği gerektirmez.

## 0. Varsayım-dışı envanter (koddan)

- Backend: Django 6.1 + DRF (ASGI: `config.asgi:application`, settings: `config.settings.prod`)
- DB: PostgreSQL (sürücü `psycopg`); worker/Redis yok; ek servis yok (Redis/PgBouncer ekleme)
- Frontend: `npm run build` → `frontend/dist/`; API tabanı relative `/api/v1` (same-origin nginx)
- Komutlar: `db_yedekle` / `db_restore` / `sistem_kontrol [--kullanici]`
- Gerekli araçlar: Python 3.12, Node 20 LTS, PostgreSQL 16, nginx, certbot

## 1. Sunucu hazırlığı

```bash
sudo apt update && sudo apt install -y python3.12-venv postgresql-client nginx certbot python3-certbot-nginx
sudo useradd -m -s /bin/bash <deploy_kullanicisi>
sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp && sudo ufw enable
# PostgreSQL: DB + kullanıcı oluştur (parola kasadan), bağlantıyı test et:
# createdb -h <db_host> -U <db_admin> <db_adi>
```

## 2. ENV (`<proje>/.env`, izin `0600`, git'e girmez)

```ini
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<50+ karakter: python -c "import secrets; print(secrets.token_urlsafe(50))">
DATABASE_URL=postgres://<db_kullanici>:<db_parola>@<db_host>:5432/<db_adi>
DJANGO_ALLOWED_HOSTS=<ornek.example.com>
DJANGO_CSRF_TRUSTED_ORIGINS=https://<ornek.example.com>
CORS_ALLOWED_ORIGINS=https://<ornek.example.com>
BACKUP_ENCRYPTION_KEY=<Fernet: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
BACKUP_OFFSITE_DIR=<offsite_mount_dizini>
```

## 3. Uygulama deployment

```bash
cd <proje> && python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
# NOT: prod servis için ASGI sunucusu gerekir (örn. uvicorn); requirements'ta yok —
# kurulumda eklenir (.venv/bin/pip install "uvicorn[standard]").
.venv/bin/python manage.py migrate --plan   # incele: yıkıcı işlem varsa DUR
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
cd frontend && npm ci && npm run build && cd ..
sudo systemctl restart emlak-erp
```

`emlak-erp.service` (systemd):

```ini
[Unit]
Description=Emlak ERP backend
After=network.target postgresql.service
[Service]
User=<deploy_kullanicisi>
WorkingDirectory=<proje>
EnvironmentFile=<proje>/.env
ExecStart=<proje>/.venv/bin/uvicorn config.asgi:application --host 127.0.0.1 --port 8000
Restart=on-failure
[Install]
WantedBy=multi-user.target
```

## 4. HTTPS (nginx + TLS)

```nginx
server {
  listen 80; server_name <ornek.example.com>;
  location / { return 301 https://$host$request_uri; }
}
server {
  listen 443 ssl; server_name <ornek.example.com>;
  # ssl_certificate ... (certbot üretir: sudo certbot --nginx -d <domain>)
  root <proje>/frontend/dist; index index.html;
  location /static/ { alias <proje>/staticfiles/; }
  location /api/ { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host; }
  location / { try_files $uri $uri/ /index.html; }
}
```

Django proxy ayarı kuralı: repoda `SECURE_PROXY_SSL_HEADER` **yok** ve yokken
eklenmez (spoof riski). nginx TLS sonlandırıp HTTP ile backend'e geçerse Django
`http` görür — bu kurulumda `SECURE_SSL_REDIRECT=True` + health muafiyeti
(`SECURE_REDIRECT_EXEMPT`) bunu tolere eder. `SECURE_PROXY_SSL_HEADER` **yalnızca**
proxy'nin `X-Forwarded-Proto` yazdığı sözleşmeyle kurulursa tek satır eklenir;
sözleşmesiz ekleme YASAK.

## 5. İlk doğrulama (sırayla)

```bash
.venv/bin/python manage.py sistem_kontrol
.venv/bin/python manage.py sistem_kontrol --kullanici <tenantli_kullanici>
curl -s https://<domain>/api/v1/health/            # {"success":true,...}
curl -s https://<domain>/api/v1/health/ready/       # db:ok, bekleyen_migration:0
# login → /auth/me (tenant) → /cari/cariler → /finance/faturalar →
# /purchase-mal-kabul → /purchase-stok-hareketleri (hepsi 200)
```

Kabul eşiği: `sistem_kontrol` TAMAM + ready `bekleyen_migration:0` + 7 uç 200.

## 6. Backup (ilk üretim yedeği)

```bash
.venv/bin/python manage.py db_yedekle --etiket ilk-uretim
# manifestte: sha256 + boyut + sifreli:true + offsite yolu → dosyayı off-site'ta gör
.venv/bin/python manage.py sistem_kontrol   # YEDEK: OK (<26 sa)
```

Restore provası (kopya DB önerilir; canlıda yalnızca gerekirse):
önce güncel `db_yedekle` (güvenlik ağı) →
`db_restore --dosya=<yedek> --hedef-db-adi=<db_adi> --onay=EVET-EMINIM` →
`sistem_kontrol --kullanici` + smoke. **Yedek dosyası doğrulanmadan
(manifest sha256 + restore provası) silinmez.**

## 7. Scheduler (günlük yedek)

`emlak-erp-backup.service` (oneshot: `.../manage.py db_yedekle --etiket gece`,
aynı `User`/`EnvironmentFile`) + `emlak-erp-backup.timer`
(`OnCalendar=daily`, `RandomizedDelaySec=15m`, `Persistent=true`).
Kontrol: `systemctl status emlak-erp-backup.timer`, `journalctl -u emlak-erp-backup`.
Başarısızlık journal'a + ertesi `sistem_kontrol` YEDEK-ESKI uyarısına düşer.
cron alternatifi: `0 3 * * * cd <proje> && .venv/bin/python manage.py db_yedekle
--etiket gece >> /var/log/emlak-backup.log 2>&1`.

## 8. Monitoring (ek servis yok)

| Sinyal | Kaynak | Eşik/aksiyon |
|---|---|---|
| readiness | `GET /api/v1/health/ready/` | 503 veya `bekleyen_migration>0` → alarm |
| 5xx | `erp.access` WARNING (`... 5xx ...`) | log tara, alarm |
| backup failure | `erp.backup` ERROR + YEDEK-ESKI/YEDEK-YOK | alarm |
| slow request/db | `event=yavas_veya_hata` (>1000 ms istek / >500 ms DB) | inceleme |
| disk | `sistem_kontrol` DISK (<1 GB uyarı) | temizlik/off-site |

## 9. Rollback (ayrı senaryolar, karıştırma)

Önkoşul: her deploy öncesi dizin snapshot'ı (`.venv/`, `node_modules/`,
`backups/`, `media/`, `staticfiles/` hariç).

- **A — uygulama kodu:** durdur → snapshot'ı geri kopyala → collectstatic →
  başlat → `sistem_kontrol` + smoke. (Migration çalışmadıysa DB'ye dokunma.)
- **B — migration sorunu:** yalnızca ilgili app `migrate <app> <önceki>`;
  geri yön önce kopya DB'de denenir. Kod geri almayla aynı anda yapma.
- **C — DB restore:** güncel `db_yedekle` → `db_restore` (çift onay yerleşik) →
  `sistem_kontrol --kullanici` + smoke. Hangi durumda: veri bozulması/kayıp;
  kod hatasında A, şema hatasında B kullanılır.

## 10. SON KABUL CHECKLISTI (GO-LIVE HAZIR için hepsi ✓)

- [ ] §2 altı ENV girili, `.env` 0600, fail-closed startup geçti
- [ ] `migrate --plan` temiz → `migrate` → `collectstatic` → servis ayakta
- [ ] HTTPS açık, HTTP→HTTPS yönleniyor, health muafiyeti çalışıyor
- [ ] `sistem_kontrol` + `--kullanici` TAMAM; §5 yedi uç 200
- [ ] İlk şifreli + off-site yedek + manifest doğrulandı; restore provası TAMAM
- [ ] Günlük timer aktif (`status` + ilk otomatik çalışma görüldü)
- [ ] Monitoring 5 sinyali bağlı (readiness/5xx/backup/slow/disk)
- [ ] Rollback snapshot prosedürü test edildi
- [ ] `check --deploy`: mail.E001 kararı kapalı (SMTP ENV veya bilinçli kabul)
- [ ] Regression yeşil: pytest 386 · check · makemigrations · vue-tsc · vitest 13
