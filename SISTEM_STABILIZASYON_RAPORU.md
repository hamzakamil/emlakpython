# SİSTEM STABİLİZASYON RAPORU

**Tarih:** 2026-09-23  
**Kapsam:** Bağımsız audit bulguları — construction migration drift + test DB / email unique  
**Kural:** FAZ 3A'ya geçilmedi. Yeni model/özellik geliştirilmedi. `users.User.email` production modeline dokunulmadı. `--fake` kullanılmadı. skip/xfail kullanılmadı.

---

## 0. KULLANICININ YAPTIKLARI vs BU OTURUMDA TAMAMLANANLAR (tespit)

Kullanıcı oturum öncesi şunları **yapmıştı** (doğrulandı, tekrar değiştirilmedi):

- `construction` için **0023** migration dosyası oluşturulmuş (6 eski modelin silinmesi + alan/constraint düzeltmeleri). Peşinden **0024, 0025, 0026** de oluşturulmuş.
- `pytest.ini` içinden `--no-migrations` kaldırılmış (dosya şu an sadece `DJANGO_SETTINGS_MODULE`, `python_files`, `addopts = -q` içeriyor).
- `conftest.py` içinde `test_user` fixture'ı `uuid` ile unique email üretecek şekilde düzeltilmiş.
- `conftest.py` içinde custom `django_db_setup` **yok** (kaldırılmış) → pytest-django varsayılanı devrede, test DB gerçek migration'larla kuruluyor.
- `config/settings/test.py` içinde `MIGRATION_MODULES = DisableMigrations()` satırı yoruma alınmış.
- `accounting/tests.py`, `cari/tests.py`, `finance/tests.py`, `construction/tests.py` içindeki `create_user` çağrıları `uuid` unique email kullanacak şekilde düzeltilmiş.
- `users/models.py` içinde `email = models.EmailField(unique=True)` **korunmuş** (production modeline dokunulmamış — doğru).

Bu oturumda **kalanlar tamamlandı**:

1. `tests/test_fatura.py` ve `tests/test_audit.py` — email'siz `create_user` düzeltilmediğini tespitini tespit edip düzelttim (audit'teki 4 failing testin gerçek kaynağı buydu).
2. `conftest.py` içindeki `test_tenant` fixture'ı bozuktu (`ad/email/telefon/adres` alanları `tenants.Tenant` modelinde yok) → `name/slug` + unique slug ile düzelttim.
3. `construction/migrations/0020_pozfiyat_source_fields.py` içindeki **yinelenen AddField** onarıldı (detay §1).
4. `construction/migrations/0024_remove_hakedis_uniq_hakedis_tenant_no.py` içindeki **stale RemoveConstraint** `SeparateDatabaseAndState` ile onarıldı (detay §1).
5. Doğrulama (`check`, `makemigrations --check`, `migrate --plan`, tam test suite) çalıştırıldı ve bu rapor yazıldı.

---

## 1. MIGRATION DRIFT KÖK NEDENİ

**Birincil neden (audit teşhisi doğrulandı):**
`0001_initial` içinde oluşturulan 6 model (`Ada`, `Parsel`, `Kirasozlesi`, `RiskliYapı`, `SözlesenTemplate`, `TahliyeSuresi`) `construction/models.py` dosyasından silinmiş, ancak silme için migration üretilmemişti. `makemigrations --check` bu yüzden 0023'ü öneriyordu. Kullanıcı 0023 (+0024/0025/0026) dosyalarını üretmişti; bu oturumda `makemigrations --check --dry-run` = **`No changes detected`** olarak doğrulandı.

**Bu oturumda bulunan ek iki zincir bozukluğu** (test DB sıfırdan kurulamıyordu, `manage.py test` ilk denemede migration sırasında patlıyordu):

a) **`0020_pozfiyat_source_fields` yinelenen AddField:** `0019_pozfiyat_donem` zaten `ice_aktarma_tarihi` dahil 5 alanı ekliyordu. `0020` aynı alanı tekrar ekliyordu → sıfırdan kurulumda `DuplicateColumn: column "ice_aktarma_tarihi" ... already exists`. Onarım: zinciri bozmamak için dosya korundu, `operations = []` yapıldı (açıklayıcı yorum eklendi). Veri kaybı yok, state değişmedi (`--check` hâlâ temiz).

b) **`0024_remove_hakedis_uniq_hakedis_tenant_no` stale RemoveConstraint:** `0003` bu constraint'i ekledi, `0004` ise `hakedis_no` kolonunu düşürdü → PostgreSQL constraint'i otomatik kaldırdı, ama migration state'te kayıt kaldı. `0024` normal `RemoveConstraint` ile sıfırdan kurulumda ve mevcut dev DB'de `UndefinedObject: constraint "uniq_hakedis_tenant_no" ... does not exist` veriyordu. Onarım: `SeparateDatabaseAndState(state_operations=[RemoveConstraint...], database_operations=[])` — state düzeltmesi korunur, DB'ye dokunulmaz. Veri kaybı yok, `--fake` yok, `--check` hâlâ temiz.

