# FAZ 6G — PROJE HAFIZASI SENKRONİZASYON RAPORU

**Tarih:** 2026-09-23 · **MOD:** salt-dokümantasyon
**Kod değişikliği: YOK · Migration: YOK · Test değişikliği: YOK**

Bu rapor, `memory-bank/` içindeki eski bilgilerin kod ağacından doğrulanarak
eşitlenmesinin kaydıdır. Önceki Cline raporları sorgulanmadan doğru kabul
edilmedi; aşağıdakilerin tamamı dosya/komut kanıtlıdır.

## Doğrulama kanıtları (bu oturum, salt-okunur)

| Kontrol | Sonuç |
|---|---|
| `python manage.py check` | OK (0 sorun) |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `python -m pytest --ignore=frontend` | **386 passed, exit 0** (~92 sn) |
| `npm run type-check` (frontend) | temiz, exit 0 |
| `npx vitest run src/utils/yetki.spec.ts` | 5/5 passed |
| `.vue` dosyalarında `console.*` | eşleşme yok |
| `vite.config.ts` | `sourcemap: false` |
| `prod.py` | `SECURE_REDIRECT_EXEMPT = ["^api/v1/health/"]` mevcut |
| `cariApi.ts` | üst-seviye kullanılmayan `hareketler` nesnesi yok |

Not: yalın `pytest` (ignore'suz) kökteki ikili `frontend/test.txt` dosyasında
collection hatası verir; testler `--ignore=frontend` ile koşar (kod dışı not,
düzeltilmedi).

Önceki beyan "Django 385/385" idi; bu oturumda sayılan **386 passed** değeri
dokümana yazıldı (1 fark; yeni test sayımı).

## Eski / yanlış bulunan bilgiler → yeni durum

1. **"Migration KULLANILMAZ, şema `db/schema.sql`"** (memory-bank 3 dosyada) →
   YANLIŞ. Django migration'ları aktif: tenants 1 · users 2 · real_estate 1 ·
   construction 0001→0031 (+0027 reconcile, 0028 merge) · cari 7 · finance 17 ·
   accounting 8 · audit 2 · purchasing 4. `db/schema.sql`, `db/rls.sql`,
   `db/tablo_olustur.py` tarihsel artefakt; otorite değil.
2. **"pytest `--no-migrations` ile şemayı modellerden üretir"** → YANLIŞ.
   `pytest.ini`/`test.py` içinde migration disable yok; migration'lar test
   DB'sinde normal koşuyor.
3. **"`.env.test` 5434 erişilemiyor, pytest beklemede"** (Oturum 8 notu) →
   ESKİ. 386 passed alındı.
4. **FAZ3A_KAPANIS_RAPORU: "`purchasing/models.py` import edilemiyor, proje
   çalışmıyor"** → ÇÖZÜLDÜ. Model içe aktarılıyor, zincir 0001→0004,
   `Depo/MalKabul/MalKabulKalemi/StokHareketi` + `StokHesapEsleme` resmi
   parçadır. Rapor gövdesi tarihsel korundu, başına çözüm notu eklendi.
5. **Ara test sayıları (22/46/62/79/131/208…)** → tarihsel; güncel: 386.
6. **"Sıradakiler: Cari/Finans/Muhasebe ekranları, şantiye günlüğü, taşeron
   hakediş…"** → tamamlandığı doğrulandı (router + ekranlar + testler mevcut).
   Yeni sırada yalnızca 7 manuel go-live maddesi (kod dışı) var.
7. **Paket/port bilgileri (techContext)** → güncellendi (openpyxl,
   cryptography, python-dotenv eklendi; DB bölümü ENV-tabanlı yazıldı).

## Faz durumu (beyan + kod izi mevcut)

FAZ 3A–3C: TAMAM · FAZ 4: TAMAM/DONDURULABİLİR · FAZ 5: TAMAM/DONDURULABİLİR ·
FAZ 6A: TAMAM · 6B: TAMAM · 6C: TAMAM (SoD kodda) · 6D: ANALİZ TAMAM ·
6E: TAMAM · 6F-1…6F-4: TAMAM/GO-LIVE HAZIR (6F-4 maddeleri kodda doğrulandı:
SLOW_DB_MS eşiği + `event=export` logları + health muafiyeti + satın alma SoD
senkronu + sourcemap kapalı + console temizliği).

## Tespit (kritik değil, kod değiştirilmedi)

- İnşaat ekranları frontend `yazabilirMi` kullanır (muhasebe/finans'a yazma
  butonu gösterir) ancak backend `IsConstructionEditor` bu rolleri reddeder;
  aynı durum muhasebe ekranlarında finans rolü için geçerlidir. Backend
  fail-closed olduğundan güvenlik açığı yoktur; UX notu olarak bırakıldı.
- Satın alma tarafında `satinAlmaYazabilirMi` ↔ `IsPurchasingEditor` birebir
  senkron (5 rol, 5/5 test).

## Güncellenen dosyalar

- `memory-bank/activeContext.md` (6G senkron notu + Oturum 10 + güncel kararlar)
- `memory-bank/progress.md` (6G notu + migration düzeltmesi + go-live sırası)
- `memory-bank/techContext.md` (stack/paket/DB/migration + doğrulanmış 6F bölümü)
- `FAZ3A_KAPANIS_RAPORU.md` (başına tarihsel-çözüm notu; gövde korundu)
- `FAZ6G_SENKRON_RAPORU.md` (bu dosya — yeni)

**Kod değişikliği: YOK · Migration: YOK**
