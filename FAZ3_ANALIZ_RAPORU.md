# FAZ 3 ANALİZ RAPORU

## 1. Yönetici Özeti

Bu rapor, Emlak ERP sisteminin FAZ 3 kapsamında geliştirilmesi gereken modülleri belirlemek amacıyla mevcut sistemin detaylı analizini içerir. Analiz, FAZ 1 ve FAZ 2'nin tamamlandığı varsayımıyla yapılmıştır ve mevcut mimarinin bozulmadığı kabul edilmiştir. Rapor, satın alma, stok yönetimi, gerçek maliyet hesaplama ve muhasebe entegrasyonu gibi alanları kapsar.

## 2. Mevcut Sistem Durumu

Mevcut sistem, Django tabanlı bir ERP uygulamasıdır. Proje yapısı aşağıdaki gibi düzenlenmiştir:

- **accounting**: Muhasebe işlemleri
- **audit**: Denetim ve log sistemi
- **cari**: Cari hesap yönetimi
- **construction**: İnşaat modülü (FAZ 1 ve FAZ 2 burada geliştirildi)
- **config**: Django yapılandırması
- **finance**: Finansal işlemler
- **tenants**: Çoklu kiracı desteği
- **users**: Kullanıcı ve yetkilendirme
- **frontend**: React/Tailwind tabanlı kullanıcı arayüzü

### Backend Modelleri ve Servisleri

#### construction/models.py
- Poz, Proje, PozFiyat, ProjePozFiyat, YfkFiyat, YfkPozVersiyon gibi modeller mevcut.
- FAZ 2 ile ProjeMalzeme, ProjeMalzemeFiyat, ProjePozMalzeme, MalzemeFiyat, TedarikciTeklifi modelleri eklendi.
- `etkin_poz_malzeme()`, `malzeme_etkin_fiyati()`, `proje_poz_etkin_fiyati()` gibi servis fonksiyonları construction/services/malzeme_fiyat.py içinde bulunur.

#### cari/models.py
- Cari, CariHareket, Fatura gibi modeller mevcut.

#### finance/models.py
- Muhasebe fişleri, ödeme ve tahsilat modelleri.

#### tenants/models.py
- Tenant (Kiracı) modeli ve ilişkileri.

### Frontend Yapısı
- frontend/ dizini altında React uygulaması bulunur.
- TypeScript, Tailwind CSS ve Vite kullanılır.
- API servisleri ile backend entegrasyonu sağlanır.

## 3. FAZ 1-2 Sonrası Mimari

FAZ 1 ve FAZ 2'de geliştirilen mimari şu şekildedir:

```
ProjePozFiyat
    ↓
poz_etkin_fiyati()

FAZ 2:
ProjeMalzeme
ProjeMalzemeFiyat
ProjePozMalzeme
MalzemeFiyat
TedarikciTeklifi
    ↓
malzeme_etkin_fiyati()
    ↓
etkin_poz_malzeme()
    ↓
proje_poz_etkin_fiyati()
    ↓
PozPlan / YaklasikMaliyet / Hakedis snapshot
```

Bu mimarinin bozulmadığı varsayımıyla FAZ 3 tasarımı yapılmıştır.

## 4. FAZ 3 İhtiyaç Tespiti

FAZ 3'te geliştirilmesi gereken temel modüller:
1. Tedarikçi teklif yönetimi
2. Satın alma talebi
3. Satın alma siparişi
4. Mal kabul / irsaliye
5. Stok giriş-çıkış
6. Gerçek malzeme maliyeti hesaplama
7. Fatura ile malzeme eşleştirme
8. Tedarikçi faturası yönetimi
9. Cari borç oluşumu entegrasyonu
10. Poz bazlı gerçek tüketim takibi

## 5. Mevcut Tedarikçi/Teklif Sistemi

Mevcut sistemde:
- `TedarikciTeklifi` modeli construction uygulamasında mevcuttur.
- Ancak, tedarikçi teklifinin tamamıyla yönetimi (durum takibi, revizyon, iptal vb.) eksiktir.
- Teklif seçimi ve satın alma talebine dönüşümü henüz uygulanmamıştır.

