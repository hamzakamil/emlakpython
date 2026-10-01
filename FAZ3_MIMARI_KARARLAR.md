# FAZ 3 MİMARİ KARARLAR

Bu doküman, FAZ 3 implementation öncesinde açık kalan mimari kararların kesinleştirilmesini amaçlar.
HENÜZ KOD YAZMA.
HENÜZ MIGRATION OLUŞTURMA.

==================================================

1. SATIN ALMA TALEBİ VE TEKLİF AYRIMI
==================================================

Karar: SatınAlmaTalebi ve TedarikciTeklifi ayrı kavramlar olarak tutulur.

- SatınAlmaTalebi: Şirket içi ihtiyaç talebi. Talebi oluşturan birim veya kişi (User) ile ilişkilendirilir.
- TedarikciTeklifi: Tedarikçinin verdiği teklif. Teklif, bir SatınAlmaTalebiKalemi ile ilişkilendirilebilir (opsiyonel) veya doğrudan bir proje/malzeme için talep olarak oluşturulabilir.

FAZ 2'deki ProjeMalzeme.selected_teklif, proje seviyesindeki seçimi temsil eder ve FAZ 3'te bu seçimi SatınAlmaTalebiKalemi üzerinden yöneteceğiz.

Karar: SatınAlmaTalebiKalemi içinde bir `secili_teklif` alanı (ForeignKey to TedarikciTeklifi, nullable) bulunur.
Bu alan, talep kalemi için seçilen teklifi gösterir. Teklif seçilmediği sürece NULL olur.

TedarikciTeklifi.secildi alanı, FAZ 3'te ana seçim kaynağı olarak KULLANILMAZ.
Bu alan, sadece FAZ 2'deki eski kullanım için korunur ve FAZ 3'te yeni teklifler için kullanılmaz.
Yeni tekliflerin seçimi, SatınAlmaTalebiKalemi.secili_teklif üzerinden yapılır.

İlişkisel veri modeli:
- SatınAlmaTalebi 1:N SatınAlmaTalebiKalemi
- SatınAlmaTalebiKalemi 0:1 TedarikciTeklifi (secili_teklif)
- TedarikciTeklifi 1:N SatınAlmaTalebiKalemi (bir teklif, birden fazla talep kalemi tarafından seçilebilir, ancak aynı proje-malzeme-tedarikçi kombinasyonu için sadece bir teklif aktif olabilir - bu kısıtlama veritabanı constraint ile sağlanır)

==================================================

2. MALZEME TEDARİKÇİ İLİŞKİSİ
==================================================

Karar: MalzemeTedarikciIliskisi modeli korunur ve aşağıdaki gibi tanımlanır:

- MalzemeTedarikciIliskisi: Malzeme/tedarikçi ilişki bilgisi ve geçmiş/lite takimi için kullanılır.
  Bu model, belirli bir malzeme ve tedarikçi arasındaki genel ilişkiyi (örn. aktiflik durumu, geçmiş siparişler, vb.) tutar.
  Fiziksel DELETE kullanılmaz, durum takibi ile yönetilir.

- SatınAlmaSiparisi: Resmi satın alma belgesi. Belirli bir proje için, belirli bir tedarikçiden, belirli malzemeler için verilen siparişidir.

Bu ayrımın mevcut veriye etkisi:
- Mevcut MalzemeTedarikciIliskisi kayıtları, FAZ 3'te de aynı şekilde kullanılmaya devam eder.
- Yeni SatınAlmaSiparisi oluşturulurken, ilgili MalzemeTedarikciIliskisi kaydına referans verilebilir (opsiyonel) ancak zorunlu değildir.
- MalzemeTedarikciIliskisi, SatınAlmaSiparisi'nin oluşturulmasını engellemez veya etkilemez. İki model bağımsız olarak çalışır.

==================================================

3. SATIN ALMA TALEBİ
==================================================

Karar: SatınAlmaTalebi'de talep sahibi için Cari FK yerine User FK kullanılır.

