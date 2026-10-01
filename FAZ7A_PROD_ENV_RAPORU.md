# FAZ 7A — PRODUCTION ENV FİNALİZASYON RAPORU

**Tarih:** 2026-09-23 · **MOD:** operasyonel son kontrol (kod değişikliği YOK)
**KARAR: MANUEL KURULUM GEREKLİ** (kodda engel yok; kalanlar gerçek sunucu +
bilgi gerektirir — değer uydurulmadı)

## 1. Zorunlu ENV (koddan çıkarıldı — `config/settings/{base,prod}.py`)

| ENV | Sınıf | Kanıt |
|---|---|---|
| `DJANGO_SECRET_KEY` | fail-closed ZORUNLU | `prod.py:18-34` — dev/default değerle startup patlar (prova edildi) |
| `DATABASE_URL` | fail-closed ZORUNLU | `prod.py:26-29` — yoksa startup patlar (prova edildi) |
| `DJANGO_ALLOWED_HOSTS` | fail-closed ZORUNLU | `prod.py:37` — `env.list` default'suz, eksikse startup patlar |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | go-live ZORUNLU (değer manuel) | `prod.py:54` — default `[]` = kapalı; JWT API etkilenmez |
| `BACKUP_ENCRYPTION_KEY` | go-live ZORUNLU (değer manuel) | boşsa şifresiz yedek + uyarı (prova logunda görüldü) |
| `BACKUP_OFFSITE_DIR` | go-live ZORUNLU (değer manuel) | boşsa off-site kopya yok + uyarı (prova logunda görüldü) |
| `PG_DUMP_PATH` / `PSQL_PATH` | opsiyonel | otomatik keşif çalıştı (PATH + ayar + program dizini) |
| `BACKUP_SAKLAMA_GUN` / `BACKUP_MAX_YAS_SAAT` | opsiyonel (30 / 26) | default devrede |
| `CORS_ALLOWED_ORIGINS` / `IFC_UPLOAD_MAX_BYTES` | opsiyonel | default devrede |

Gerçek prod değerleri bilinmediğinden `.env` / sunucuya yazılmadı; ilk kurulumda
yukarıdaki 6 değer girilecek (runbook sırası §6).

## 2. Backup / off-site (uçtan uca prova edildi)

ENV override ile (`BACKUP_ENCRYPTION_KEY=<geçici Fernet>` +
`BACKUP_OFFSITE_DIR=<geçici dizin>`, kod değişmeden):

- `db_yedekle --etiket faz7a-sifreli` → `.sql.fernet` (625.804 bayt,
  `sifreli:true`, `offsite` yolu manifestte) + off-site kopya birebir mevcut.
- `db_restore` (aynı anahtar) → sha256 + decrypt + uyumluluk ayıklama +
  psql `--single-transaction` → **RESTORE TAMAM**.
- Anahtar güvenliği: `Fernet(anahtar.encode())` — geçersiz anahtar
  `CommandError` verir (`db_yedekle.py:45-51`); anahtar asla loglanmaz
  (loglarda yalnızca dosya adı/boyut/sha256 özeti).
- Prova artefaktları temizlendi; `backups/` içinde yalnızca FAZ7 prova yedeği durur.
- Sonuç: zincir kodda sağlam; prod'da yapılması gereken yalnızca 2 ENV değerini
  girmek + ilk yedek sonrası `sistem_kontrol` YEDEK-satırını görmek.

## 3. mail.E001 (neden + karar)

- Kaynak: Django 6.1 `mail.E001` — `MAILERS["default"]["BACKEND"]`
  (`base.py:166` console) prod-dışı listede. `prod.py` MAILERS'ı ezmiyor.
- Proje kodu **hiç e-posta göndermiyor** (tüm `send_mail` eşleşmeleri venv +
  settings; app kodunda yok). İşlevsel etki: sıfır.
- Buna rağmen `check --deploy` kapısı ERROR ile kırmızı kalır.
- Karar (kod değişmedi): gereksiz SMTP entegrasyonu eklenmedi. Prod'da iki yol:
  (a) gerçek SMTP varsa `MAILERS` prod girdisi (ENV'den host/port/kullanıcı/parola —
  bilgi gelince tek noktadan eklenir); (b) e-posta yoksa kapı bilinçli kabulle
  geçilir. SMTP bilgisi bilinmediğinden varsayımla yazılmadı.