## 6. Mevcut Stok Sistemi

Mevcut sistemde stok yönetimi modülü bulunmamaktadır. Stok hareketleri, depo yönetimi ve şantiye stoku gibi temel stok işlemleri henüz uygulanmamıştır.

## 7. Mevcut Fatura/Cari Sistemi

- `cari` uygulamasında `Cari`, `CariHareket`, `Fatura` modelleri mevcuttur.
- Fatura oluşturma ve cari harekete entegrasyonu kısmıyla mevcuttur.
- Ancak, fatura ile malzeme eşleştirmesi ve stok girişiyle bağlantısı yoktur.

## 8. Satın Alma Aday Mimarisi

Önerilen satın alma akışı:
```
Tedarikçi
    ↓
Teklif
    ↓
Seçilen Teklif
    ↓
Satın Alma Talebi
    ↓
Satın Alma Siparişi
    ↓
Mal Kabul / İrsaliye
    ↓
Stok
    ↓
Fatura
    ↓
Cari
    ↓
Gerçek Maliyet
```

Her adım için model, ilişki, durum, numara, tarih, kullanıcı, tenant, audit, iptal ve ters kayıt mekanizmaları tanımlanmalıdır.

## 9. Mal Kabul Aday Mimarisi

Mal kabul süreci:
- Satın alma siparişi ile eşleştirilir.
- Kabul edilen miktar ve fiyat kaydedilir.
- Stok girişi oluşturulur.
- Fatura eşleştirmesi için temel oluşturulur.
- Kabul reddi, kısmi kabul ve fark yönetimi desteklenmelidir.

## 10. Stok Aday Mimarisi

Stok modülü için gerekli varlıklar:
- Depo (Warehouse)
- Şantiye (Site)
- Malzeme (Material)
- Stok Hareketi (Stock Movement) - giriş, çıkış, transfer, iade, sayım
- Birim (Unit)
- Stok Seviyesi ve Uyarıları

## 11. Gerçek Maliyet Aday Mimarisi

Gerçek maliyet hesaplama:
- Satın alma siparişi fiyatı
- Mal kabul fiyatı
- Fatura fiyatı
- Gerçek tüketim miktarı
Bu verilerle gerçek maliyet hesaplanır ve proje/paz/mahal bazında tutulur.

## 12. Planlanan vs Gerçekleşen Maliyet

Planlanan maliyet:
- PozPlan / Yaklaşık Maliyet modellerinden türetilir.

Gerçekleşen maliyet:
- Satın alma, fatura ve tüketim verilerinden hesaplanır.

Fark analizi için:
- Her poz/mahal için planlanan ve gerçek maliyet karşılaştırılır.
- Farklar, maliyet kontrolü ve raporlama için kullanılır.

## 13. Poz/Mahal Gerçek Tüketim

Gerçek tüketim takibi:
- Malzemenin depo → şantiye → poz/mahal akışı üzerinden takip edilir.
- Her poz/mahal için tüketilen miktar kaydedilir.
- Fire, iade ve stok dönüşleri ayrı ayrı tutulur.
- Gerçek maliyet hesaplamasında sadece tüketilen miktar kullanılır.

## 14. Veri Modeli

Önerilen FAZ 3 modelleri:

### Tedarikci (Supplier)
- id, tenant, ad, vergi_no, adres, telefon, email, durum, oluşturulma_tarihi, güncelleme_tarihi

### Teklif (Quotation)
- id, tenant, tedarikci, proje, tarih, geçerlilik_tarihi, durum, toplam_tutar, para_birimi, oluşturulan_kullanıcı, oluşturulma_tarihi

### TeklifKalemi (QuotationItem)
- id, teklif, poz/malzeme, miktar, birim_fiyat, toplam_fiyat, para_birimi, açıklama

### SatınAlmaTalebi (PurchaseRequest)
- id, tenant, proje, tarih, durum, toplam_tutar, para_birimi, oluşturulan_kullanıcı, oluşturulma_tarihi