**Tarihsel zemin:** Dev DB (`emlak_erp`, port 5433) geçmişte `--no-migrations` ile modellerden (syncdb) kurulduğu için migration state (`django_migrations`) ile gerçek şema ayrışmış. Kanıt: 0021/0022 tabloları DB'de **var + verili**, ama `showmigrations` 0021–0026'yı **unapplied** gösteriyor; 6 eski tablo DB'de **yok**, ama state'te 0001 ile var görünüyor.

---

## 2. ESKİ TABLOLARIN GERÇEK KAYIT SAYILARI (dev DB: `emlak_erp` @ localhost:5433)

| Tablo (construction_*) | Kayıt sayısı |
|---|---|
| `construction_ada` | **TABLO YOK** (relation does not exist) → 0, DROP edilecek veri yok |
| `construction_parsel` | **TABLO YOK** → 0 |
| `construction_kirasozlesi` | **TABLO YOK** → 0 |
| `construction_riskliyapi` (`riskliyapı` dahil varyantlar tarandı) | **TABLO YOK** → 0 |
| `construction_sozlesentemplate` | **TABLO YOK** → 0 |
| `construction_tahliyesuresi` | **TABLO YOK** → 0 |

Not: `real_estate_ada` ve `real_estate_parsel` **ayrı app'te mevcuttur** (Ada/Parsel işlevi `real_estate` tarafındadır); construction tarafındaki silme bunları etkilemez.

