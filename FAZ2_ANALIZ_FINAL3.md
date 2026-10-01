# FAZ 2 REVİZE ANALİZ RAPORU

## 1. PROJE POZ ETKİN FİYATI
- **Servis adı:** `proje_poz_etkin_fiyati(proje, poz, yil)`
- **Açıklama:** Belirli bir proje ve poz için, projeye özel malzeme değişiklikleri ve güncel malzeme fiyatları dikkate alınarak etkin birim fiyatını döndürür.
- **Fiyat önceliği:**
  1. `ProjePozFiyat` varsa → doğrudan kullan (override, analiz tekrarı yapılmaz)
  2. Yoksa → poz analizinden proje bazlı yeniden hesapla
  3. Hesaplama yapılamıyorsa → `PozFiyat`
  4. `PozFiyat` yoksa → `YfkFiyat`
  5. Bulunamazsa → `None`
- **Önemli Not:** `ProjePozFiyat` bulunduğunda malzeme analizi tekrar hesaplanmaz; bu, projeye özel nihai override’dır.
## 2. PROJE BAZLI POZ ANALİZİ
- Poz analizinden proje poz fiyatı hesaplanırken her madde için:
  - **Kaynak Malzeme:** `etkin_poz_malzeme(proje, poz, kaynak_malzeme)` → `malzeme_etkin_fiyati(proje, etkin_malzeme, yil)` → etkin miktar → malzeme tutarı
  - **Diğer Kalemler (ISCİK, MAKİNE, NAKLIYE, DİGER):** mevcut analiz mantığıyla hesaba katılır.
- **Sonuç:** toplam analiz maliyeti / poz analiz birim miktarı → proje poz birim fiyatına dönüştürülebiliyorsa hesaplanır.
- **Uyarı:** Mevcut `PozAnaliz` modelinin gerçek alanları incelenmeden varsayımsal kod yazılmamalı; önce mevcut hesaplama yapısının bu akıma uygun olup olmadığı analiz edilmelidir.

## 3. PROJE POZ MALZEME DEĞİŞİKLİĞİ GERÇEKTEN MALİYETE YANSIMALI
- Frontend’te sadece görsel değişiklik yeterli değildir; malzeme override gerçek maliyeti yansıtmalıdır.
- **Örnek:** Poz 15’te Çimento A (0.250 birim, 500 TL) → Proje override ile Çimento B (650 TL) yapılırsa, yeni analiz maliyeti: `0.250 × 650 = 162.5 TL` olmalı ve bu değer proje poz etkin fiyatına yansımalıdır.

## 4. PROJE POZ FİYATI İLE MALZEME OVERRIDE AYRIMI
- **ProjePozFiyat:** pozun nihai toplam birim fiyat override’ı (tamamen dışarıdan verilen değer).
- **ProjePozMalzeme:** poz analizindeki malzeme bileşenini değiştiren yapı (malzeme tipi/miktarı).
- İkisi birbirinin yerine kullanılamaz; ayrı tutulmalı ve servislerde ayrı ayrı kontrol edilmelidir.
## 5. YFK MALZEME FALLBACK’İ
- FAZ 2’de `YfkAnaliz` üzerinden otomatik malzeme fiyatı alınmaz çünkü `YfkAnaliz.malzeme_kodu` ile `Malzeme.malzeme_kodu` arasında güvenilir mapping yoktur.
- `malzeme_etkin_fiyati()` fallback sırası:
  1. `ProjeMalzemeFiyat`
  2. `ProjeMalzeme.selected_teklif`
  3. `MalzemeFiyat`
  4. `None`
- YFK malzeme eşleştirme ayrı bir milestone olarak planlanacak.

## 6. SELECTED_TEKLIF TEK GERÇEK KAYNAK OLSUN
- Fiyat servislerinde `TedarikciTeklifi.secildi` kullanılmaz; tek kaynak `ProjeMalzeme.selected_teklif` olur.
- `TedarikciTeklifi.secidi` sadece geriye dönük uyumluluk için korunabilir.
- Migration sırasında aynı proje+malzeme için birden fazla `secildi=True` bulunduysa:
  - Rastgele ilk kayıt seçilmemeli.
  - Çakışma raporu oluşturulmalı ve `selected_teklif` boş bırakılmalı.

