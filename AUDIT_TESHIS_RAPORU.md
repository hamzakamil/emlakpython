# AUDIT TEŞHİS RAPORU

**Tarih:** 2026-09-21  
**Hazırlayan:** AI Asistan  
**Kapsam:** Migration drift ve test veritabanı/email unique hatalarının kök neden analizi

---

## 1. MIGRATION DRIFT'İN GERÇEK NEDENİ

### Özet
`python manage.py makemigrations --check --dry-run` çıktısı, **construction** app için **0023** numaralı yeni bir migration bekleniyor. Bu migration, **models.py'de artık olmayan modellerin ve alanların silinmesini** içeriyor.

### Beklenen Değişikliklerin Tam Listesi (0023 migration içeriği)

#### Silinecek Modeller (DeleteModel)
| Model | Açıklama |
|-------|----------|
| `Ada` | 0001_initial'da oluşturulmuş, models.py'den silinmiş |
| `Parsel` | 0001_initial'da oluşturulmuş, models.py'den silinmiş |
| `Kirasozlesi` | 0001_initial'da oluşturulmuş, models.py'den silinmiş |
| `RiskliYapı` | 0001_initial'da oluşturulmuş, models.py'den silinmiş |
| `SözlesenTemplate` | 0001_initial'da oluşturulmuş, models.py'den silinmiş |
| `TahliyeSuresi` | 0001_initial'da oluşturulmuş, models.py'den silinmiş |

#### Silinecek Alanlar (RemoveField)
| Model | Alan | Tür |
|-------|------|-----|
| `riskliyapı` | `ada` | ForeignKey |
| `riskliyapı` | `parsell` | ForeignKey |
| `riskliyapı` | `proje` | ForeignKey |
| `riskliyapı` | `tenant` | ForeignKey |
| `kirasozlesi` | `ada` | ForeignKey |
| `kirasozlesi` | `parsell` | ForeignKey |
| `kirasozlesi` | `proje` | ForeignKey |
| `kirasozlesi` | `tenant` | ForeignKey |
| `tahliyesuresi` | `kirasozlesi` | ForeignKey |
| `parsel` | `ada` | ForeignKey |
| `sözlesentemplate` | `tenant` | ForeignKey |
| `tahliyesuresi` | `tenant` | ForeignKey |
| `ada` | `proje` | ForeignKey |
| `ada` | `tenant` | ForeignKey |

#### Silinecek Constraint'ler (RemoveConstraint)
| Model | Constraint |
|-------|------------|
| `ada` | `uniq_ada_tenant_kod` |
| `parsel` | `uniq_parsel_ada_no` |
| `hakedis` | `uniq_hakedis_tenant_no` |
| `pozfiyat` | `uniq_poz_fiyat_yil` |

#### Değişen Meta Options (AlterModelOptions)
| Model | Değişiklik |
|-------|------------|
| `hakedis` | ordering, verbose_name güncellendi |
| `kalitekabulteminati` | verbose_name_plural düzeltildi (Kaufmanninatı → Teminatları) |
| `nakliyemesafe` | ordering güncellendi |
| `pozanaliz` | ordering güncellendi |
| `pozfiyat` | ordering, verbose_name güncellendi |

