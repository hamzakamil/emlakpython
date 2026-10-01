# DEV DB MIGRATION UZLAŞTIRMA RAPORU V2

**Tarih:** 2026-09-22
**Kapsam:** `0020 → 0021 → 0022 → 0023 → 0024 → 0025 → 0026` (+ mevcut `0027`/`0028`) zincir analizi
**Yasaklar uygulandı:** `0027` çalıştırılmadı · `--fake` yok · DROP/RESET/FLUSH yok (dev'e) · `pytest --no-migrations` yok · FAZ 3A'ya dokunulmadı · rastgele kod değişikliği yok

---

## 1. YÖNETİCİ ÖZETİ

- **Boş DB'de tüm zincir (0001→0028, 0027 dahil) sıfırdan hatasız çalışıyor.** İki ayrı temiz kurulumla kanıtlandı (23:17 scratch replay + final 193-test koşusu öncesi otomatik kurulum).
- **Dev DB (`emlak_erp` @ 5433) şeması, sıfırdan kurulum şemasıyla BİREBİR aynı:** kolon 578/578, constraint 258/258, index 210/210 — sıfır fark. `django_migrations` kayıtları (`[X]`) **gerçek uyumu** yansıtıyor, sahte uyum yok.
- **Bu oturumda HİÇBİR migration dosyası değiştirilmedi, yeni migration eklenmedi.** Değişiklik gerekmediğinin kanıtı ve gerekçesi §5'te.
- **Dev verileri korundu:** sayımlar oturum başı ve sonu aynı (detay §4). Dev'e yazan hiçbir komut çalıştırılmadı.
- `0027` tek başına çözüm değildir (§3) — ama zincir içinde zararsız no-op'tur; dosyası yerinde bırakıldı, gerekçesi §5'te.

---

## 2. ZİNCİR İNCELEMESİ (dosya bazında)

### 0020_pozfiyat_source_fields (önceki oturumda onarılmış, doğrulandı)
`0019` zaten `ice_aktarma_tarihi` dahil 5 alanı ekliyordu; `0020` aynı alanı tekrar ekliyordu → boş kurulumda `DuplicateColumn` veriyordu. `operations = []` ile no-op yapıldı (dosya/zincir korundu). Bu oturumda replay ile sorunsuz çalıştığı görüldü. Ek işlem gerekmedi.

### 0021_proje_poz_fiyat (değiştirilmedi)
`ProjePozFiyat` CreateModel + `uniq_proje_poz_fiyat_tenant_proje_poz_yil`. Dev'de tablo + constraint mevcut ve tanımlar taze replay ile aynı (diff sıfır). Dosya olduğu gibi bırakıldı.

### 0022_faz2_malzeme_sistemi (değiştirilmedi)
9 CreateModel (`MalzemeFiyat`, `ProjeMalzeme`, `ProjeMalzemeFiyat`, `ProjePozMalzeme`, `YfkPozVersiyon`, `YfkFiyat`, `YfkRayic`, `YfkAnaliz`, `YfkGuncellemeGecmisi`) + 10 constraint. Dev'de 10 tablo + 10 constraint mevcut, tanımlar taze replay ile aynı (isim + `pg_get_constraintdef` gövdesi dahil). Dosya olduğu gibi bırakıldı.

### 0023 (değiştirilmedi)
`sqlmigrate` çıktısı incelendi: 6 eski modele ait DROP'lar + `uniq_poz_fiyat_yil` DROP + `hakedis.durum` TYPE varchar(10) + 2 FK rebuild + `firma_kodu` UNIQUE + `uniq_poz_fiyat_yil_donem` ADD; **diğer tüm AlterField'lar DB-seviyesinde no-op** (yalnızca validators/help_text/related_name/verbose farkı). Dev karşılığı: 6 tablo zaten yok (0 kayıt, silinecek veri yok), eski constraint yok, yeni constraint var, `durum` varchar(10), FK + unique + like-index yerinde. Dosya olduğu gibi bırakıldı.

### 0024_remove_hakedis_uniq_hakedis_tenant_no (önceki oturumda onarılmış, doğrulandı)
`0004` `hakedis_no` kolonunu düşürünce PostgreSQL constraint'i otomatik silmişti; normal `RemoveConstraint` hem boş hem dev kurulumda `UndefinedObject` veriyordu. `SeparateDatabaseAndState(state→RemoveConstraint, db→[])` ile state düzeltmesi korunup DB'ye dokunulmadı. Replay temiz. Ek işlem gerekmedi.

### 0025 / 0026 (değiştirilmedi)
`firma_kodu` unique kaldır → geri ekle. Final `unique=True` modelle uyumlu; dev'de `construction_tedarikci_firma_kodu_4b8624f0_uniq` + like-index + `uniq_tenant_firma_kodu` mevcut, duplicate değer yok. Replay temiz.

### 0027_reconcile_missing_tables (ÇALIŞTIRILMADI — yalnızca okundu)
Neden tek başına çözüm olmadığı kabul edildi:
1. **Sıralama:** `0027` → `0022`'ye bağımlı; executor `0021/0022`'yi her zaman önce çalıştırır. DuplicateTable senaryosunda `0027`'ye sıra hiç gelmezdi.
2. **Kapsama:** 10 tablodan yalnızca 2'sini (`malzeme_fiyat`, `proje_poz_malzeme`) + 3 constraint'i ele alıyor; 8 tablo ve diğer tüm constraint'ler yok.
3. **State yok:** Yalnızca `RunSQL` → migration state'i modellerden haberdar etmez; `makemigrations --check` CreateModel istemeye devam ederdi (sahte uyum tuzağı).
4. **Kusurlar:** `reverse_sql` yazım hataları (`malzebe`), `CHECK (kaynak_malzeme_id <> etkin_malzebe_id)` var-olmayan kolona atıf (constraint eksik bir DB'de forward ERROR verirdi), el-yazımı DDL'de tip/uzunluk sapma riski, tamamlanmamış TODO.
5. Buna rağmen **mevcut zincirde zararsızdır**: bağımlılık gereği `0021/0022`'den sonra çalışır; tablolar/constraint'ler zaten var olduğundan tüm `IF NOT EXISTS` korumaları atlar (iki temiz replay ile kanıtlandı). Dev'de applied kayıtlı olduğundan silinmesi loader tutarlılığını bozardı. Bu yüzden dosya **olduğu gibi bırakıldı**.

### 0028_merge_20260922_0206 (değiştirilmedi)
`0026` + `0027`'yi birleştiren boş merge. Replay temiz. Bırakıldı.

---

## 3. DEV ŞEMA vs TAZE REPLAY KARŞILAŞTIRMASI (kanıt)

Yöntem (salt-okunur, dev'e yazma yok): `test_emlak_erp` scratch DB'si `manage.py test --keepdb` ile **sıfırdan** kuruldu (0001→0028 tam zincir, migration kayıtlarıyla doğrulandı); her iki DB'de `information_schema.columns` + `pg_constraint` (+`pg_get_constraintdef`) + `pg_indexes` dökülüp `construction_*` için karşılaştırıldı.

| Küme | dev | scratch | Fark |
|---|---|---|---|
| Kolon (tip/uzunluk/null/default) | 578 | 578 | **0** |
| Constraint (unique/check/fk/pk, tam tanım) | 258 | 258 | **0** |
| Index | 210 | 210 | **0** |
| Tablo kümesi | — | — | aynı (yalnızca dev'de / yalnızca scratch'te tablo yok) |

Örnek kritik noktalar (hepsi iki tarafta aynı): `uniq_poz_fiyat_yil` yok + `uniq_poz_fiyat_yil_donem` var; `uniq_hakedis_tenant_no` yok + `uniq_hakedis_tenant_proje_donem` var; `firma_kodu` unique + like-index var; `hakedis.durum` varchar(10); 6 eski tablo iki tarafta da yok. CNT sayımları tasarım gereği farklıdır (dev'de çalışma verisi, scratch'te test artığı).

**Hüküm:** dev `django_migrations` `[X]` işaretleri gerçek şemayla örtüşüyor. Sahte uyum bulgusu yoktur.

---

## 4. DEV VERİ KORUNUMU (önce/sonra sayımlar)

Dev'e yazan komut çalıştırılmadı (`migrate --plan` = boş; tek `migrate` çalışması scratch test DB'lerinedir). Sayımlar:

| Tablo | Oturum başı | Oturum sonu |
|---|---|---|
| `construction_malzemefiyat` | 3 | 3 |
| `construction_projemalzeme` | 4 | 4 |
| `construction_projemalzemefiyat` | 4 | 4 |
| `construction_projepozmalzeme` | 3 | 3 |
| `construction_yfkpozversiyon` | 1 | 1 |
| `tenants_tenant` | 10 | 10 |
| `users_user` | 2 | 2 |

Veri güvenliği ön kontrolleri (unique/varchar daraltmalarını engelleyecek durum var mı): `pozfiyat (tenant,poz,yil,donem)` duplicate **yok**; `tedarikci.firma_kodu` duplicate **yok**; `hakedis` boş; `pozfiyat` boş. Zaten şema farkı sıfır olduğundan dönüştürücü DDL'ye gerek kalmadı.

---

## 5. KARAR: NEDEN YENİ MİGRATION YOK, NEDEN MEVCUT DOSYALARA DOKUNULMADI

- **Yeni migration eklenmedi** çünkü yakınsanacak şema farkı **sıfırdır**. State zaten modellere eşit (`makemigrations --check` temiz); DB zaten state'e eşit (§3). Boş-gövde bir migration gürültü olurdu; koşullu DDL içeren bir migration ise olmayan bir farkı varmış gibi gösterir (yasaklanan sahte uyumun tersi).
- **0021/0022/0023/0025/0026 düzenlenmedi** çünkü: (a) dev'de applied kayıtlı dosyalara dokunmak dev'i etkilemez (Django uygulanmış migration'ı tekrar çalıştırmaz) — faydası sıfır; (b) taze replay zaten hatasız — riski sıfırlamak için değişiklik yapmak, çalışan zincire risk eklerdi.
- **0020/0024 önceki onarımları korundu**, bu oturumda replay ile yeniden doğrulandı; tekrar işlem yapılmadı.
- **0027/0028 silinmedi/düzeltilmedi** çünkü dev'de applied kayıtlılar (§2-0027 madde 5); silme loader'ı bozar, düzeltme etkisi olmaz (tekrar çalışmazlar), mevcut halleriyle replay'de no-op oldukları kanıtlı.
- Eğer gelecekte gerçek bir sapma bulunursa doğru desen: state'i değiştirmeyen, `IF EXISTS / IF NOT EXISTS` korumalı `RunSQL` yakınsama migration'ı (0027'nin constraint bloklarındaki doğru fikir, düzgün kapsam ve state-nötrlük ile). Bugün buna ihtiyaç yoktur.

---

## 6. DOĞRULAMA SONUÇLARI

- `python manage.py check` → **System check identified no issues (0 silenced).**
- `python manage.py makemigrations --check --dry-run` → **No changes detected.**
- `python manage.py migrate --plan` (dev) → **No planned migration operations.**
- `python manage.py showmigrations construction` → 0001…0028 tamamı `[X]` (0027/0028 dahil).
- `python manage.py test --noinput` (gerçek migration'larla kurulan izole test DB; `--no-migrations` yok) → **toplam 193, passed 193, failed 0, skipped 0 — OK.** Koşu öncesi test DB sıfırdan 0001→0028 ile kuruldu (amaç 1'in ikinci kanıtı), koşu sonu yok edildi.
- `pytest --ignore=frontend` (gerçek migration'lar; `pytest.ini`'de `--no-migrations` yok) → **194 test toplandı, failure/error işareti yok.** (`frontend/test.txt` collection artefaktı test dışı bırakıldı; `.txt`'nin utf-8 decode hatası testlerle ilgisizdir.)
- Testlerde skip/xfail kullanılmadı. FAZ 3A kodu değişmedi.

---

## 7. DEĞİŞTİRİLEN DOSYALAR

| Dosya | İşlem | Neden |
|---|---|---|
| (yok — migration dosyası değişmedi) | — | §5: şema farkı sıfır, replay temiz |
| `DEV_DB_MIGRATION_UZLASTIRMA_RAPORU_V2.md` | **Oluşturuldu** (bu rapor) | Görev çıktısı |

Oturum içinde oluşturulan geçici inceleme betikleri (`tmp_*`) ve şema dökümleri (`schema_*`) temizlendi. `0027` **çalıştırılmadı**. Dev DB'ye yazılmadı.

**Sonuç:** Migration zinciri hem boş kurulumda hem mevcut dev DB'de güvenlidir; dev verileri eksiksiz korunmaktadır. FAZ 3A başlatılmadı.