- Not: düzgün uzunlukta anahtarla `check --deploy` çıktısında security-tag
  uyarı **0** (önceki `W009` yalnızca kısa prova anahtarının artefaktıydı).

## 4. Migration drift nedeni (finance_fatura 10 kolon)

Kanıtlar (kod/DB'den, varsayımsız):

1. `django_migrations`: finance 0002→0015 **aynı saniyede** (2026-09-21 01:20:34,
   ~2 ms aralık) — normal ardışık `migrate` çalışması değil, toplu kayıt.
2. Uzlaştırma raporlarında kayıt-uygulamadan-yazma pratiği belgeli
   (construction 0021–0026).
3. `0016_alter_fatura_fatura_turu` (09-22) eksik kolon üzerine ALTER — bu DB'de
   gerçekten çalışmış olamaz.
4. V2 uzlaştırma yalnızca `construction_*` karşılaştırmış (`...construction_* için
   karşılaştırıldı`) — finance kapsam dışı kaldığı için drift yakalanamadı.
5. FAZ7 HTTP smoke yakaladı → yalnızca `sqlmigrate` çıktısıyla onarıldı
   (migration dosyası değişmedi, yeni migration yok).

Sonuç: kayıt–DDL kopukluğu (dev'e özgü, kod dışı). Prod runbook tespiti
(zorunlu adımlar): `migrate --plan` incelemesi → `migrate` → `sistem_kontrol` →
kritik tablolarda HTTP okuma smoke'u (fatura/cari/stok) → şüphede sıfırdan test
DB'si kurup `information_schema` karşılaştırma (V2 yöntemi). Prod'da `--fake` /
kayıt-ile-uzlaştırma yasak.

## 5. Scheduler (Ubuntu VPS)

Komut (aynı): `python manage.py db_yedekle [--etiket gece]` — sıfır-dışı çıkış +
ERROR log; parola/anahtar loglanmaz.

**systemd (önerilen):** `emlak-erp-backup.service` (oneshot; `ExecStart=<venv-python>
<proje>/manage.py db_yedekle --etiket gece`, `WorkingDirectory=<proje>`,
`User=<servis-kullanıcısı>`) + `emlak-erp-backup.timer` (`OnCalendar=daily`,
rastgele gecikme için `RandomizedDelaySec=`). Neden önerilir: journal logu,
başarısızlık görünürlüğü, VPS standardı. Gerçek path/kullanıcı değerleri
kurulumda doldurulacak (uydurulmadı).

**cron (kısa alternatif):** `0 3 * * * cd <proje> && <venv-python> manage.py
db_yedekle --etiket gece >> /var/log/emlak-backup.log 2>&1`.

**Task Scheduler:** yalnızca Windows host'ta; prod hedefi Linux → önerilmez.

## 6. Son testler (bu oturum)

| Kontrol | Sonuç |
|---|---|
| `check` | OK |
| `check --deploy` (ENV'siz) | fail-closed (tasarlanan) |
| `check --deploy` (geçici ENV) | tek ERROR `mail.E001`; security 0; spectacular şema uyarıları (pre-existing) |
| `makemigrations --check` | temiz |
| `pytest --ignore=frontend` | **386 passed, exit 0** |
| `vue-tsc` | exit 0 |
| `vitest` | **13/13 passed** |

## Değişen dosyalar / migration durumu

- **Repo kodu:** DEĞİŞİKLİK YOK. **Migration dosyası:** YOK (üretilmedi/değiştirilmedi).
- **Yeni doküman:** bu dosya + memory-bank Oturum 12.
- Migration zinciri güncel; dev DB FAZ7'de senkronlandı; test DB'si sıfırdan yeşil.

## Kalan manuel işlemler (sıralı)

1. Sunucuda 6 ENV değerini gir (SECRET_KEY 50+ karakter, DATABASE_URL,
   ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, BACKUP_ENCRYPTION_KEY Fernet,
   BACKUP_OFFSITE_DIR mount).
2. Prod MAILERS kararı (SMTP bilgisiyle (a) veya bilinçli kabul (b)).
3. TLS reverse proxy/nginx + Let's Encrypt.
4. Kodu konuşlandır (snapshot önkoşuluyla) → `migrate --plan` → `migrate` →
   `collectstatic` → servis restart (uvicorn+systemd veya Docker — hedefe göre).
5. `sistem_kontrol` + `--kullanici` + HTTP smoke + ilk şifreli/off-site yedek doğrulaması.
6. Günlük scheduler aktivasyonu + log collector/alerting.