## 7. SELECTED_TEKLIF VALIDASYONU
`selected_teklif` atanmadan önce şu kontroller zorunlu:
- `teklif.tenant == proje.tenant`
- `teklif.proje == proje`
- `teklif.malzeme == proje_malzeme.malzeme`
- `teklif.is_active == True`
- Herhangi biri sağlanmıyorsa işlem reddedilmelidir.
## 8. PROJE POZ MALZEMESİ VE PROJE MALZEMESİ BAĞI
- `ProjePozMalzeme.etkin_malzeme` seçildiğinde, karşılık gelen `ProjeMalzeme` (proje + etkin_malzeme) kaydı mevcut olmalıdır.
- Yoksa aynı transaction içinde oluşturulması değerlendirilmelidir (amac: projedeki etkin tüm malzemelerin `ProjeMalzeme` katmanında bulunması).
- Bu, analiz sırasında `malzeme_etkin_fiyati` fonksiyonunun güvenli çalışmasını sağlar.

## 9. PARA BİRİMİ
- FAZ 2 maliyet hesaplarında **sadece TRY** kullanılır.
- Farklı para birimleri doğrudan snapshot’a yazılmaz; EUR/USD desteği ayrı bir fazda şu yapıyla ele alınacak:
  - `kur`
  - `kur_tarihi`
  - `TL_karsiligi`
  - `snapshot_para_birimi`
- Bu sayede temel maliyet modülüTRY üzerinden sabit kalır.

## 10. SOFT DELETE VE TENANT
- Yeni ViewSet’lerde **DELETE** işlemi fiziksel silme yapmaz; `is_active=False` yapar.
- Serializer ve service katmanında ilişkili tüm nesnelerin tenant uyumu kontrol edilir:
  - `proje`
  - `poz`
  - `kaynak_malzeme`
  - `etkin_malzeme`
  - `tedarikci`
  - `cari`
  - `selected_teklif`
- Her silme/güncelleme işleminde tenant eşleşmesi doğrulanmalıdır.
### EKLENEN BÖLÜMLER
1. **Proje Poz Etkin Fiyatı** – servis tanımları ve öncelik sırası.
2. **Proje Bazlı Poz Analizi** – poz analizinden projeye özel fiyat çıkarma süreci.
3. **Malzeme Değişikliğinin Poz Maliyetine Yansıması** – override’un maliyete etkisi ve örnek uygulama.
4. **ProjePozFiyat vs ProjePozMalzeme ayrımı** – iki modelin rolü ve kullanım sınırları.
5. **Selected Teklif Veri Bütünlüğü** – tek gerçek kaynak, validation ve migration prosedürü.
6. **Para Birimi Kısıtı** – sadece TRY kullanımı ve çoklu para birimi gelecek faz taslağı.
7. **YFK Malzeme Eşleştirme Milestone’u** – neden fallback kullanılıyor ve gelecek çalışma alanı.

### ZORUNLU TEST SENARYOLARI
**TEST 9:** `ProjePozFiyat` varsa, `ProjePozMalzeme` değişikliğine rağmen doğrudan `ProjePozFiyat` kullanılmalı.

**TEST 10:** `ProjePozFiyat` yoksa, malzeme A → B değişikliği proje poz analiz toplam maliyetini değiştirmeli.

**TEST 11:** Aynı pozda A → B yapılırken işçilik/makine/nakliye kalemleri değişmemeli.

**TEST 12:** Etkin malzeme fiyatı bulunamazsa proje poz etkin fiyatı hatalı bir tahmin üretmemeli; tanımlanan fallback’e göre ilerlemeli.

**TEST 13:** USD/EUR fiyat maliyet hesabına yanlışlıkla TRY gibi sokulmamalı.

**TEST 14:** `selected_teklif` başka proje veya başka malzemeye aitse atama reddedilmeli.

**TEST 15:** Aynı proje+malzeme için birden fazla `secildi=True` varsa migration rastgele seçim yapmamalı; çakışma raporu oluştur ve boş bırak.

**TEST 16:** DELETE işleminden sonra kayıt veritabanından silinmemeli, `is_active=False` olmalı.

## SONUÇ
Bu belge, FAZ 2 revize analizinin tek referans dokümanıdır. Kod yazma ve migration oluşturma adımları yapılmadan önce tüm kararlar ve gereksinimler bu raporda netleştirilmiştir. Implementasyon sürecinde bu maddeler eksiksiz uygulanmalıdır.