- Sebep: Talebi oluşturan kişi, sisteme giriş yapmış bir kullanıcıdır ve bu kullanıcı, cari modülünün bir parçası olmayabilir (örn. bir proje yöneticisi, mühendis, vb.).
- Mevcut users sistemini inceledik: `users.User` modeli mevcuttur ve bu model, sistemdeki tüm kullanıcıları içerir.
- Dolayısıyla, SatınAlmaTalebi modelinde `talep_sahibi` alanı olarak `ForeignKey to users.User` kullanılır.

Cari: Ticari taraf içindir (tedarikçi, müşteri, vb.).
User: Talebi oluşturan personel içindir.

Bu ayrım kesinleştirilir: Talep sahibi her zaman bir kullanıcıdır ve cari ile ilişkilendirilmelidir (örn. kullanıcının cari kartı olabilir ancak bu zorunlu değildir).

==================================================

4. SATIN ALMA TALEBİ KALEMİ
==================================================

Karar: SatınAlmaTalebiKalemi aşağıdaki alanları gerektirir:

- proje (ForeignKey to Proje) - zorunlu
- malzeme (ForeignKey to Malzeme, nullable) - malzeme veya poz/mahal için biri zorunlu
- poz (ForeignKey to Poz, nullable) - malzeme veya poz/mahal için biri zorunlu
- mahal (ForeignKey to Mahal, nullable) - opsiyonel, poz içinde mahal belirtilirse kullanılır
- miktar (DecimalField) - zorunlu
- birim (CharField) - zorunlu (malzemenin birimi veya pozun birimi)
- ihtiyaç_tarihi (DateField) - zorunlu
- açıklama (TextField) - opsiyonel
- tahmini_fiyat (DecimalField) - opsiyonel, teklif beklenirken tahmini bir fiyat
- secili_teklif (ForeignKey to TedarikciTeklifi, nullable) - seçilen teklif

Proje header'da varsa gereksiz tekrarları kaldırıldı: SatınAlmaTalebi zaten projeye bağlı olduğundan, SatınAlmaTalebiKalemi'de proje alanı aslında gereksiz olabilir.
Ancak, her talep kalemi farklı bir proje için olabileceği (örn. bir talev birden fazla proje için) ve proje bazlı raporlama gereğiyle proje alanı kalemde tutulur.
Bu durumda, veri bütünlüğü için SatınAlmaTalebiKalemi.proje, SatınAlmaTalebi.proje ile aynı olmalıdır ve bu kısıtlama veritabanı constraint veya uygulama mantığıyla sağlanır.

==================================================

5. SATIN ALMA SİPARİŞİ
==================================================

Karar: SatınAlmaSiparisi ve SatınAlmaSiparisiKalemi aşağıdaki alanlara sahiptir:

SatınAlmaSiparisi:
- tedarikci (ForeignKey to Tedarikci) - zorunlu
- proje (ForeignKey to Proje) - zorunlu
- tarih (DateField, sipariş tarihi) - zorunlu
- teslim_tarihi (DateField, tahmini teslim tarihi) - zorunlu
- para_birimi (CharField) - zorunlu
- kur (DecimalField) - zorunlu
- durum (State Machine) - zorunlu
- kaynak_talep (ForeignKey to SatınAlmaTalebi, nullable) - opsiyonel, doğrudan sipariş de oluşturulabilir

SatınAlmaSiparisiKalemi:
- malzeme (ForeignKey to Malzeme) - zorunlu
- poz (ForeignKey to Poz, nullable) - opsiyonel, poz bazlı sipariş için
- mahal (ForeignKey to Mahal, nullable) - opsiyonel, mahal bazlı sipariş için
- miktar (DecimalField) - zorunlu
- birim (CharField) - zorunlu
- birim_fiyat (DecimalField) - zorunlu, sipariş fiyatı
- toplam_tutar (DecimalField, hesaplanabilir) - hesaplanabilir, saklanabilir
- kaynak_teklif (ForeignKey to TedarikciTeklifi, nullable) - opsiyonel, siparişin kaynağı olan teklif
- teklif_fiyat_snapshot (DecimalField) - zorunlu, sipariş oluşturulduğunda teklif fiyatının kopyası
- açıklama (TextField) - opsiyonel