Referans (0021/0022 tabloları dev DB'de mevcut + kayıtlı — bu yüzden dev'de normal `migrate` çalışmaz, §6'ya bak):
`construction_projepozfiyat: 0`, `construction_malzemefiyat: 3`, `construction_projemalzeme: 4`, `construction_projemalzemefiyat: 4`, `construction_projepozmalzeme: 3`, `construction_yfkpozversiyon: 1`, `construction_yfkfiyat: 0`, `construction_yfkrayic: 0`, `construction_yfkanaliz: 0`, `construction_yfkguncellemegecmisi: 0`. İçerik test artığıdır (`Test kaynak`, `Test genel`, 2026-09-21 tarihli).

**Sonuç:** 6 eski tabloda veri **yok** (tablolar zaten yok). Hiçbir tablo DROP edilmedi, `--fake` kullanılmadı.

---

## 3. OLUŞTURULAN / ONARILAN MIGRATION

- **Kullanıcı tarafından oluşturulmuş (içeriği bu oturumda kontrol edildi, değiştirilmedi):**
  - `0023_remove_ada_uniq_ada_tenant_kod_remove_riskliyapı_ada_and_more` — 6 modelin `DeleteModel` + FK/constraint temizliği + `hakedis/pozfiyat/...` alan düzeltmeleri + `uniq_poz_fiyat_yil_donem` ekleme. İçerik audit raporundaki beklenen listeyle uyumlu.
  - `0024_remove_hakedis_uniq_hakedis_tenant_no` (bu oturumda §1-b onarımı uygulandı).
  - `0025_alter_tedarikci_firma_kodu` (`firma_kodu` unique kaldırma), `0026_alter_tedarikci_firma_kodu` (unique geri ekleme; final model `unique=True` ile uyumlu).
- **Bu oturumda yeni numaralı migration oluşturulmadı.** Yapılanlar yalnızca mevcut zincirin **onarımıdır**: `0020` (no-op) + `0024` (`SeparateDatabaseAndState`). Her ikisinde de DB'ye zararlı operasyon yok.
- Dev DB'ye `migrate` **uygulanmadı** (gerekçe §6). Test DB sıfırdan tüm migration'ları başarıyla uyguladı (§5 kanıtı).

---

## 4. TEST DB DÜZELTMESİ

- `pytest.ini`: `--no-migrations` yok (kullanıcı yapmıştı, doğrulandı).
- `conftest.py`: custom `django_db_setup` yok → pytest-django varsayılanı ile **gerçek migration'lar** çalışıyor (kullanıcı yapmıştı, doğrulandı). `pytest_sessionstart` yalnızca bağlantı bilgisi yazdırır, migration engellemez.
- `config/settings/test.py`: `MIGRATION_MODULES` disable satırı yorumlu (kullanıcı yapmıştı, doğrulandı).
- Bu oturumun düzeltmesi: `test_tenant` fixture'ı modelle uyumsuzdu, düzeltildi (Bkz. §0).
- Mevcut testlerin davranışı değiştirilmedi (TestCase izolasyonu aynı; yalnızca unique veri üretimi eklendi).
- Not: `.env.test` 5434 portundaki ayrı test Postgres'ine işaret ediyor; bu sunucu **kapalı** (`Test-NetConnection 5434` = False; yalnızca 5433 dev DB + Docker `emlak_erp_db` ayakta). Doğrulama, Django test runner'ın 5433 üzerinde açtığı izole `test_emlak_erp` DB ile yapıldı — **gerçek migration'lar sıfırdan uygulandı** (çıktıda 0001→0026 dahil tüm `Applying ... OK` adımları görüldü). `memory-bank`/dokümanlardaki `--no-migrations` ifadeleri yalnızca metindir, kod davranışı gerçek migration'dır.

---

## 5. EMAIL TEST DÜZELTMESİ (production modeline dokunulmadı)

- `users/models.py`: `email = models.EmailField(unique=True, ...)` **aynen korundu**.
- Kök neden doğrulandı: `tests/test_fatura.py` (`FaturaApiTest.setUp`) ve `tests/test_audit.py` (`AuditModelTest.setUp`) `create_user` çağrısında **email vermiyordu** → tüm kullanıcılar `email=""` ile yazılmaya çalışılıp `users_user_email_key` unique ihlali veriyordu. Diğer app testleri kullanıcı tarafından zaten `uuid` pattern'ine geçirilmişti; sadece bu iki dosya kalmıştı.
- Düzeltme (yalnızca test kodu): her `setUp` içinde `unique = uuid.uuid4().hex[:8]` üretilip `username`, `email` (`...@example.com`) ve `Tenant.slug` unique yapıldı. `TestCase` rollback izolasyonu korunur.
- Sonuç: audit'te failing olan 4 test (`test_log_change_keeps_tenant_and_values`, `test_fatura_olusturulur_ve_listelenir`, `test_satirli_fatura_kdv_tevkifat_hesaplar`, `test_zero_tutar_reddedilir`) artık geçiyor — hem Django runner hem pytest ile doğrulandı.

---

## 6. DOĞRULAMA SONUÇLARI

- `python manage.py check` → **System check identified no issues (0 silenced).**
- `python manage.py makemigrations --check --dry-run` → **No changes detected.**
- `python manage.py migrate --plan` → dev DB'de **0021–0026 pending** gösteriyor (çıktı §3'teki operasyon listesi). Dev DB'ye `migrate` uygulanmadı çünkü:
  - `0021/0022` normal `migrate` denemesinde `DuplicateTable: relation "construction_projepozfiyat" already exists` veriyor (tablolar + veriler dev'de önceden var → DROP yapılmadı, `--fake` kullanılmadı);
  - `0023` eski 6 tabloyu DROP etmeye çalışırdı ama tablolar zaten yok (veri kaybı riski yok, yine de dev'e uygulanmadı).
  - Buna karşılık **sıfırdan test DB** tüm zinciri (0020/0024 onarımları dahil) hatasız uyguluyor → migration dosyaları doğru, sorun yalnızca kirlenmiş dev DB şeması. Dev DB için öneri (bu görev dışında): yedek al → boş DB'ye `migrate` → gerçek veriyi geri yükle; dev'deki `Test Tenant <uuid>` kayıtları test kirliliğidir.
- Test suite (skip/xfail yok):
  - **Django runner:** `manage.py test` → **toplam 385, passed 385, failed 0, skipped 0 — OK** (385 test, ~294 sn; `test_emlak_erp` izole DB gerçek migration'larla kuruldu, sonra yok edildi).
  - **pytest:** `--ignore=frontend` ile **386 test toplandı, tamamı geçti** (çıktıda failures yok; `frontend/test.txt` pytest collection artefaktı olduğu için hariç tutuldu — `.txt` dosyasının `utf-8` decode hatası testlerle ilgisizdir).
  - Önceki `test_output.txt` içindeki 6 Hakedis pytest failure'ı kirli dev şemasından kaynaklanıyordu; temiz izole DB'de **tekrarlamıyor**.

---

## 7. ÖZET TABLO (istenen alanlar)

| Alan | Değer |
|---|---|
| migration drift kök nedeni | 6 model silinmiş, migration üretilmemiş (0023 ile kapatıldı) + zincirde 0020 yinelenen AddField ve 0024 stale RemoveConstraint (onarıldı); tarihsel zemin `--no-migrations` syncdb |
| eski tabloların gerçek kayıt sayıları | 6 tablo da dev DB'de YOK → 0'ar kayıt (tablo §2) |
| oluşturulan migration | Kullanıcı: 0023/0024/0025/0026 (içerik kontrol edildi). Bu oturum: yeni numara yok; 0020 no-op + 0024 SeparateDatabaseAndState onarımı |
| test DB düzeltmesi | Zaten yapılmıştı (pytest.ini/conftest/test.py); bu oturumda `test_tenant` fixture onarımı + gerçek migration ile sıfırdan kurulum doğrulaması |
| email test düzeltmesi | `tests/test_fatura.py` + `tests/test_audit.py` uuid unique email; production model değişmedi |
| toplam test | 385 (Django runner) / 386 (pytest collect) |
| passed | 385 / 386 (tümü) |
| failed | 0 |
| skipped | 0 |
| migration check sonucu | `No changes detected` |
| Django check sonucu | `System check identified no issues (0 silenced)` |

**FAZ 3A:** Başlanmadı (talimat gereği). Sistem mevcut durumda stabildir: check temiz, migration drift kapatıldı, test DB gerçek migration'larla kuruluyor, tüm testler geçiyor. Tek bilinen açık konu kirlenmiş **dev DB** (`emlak_erp`) üzerindeki 0021–0026 pending durumudur; test izolasyonu bunu etkilemez, takip işi olarak yedek+rebuild önerilir.