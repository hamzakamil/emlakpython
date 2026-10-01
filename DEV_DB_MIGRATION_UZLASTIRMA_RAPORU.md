# DEV DB MIGRATION UZLASTIRMA RAPORU

## 1. Dev DB'nin mevcut durumu
- Development veritabanı `emlak_erp` (Port 5433) şu anda sadece önceki schema dump ile oluşturulmuş tablolar içerir.
- `django_migrations` tablosu sadece 0001_initial–0020_(construction) kayıtlarını gösterir; 0021–0026 migrations'ları uygulanmamıştır.
- Tabloların varlığı kontrol edildi:
  - `construction_tedarikci`: **VAR**
  - `construction_projepozfiyat`: **VAR**
  - `construction_malzeme_fiyat`: **YOK**
  - `construction_projemalzeme`: **VAR**
  - `construction_projemalzemefiyat`: **VAR**
  - `construction_proje_poz_malzeme`: **YOK**
  - YFK related tablolar (`construction_yfkpozversiyon`, `construction_yfkfiyat`, `construction_yfkanaliz`, `construction_yfkrayic`): **VAR**
  - Silinmesi planlanan tablolar (Ada, Parsel, Kirasozlesi, RiskliYapı, SözlesenTemplate, TahliyeSuresi): **YOK**

## 2. 0021–0026 migration dosyaları ile gerçek DB şemasının karşılaştırılması
- 0021: `ProjePozFiyat` tablosunu oluşturur → zaten mevcut.
- 0022: `MalzemeFiyat`, `ProjeMalzeme`, `ProjeMalzemeFiyat`, `ProjePozMalzeme`, YFK tablolarını oluşturur → `MalzemeFiyat` ve `ProjePozMalzeme` yok, diğerleri mevcut.
- 0023–0026: Ada, Parsel, Kirasozlesi, RiskliYapı, SözlesenTemplate, TahliyeSuresi modellervi siler; `ProjePozFiyat` ve `ProjeMalzemeFiyat` üzerine ek kısıtlar/ordering ekler; `Tedarikci.firma_kodu` unique kaldırılıp yeniden eklenir.
- Silinen modellerin tabloları dev DB'de bulunmadığından, doğrudan uygulama `DeleteModel` hatası verir.

## 3. Veri kaybı yaratmadan en güvenli çözüm
- Yeni bir reconciliation migration (0027) oluşturularak:
  1. Eksik tablolar (`construction_malzeme_fiyat`, `construction_proje_poz_malzeme`) `CREATE TABLE IF NOT EXISTS` ile eklenir.
  2. Eksik unique constraint ve check constraint'ler `DO $$ ... END $$;` bloklarıyla eklenir (varlık kontrolü ile).
  3. 0023–0026 migrations'sındaki işlemler kopyalanır ancak:
     - `DeleteModel`, `RemoveConstraint`, `RemoveField` gibi silme işlemleri `migrations.SeparateDatabaseAndState(state_operations=[...], database_operations=[])` yapılarak **sadece durum (state)** güncellenir, DB'ye dokunulmaz.
     - Diğer işlemler (AlterModelOptions, AlterField, AddConstraint vb.) mevcut tablolar üzerinde olduğu için **normal** olarak bırakılır.
- Bu sayede veri kaybı riski olmadan şema hedef durumuna getirilir.

## 4. Çözüm uygulanacaksa önce yedek doğrulaması yap
- Migration çalıştırılmadan önce mevcut veritabanının yedeği alınması önerilir (örn. `pg_dump -Fc -f backup_$(date +%F).dump emlak_erp`).
- Ancak bu migration sadece **CREATE TABLE IF NOT EXISTS** ve constraint ekleme işlemleri yapar; mevcut verileri silmez veya değiştirmez.

## 5. İşlem sonunda `check`, `makemigrations --check` ve ilgili migration kontrollerini çalıştır
- Migration eklendikten sonra:
  - `python manage.py check` → hata vermemeli.
  - `python manage.py makemigrations --check` → bekleyen değişiklik olmamalı.
  - `python manage.py showmigrations construction` → 0027 uygulandı olarak göstermeli.
  - Test veritabanı üzerinde (`pytest --no-migrations`) tüm testlerin geçtiğini doğrulanmalı (bu adım dev DB üzerinde zorunlu değildir).

## 6. FAZ 3A koduna dokunulmamıştır.
- Sadece migration dosyası eklenmiştir; uygulama kodu hiç değiştirilmemiş.

## Ek: Oluşturulan Dosya
- `c:\proje\emlakpython\construction\migrations\0027_reconcile_missing_tables.py`

Bu rapor, gerçekleştirilen adımları ve önerilen çözümü belgelemek için hazırlanmıştır.