Sipariş oluşturulduktan sonra kaynak teklif değişse bile sipariş fiyatı DEĞİŞMEMELİ.
Bu sağlanmak için:
- SatınAlmaSiparisiKalemi.teklif_fiyat_snapshot alanı, sipariş oluşturulduğunda Kaynak teklifin birim_fiyat değerini kopyalar ve bu değer asla güncellenmez.
- SatınAlmaSiparisiKalemi.birim_fiyat alanı, teklif_fiyat_snapshot ile aynı değeri tutar ve bu da asla güncellenmez (sipariş fiyatı sabittir).
- Kaynak teklif değişirse, bu yeni teklif sadece yeni siparişler için kullanılır.

==================================================

6. MAL KABUL
==================================================

Karar: Yeni modeller MalKabul ve MalKabulKalemi olarak kesinleştirilir.

MalKabul:
- satın_alma_siparişi (ForeignKey to SatınAlmaSiparisi) - zorunlu
- mal_kabul_tarihi (DateField) - zorunlu
- kabul_eden (ForeignKey to users.User) - zorunlu
- notlar (TextField) - opsiyonel
- durum (State Machine: TASLAK → ONAYLANDI → KISMI → TAMAMLANDI → IPTAL) - zorunlu
- created_at, updated_at

MalKabulKalemi:
- mal_kabul (ForeignKey to MalKabul) - zorunlu
- satın_alma_siparişi_kalemi (ForeignKey to SatınAlmaSiparisiKalemi) - zorunlu
- ordered_qty (DecimalField) - zorunlu, sipariş kalemindeki miktar
- accepted_qty (DecimalField) - zorunlu, kabul edilen miktar
- rejected_qty (DecimalField) - zorunlu, reddedilen miktar (kötü kalte, vb.)
- remaining_qty (DecimalField, hesaplanabilir) - ordered_qty - accepted_qty - rejected_qty
- kabul_edilen_birim_fiyat (DecimalField) - zorunlu, kabul anındaki birim fiyat (sipariş fiyatından farklı olabilir)
- toplam_kabul_tutarı (DecimalField, hesaplanabilir) - accepted_qty * kabul_edilen_birim_fiyat
- aciklama (TextField) - opsiyonel
- created_at, updated_at

Matematiksel ilişkiler:
- ordered_qty = accepted_qty + rejected_qty + remaining_qty
- remaining_qty ≥ 0
- accepted_qty ≥ 0
- rejected_qty ≥ 0

Bir sipariş kaleminin 100 adet sipariş, 95 kabul, 5 kalan örneği:
- ordered_qty = 100
- accepted_qty = 95
- rejected_qty = 0
- remaining_qty = 5

Aynı miktarın iki kez kabul edilmesini engellemek için:
- MalKabulKalemi oluşturulurken, ilgili satın_alma_siparişi_kalemi için zaten kabul edilmiş miktar (accepted_qty toplamı) kontrol edilir ve yeni accepted_qty bu limiti aşamaz.
- Bu kontrol, transaction.atomic() içinde yapılır ve veritabanı constraint ile de desteklenebilir (örn. check constraint veya unique constraint ile birlikte bir toplam kabul miktarı alanı).

==================================================

7. STOK HAREKETİ
==================================================

Karar: StokHareketi değişmez finansal/operasyonel transaction olarak tasarlanır ve aşağıdaki alanları zorunlu kılar:

- depo (ForeignKey to Depo) - zorunlu
- malzeme (ForeignKey to Malzeme) - zorunlu
- hareket_tipi (Choices: GIRIS, CIKIS, TRANSFER, IADE, FIRE, SAYIM, DUZELTME) - zorunlu
- miktar (DecimalField) - zorunlu (GIRIS için pozitif, CIKIS için negatif olarak tutulur ama mutlak değer kullanılır)
- birim (CharField) - zorunlu (malzemenin birimi)
- maliyet (DecimalField) - zorunlu, hareket birimindeki maliyet (birim maliyet)
- tarih (DateField) - zorunlu
- kaynak_belge (GenericForeignKey) - zorunlu, hareketin kaynağı olan belge (SatınAlmaSiparisi, MalKabul, Poz, Mahal, vb.)
- kullanıcı (ForeignKey to users.User) - zorunlu, hareketi yapan kişi