### SatınAlmaSiparisi (PurchaseOrder)
- id, tenant, tedarikci, proje, tarih, teslim_tarihi, durum, toplam_tutar, para_birimi, oluşturulan_kullanıcı, oluşturulma_tarihi

### SiparisKalemi (PurchaseOrderItem)
- id, sipariş, teklif_kalemesi/poz/malzeme, sipariş_miktarı, kabul_edilen_miktar, birim_fiyat, toplam_fiyat, para_birimi

### MalKabul (GoodsReceipt)
- id, tenant, sipariş, tarih, durum, toplam_tutar, para_birimi, oluşturulan_kullanıcı, oluşturulma_tarihi

### MalKabulKalemi (GoodsReceiptItem)
- id, mal_kabul, siparis_kalemesi, kabul_edilen_miktar, birim_fiyat, toplam_fiyat, para_birimi

### StokHareketi (StockMovement)
- id, tenant, depo, malzeme, hareket_tipi (giriş/çıkış/transfer/iade/sayım), miktar, birim, referans (sipariş/mal_kabul/fatura/etc.), tarih, oluşturulan_kullanıcı

### Fatura (Invoice)
- id, tenant, tedarikci, proje, tarih, venceme_tarihi, durum, toplam_tutar, para_birimi, oluşturulan_kullanıcı, oluşturulma_tarihi

### FaturaKalemi (InvoiceItem)
- id, fatura, malzeme/poz, miktar, birim_fiyat, toplam_fiyat, para_birimi

### GerceklesenMaliyet (ActualCost)
- id, tenant, proje, poz/malzeme, tarih, miktar, birim_fiyat, toplam_maliyet, para_birimi, kaynak_tipi (sipariş/mal_kabul/fatura/tüketim)

## 15. State Machine

Her iş belgesi için durum makinesi:
- Taslak
- Gönderildi
- Onaylandı
- Reddedildi
- İptal edildi
- Tamamlandı
- Kapalı

Geçiş kuralları ve yetkilendirmeler tanımlanmalıdır.

## 16. Snapshot Stratejisi

FAZ 2 snapshot sistemiyle entegrasyon:
- Planlanan maliyet snapshot'ı: PozPlan / Yaklaşık Maliyet
- Gerçek maliyet snapshot'ı: Her iş belgesi (sipariş, mal kabul, fatura) için ilgili tutarlar
- Tüketim maliyet snapshot'ı: Gerçek tüketim verileri
Snapshot'lar, maliyet karşılaştırması ve raporlama için kullanılır.

## 17. API Tasarımı

Önerilen REST endpointleri:
- /tedarikciler/
- /teklifler/
- /teklif-kalemeleri/
- /satinalma-talepleri/
- /satinalma-siparisleri/
- /siparis-kalemeleri/
- /mal-kabuller/
- /mal-kabul-kalemeleri/
- /stok-hareketleri/
- /faturalar/
- /fatura-kalemeleri/
- /gerceklesen-maliyetler/

Her endpoint için CRUD işlemleri ve özel eylemler (onaylama, iptal, raporlama vb.) tanımlanmalıdır.

## 18. Frontend Bilgi Mimarisi

Frontend ekranları:
- Liste görünümleri (filtreleme, arama, sayfalama)
- Detay görünümleri (sekme yapısı)
- Sağ detay paneli (ilişkili veriler, geçmiş, ek bilgiler)
- Durum badge'leri
- Zaman çizelgesi (timeline)
- Belge ilişkileri (örnek: sipariş → fatura → ödeme)
- Tedarikçi, fiyat, miktar, proje, mahal, poz bilgileri

## 19. Yetkilendirme

Gerekli roller:
- Süper Admin
- Bayi Admin
- Şirket Admin
- İnşaat yöneticisi
- Satın alma kullanıcısı
- Depo kullanıcısı
- Muhasebe kullanıcısı

Mevcut permission sistemi (grup ve yetki) üzerinden genişletilmelidir.

