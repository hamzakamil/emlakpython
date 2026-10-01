# Kurulum — Emlak ERP (Geliştirme Ortamı)

## Gereksinimler
- Windows 10/11, Python 3.12+
- Docker Desktop (PostgreSQL 16 konteyneri için)

> ⚠ **Windows notu:** Makinede 127.0.0.1:5432'yi dinleyen `postgres.exe`
> (PID ile sabitlenmiş yerel bir PostgreSQL servisi) bulunuyor. Çakışmamak için
> Docker DB dışarıdan **5433** portundan yayınlanır (`docker-compose.yml` ve
> `.env` buna göre ayarlıdır).

## 1. Bağımlılıklar
```powershell
python -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt
```

## 2. Veritabanı (Docker)
```powershell
docker compose up -d db
docker compose ps   # emlak_erp_db (healthy) olmalı
```

Konteyner ilk çalıştırıldığında:
- DB: `emlak_erp`
- Kullanıcı: `emlak` / şifre `emlak_dev_password` (sadece yerel geliştirme)
- Host port: **5433**

## 3. Ortam değişkenleri
`.env.example` kopyala → `.env` (yerel geliştirme için `.env` zaten oluşturulmuştur).

```powershell
Copy-Item .env.example .env
```

| Değişken | Açıklama |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` / `config.settings.prod` |
| `DJANGO_SECRET_KEY` | prod'da 32+ byte güçlü/saklı anahtar |
| `DJANGO_DEBUG` | dev `True`, prod `False` |
| `DATABASE_URL` | `postgres://emlak:emlak_dev_password@localhost:5433/emlak_erp` |

## 4. Şema + süper kullanıcı

> **Migration kullanılmaz.** Şema `db/schema.sql` (pg_dump çıktısı) içinde
> version-controllu tek dosyada tutulur.

Boş/yeni veritabanında şemayı kurmak için (mevcut `emlak_erp_db` zaten kuruludur):
```powershell
Get-Content db\schema.sql -Raw | docker exec -i emlak_erp_db psql -U emlak -d emlak_erp
```

Süper kullanıcı:
```powershell
$env:DJANGO_SUPERUSER_PASSWORD="admin123"
.venv\Scripts\python.exe manage.py createsuperuser --noinput --username admin --email admin@example.com
```

> Not: Model değişiklikleri otomatik şema güncellemesi üretmez; şema yalnızca
> `db/schema.sql`'den yönetilir. Şema değişikliği elle `ALTER` SQL ile (ya da
> değişen modeller için pg_dump'ın tazelenmesiyle) uygulanır.

### 4.1 Yeni tablo ekleme (dev)

`db/tablo_olustur.py` eksik tabloları modellerden üretir (idempotent):

```powershell
.venv\Scripts\python.exe db\tablo_olustur.py construction.PozPlan
```

Sıra: (1) tabloyu oluştur, (2) `db/rls.sql`'i yeniden uygula (tenant policy'si
yeni tablo için de kurulur — tablo listesi `db/rls.sql` içindedir), (3)
`db/schema.sql`'i tazele:

```powershell
Get-Content db\rls.sql -Raw | docker exec -i emlak_erp_db psql -U emlak -d emlak_erp
cmd /c "docker exec emlak_erp_db pg_dump -U emlak -d emlak_erp --schema-only --exclude-table=django_migrations > db\schema.sql"
```

### 4.2 Veritabanı Yönetimi

Süper admin, frontend içindeki **Veritabanı Yönetimi** ekranından tablo ağacını,
kolonları ve sayfalı kayıtları görebilir. Birincil anahtarlı kayıtlarda yalnızca
güvenli alanlar düzenlenebilir; parola, tenant, kimlik ve oluşturulma alanları
salt okunurdur. Ham SQL ve fiziksel tablo silme bilinçli olarak kapalıdır.

- Yedek oluşturma: `pg_dump` ile `backups/` klasörüne tam `.sql` dump alınır.
- Geri yükleme: yalnızca `.sql` dosyası ve `RESTORE DATABASE` onayı kabul edilir;
  işlemden önce otomatik `pre_restore_*.sql` güvenlik yedeği oluşturulur.
- Araç yolu: `PG_DUMP_PATH` ve `PSQL_PATH` ortam değişkenleri verilebilir; yoksa
  PATH ve Windows PostgreSQL kurulum yolları aranır.
- API: `/api/v1/database/`; tüm uçlar yalnızca `is_superuser` kullanıcılarına açık.

#### Excel ile veri yükleme

Veritabanı ekranında tablo ağacındaki kutulardan tabloları seçin ve **Excel
şablonu indir** düğmesine basın. İndirilen dosyada her tablo ayrı sayfadır;
`Talimatlar` sayfası ve uzun tablo adları için gizli `__TabloEsleme` sayfası
bulunur. Şablondaki başlıkları değiştirmeden satırları doldurun.

1. Hedef tenant'ı seçin (tenant alanı olan tablolar için zorunludur).
2. Excel dosyasını seçin.
3. Önce **Önce sadece doğrula** seçeneğiyle dry-run çalıştırın.
4. Hatalar yoksa seçeneği kapatıp **Excel verilerini yükle** düğmesine basın.