GenericForeignKey riskleri değerlendirildi: Esnekliği sağlar ancak sorguları zorlaştırır ve referans bütünlüğü veritabanı seviyesinde garanti edilemez.
Alternatif olarak, polymorphic relation veya ayrı ayrı FK alanları (kaynak_talep, kaynak_siparis, kaynak_mal_kabul, vb.) kullanılması önerildi ancak bu modeli çok şişkın yapar.
Karar: GenericForeignKey kullanılır ancak uygulama katmanında kaynak belgesinin varlığı ve tipi kontrol edilir.
Gelişmiş bir çözüm için, kaynak belgesi için ayrı bir model (örn. KaynakBelge) ve bu model üzerinden polymorphic relation kullanılabilir ancak bu FAZ 3 için gereksiz görüldü ve teknik borç olarak bırakıldı.

==================================================

8. POZ/MAHAL TÜKETİMİ
==================================================

Karar: "Yeni model gerekmez" kararını yeniden değerlendirdik ve iki seçenek karşılaştırıldı:

A) StokHareketi içine proje/poz/mahal alanları
B) StokHareketi + ayrı StokTuketim modeli

Avantaj/Dezavantaj:

Seçenek A:
- Avantaj: Tek model, daha az join, basit sorgular.
- Dezavantaj: StokHareketi modeli her hareket için proje/poz/mahal alanlarını taşır, bu alanlar sadece CIKIS hareketleri (tüketim) için anlamlıdır; diğer hareket tipleri için boş veya gereksiz olur.

Seçenek B:
- Avantaj: StokHareketi temiz olur, sadece stok işlemleri için. Tüketim özelinde ayrı bir model, sadece tüketim hareketleri için gerekli alanları taşır.
- Dezavantaj: İki model, daha fazla join ve kompleksite.

FAZ 3C için nihai seçim: **Seçenek A** (StokHareketi içine proje/poz/mahal alanları)
- Sebep: İnşaat ERP'sinde stok çıkışının büyük bölümü proje/poz/mahal tüketimidir ve bu bilgilerin StokHareketi içinde bulunması, raporlama ve analiz için daha doğrudur.
- Ek alanlar:
  - proje (ForeignKey to Proje, nullable) - sadece CIKIS hareketleri için zorunlu (tüketim)
  - poz (ForeignKey to Poz, nullable) - sadece CIKIS hareketleri için zorunlu
  - mahal (ForeignKey to Mahal, nullable) - sadece CIKIS hareketleri için opsiyonel
  - tüketim_amaci (CharField, Choices: POZ_TUKETIMI, MAHAL_TUKETIMI, FIRE, vb.) - opsiyonel, hareket amacını belirtir

Bu sayede, StokHareketi.CIKIS hareketleri, proje/poz/mahal tüketimi için gerekli tüm bilgiyi taşır ve diğer hareket tipleri (GIRIS, TRANSFER, vb.) için bu alanlar NULL olur.

==================================================

9. STOK MALİYETLEME
==================================================

Karar: "Hareket bazlı maliyet" ifadesini tek başına yeterli kabul etmeyelim ve aşağıdaki hibrit yaklaşımı değerlendirdik:

A) Projeye doğrudan teslim edilen malzeme: gerçek Mal Kabul birim maliyeti
B) Ortak depo: Depo + Malzeme bazında hareketli ağırlıklı ortalama maliyet
C) İade: ilgili hareket maliyeti
D) Fire: mevcut maliyeti koruyarak fire gideri
E) Transfer: maliyet değişmez