#### Değişen Alanlar (AlterField)
| Model | Alan | Değişiklik |
|-------|------|------------|
| `hakedis` | `cari` | `blank=True, null=True` eklendi, help_text güncellendi |
| `hakedis` | `donem` | `max_length=7`, help_text eklendi (YYYY-MM formatı) |
| `hakedis` | `durum` | choices güncellendi, default='taslak', max_length=10 |
| `ifcimportjob` | `project` | related_name='ifc_import_jobs' |
| `ifcimportjob` | `tenant` | related_name='+' |
| `ifcquantitydraft` | `tenant` | related_name='+' |
| `kalitekontrol` | `kontrol_eden` | related_name='kalite_kontrol_eden' |
| `kalitekontrol` | `tarih` | verbose_name='Tarih' |
| `nakliyemesafe` | `k_katsayisi` | default=Decimal('1') eklendi |
| `nakliyemesafe` | `mesafe_km` | validators güncellendi |
| `pozanaliz` | `miktar` | validators güncellendi |
| `pozfiyat` | `gecerlilik_tarihi` | null=True, blank=True eklendi |
| `pozfiyat` | `ice_aktarma_tarihi` | null=True, blank=True eklendi |
| `pozfiyat` | `kaynak` | max_length=100, blank=True, default='' |
| `pozfiyat` | `kaynak_url` | max_length=250, blank=True |
| `pozfiyat` | `yayin_tarihi` | null=True, blank=True eklendi |
| `santiyegunlugu` | `created_by` | related_name='+' |
| `santiyegunlugu` | `tarih` | verbose_name='Tarih' |
| `santiyegunlugu` | `yapilan_isler` | verbose_name='Yapılan İşler' |
| `tedarikci` | `firma_kodu` | unique=True kaldırıldı (tenant bazlı unique constraint'e taşındı) |

#### Eklenecek Constraint (AddConstraint)
| Model | Constraint |
|-------|------------|
| `pozfiyat` | `uniq_poz_fiyat_yil_donem` (tenant, poz, yil, donem unique) |

---

### Kök Neden Analizi

**Migration drift'in gerçek nedeni:**  
**0001_initial migration'da oluşturulan 6 model (Ada, Parsel, Kirasozlesi, RiskliYapı, SözlesenTemplate, TahliyeSuresi) models.py dosyasından silinmiş ancak bu silinme işlemi için migration oluşturulmamış.**

Bu modeller FAZ 1'in erken aşamasında (0001_initial) oluşturulmuş, ancak daha sonra (muhtemelen FAZ 2 sırasında veya sonrasında) models.py'den kaldırılmış. Django migration sistemi, models.py ile migration dosyaları arasındaki farkı tespit ediyor ve 0023 migration'ını öneriyor.

**Hangi migration dosyasından sonra ortaya çıktı?**  
- 0001_initial: Bu modeller oluşturuldu
- 0022_faz2_malzeme_sistemi: Son migration (FAZ 2 tamamlandı)
- **Arada bu modelleri silen bir migration YOK**

**Üretim Riski:** **YÜKSEK**  
- Bu migration production'da çalıştırılırsa, bu tablolardaki **tüm veri kaybolur** (DROP TABLE)
- Eğer bu tablolarda hâlâ veri varsa (eski test verisi, manuel eklenmiş veri), veri kaybı yaşanır
- `makemigrations --check` CI/CD pipeline'ında fail verecek

---

## 2. TEST VERİTABANI DURUMU

### Test vs Development Veritabanı Ayarları

| Ayar | Development (dev.py) | Test (test.py) |
|------|---------------------|----------------|
| **Settings** | config.settings.dev | config.settings.test |
| **Veritabanı** | `emlak_erp` (port 5432) | `emlak_erp_test` (port 5434) |
| **DATABASE_URL** | .env dosyasından | .env.test dosyasından |
| **Migrations** | Normal çalışır | `--no-migrations` flag ile pytest çalışır |

### Kritik Bulgular

1. **Test veritabanı izole:** Farklı port (5434) ve farklı DB adı (emlak_erp_test) kullanıyor ✓
2. **pytest.ini:** `--no-migrations` flag'i var → Testler migration'ları çalıştırmaz, mevcut şemayı kullanır
3. **conftest.py:** `django_db_setup` fixture'ı boş (pass) → pytest-django'nun migration çalışmasını engelliyor
4. **Test veritabanı oluşturma:** `pytest_sessionstart` sadece bağlantıyı test ediyor, migration çalıştırmıyor

**Sorun:** Test veritabanı (emlak_erp_test) **migration'larla oluşturulmuyor**. Mevcut şema ya:
- Boş bir veritabanı (tablo yok)
- Eski migration'larla oluşturulmuş eski şema
- Manuel oluşturulmuş şema

Bu durumda testler `--no-migrations` ile çalışırken, **models.py ile test DB şeması uyuşmuyor olabilir**.

---

## 3. USERS_USER_EMAIL_KEY HATASININ GERÇEK NEDENİ

### User Modeli Analizi (users/models.py)

```python
email = models.EmailField(unique=True, verbose_name="E-posta")
```

**Özellikler:**
- `unique=True` → Veritabanında unique index (users_user_email_key)
- `null=True` **YOK** → NULL değer kabul etmez
- `blank=True` **YOK** → Form/validation'da boş bırakılamaz
- `default` **YOK** → Varsayılan değer yok

**Sonuç:** Her User **zorunlu ve benzersiz** bir email adresine sahip olmalı.

### Hatanın Kaynağı

**Test fixture/factory'lerde birden fazla User aynı email ile oluşturuluyor.**

Hangi testler aynı fixture'ı kullanıyor?

| Test Sınıfı | Fixture/Setup | Email |
|-------------|---------------|-------|
| `AuditModelTest::test_log_change_keeps_tenant_and_values` | `test_user` fixture (conftest.py) | `testuser@example.com` |
| `FaturaApiTest::test_fatura_olusturulur_ve_listelenir` | `FinanceBase.setUp()` | `fin@f.com` / `sat@f.com` |
| `FaturaApiTest::test_satirli_fatura_kdv_tevkifat_hesaplar` | `FinanceBase.setUp()` | `fin@f.com` / `sat@f.com` |
| `FaturaApiTest::test_zero_tutar_reddedilir` | `FinanceBase.setUp()` | `fin@f.com` / `sat@f.com` |

**Ortak Nokta:** Bu testler **farklı TestCase sınıflarında** (AuditModelTest, FaturaApiTest) ve **farklı tenant'larda** çalışıyor olabilir.

### Kök Neden: **Test İzolasyonu Eksikliği**

1. **pytest-django** her test sınıfı için transaction rollback yapar (TestCase)
2. Ancak **farklı TestCase sınıfları** aynı veritabanını paylaşıyor
3. `conftest.py`deki `test_user` fixture'ı `scope="function"` (varsayılan) → her test fonksiyonu için yeni user oluşturur
4. **Ama** `FinanceBase.setUp()` her test metodu için yeni user oluşturur
5. **Sorun:** Eğer testler **paralel çalışıyorsa** (pytest-xdist) veya **transaction izolasyonu bozulmuşsa**, aynı email ile ikinci user oluşturulmaya çalışılır → `IntegrityError: duplicate key value violates unique constraint "users_user_email_key"`

### Hangi Kategori? **A) Sadece test fixture problemi** ✓

**Değil:** B) users model tasarım problemi (model doğru, unique email iş mantığı gerektirir)  
**Değil:** C) test database problemi (DB doğru, izolasyon sorunu)

