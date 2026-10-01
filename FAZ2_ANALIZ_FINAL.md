# FAZ 2 REVİZE ANALİZ RAPORU - FINAL

**Tarih:** 2026-09-21  
**Hazırlayan:** GitHub Copilot  
**Durum:** Tamamlandı - Implementation için referans doküman  
**Not:** Kod yazma, migration oluşturma yapılmadı. Sadece analiz raporu.

---

## İÇİNDEKİLER

1. [Proje Poz Etkin Fiyatı](#1-proje-poz-etkin-fiyatı)
2. [Proje Bazlı Poz Analizi](#2-proje-bazlı-poz-analizi)
3. [Malzeme Değişikliğinin Poz Maliyetine Yansıması](#3-malzeme-değişikliğinin-poz-maliyete-yansıması)
4. [ProjePozFiyat vs ProjePozMalzeme Ayrımı](#4-proje-poz-fiyat-vs-proje-poz-malzeme-ayrımı)
5. [Selected Teklif Veri Bütünlüğü](#5-selected-teklif-veri-bütünlüğü)
6. [Para Birimi Kısıtı](#6-para-birimi-kısıtı)
7. [YFK Malzeme Eşleştirme Milestone'u](#7-yfk-malzeme-eşleştirme-milestone-u)
8. [Zorunlu Testler](#8-zorunlu-testler)
9. [Ek Bölümler](#9-ek-bölümler)

---

## 1. PROJE POZ ETKİN FİYATI

### Servis Tanımı
```python
def proje_poz_etkin_fiyati(proje: Proje, poz: Poz, yil: int) -> Optional[Decimal]:
    """
    Belirli bir projenin belirli pozunun, proje özel malzeme değişiklikleri ve 
    malzeme fiyatları dikkate alınarak hesaplanan etkin birim fiyatını bulur.
    """
```

### Fiyat Önceliği
1. **ProjePozFiyat varsa → doğrudan kullan** (override, analiz tekrarı yapılmaz)
2. **Yoksa → poz analizinden proje bazlı yeniden hesapla**
3. **Hesaplama yapılamıyorsa → PozFiyat**
4. **PozFiyat yoksa → YfkFiyat**
5. **Bulunamazsa → None**

### Önemli Not
ProjePozFiyat bulunduğunda malzeme analizi tekrar hesaplanmaz. Çünkü ProjePozFiyat açık ve nihai bir proje override'ıdır.

---

## 2. PROJE BAZLI POZ ANALİZİ

### Poz analizinden proje poz fiyatı hesaplanırken:
Her malzeme kalemi için:
- **Kaynak Malzeme** → `etkin_poz_malzeme(proje, poz, kaynak_malzeme)`
- **Malzeme Etkin Fiyatı** → `malzeme_etkin_fiyati(proje, etkin_malzeme, yil)`
- **Etkin Miktar** → ProjePozMalzeme.miktar_override varsa onu kullan, yoksa PozMalzemeIliskisi.miktar
- **Malzeme Tutarı** → etkin miktar × malzeme etkin fiyatı

### Diğer analiz kalemleri:
- **IŞCIK** (İşçilik)
- **MAKİNE** 
- **NAKLIYE**
- **DİĞER**
mevcut analiz mantığıyla hesaba katılmalı.

### Sonuç:
`toplam analiz maliyeti / poz analiz birim miktarı` mantığıyla proje poz birim fiyatına dönüştürülebiliyorsa hesaplanmalı.

### Önemli Not
Mevcut PozAnaliz modelinin gerçek alanlarını incelemeden varsayımsal kod yazma. Önce mevcut hesaplama yapısının buna uygun olup olmadığını analiz et.

---

## 3. MALZEME DEĞİŞİKLİĞİNİN POZ MALİYETİNE YANSIMASI

### Temel İlkeler
Sadece frontend'de malzeme değiştirilmiş görünmesi yeterli değildir. Gerçek maliyette yansımak zorundadır.

### Örnek Senaryo
**Poz 15:**
- Çimento A
- Miktar: 0.250

**Proje override:**
- Çimento A → Çimento B

**Fiyatlar:**
- Çimento A = 500 TL
- Çimento B = 650 TL

**Yeni proje poz analizinin malzeme maliyeti:**
`0.250 × 650 = 162.50 TL` olmalıdır.

**Sonuç:** Bu değer proje poz etkin fiyatına yansımak zorundadır.

---

## 4. PROJEPOZFİYAT VS PROJEPOZMALZEME AYRIMI

### Kesin Ayrım Korunacak

| Özellik | ProjePozFiyat | ProjePozMalzeme |
|---------|---------------|-----------------|
| **Amaç** | Pozun nihai toplam birim fiyat override'ı | Poz analizindeki malzeme bileşenini değiştiren yapı |
| **Kapsam** | Poz toplam fiyatı | Sadece malzeme kalemi |
| **Etki** | Tüm poz maliyetini override eder | Sadece malzeme maliyetini etkiler |
| **Kullanım Önceliği** | İlk öncelik (varsa kullanılır, analiz yapmaz) | İkinci öncelik (ProjePozFiyat yoksa uygulanır) |
| **İlişki** | Birbirinin yerine **kullanılmayacak** | Birbirini tamamlar |

### Kural
ProjePozFiyat bulunduğunda ProjePozMalzeme üzerinden yapılan malzeme değişiklikleri **hesaba katılmaz**. Çünkü ProjePozFiyat açık ve nihai bir proje override'ıdır.

---

## 5. SELECTED TEKLİF VERİ BÜTÜNLÜĞÜ

### Yeni Yaklaşım
Yeni fiyat servislerinde:
- **TedarikciTeklifi.secildi** alanını temel alarak fiyat arama **YAPMA**
- **Ana kaynak:** `ProjeMalzeme.selected_teklif` olacak

### TedarikciTeklifi.secildi Korumu
- Mevcut sistemle uyumluluk amacıyla korunabilir
- Ancak güvenilir kaynak olarak **kullanılmayacak**

### Migration Süreci
Data migration sırasında aynı proje+malzeme için birden fazla `secildi=True` bulunursa:
- **Rastgele ilk kaydı seçme YASAK**
- **Migration conflict raporu oluştur ve selected_teklif'i boş bırak**

### Selected Teklif Validasyonu
`selected_teklif` atanırken mutlaka doğrulanacak:
- `teklif.tenant == proje.tenant`
- `teklif.proje == proje`
- `teklif.malzeme == proje_malzeme.malzeme`
- `teklif.is_active == True`
Uymuyorsa işlem **reddedilmeli**.

---

## 6. PARA BİRİMİ KISITI

### FAZ 2 Maliyet Hesaplarında Kural
- **SADECE TRY** kullanılır
- Farklı para birimlerini kabul edip doğrudan snapshot'a yazma **YASAK**

### EUR/USD Desteği Ayrı Fazda
Ayrı bir fazda şu yapıyla tasarlanacak:
- `kur` (döviz kuru)
- `kur_tarihi` (kurun geçerli olduğu tarih)
- `TL karşılığı` (dövizin TL değeri)
- `snapshot para birimi` (snapshot'ın hangi para biriminde tutulduğu)

### Kural
FAZ 2'de para birimi dönüşümü yapmadan doğrudan farklı para birimleriyle işlem yapılamaz.

---

## 7. YFK MALZEME EŞLEŞTİRME MILESTONE'U

### FAZ 2 Implementation Durumu
- **YFKAnaliz üzerinden otomatik malzeme fiyatı alma YAPILMAYACAK**
- **Nedeni:** `YFKAnaliz.malzeme_kodu` ile `Malzeme.malzeme_kodu` arasında güvenilir ve doğrulanmış bir mapping bulunmuyor

### Malzeme Etkin Fiyatı Servisi (`malzeme_etkin_fiyati`) Fallback Zinciri
1. **ProjeMalzemeFiyat** (proje + malzeme + yıl)
2. **ProjeMalzeme.selected_teklif** → `TedarikciTeklifi.birim_fiyat`
3. **MalzemeFiyat** (YENİ MODEL - opsiyonel)
4. **YFKAnaliz** gerçek malzeme rayıcı (malzeme_kodu eşleşmesi, güvenilir değilse None)
5. **None**

### Önemli Not
YFK malzeme eşleştirme ayrı bir milestone olacak ve FAZ 2'de implement edilmeyecek.

---

## 8. ZORUNLU TESTLER

### TEST 9: ProjePozFiyat Önceliği
**Amaç:** ProjePozFiyat varsa, ProjePozMalzeme değişikliğine rağmen doğrudan ProjePozFiyat kullanılmalı.
**Test Senaryosu:**
1. ProjePozFiyat oluştur (birim fiyat: 1000 TL)
2. Aynı poz için ProjePozMalzeme oluştur (malzeme A → B değişikliği)
3. `proje_poz_etkin_fiyati()` çağrısı
4. **Beklenen Sonuç:** 1000 TL (ProjePozFiyat kullanılır, analiz tekrarı yapılmaz)

### TEST 10: Malzeme Değişikliğinin Poz Maliyetine Etkisi
**Amaç:** ProjePozFiyat yoksa, malzeme A→B değişikliği proje poz analiz toplam maliyetini değiştirmeli.
**Test Senaryosu:**
1. ProjePozFiyat yok
2. Poz analizinde: Malzeme A, miktar: 2.0, birim fiyat: 100 TL → maliyet: 200 TL
3. ProjePozMalzeme oluştur: Malzeme A → Malzeme B (birim fiyat: 150 TL)
4. `proje_poz_etkin_fiyati()` çağrısı
5. **Beklenen Sonuç:** (2.0 × 150) + diğer analiz kalemleri = 300 TL + diğerleri

### TEST 11: İşçilik/Makine/Nakliye Kalemlerinin Korunması
**Amaç:** Aynı pozda A→B yapılırken işçilik/makine/nakliye kalemleri değişmemeli.
**Test Senaryosu:**
1. Poz analizinde: Malzeme A (200 TL), İşçilik (100 TL), Makine (50 TL)
2. ProjePozMalzeme oluştur: Malzeme A → Malzeme B (300 TL)
3. `proje_poz_etkin_fiyati()` çağrısı
4. **Beklenen Sonuç:** Malzeme: 300 TL, İşçilik: 100 TL, Makine: 50 TL (işçilik/makine değişmez)

### TEST 12: Fallback Mekanizması
**Amaç:** Etkin malzeme fiyatı bulunamazsa proje poz etkin fiyatı hatalı bir tahmin üretmemeli; tanımlanan fallback'e göre ilerlemeli.
**Test Senaryosu:**
1. ProjePozFiyat yok
2. Malzeme fiyatı bulunamıyor (hiçbir kaynak yok)
3. `proje_poz_etkin_fiyati()` çağrısı
4. **Beklenen Sonuç:** None (hatalı tahmin üretmez)

### TEST 13: Para Birimi Kısıtı
**Amaç:** USD/EUR fiyat maliyet hesabına yanlışlıkla TRY gibi sokulmamalı.
**Test Senaryosu:**
1. Malzeme fiyatı 100 USD olarak girildi
2. `malzeme_etkin_fiyati()` çağrısı
3. **Beklenen Sonuç:** None veya hata (USD doğrudan TRY olarak kullanılmaz)

### TEST 14: Selected Teklif Validasyonu
**Amaç:** selected_teklif başka proje veya başka malzemeye aitse atama reddedilmeli.
**Test Senaryosu:**
1. Proje A ve Proje B farklı
2. Malzeme X
3. Proje A için ProjeMalzeme oluşturuluyor
4. Seçilen teklif: Proje B + Malzeme X için
5. **Beklenen Sonuç:** Atama reddedilir (validation hatası)

### TEST 15: Çoklu Selected Teklif Durumu
**Amaç:** Aynı proje+malzeme için birden fazla secildi=True varsa migration rastgele seçim yapmamalı.
**Test Senaryosu:**
1. Proje X + Malzeme Y için 2 farklı tedarikçi teklifi secildi=True
2. Migration çalıştırılır
3. **Beklenen Sonuç:** Conflict raporu oluşturulur, selected_teklif boş bırakılır

### TEST 16: Soft Delete Mekanizması
**Amaç:** DELETE işleminden sonra kayıt veritabanından silinmemeli, is_active=False olmalı.
**Test Senaryosu:**
1. Bir ProjeMalzeme kaydı oluşturulur (is_active=True)
2. DELETE işlemi yapılır (API üzerinden)
3. Veritabanı kontrolü yapılır
4. **Beklenen Sonuç:** Kayıt hâlâ var, is_active=False

---

## 9. EK BÖLÜMLER

### 9.1 Yeni Servisler

#### `etkin_poz_malzeme(proje, poz, kaynak_malzeme)`
Belirli bir projede, belirli bir poz için, belirli bir kaynak malzemenin etkin (gerçek kullanılacak) malzemeyi döndürür.

#### `malzeme_etkin_fiyati(proje, malzeme, yil)`
Malzeme etkin birim fiyatını fallback zinciriyle çözer. Returns: `FiyatSonucu` dataclass (fiyat, kaynak, kaynak_id, para_birimi).

#### `FiyatSonucu` Dataclass
```python
@dataclass
class FiyatSonucu:
    fiyat: Optional[Decimal]
    kaynak: str           # "proje_malzeme_fiyat", "tedarikci_teklifi", "genel_malzeme_fiyat", "yfk_analiz", "none"
    kaynak_id: Optional[int]  # İlgili modelin PK'si
    para_birimi: str      # "TRY" (varsayılan)
```

### 9.2 Model İlişkileri

```
Proje
 ├── ProjePozFiyat (mevcut - poz fiyat override)
 ├── ProjeMalzemeFiyat (YENİ - malzeme fiyat override)
 ├── ProjeMalzeme (YENİ - proje özel malzeme tanımı)
 │      └── Malzeme (global malzeme kartı - ANA KİMLİK)
 └── ProjePozMalzeme (YENİ - poz+malzeme bazlı alternatif seçim)

Poz
 └── Poz Analizi
       ├── İşçilik (PozAnaliz tip=ISCIK)
       ├── Makine (PozAnaliz tip=MAKINE)
       ├── Malzeme (PozMalzemeIliskisi + PozAnaliz tip=MALZEME)
       └── Diğer (PozAnaliz tip=NAKLIYE/DIGER)
```

### 9.3 Snapshot Mekanizması Koruması
Mevcut snapshot değerleri **KESİNLİKLE** yeniden hesaplanmayacak:
- `YaklasikMaliyetSatiri.birim_fiyat_snapshot`
- `PozPlan.birim_fiyat_snapshot` 
- `HakedisSatiri.birim_fiyat`

Yeni kayıtlar için:
- `malzeme_etkin_fiyati(proje, malzeme, yil).fiyat` kullanılır
- Eski değerler `read_only=True` ve `save()` override'ıyla korunur

---

## SONUÇ

Bu rapor, FAZ 2 Projeye Özel Malzeme Sistemi için **tek referans doküman** olarak kabul edilir. 

**İmplementation Başlangıcı:**
- **HENÜZ KOD YAZMA**
- **HENÜZ MIGRATION OLUŞTURMA**

Bu rapor onaylandıktan sonra implementation aşamasına geçilebilir.

---
*Rapor Tamamlandı: 2026-09-21*