İçe aktarma tek transaction'dır; bir satırda hata olursa workbook'un hiçbir
sayfası yazılmaz. `id`, tenant, parola, audit tarihleri ve oluşturan kullanıcı
şablona alınmaz; audit alanları sistem tarafından doldurulur. İlişkili alanlarda
ilgili kaydın numeric id değeri kullanılmalıdır. Kullanıcı tablosu gibi parola
gerektiren sistem tabloları Excel ile oluşturulmak yerine yönetim panelinden
veya özel kullanıcı akışından yönetilmelidir.

**Mevcut veriyi dışa aktarma:** Aynı tablo ve alan seçimleriyle **Mevcut verileri
Excel'e aktar** düğmesi seçilen kayıtları dolu `.xlsx` dosyası olarak indirir.

Yedekleri kaynak kontrole almamak için `.gitignore` içinde `backups/*.sql` kuralı
vardır. Üretimde `DB_BACKUP_DIR` uygulama web kökü dışında, erişim kontrollü bir
disk veya nesne depolama alanına yönlendirilmelidir.

## 5. Çalıştırma
```powershell
.venv\Scripts\python.exe manage.py runserver
```

- Health: http://127.0.0.1:8000/api/v1/health/
- JWT token: POST `http://127.0.0.1:8000/api/v1/auth/token/`
- Swagger: http://127.0.0.1:8000/api/v1/docs/
- Admin: http://127.0.0.1:8000/admin/

Faz 2 (poz planı) uçları:

| Uç | Açıklama |
|---|---|
| `GET/POST/PATCH /api/v1/construction/poz-planlari/` | Planlanan/gerçekleşen metraj (filtre: `proje`, `poz`, `yil`) |
| `GET /api/v1/construction/poz-planlari/s-egrisi/?proje=<id>&yil=<yıl>` | PV/AV/sapma raporu (tenant izole) |

## 6. Test
```powershell
.venv\Scripts\python.exe -m pytest
```

## 7. ÇŞİDB verisi içe aktarma (Faz 1 — poz parser)

Kaynak veri (ÇŞİDB tebliği / acikpoz vb.) CSV'ye dönüştürülerek içe alınır.
Örnek şablonlar: `docs/ornekler/import_poz_ornek.csv` ve
`docs/ornekler/import_yapi_sinifi_ornek.csv` (ayraç `;`, ondalık ayraç nokta,
kodlama UTF-8 — Excel'de "UTF-8 CSV" olarak kaydedin).

Pozlar (PozGrubu + Poz + yıl bazlı PozFiyat):
```powershell
.venv\Scripts\python.exe manage.py import_pozlar --tenant insaat `
    --dosya pozlar.csv --yil 2026 --kaynak "ÇŞİDB 2026 tebliği" --arsivle 2025
```

Yapı sınıfı birim maliyetleri (`4A` girişi otomatik `IV-A`'ya normalize edilir):
```powershell
.venv\Scripts\python.exe manage.py import_yapi_sinifi --tenant insaat `
    --dosya yapi_sinifi.csv
```

Kurallar:
- Tek transaction + fail-fast: bir satır hatalıysa tüm import geri alınır.
- Hiçbir kayıt silinmez; `--arsivle YIL` verilen yıla ait aktif fiyatı olup
  yeni importta gelmeyen pozlar `is_active=False` ile arşivlenir.
- Aynı `poz_no` tekrar içe alınırsa kart güncellenir (idempotent); fiyatlar
  yıl bazlı version'lanır. `birim_fiyat` sütunu boşsa yalnızca poz kartı alınır.
- `--tenant` zorunludur; veri seçilen tenant'a izole şekilde yazılır.

## 8. RLS — tenant izolasyonu DB katmanında

Plan: `docs/rls-plani.md` · Script: `db/rls.sql` (idempotent).

```powershell
Get-Content db\rls.sql -Raw | docker exec -i emlak_erp_db psql -U emlak -d emlak_erp
```

- Middleware (`tenants/middleware.py`) her istekte `app.current_tenant`
  değişkenini ayarlar; anonim/geçersiz isteklerde boş bırakılır.
- Geliştirmede tablo sahibi (`emlak`) RLS'den muaftır (FORCE kapalı) — uygulama
  ve komutlar etkilenmez; izolasyon `rls_deneme` rolüyle doğrulanır (plan §6).
- Üretimde ayrı uygulama rolü + `FORCE ROW LEVEL SECURITY` (plan §5 kontrol listesi).

## Modül yapısı
```
config/settings/   # base.py + dev.py + prod.py
tenants/           # Tenant + TenantAwareModel + tenant izolasyon çekirdeği (api.py, middleware.py)
users/             # User (AbstractUser + tenant + rol)
real_estate/       # Gayrimenkul (proje FK)
construction/      # İnşaat: Poz, PozGrubu, Malzeme, PozFiyat, Yapı Sınıfı, Proje, PozPlan (metraj)
                   #   imports.py (ÇŞİDB CSV parser) + services.py (maliyet motoru, S-eğrisi)
db/schema.sql      # şema (pg_dump) — migration YOK
db/rls.sql         # RLS policy'leri (idempotent)
db/tablo_olustur.py# eksik tabloları şema oluşturucuyla açan yardımcı
cari/               # Cari kartlar + cari hareketler (API + izolasyon)
finance/            # Kasa/banka hesapları + finansal işlemler
accounting/         # Hesap planı + muhasebe fişleri (borç==alacak doğrulamalı)
# Hakediş akışı: construction/ (Hakedis modeli + services.hakedis_onayla —
# onayda CariHareket + MuhasebeFişi üretir; frontend HakedislerView.vue)
frontend/          # Vue 3 + TS + Pinia + Tailwind (src/)
```