---

## 4. FAZ 1/2/3A DURUMU

> **Not:** Kullanıcı talimatına göre FAZ 1/2/3A sonuçları "doğrulandı" olarak kabul edilmiyor. Bu rapor sadece teşhis içindir.

---

## 5. ÇÖZÜM ÖNERİLERİ

### 5.1 Migration Drift Çözümü

**Seçenek A: Migration oluştur (Önerilen - Eğer tablolar boşsa)**
```bash
python manage.py makemigrations construction
# 0023 migration oluşturulur
python manage.py migrate
```

**Seçenek B: Fake migration (Eğer tablolarda veri varsa ve silinmemeli)**
```bash
# Önce veri yedek al
python manage.py makemigrations construction --empty
# Oluşan boş migration'ı düzenle: operations = [] 
python manage.py migrate construction 0023 --fake
```

**Seçenek C: Modelleri geri ekle (Eğer modeller hâlâ gerekliyse)**
- models.py'ye Ada, Parsel, vb. modelleri geri ekle
- `makemigrations` yapma

**Öneri:** **Seçenek A** - Tablolar muhtemelen boş (test verisi), production'da da kullanılmıyor. Migration oluşturup migrate et.

### 5.2 Email Unique Hatası Çözümü

**Kök Neden:** Test fixture'larında email çakışması.

**Çözüm 1: Fixture'larda unique email kullan (Hızlı)**
```python
# conftest.py
@pytest.fixture
def test_user(db, test_tenant):
    import uuid
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    return User.objects.create_user(
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        email=unique_email,
        ...
    )
```

**Çözüm 2: User modelinde email nullable yap (İş mantığı değişir - ÖNERİLMEZ)**
```python
email = models.EmailField(unique=True, null=True, blank=True, verbose_name="E-posta")
# unique=True + null=True → PostgreSQL'de multiple NULL izin verir
```

**Çözüm 3: Testlerde transaction izolasyonu sağla (Doğru çözüm)**
- `pytest.ini` den `--no-migrations` kaldır
- Test veritabanını migration'larla oluştur
- Her test sınıfı için `TransactionTestCase` veya `django_db_reset_sequences` kullan

**Öneri:** **Çözüm 1** (Hızlı düzeltme) + **Çözüm 3** (Kalıcı çözüm - ayrı task olarak)

### 5.3 Test Veritabanı Sorunu Çözümü

**Kalıcı Çözüm:**
1. `pytest.ini` den `--no-migrations` kaldır
2. `conftest.py` de `django_db_setup` fixture'ını düzelt (migration çalıştır)
3. Test veritabanını (emlak_erp_test) migration'larla sıfırdan oluştur
4. CI/CD'de test veritabanı container'ı (port 5434) başlat

---

## 6. HANGİ AJANLA HANGİ DÜZELTME YAPILMALI?

| Sorumluluk | Ajan | Açıklama |
|------------|------|----------|
| **Migration drift analizi & rapor** | **Bu ajan (AI Asistan)** | ✓ Tamamlandı |
| **0023 migration oluşturma & migrate** | **Backend Developer** | `makemigrations construction` → `migrate` |
| **Email unique test fixture düzeltmesi** | **Backend Developer / QA** | conftest.py ve test base sınıflarını düzelt |
| **Test DB migration entegrasyonu** | **DevOps / Backend** | pytest.ini, conftest.py, docker-compose.test.yml |
| **Production deployment risk analizi** | **Tech Lead** | Migration 0023 production'da veri kaybı riski değerlendir |

---

## 7. ÖZET

| Sorun | Ciddiyet | Kök Neden | Çözüm Süresi |
|-------|----------|-----------|--------------|
| Migration drift (0023) | **YÜKSEK** | 6 model silinmiş, migration oluşturulmamış | 15 dk (migration oluştur + migrate) |
| users_user_email_key | **ORTA** | Test fixture'larında email çakışması | 10 dk (unique email fixture) |
| Test DB migration'sız | **ORTA** | `--no-migrations` + boş django_db_setup | 30 dk (pytest config + docker) |

**Üretim Riski:** Migration 0023 production'da çalıştırılırsa **6 tablo DROP edilir** → Veri kaybı riski var. Önce staging'de test edilmeli.

---

**Sonuç:** Migration drift ve email unique hatası **bağımsız sorunlardır**. Migration drift model/migration senkronizasyon eksikliğinden, email hatası test izolasyonundan kaynaklanıyor. İkisi de FAZ 3A implementasyonunu engellemez ama CI/CD'yi kırar.