## 20. Tenant İzolasyonu

Tenant bazlı veri izolasyonu:
- Her modelde tenant foreign key'i
- Tenant bazlı sorgular
- Tenant bazlı numara sıralamaları

## 21. Performans

Performans optimizasyonları:
- select_related ve prefetch_related kullanımı
- Veritabanı indeksleri (foreign key, durum, tarih alanları)
- Toplu işlemler (bulk create/update)
- Transaction yönetimi (atomic)
- Kilitleme mekanizmaları (select_for_update) därttaki senaryolar için

## 22. Transaction ve Concurrency

Concurrency kontrolü:
- İş belgesi numaralama için sequence tablosu veya veritabanı sequence
- Stok hareketleri için pessimistic locking
- Numara üretirken race condition önleme

## 23. Raporlama

Önerilen raporlar:
- Planlanan vs gerçekleşen maliyet
- Malzeme bazlı maliyet
- Tedarikçi bazlı maliyet
- Poz bazlı gerçek maliyet
- Mahal bazlı gerçek maliyet
- Proje bazlı satın alma
- Açık siparişler
- Açık teklifler
- Stok durumu
- Kritik stok
- Fiyat farkı (teklif-sipariş, sipariş-fatura, plan-gerçek)

## 24. Migration Stratejisi

FAZ 3 için yeni modeller oluşturulacak, mevcut modeller değiştirilmeyecek.
Migration dosyaları, yeni modellerin eklenmesi ve ilişkilerin kurulması için oluşturulacaktır.

## 25. Riskler

- Faz 3 kapsamının aşırı genişletilmesi
- Mevcut sistemle entegrasyon kompleksitesi
- Performans sorunları (özellikle stok hareketleri)
- Kullanıcı eğitimi ve adapton süreci

## 26. FAZ 3 Çekirdek

FAZ 3'te geliştirilmesi gereken temel modüller:
1. Tedarikçi yönetimi
2. Teklif yönetimi
3. Satın alma talebi
4. Satın alma siparişi
5. Mal kabul / irsaliye
6. Stok hareketleri
7. Fatura yönetimi (tedarikçi faturaları entegrasyonu)
8. Gerçek maliyet hesaplama
9. Poz/mahal gerçek tüketim takibi

## 27. FAZ 3.1

FAZ 3.1'de genişletilebilecek alanlar:
- Üretim emri yönetimi
- Proje faturalandırması
- Kaynak planlama
- Gelişmiş maliyet analizleri

## 28. Sonraki Fazlar

Daha sonraki fazlarda ele alınabilecek konular:
- Muhasebe entegrasyonunun tamamlanması
- Bütçe yönetimi
- Proje yönetimi entegrasyonu
- İnsan kaynakları ve maaş
- Yönetim raporları ve KPI'lar

## 29. Önerilen Nihai Mimari

Önerilen FAZ 3 mimarisi:
```
Tedarikçi
    ↓
Teklif
    ↓
Satın Alma Talebi
    ↓
Satın Alma Siparişi
    ↓
Mal Kabul / İrsaliye
    ↓
Stok
    ↓
Fatura
    ↓
Cari
    ↓
Gerçekleşen Maliyet
    ↓
Poz / Mahal
    ↓
Planlanan vs Gerçekleşen Maliyet
```

## 30. Implementation Sırası

1. Tedarikçi ve teklif yönetimi
2. Satın alma talebi ve siparişi
3. Mal kabul ve stok hareketleri
4. Fatura yönetimi
5. Gerçek maliyet hesaplama
6. Poz/mahal tüketim takibi
7. Raporlama ve analiz
8. Frontend entegrasyonu
9. Testler ve performans optimizasyonu

## 31. Test Stratejisi

- Birim testleri (modeller, servisler, API view'leri)
- Entegrasyon testleri (API akışları)
- Kullanıcı arayüzü testleri (frontend)
- Performans testleri (yük testi)
- Güvenlik testleri (yetkilendirme, veri izolasyonu)