Bu hibrit yaklaşımın uygun olup olmadığını değerlendirdik ve karar: **Bu hibrit yaklaşım FAZ 3 standardı olarak kesinleştirilir.**

Açıklama:
- Her StokHareketi kaydındaki `maliyet` alanı, hareket anındaki birim maliyeti tutar.
- Bu maliyet, hareketin kaynağına göre farklı şekilde belirlenir:
  - Mal Kabul sonrası stok girişi (GIRIS): MalKabulKalemi.kabul_edilen_birim_fiyat kullanılır.
  - Stok transferi (TRANSFER): Kaynak stok hareketinin maliyeti kullanılır (maliyet korunur).
  - Stok çıkışı (CIKIS): Stokta o anki birim maliyet (örn. ağırlıklı ortalama veya hareket bazlı) kullanılır. Ancak, hareket bazlı maliyet yaklaşımında, her stok girişi kendi maliyetini taşır ve çıkışta bu maliyetler FIFO, LIFO veya ağırlıklı ortalama gibi bir yöntemle hesaplanır. Karar: Ağırlıklı ortalama (WA) kullanılır ve bu maliyet, StokHareketi kaydında saklanır. Yani, her stok girişi (GIRIS) için maliyet, girilen miktarın birim maliyetiyle hesaplanır ve stoktaki ortalama maliyet güncellenir. Stok çıkışı (CIKIS) için kullanılan maliyet, o anki stok ortalama maliyeti olur.
  - İade (IADE): İade edilen malzemenin maliyeti, iade anındaki stok ortalama maliyeti olur (veya orijinal giriş maliyeti, kararlaşılacak).
  - Fire (FIRE): Fire edilen malzemenin maliyeti, fire anındaki stok ortalama maliyeti olur ve bu maliyet, fire gideri olarak muhasebeye aktarılır.
  - Sayım (SAYIM) ve Düzeltme (DUZELTME): Fark, maliyet farkı olarak hesaplanır ve ilgili gider/gelir hesabına yansıtılır.

Not: Bu yaklaşım, StokHareketi.maliyet alanının her hareket için geçerli bir birim maliyet tutmasını gerektirir ve bu maliyet, hareketin tipi ve kaynağına göre uygulama mantığıyla belirlenir.

==================================================

10. GERÇEK MALİYET
==================================================

Karar: GerceklesenMaliyet adlı yeni tabloyu şu aşada oluşturmayız.

Source of truth: Stok hareketleri + tüketim hareketleri (StokHareketi.CIKIS).

Gerçek tüketim maliyeti: tüketilen_miktar × tüketim_anındaki_birim_maliyet
- Bu, StokHareketi.CIKIS hareketlerinin `miktar * maliyet` toplamıdır.

Planlanan maliyet: PozPlan / YaklasikMaliyet snapshot
- Bu, FAZ 2'deki YaklasikMaliyet ve YaklasikMaliyetSatiri modellerindeki birim_fiyat_snapshot ve miktar alanlarından hesaplanır.

Plan vs gerçek raporu ayrı aggregation service olarak tasarlanmalı.
- Bu service, planlanan maliyet (YaklasikMaliyet üzerinden) ve gerçek maliyet (StokHareketi üzerinden) hesaplar ve farkı raporlar.

==================================================

11. FATURA EŞLEŞTİRMESİ
==================================================

Karar: Mevcut Finance.Fatura ve CariHareket yapısını kullanır, yeni Fatura modeli oluşturmayız.

Sipariş → Mal Kabul → Fatura
üçlü eşleştirmesini şu şekilde tasarlarız:

- Her Faturalar, cari modülüyle ilişkilendirilir (cari.ForeignKey to cari.Cari).
- Fatura, ilgili SatınAlmaSiparisi ve MalKabul ile ilişkilendirilebilir (opsiyonel ForeignKey alanlar).
- Aşağıdaki karşılaştırmalar, bir reconciliation service/read model ile yapılır:
  - sipariş miktarı (SatınAlmaSiparisiKalemi.miktar)
  - kabul miktarı (MalKabulKalemi.accepted_qty)
  - fatura miktarı (Finance.Fatura.tutar, birim fiyat ile çarpılarak veya fatura kalemleriyle)
  - sipariş fiyatı (SatınAlmaSiparisiKalemi.teklif_fiyat_snapshot)
  - kabul fiyatı (MalKabulKalemi.kabul_edilen_birim_fiyat)
  - fatura fiyatı (Finance.Fatura.tutar / fatura miktarı, eğer fatura miktarı biliniyorsa)

İlk versiyonda reconciliation service/read model olarak taslanır ve yeni FaturaFark modeli oluşturulmaz.

==================================================

12. MUHASEBE
==================================================

Karar: Tedarikçi faturası için mevcut sistem üzerinden ilerlenir:
Finance.Fatura → CariHareket → MuhasebeFisi

Yeni muhasebe modeli oluşturulmaz.
Gerçek hesap kodları mevcut accounting sisteminden doğrulanmadan varsayım yapılmaz.

Not: Muhasebe entegrasyonu, CariHareket üzerinden yapılır ve CariHareket.muhasebe_fisi alanı ile bağlantı sağlanır.
Bu alan, fatura oluşturulduğunda veya fatura öndendiğinde doldurulabilir (otomatik veya manuel).

==================================================

13. NUMARALANDIRMA
==================================================

Karar: Merkezi servis kullanılır. Model save() içine dağınık numara üretme koyulmaz.

Sequence mantığı: tenant + yıl + belge_tipi
- Örnek: SAT-2026-000001 (SatınAlmaTalebi), SIP-2026-000001 (SatınAlmaSiparisi), MK-2026-000001 (MalKabul)

transaction.atomic() ve select_for_update() ile concurrency güvenliği sağlanır.

Mevcut projede sequence/number generator varsa onu yeniden kullanılır. İncelenerek:
- Projede şu anda bir sequence/number generator bulunmamaktadır.
- Dolayısıyla, yeni bir merkezi sequence yapısı sadece tasarlanır ve FAZ 3'te uygulanır.

Bu yapı, bir servis sınıfı (örn. NumberGeneratorService) olarak uygulanır ve her belge türü için ayrı bir sıralar tutar.

==================================================

14. API
==================================================

Karar: FAZ 3 için mevcut /api/v1/ versiyonunu kullanılır. Yeni API v2 açılmaz.

Aday endpointler değerlendirilir ve aşağıdaki gibi belirlenir:
- /api/v1/purchase-requests/ (SatınAlmaTalebi)
- /api/v1/purchase-orders/ (SatınAlmaSiparisi)
- /api/v1/goods-receipts/ (MalKabul)
- /api/v1/warehouses/ (Depo)
- /api/v1/stock-movements/ (StokHareketi)
- /api/v1/consumption/ (StokHareketi.CIKIS filtresi)
- /api/v1/reconciliation/ (Fatura eşleştirmesi raporu)

Bu endpointler, mevcut API yapısına eklenir ve versioning /api/v1/ içinde kalır.

==================================================

15. FRONTEND
==================================================

Karar: Gerçek mevcut frontend teknolojisi dosyalardan doğrulanmıştır ve şu şekilde belirlenmiştir:
- frontend/ dizini altında React uygulaması bulunur.
- package.json: React, TypeScript, Vite kullanılıyor.
- tsconfig.json: TypeScript yapılandırması.
- postcss.config.js ve tailwind.config.js: Tailwind CSS kullanılıyor.
- index.html: Ana HTML dosyası.

Karar: Mevcut state sistemini aynen kullanılır. Yeni state framework kurulmaz.
- Mevcut proje, React Context veya benzeri bir state yönetimi kullanıyorsa bu devam eder.
- Eğer bir state yönetimi yoksa, FAZ 3 için React Context veya Redux (projeye uygun) eklenir ancak bu kararı frontend ekibi verir. Dokümanda, mevcut sistemin kullanılması önerilir.

==================================================

16. YETKİ
==================================================

Karar: Mevcut users/permission altyapısı kullanılır. Yeni rol oluşturmak yerine mevcut rollerin hangi işlemlere erişebileceği belirlenir.

Minimum izinler:
- Talep oluşturma: Talep oluşturma izni (örn. proje üyesi, talepçi)
- Talep onaylama: Talep onaylama izni (örn. proje yöneticisi, müşteri temsilcisi)
- Sipariş oluşturma: Sipariş oluşturma izni (örn. tedarikçi yöneticisi, alım sorumlusu)
- Sipariş onaylama: Sipariş onaylama izni (örn. proje yöneticisi, finans sorumlusu)
- Mal kabul: Mal kabul izni (örn. depo sorumlusu, reçete sorumlusu)
- Stok hareketi: Stok hareketi izni (örn. depo sorumlusu, stokçu)
- İptal: İptal izni (örn. proje yöneticisi, yetkili)
- Rapor görüntüleme: Rapor görüntüleme izni (örn. proje yöneticisi, finans sorumlusu, yetkili)

Bu izinler, mevcut Django yetkilendirme sistemi (örn. groups ve permissions) veya özel bir yetkilendirme mantığıyla uygulanır.

==================================================

17. FAZ 3A SINIRI
==================================================

Karar: FAZ 3A: Sadece satın alma talebi + satın alma siparişi.
FAZ 3B: Mal kabul + depo + stok.
FAZ 3C: Poz/Mahal tüketimi.
FAZ 3D: Gerçek maliyet + plan/gerçek rapor.

3A implementation'ı sırasında 3B/3C/3D kodları yazılmaz.
Her faz, bağımlı olduğu önceki fazların tamamlandığı varsayımıyla uygulanır.

==================================================

18. TEKNİK BORÇ
==================================================

Karar: Aşağıdakileri sonraki faza bırakılır:
- YFK malzeme eşleştirme
- EUR/USD TL dönüşümü
- Gelişmiş fiyat farkı yönetimi
- gelişmiş satın alma analitiği
- gelişmiş stok tahminleri
- otomatik tedarikçi değerlendirme

Bu maddeler, FAZ 3 implementation'ı tamamlandıktan sonra değerlendirilecek ve sonraki fazlarda ele alınacaktır.

==================================================

19. SON KARAR TABLOSU
==================================================

| Karar                     | Nihai değer                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| Talif seçim kaynağı?      | SatınAlmaTalebiKalemi.secili_teklif (ForeignKey to TedarikciTeklifi)       |
| Talep sahibi?             | users.User (ForeignKey)                                                     |
| Sipariş source of truth?  | SatınAlmaSiparisi (tedarikci, proje, tarih, vb.) ve SatınAlmaSiparisiKalemi |
| Mal kabul modeli?         | MalKabul ve MalKabulKalemi                                                  |
| Stok modeli?              | StokHareketi (proje/poz/mahal alanları ile)                                 |
| Tüketim modeli?           | StokHareketi.CIKIS (proje/poz/mahal dolu)                                   |
| Stok maliyet yöntemi?     | Hibrit hareket bazlı maliyet (Ağırlıklı ortalama ile stok maliyeti)         |
| Gerçek maliyet source of truth? | StokHareketi (miktar * maliyet)                                         |
| Fatura entegrasyonu?      | Mevcut Finance.Fatura ve CariHareket, reconciliation service ile           |
| Numara servisi?           | Merkezi servis (tenant + yıl + belge_tipi)                                  |
| API versiyonu?            | /api/v1/ (yeni v2 açılmaz)                                                  |
| Frontend state?           | Mevcut sistem (React Context veya benzeri)                                  |
| Yetki sistemi?            | Mevcut users/permission altyapısı                                           |

==================================================

20. IMPLEMENTATION HAZIRLIK KARARI
==================================================

FAZ 3A IMPLEMENTATION'A HAZIR

Not: Yukarıdaki tüm kararlar kesinleştirildi ve FAZ 3A implementation'ı için gerekli mimari tasarım tamamlandı.
Kod yazma ve migration oluşturma aşamasına geçilebilir.