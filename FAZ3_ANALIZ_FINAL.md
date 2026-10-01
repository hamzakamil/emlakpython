# FAZ 3 ANALİZ RAPORU (FINAL)

## 1. MEVCUT MODELLERİ YENİDEN OLUŞTURMA

### 1.1 Tedarikci Modeli
- **Dosya**: `construction/models.py`
- **Sınıf**: `Tedarikci`
- **Açıklama**: Tedarikçi / tedarik firması kartı.
- **Alanlar**:
  - `firma_adi` (CharField)
  - `firma_kodu` (CharField, unique)
  - `il`, `ilce`, `telefon`, `email`, `adres`
  - `is_active` (BooleanField)
  - `created_at`, `updated_at` (DateTimeField)
- **Kısıtlamalar**: `tenant` ve `firma_kodu` ile unique constraint.
- **Notlar**: Fiziksel DELETE kullanılmaz, `is_active` ile arşivlenir.

### 1.2 TedarikciTeklifi Modeli
- **Dosya**: `construction/models.py`
- **Sınıf**: `TedarikciTeklifi`
- **Açıklama**: Proje/malzeme için tedarikçilerden alınan karşılaştırmalı teklifler.
- **Alanlar**:
  - `proje` (ForeignKey to Proje)
  - `malzeme` (ForeignKey to Malzeme)
  - `tedarikci` (ForeignKey to Tedarikci)
  - `miktar` (DecimalField)
  - `birim_fiyat` (DecimalField)
  - `toplam_tutar` (DecimalField, otomatik hesaplanır)
  - `durum` (Choices: TASLAK, ISTENDI, GELDI, DEGERLENDIRILIYOR, KABUL, RED, IPTAL)
  - `gecerlilik_tarihi` (DateField)
  - `notlar` (TextField)
  - `secildi` (BooleanField, varsayılan False)
  - `is_active` (BooleanField)
  - `created_at`, `updated_at` (DateTimeField)
- **Kısıtlamalar**:
  - `tenant`, `proje`, `malzeme`, `tedarikci` ile unique constraint (sadece aktif teklifler için)
  - `miktar` ve `birim_fiyat` pozitif olmalı
- **Notlar**: Teklifler fiziksel olarak silinmez, `is_active` ile arşivlenir. Bir proje-malzeme grubu içinde aynı anda yalnızca bir teklif seçilebilir (`secildi` alanı).

### 1.3 MalzemeTedarikciIliskisi Modeli
- **Dosya**: `construction/models.py`
- **Sınıf**: `MalzemeTedarikciIliskisi`
- **Açıklama**: Malzeme - tedarikçi ilişki ve sipariş takibi.
- **Alanlar**:
  - `malzeme` (ForeignKey to Malzeme)
  - `tedarikci` (ForeignKey to Tedarikci)
  - `miktar` (DecimalField, sipariş miktarı)
  - `birim` (CharField, varsayılan "adet")
  - `durum` (Choices: BASLIYOR, AKTIF, GECIKIYOR, TAMAMLANDI, iptal)
  - `teslim_tarihi` (DateField)
  - `aciklama` (TextField)
  - `created_at`, `updated_at` (DateTimeField)
- **Kısıtlamalar**: `tenant`, `malzeme`, `tedarikci` ile unique constraint.
- **Notlar**: Fiziksel DELETE kullanılmaz, durum takibi ile yönetilir.

### 1.4 Cari Modeli
- **Dosya**: `cari/models.py`
- **Sınıf**: `Cari`
- **Açıklama**: Cari kartı — kiracı, malik, tedarikçi, taşeron vb. taraf.
- **Alanlar**:
  - `ad` (CharField)
  - `tip` (Choices: KIRACI, MALIK, TEDARIKCI, TASERON, DIGER)
  - `tur` (Choices: BIREYSEL, KURUMSAL)
  - `vergi_no`, `vergi_dairesi`, `tc_kimlik_no`, `ticaret_sicil_no`, `mersis_no`
  - `vergi_mukellefiyeti` (Choices)
  - `telefon`, `telefonlar` (JSONField)
  - `fatura_adresi`, `sevk_adresi`
  - `il`, `ilce`, `posta_kodu`
  - `yetkili_kisi`, `yetkili_telefon`, `yetkili_kisiler` (JSONField)
  - `cep_telefonu`, `cep_telefonlari` (JSONField)
  - `eposta`, `epostalar` (JSONField)
  - `web_sitesi`
  - `iban`, `banka_adi`, `sube_adi`
  - `odeme_sekli` (Choices)
  - `vade_gunu`
  - `iskonto_orani`
  - `risk_limiti`
  - `para_birimi` (Choices: TRY, USD, EUR, GBP)
  - `muhasebe_hesap_kodu`
  - `e_fatura_profili` (Choices)
  - `adres`, `eski_adres`
  - `ulke`
  - `grup`
  - `proje` (ForeignKey to construction.Proje, nullable)
  - `notlar` (TextField)
  - `is_active` (BooleanField)
  - `created_at`, `updated_at` (DateTimeField)
- **Kısıtlamalar**: `tenant` ve `ad` ile unique constraint.
- **Notlar**: Cari tipinde TEDARIKCI seçildiğinde tedarikçi modülüyle entegrasyon sağlanır.

### 1.5 CariHareket Modeli
- **Dosya**: `cari/models.py`
- **Sınıf**: `CariHareket`
- **Açıklama**: Cari hesap hareketi — borç/alacak kalemi (iptal deseni, fiziksel DELETE yok).
- **Alanlar**:
  - `cari` (ForeignKey to Cari)
  - `fatura` (ForeignKey to finance.Fatura, nullable)
  - `muhasebe_fisi` (ForeignKey to accounting.MuhasebeFisi, nullable)
  - `yon` (Choices: BORC, ALACAK)
  - `tutar` (DecimalField)
  - `aciklama` (CharField)
  - `islem_tarihi` (DateField)
  - `is_cancelled` (BooleanField)
  - `iptal_nedeni` (CharField)
  - `created_at` (DateTimeField)
- **Kısıtlamalar**: `fatura` alanı için unique constraint (fatura null değilse).
- **Notlar**: Fiziksel DELETE kullanılmaz, `is_cancelled` ile iptal edilir. Fatura ile ilişkilendirilerek muhasebe akışı oluşturulur.

### 1.6 Finance.Fatura Modeli
- **Dosya**: `finance/models.py`
- **Sınıf**: `Fatura`
- **Açıklama**: Fatura kaydı — borç/alacak takibi.
- **Alanlar**:
  - `No` (CharField, unique)
  - `cari` (ForeignKey to cari.Cari, nullable)
  - `kasa_banka_hesabi` (ForeignKey to KasaBankaHesabi, nullable)
  - `iade_faturasi` (Self-referential ForeignKey, nullable)
  - `durum` (Choices: DRAFT, ACTIVE, PAID, CANCELLED)
  - `tarih` (DateField)
  - `vade_tarihi` (DateField, nullable)
  - `tutar` (DecimalField)
  - `alacakli` (BooleanField)
  - `aciklama` (CharField)
  - `fatura_turu` (Choices: satis, kira, hakedis, iade, aidat, hizmet, proforma)
  - `senaryo` (Choices: e_fatura, e_arsiv, kagit)
  - `para_birimi` (Choices: TRY, USD, EUR, GBP)
  - `kur` (DecimalField)
  - `kdv_dahil_mi` (BooleanField)
  - `iskonto_tutari` (DecimalField)
  - `odenen_tutar` (DecimalField)
  - `e_fatura_uuid` (CharField)
  - `e_fatura_durum` (Choices)
  - `created_at`, `updated_at` (DateTimeField)
- **Kısıtlamalar**: `No` alanı unique.
- **Notlar**: Fiziksel DELETE kullanılmaz, `durum` ile yönetilir. Cari ile ilişkilendirilerek cari harekete entegrasyon sağlanır.

### 1.7 Muhasebe/Finance Modelleri (Ekstra)
- **Dosya**: `finance/models.py`
- **Sınıflar**: `KasaBankaHesabi`, `FinansalIslem`, `CekSenet`, `IdempotencyKey`, `FinansalOlay`
- **Açıklama**: Muhasebe ve finansal işlemler için temel modeller.
- **Notlar**: Bu modeller, FAZ 3'te fatura ve cari hareketlerle entegrasyon için kullanılacaktır.

## 2. FAZ 3'Ü ALT FAZLARA BÖL

FAZ 3, aşağıdaki dört ana alt fazla yeniden yapılandırılmıştır:

- **FAZ 3A**: Satın Alma Çekirdeği
- **FAZ 3B**: Mal Kabul + Stok
- **FAZ 3C**: Poz/Mahal Gerçek Tüketim
- **FAZ 3D**: Gerçekleşen Maliyet + Plan/Gerçek Analizi

Her alt fazın bağımlılıkları:
- FAZ 3A, FAZ 3B'nin girdisi (satın alma siparişi) üretir.
- FAZ 3B, FAZ 3A'nın çıktısı (sipariş) ve FAZ 3C'nin girdisi (stok girişi) üretir.
- FAZ 3C, FAZ 3B'nin çıktısı (stok) ve FAZ 3D'nin girdisi (tüketim) üretir.
- FAZ 3D, FAZ 3A, FAZ 3B ve FAZ 3C'nin çıktılarını kullanarak gerçek maliyet hesaplar ve plan/gerçek analizini yapar.

## 3. FAZ 3A ÇEKİRDEK MODELLER

FAZ 3A'da yeni oluşturulması gereken gerçek modeller:

### 3.1 SatınAlmaTalebi
- **Açıklama**: "Şu malzeme veya hizmete ihtiyacım var." talebi.
- **Bağlantılar**:
  - `proje` (ForeignKey to Proje)
  - `malzeme` (ForeignKey to Malzeme) veya `poz` (ForeignKey to Poz) veya hizmet açıklaması
  - `miktar` (DecimalField)
  - `birim` (CharField)
  - `talebi_olan` (ForeignKey to Cari, talebi oluşturan birim veya kişi)
  - `durum` (State Machine: TASLAK → ONAYA_GONDERILDI → ONAYLANDI → REDDEDILDI → SIPARISE_DONUSTU → IPTAL)
  - `created_at`, `updated_at`
- **Notlar**: TedarikciTeklifi modeli yeniden oluşturulmayacak. Bunun yerine, SatınAlmaTalebi, tedarikçi teklif talebi olarak kullanılarak TedarikciTeklifi modeline bağlanacak.

### 3.2 SatınAlmaTalebiKalemi
- **Açıklama**: Satın alma talebindeki her kalem (malzeme/hizmet) için ayrı satır.
- **Bağlantılar**:
  - `satın_alma_talebi` (ForeignKey to SatınAlmaTalebi)
  - `malzeme` (ForeignKey to Malzeme, nullable)
  - `hizmet_aciklamasi` (TextField, nullable)
  - `miktar` (DecimalField)
  - `birim` (CharField)
  - `birim_fiyat_tahmini` (DecimalField, opsiyonel)
  - `toplam_tutar_tahmini` (DecimalField, hesaplanabilir)
  - `durum` (Talebin durumunu yansıtır, ayrı durum gerekmeyebilir)
- **Notlar**: Malzeme veya hizmet seçimi zorunlu olarak tanımlanacak.

### 3.3 SatınAlmaSiparisi
- **Açıklama**: "Şu tedarikçiden şu miktarı şu fiyatla sipariş ettim." belgesi.
- **Bağlantılar**:
  - `satın_alma_talebi` (ForeignKey to SatınAlmaTalebi, opsiyonel - doğrudan sipariş de oluşturulabilir)
  - `tedarikci` (ForeignKey to Tedarikci)
  - `proje` (ForeignKey to Proje)
  - `para_birimi` (CharField)
  - `kur` (DecimalField)
  - `durum` (State Machine: TASLAK → ONAY_BEKLIYOR → ONAYLANDI → KISMI_TESLIM → TAMAMLANDI → IPTAL)
  - `siparis_tarihi` (DateField)
  - `teslim_tarihi` (DateField)
  - `notlar` (TextField)
  - `created_at`, `updated_at`
- **Notlar**: Sipariş, talepteki malzemeleri ve miktarları içerir ancak fiyat ve tedarikçi bilgisiyle zenginleştirilir.

### 3.4 SatınAlmaSiparisiKalemi
- **Açıklama**: Satın alma siparişindeki her kalem için ayrı satır.
- **Bağlantılar**:
  - `satın_alma_siparişi` (ForeignKey to SatınAlmaSiparisi)
  - `malzeme` (ForeignKey to Malzeme)
  - `miktar` (DecimalField)
  - `birim` (CharField)
  - `birim_fiyat` (DecimalField, sipariş fiyatı)
  - `toplam_tutar` (DecimalField, hesaplanabilir)
  - `teslim_tarihi` (DateField, opsiyonel)
  - `durum` (Sipariş kalemi durumu: BEKLENİYOR, KISMI_TESLIM, TAMAMLANDI, IPTAL)
  - `created_at`, `updated_at`
- **Notlar**: Sipariş kalemi, SatınAlmaTalebiKalemi'nden veya doğrudan tedarikçi teklifinden oluşturulabilir.

## 4. TEKLİF -> SATIN ALMA

FAZ 2'de ProjeMalzeme.selected_teklif alanı ile kullanılan yapı, FAZ 3A'da aşağıdaki şekilde dönüştürülecektir:

### 4.1 Seçili Teklifin Satın Alma Talebi ve Siparişe Dönüşümü
- **Adım 1**: Kullanıcı, bir proje ve malzeme için tedarikçi teklifi talebi oluşturur (SatınAlmaTalebi).
- **Adım 2**: Tedarikçilerden teklifler alınır ve TedarikciTeklifi modeline kaydedilir.
- **Adım 3**: En uygun teklif seçilir (TedarikciTeklifi.secildi = True).
- **Adım 4**: Seçilen teklif, SatınAlmaSiparisi oluşturmak için kullanılır:
  - Siparişin `tedarikci` alanı, teklifin `tedarikci` alanına eşlenir.
  - Siparişin `proje` alanı, teklifin `proje` alanına eşlenir.
  - Siparişin kalemleri (SatınAlmaSiparisiKalemi), teklifin malzeme, miktar ve birim fiyat bilgilerini kullanılarak oluşturulur:
    - `malzeme` → teklifin `malzeme`
    - `miktar` → teklifin `miktar`
    - `birim_fiyat` → teklifin `birim_fiyat`
    - `toplam_tutar` → teklifin `toplam_tutar` (opsiyonel olarak yeniden hesaplanabilir)
- **Adım 5**: Sipariş oluşturulduktan sonra, teklifin `secildi` alanı True olarak kalır ve geçmişteki referans için korunur.
- **Notlar**: Teklifteki bilgiler (malzeme, miktar, birim fiyat, tedarikçi, proje) siparişe snapshot olarak kopyalanır. Bu sayede teklif fiyatı değişse de sipariş fiyatı korunur.

## 5. SATIN ALMA TALEBİ VE SİPARİŞ AYRIMI

### 5.1 Satın Alma Talebi
- **Tanım**: "Şu malzeme veya hizmete ihtiyacım var."
- **Amaç**: İhtiyaç belirleme ve tedarikçi teklif toplama sürecini başlatma.
- **State Machine**:
  - TASLAK: Talev oluşturuldu, henüz gönderilmedi.
  - ONAYA_GONDERILDI: Talev onay için gönderildi.
  - ONAYLANDI: Talev onaylandı, tedarikçi teklifi talebi gönderilebilir.
  - REDDEDILDI: Talev reddedildi, süreç sona erdi.
  - SIPARISE_DONUSTU: Talev onaylandı ve siparişe dönüştürüldü.
  - IPTAL: Talev iptal edildi.
- **Notlar**: Talev, birden fazla tedarikçi teklifi alabilir. Seçilen teklif, sipariş oluşturmak için kullanılır.

### 5.2 Satın Alma Siparişi
- **Tanım**: "Şu tedarikçiden şu miktarı şu fiyatla sipariş ettim."
- **Amaç**: Satın alma sözleşmesinin oluşturulması ve teslimat takibi.
- **State Machine**:
  - TASLAK: Sipariş oluşturuldu, henüz gönderilmedi.
  - ONAY_BEKLIYOR: Sipariş tedarikçiye gönderildi, onay bekleniyor.
  - ONAYLANDI: Tedarikçi siparişi onayladı.
  - KISMI_TESLIM: Sipariş kısmen teslim edildi.
  - TAMAMLANDI: Sipariş tamamen teslim edildi.
  - IPTAL: Sipariş iptal edildi (tedarikçi veya alacak tarafından).
- **Notlar**: Sipariş, bir SatınAlmaTalebi'nden veya doğrudan oluşturulabilir. Sipariş durumu, teslimat takibi için kullanılır.

## 6. FAZ 3B STOK

FAZ 3B'de yeni modeller:

### 6.1 Depo
- **Açıklama**: Malzemenin saklandığı fiziksel veya mantıksal yer.
- **Alanlar**:
  - `ad` (CharField)
  - `kod` (CharField, unique ile tenant)
  - `tip` (Choices: ANA_DEPO, SANTIYE_DEPO, GEÇICI_DEPO, HARIC_DEPO)
  - `sorumlu` (ForeignKey to users.User, opsiyonel)
  - `adres` (TextField)
  - `is_active` (BooleanField)
  - `created_at`, `updated_at`
- **Kısıtlamalar**: `tenant` ve `kod` ile unique constraint.
- **Notlar**: Depo, şantiye ile ilişkilendirilebilir (DepoSantiyeIlkisi modeli üzerinden).

### 6.2 Depo/Şantiye İlişkisi
- **Açıklama**: Bir deponun hangi şantiye(ler) ile ilişkili olduğunu tanımlar.
- **Alanlar**:
  - `depo` (ForeignKey to Depo)
  - `santiye` (ForeignKey to construction.Mahal veya construction.Proje, şantiye mahal veya proje olarak temsil edilebilir)
  - `baslangic_tarihi` (DateField)
  - `bitis_tarihi` (DateField, nullable)
  - `is_active` (BooleanField)
  - `created_at`, `updated_at`
- **Kısıtlamalar**: `tenant`, `depo`, `santiye` ile unique constraint.
- **Notlar**: Şantiye, proje veya mahal olarak temsil edilebilir. Bir depo birden fazla şantiyeyle ilişkili olabilir.

### 6.3 StokHareketi
- **Açıklama**: Stok giriş/çıkış/transfer/iade/fire/sayım/ düzeltme hareketleri.
- **Alanlar**:
  - `tenant` (ForeignKey to tenants.Tenant, inherited from TenantAwareModel)
  - `depo` (ForeignKey to Depo)
  - `malzeme` (ForeignKey to Malzeme)
  - `miktar` (DecimalField)
  - `birim` (CharField, malzemenin birimiyle eşleşmeli)
  - `hareket_tipi` (Choices: GIRIS, CIKIS, TRANSFER, IADE, FIRE, SAYIM, DUZELTME)
  - `hareket_tarihi` (DateField)
  - `kaynak_belge` (GenericForeignKey veya polymorphic relation için: SatınAlmaSiparisi, SatınAlmaSiparisiKalemi, MalKabul, vb.)
  - `kaynak_belge_tipi` (CharField, kaynak belgesinin model adı)
  - `kaynak_belge_id` (PositiveBigIntegerField, kaynak belgesinin ID'si)
  - `kullanici` (ForeignKey to users.User, hareketi yapan kişi)
  - `maliyet` (DecimalField, hareket birimindeki maliyet, opsiyonel)
  - `aciklama` (TextField)
  - `created_at`, `updated_at`
- **Kısıtlamalar**: `miktar` pozitif olmalı (GIRIS için), CIKIS için negatif olabilir ama mutlak değer kullanılır.
- **Notlar**: 
  - GIRIS: Satın alma siparişi → Mal kabul → Stok girişi
  - CIKIS: Stok → Şantiye → Poz/Mahal tüketimi
  - TRANSFER: Depo A → Depo B
  - IADE: Satıcıya iade
  - FIRE: Haset, çöp, kullanım dışı
  - SAYIM: Periyodik stok sayımı
  - DUZELTME: Hatalı girişlerin düzeltmesi
- **Notlar**: StokHareketi, fiziksel DELETE kullanılmaz. Hatalı hareketler için ters hareket (reverse entry) oluşturulur.

## 7. MAL KABUL

Mal Kabul, satın alma siparişine bağlanır.

### 7.1 Desteklenmesi Gereken Durumlar
- Tam kabul: Sipariş miktarı ile kabul edilen miktar eşittir.
- Kısmi kabul: Kabul edilen miktar, sipariş miktarından azdır.
- Fazla kabul: Kabul edilen miktar, sipariş miktarından fazladır (hata durumu, tedarikçi ile uzlaşılarak çözülür).
- Eksik kabul: Kabul edilen miktar, sipariş miktarından azdır ve eksik miktar geri teslim edilmesi beklenir.
- Reddedilen miktar: Kabul edilmeyen miktar (kötü kalte,規格 dışı).
- İade: Kabul edilen malzemenin geri gönderilmesi.

### 7.2 Mal Kabul Süreci
- **Adım 1**: Satın alma siparişi oluşturulur ve tedarikçi tarafından onaylanır.
- **Adım 2**: Malzemeler teslim edilir ve depo tarafından kabul edilir.
- **Adım 3**: Mal kabul belgesi oluşturulur:
  - `satın_alma_siparişi` (ForeignKey to SatınAlmaSiparisi)
  - `mal_kabul_tarihi` (DateField)
  - `kabul_eden` (ForeignKey to users.User)
  - `notlar` (TextField)
  - `durum` (State Machine: TASLAK → ONAYLANDI → KISMI → TAMAMLANDI → IPTAL)
- **Adım 4**: Her sipariş kalemi için mal kabul kalemi oluşturulur:
  - `mal_kabul` (ForeignKey to MalKabul)
  - `satın_alma_siparişi_kalemi` (ForeignKey to SatınAlmaSiparisiKalemi)
  - `kabul_edilen_miktar` (DecimalField)
  - `reddedilen_miktar` (DecimalField, varsayılan 0)
  - `kabul_edilen_birim_fiyat` (DecimalField, sipariş fiyatındannapshot)
  - `toplam_kabul_tutarı` (DecimalField, hesaplanabilir)
  - `durum` (Choices: KABUL, RED, KISMI)
- **Adım 5**: Mal kabul gerçekleştiğinde:
  - Stok girişi (StokHareketi.GIRIS) oluşturulur:
    - `depo` → kabul edilen malzemenin saklanacağı depo
    - `malzeme` → kabul edilen malzeme
    - `miktar` → kabul_edilen_miktar
    - `birim` → malzemenin birimi
    - `hareket_tipi` → GIRIS
    - `kaynak_belge` → mal_kabul
    - `maliyet` → kabul_edilen_birim_fiyat (opsiyonel)
- **Adım 6**: Idempotency ve transaction mekanizması:
  - Mal kabul işlemi, `transaction.atomic` içinde yapılır.
  - Aynı sipariş kalemi için birden fazla mal kabul oluşturulmasını önlemek için, `satın_alma_siparişi_kalemi` ve `kabul_edilen_miktar` ile bir unique constraint veya kontrol mekanizması eklenir.
  - Alternatif olarak, mal kabul kalemi oluşturulurken, sipariş kaleminin zaten kabul edilmiş miktarı kontrol edilir ve sadece kalan miktar için kabul oluşturulur.

## 8. FATURA

YENİ FATURA MODELİ OLUŞTURMA yerine, mevcut Finance.Cari Fatura sistemi kullanılır ve genişletilir.

### 8.1 Satın Alma Siparişi → Mal Kabul → Fatura Bağlantısı
- **Adım 1**: Satın alma siparişi oluşturulur ve onaylanır.
- **Adım 2**: Mal kabul gerçekleşir ve stok girişi oluşturulur.
- **Adım 3**: Tedarikçi, mal kabul veya teslimatina göre fatura gönderir.
- **Adım 4**: Fatura, cari modülüyle oluşturulur:
  - `cari` → tedarikçi cari kartı
  - `fatura_turu` → "hizmet" veya "satis" (tedarikçi faturası için)
  - `senaryo` → "e_fatura", "e_arsiv" veya "kagit"
  - `tarih` → fatura tarihi
  - `vade_tarihi` → ödeme vadesi
  - `tutar` → fatura tutarı (tedarikçi tarafından belirtilen)
  - `kdv_dahil_mi` → KDV durumu
  - `iskonto_tutari` → fatura iskontosu
  - `odenen_tutar` → ödenen tutar (başlangıçta 0)
  - `aciklama` → fatura açıklaması, sipariş ve mal kabul referansları
- **Adım 5**: Fatura, cari harekete bağlanır:
  - `CariHareket` oluşturulur:
    - `cari` → tedarikçi cari kartı
    - `yon` → BORC (tedarikçi borcu)
    - `fatura` → oluşturulan fatura
    - `tutar` → fatura tutarı
    - `islem_tarihi` → fatura tarihi
- **Adım 6**: Fatura fiyatının sipariş fiyatından farklı olabileceği durumlar:
  - Fark, fatura açıklamasında veya ayrı bir fatura fark modeli ile takip edilebilir.
  - Alternatif olarak, fatura tutarı, sipariş tutarıyla karşılaştırılır ve fark, maliyet analizi için kullanılır.
  - Fark, `Fatura` modelinde yeni bir alan (örn. `fark_tutari`) ile veya ayrı bir `FaturaFark` modeli ile saklanabilir.
- **Adım 7**: Fatura, mevcut cari ve muhasebe sistemine bağlanır:
  - Cari hareket üzerinden, muhasebe fişine entegrasyon sağlanır (eğer fatura muhasebe fişiyle bağlanıyorsa).
  - Alternatif olarak, fatura doğrudan muhasebe fişiyle bağlanabilir (şu anda cari hareket üzerinden indirekt bağlanıyor).

### 8.2 Fatura Modelinde Güncellemeler (Opsiyonel)
- Yeni eklenebilecek alanlar:
  - `satın_alma_siparişi` (ForeignKey to SatınAlmaSiparisi, nullable)
  - `mal_kabul` (ForeignKey to MalKabul, nullable)
  - `fark_tutari` (DecimalField, sipariş tutarıyla fark)
  - `fark_aciklamasi` (TextField, farkın açıklaması)

## 9. CARİ

Mevcut Cari ve CariHareket yapısı kullanılır, yeni Cari modeli oluşturulmaz.

### 9.1 Tedarikçi Faturası Onaylandığında Bağlantı
- **Adım 1**: Tedarikçi faturası (Finance.Fatura) oluşturulur ve onaylanır.
- **Adım 2**: Fatura, cari harekete bağlanır:
  - `CariHareket` oluşturulur:
    - `cari` → tedarikçi cari kartı
    - `yon` → BORC
    - `fatura` → ilgili fatura
    - `tutar` → fatura tutarı
    - `islem_tarihi` → fatura tarihi
- **Adım 3**: Cari hareket, muhasebe fişiyle bağlanır (eğer fatura muhasebe fişiyle doğrudan bağlanmıyorsa):
  - Muhasebe fişi oluşturulur veya mevcut fişe bağlanır (örn. gider fişi).
  - `MuhasebeFisi` üzerinden, genel muhasebe akışı sağlanır.
- **Adım 4**: 320 / muhasebe akışı:
  - Tedarikçi borcu, cari hareket üzerinden muhasebe sistemine nakledilir.
  - Muhasebe fişi, ilgili gider hesabına (örn. ham mal gideri) ve borç hesabına (tedarikçi borcu) yönlendirir.
- **Notlar**: Bağlantı, mevcut cari ve muhasebe modüllerinin yapısına göre yapılır. Yeni model gerekmez.

## 10. GERÇEK MALİYET

### 10.1 Gerçek Maliyetin SOURCE OF TRUTH'ü
- **Kaynaklar**:
  - Satın Alma Siparişi: Planlanan maliyet (sipariş fiyatı).
  - Mal Kabul: Gerçek alınan miktar ve kabul edilen fiyat (stok girişi maliyeti).
  - Fatura: Tedarikçi tarafından ödenecek tutar (borç).
  - Stok: Stok hareketleri üzerinden ortalama maliyet veya hareket bazlı maliyet.
  - Tüketim: Stok tüketimi üzerinden gerçek maliyet.
- **Source of Truth Seçimi**: 
  - **Maliyetin kaynağı olarak Mal Kabul seçilir.** 
  - Nedenleri:
    - Mal kabul, gerçek alınan miktar ve kabul edilen fiyatı içerir.
    - Stok girişi, mal kabul sonrası oluşturulur ve stok maliyeti hesaplamasının temelini oluşturur.
    - Fatura, ödeme takibi için kullanılır ancak maliyet kaynağı olarak güvenilir değildir (fiyat farkları, indirimler, ekstra ücretler gibi faktörler etkileyebilir).
    - Tüketim, stoktan çıkan miktarı gösterir ancak maliyet bilgisi stokta zaten bulunmalıdır.
- **Notlar**: Gerçek maliyet, stok hareketleri üzerinden hesaplanır ve StokHareketi modelindeki `maliyet` alanı (veya ayrı bir maliyet modeli) kullanılır.

### 10.2 Gereksiz Kopyalamanın Önlenmesi
- Aynı maliyeti birden fazla tabloda kopyalamaktan kaçınılır.
- StokHareketi modelindeki `maliyet` alanı, her hareketin birimindeki maliyeti tutar.
- Stok değeri, StokHareketi kayıtları üzerinden hesaplanır (örn. hareket bazlı maliyet veya ağırlıklı ortalama).
- Poz/Mahal tüketimi, StokHareketi.CIKIS hareketleri üzerinden maliyet alınır.
- Gerçek maliyet raporu, StokHareketi ve ilgili modeller (Depo, Malzeme, Proje, Poz, Mahal) üzerinden oluşturulur.

### 10.3 Service/Read Model Yaklaşımı
- Gerçek maliyet, transaction'lardan türeten bir service veya read model ile hesaplanabilir.
- Örnek service metodu: `get_real_cost_for_malzeme_in_depo_on_date(depo, malzeme, tarih)`
- Bu approach, maliyetin tek bir kaynaktan tutulmasını ve tutarsızlıkların önlenmesini sağlar.

## 11. STOK MALİYETLEME YÖNTEMİ

FAZ 3D gerçek maliyet için stok maliyetleme yöntemi seçiminde analiz edilen seçenekler:

### 11.1 Seçenekler
- **Hareket Bazlı Maliyet**: Her StokHareketi kaydındaki `maliyet` alanı kullanılır. En basit ve şeffaf yöntemdir.
- **Ağırlıklı Ortalama (WA)**: Stok ortalama maliyeti, toplam maliyet / toplam miktar şeklinde hesaplanır.
- **Maliyet Katmanı (LIFO/FIFO)**: Stok katmanları oluşturulur ve her katman farklı maliyet taşır.
- **FIFO (First-In, First-Out)**: İlk giren ilk çıkar prensibiyle maliyet hesaplanır.

### 11.2 Seçilen Yaklaşım: Hareket Bazlı Maliyet
- **Nedenleri**:
  - İnşaat ERP'sinin mevcut hedefleri (şeffaflık, geri izlenebilirlik, basitlik) açısından en uygunudur.
  - Her stok hareketinin maliyeti açıkça bilinir ve raporlamada kullanılabilir.
  - Maliyet katmanı veya ağırlıklı ortalama gibi karmaşık yöntemler gerekmez.
  - İnşaat sektöründe, malzemeler genellikle projeye özel ve kısa süreli kullanılır; dolayısıyla katmanlama veya ağırlıklı ortalama gerekmeyebilir.
- **Etkileri**:
  - **Stok**: Stok değeri, StokHareketi kayıtları üzerinden `miktar * maliyet` toplamıyla hesaplanır.
  - **Tüketim**: Tüketilen malzemenin maliyeti, StokHareketi.CIKIS hareketlerinin `miktar * maliyet` toplamıdır.
  - **Poz/Mahal Maliyeti**: Poz veya mahal için tüketilen malzemenin maliyeti, ilgili tüketim hareketlerinden hesaplanır.
  - **Plan/Gerçek Rapor**: Planlanan maliyet (SatınAlmaSiparisi) ile gerçek maliyet (StokHareketi.CIKIS) karşılaştırılır.

## 12. POZ/MAHAL TÜKETİMİ

### 12.1 Malzeme Akışı
- **Akış**: Depo → Şantiye → Poz/Mahal
- **Örnek Senaryo**:
  - 100 ton malzeme satın alındı (SatınAlmaSiparisi).
  - 80 ton şantiyeye geldi (StokHareketi.GIRIS, 80 ton).
  - 65 ton tüketildi (StokHareketi.CIKIS, 65 ton, Poz/Mahal tüketimi).
  - 10 ton fire (StokHareketi.CIKIS, FIRE tipi).
  - 5 ton stokta kaldı (StokHareketi kayıtlarıyla hesaplanan bakiye).

### 12.2 Veri Modeli
- **Bağlantı**: 
  - Poz/Mahal tüketimi, StokHareketi.CIKIS hareketleri üzerinden takip edilir.
  - Her tüketim hareketi için:
    - `depo` → tüketimin kaynak olduğu depo
    - `malzeme` → tüketilen malzeme
    - `miktar` → tüketilen miktar
    - `birim` → malzemenin birimi
    - `hareket_tipi` → CIKIS (ve opsiyonel olarak `tüketim_tipi` veya `poz_mahal_id` gibi ek bilgi)
    - `kaynak_belge` → Poz veya Mahal ile ilgili bir iş emri veya görev (opsiyonel)
    - `kullanici` → tüketimi yapan kişi veya ekip
    - `maliyet` → tüketim anındaki stok birim maliyeti (StokHareketi.maliyet)
- **Notlar**: 
  - Satın alma miktarı ile gerçek tüketimi birbirine eşitlemek için, toplam satın alınan miktar (StokHareketi.GIRIS) ile toplam tüketilen miktar (StokHareketi.CIKIS, poz/mahal için) ve stoctaki miktar karşılaştırılır.
  - Fark, fire, sayım farkı veya hata olarak analiz edilir.

## 13. SNAPSHOT

FAZ 2 snapshot'larını bozma. Ayrı seviyeleri tanımlanır:

### 13.1 Tanımlanan Snapshot Seviyeleri
- **Teklif Fiyat Snapshot**: TedarikciTeklifi.birim_fiyat ve toplam_tutar.
- **Sipariş Fiyat Snapshot**: SatınAlmaSiparisiKalemi.birim_fiyat ve toplam_tutar.
- **Mal Kabul Fiyat Snapshot**: MalKabulKalemi.kabul_edilen_birim_fiyat ve toplam_kabul_tutarı.
- **Fatura Fiyatı**: Finance.Fatura.tutar (tedarikçi tarafından belirtilen fatura tutarı).
- **Gerçek Tüketim Maliyet Snapshot**: StokHareketi.maliyet (her hareket birimindeki maliyet).
- **Plan Maliyeti**: SatınAlmaSiparisiKalemi.birim_fiyat * miktar (teklif fiyatı üzerinden planlanan maliyet).
- **Gerçekleşen Maliyet**: StokHareketi.maliyet * miktar (gerçek tüketim maliyeti).

### 13.2 Notlar
- Plan maliyeti ile gerçekleşen maliyet birbirine karıştırılmayacak.
- Her snapshot seviyesi, ilgili modeldeki fiyat ve tutar alanlarıyla korunur.
- Snapshot'lar, fiziksel DELETE kullanılmaz; geçmişteki değerler değişmez ve referans olarak korunur.

## 14. NUMARALANDIRMA

Yeni FAZ 3 belgeleri için numara sistemi tasarlanmıştır.

### 14.1 Numara Formatları
- **Satın Alma Talebi**: SAT-2026-000001
- **Satın Alma Siparişi**: SIP-2026-000001
- **Mal Kabul**: MK-2026-000001
- **Stok Hareketi**: SH-2026-000001 (opsiyonel, hareket tipi ile birlikte)
- **Fatura**: FINV-2026-000001 (mevcut finance.Fatura.No ile uyumlu)

### 14.2 Numara Üretiminde Değerlendirilen Konular
- **Tenant**: Numara üretimi tenant bazlıdır (her tenant için kendi numara dizisi).
- **Yıl**: Numarada yıl bilgisi bulunur (örn. 2026).
- **Concurrency**: `select_for_update` ve `transaction.atomic` kullanılarak aynı anda numara üretiminde çakışmalar önlenir.
- **Transaction.atomic**: Numara üretimi ve belge oluşturma aynı transaction içinde yapılır.
- **Notlar**: Numara üretimi, bir service veya model save metodu içinde `select_for_update` kullanılarak yapılır.

## 15. STATE MACHINE

Her belge için ayrı state machine tasarlanmıştır.

### 15.1 Satın Alma Talebi
- TASLAK → ONAYA_GONDERILDI → ONAYLANDI → REDDEDILDI → SIPARISE_DONUSTU → IPTAL

### 15.2 Sipariş
- TASLAK → ONAY_BEKLIYOR → ONAYLANDI → KISMI_TESLIM → TAMAMLANDI → IPTAL

### 15.3 Mal Kabul
- TASLAK → ONAYLANDI → KISMI → TAMAMLANDI → IPTAL

### 15.4 Fatura
- DRAFT → ACTIVE → PAID → CANCELLED (mevcut Finance.Fatura.DurumChoices)

### 15.5 Stok Hareketi
- OLUŞTURULDU → UYGULANDI → İPTAL (opsiyonel durum alanı eklenebilir)

### 15.6 Notlar
- Mevcut projedeki state pattern'i incelen ve uygun şekilde uyarlanmıştır.
- Her state machine, modeldeki `durum` alanıyla yönetilir.
- Geçişler, servis katmanında veya model metodlarıyla kontrol edilir.

## 16. NO DELETE

Fiziksel DELETE kullanmaz. Belgeler için alternatif mekanizmalar:

### 16.1 Mekanizmalar
- **İptal**: Belge durumu iptal olarak değiştirilir (örn. SatınAlmaSiparisi.durum = IPTAL).
- **Ters Kayıt**: Stok hareketi gibi işlemler için ters hareket oluşturulur (örn. GIRIS için CIKIS hareketi).
- **Revizyon**: Belgeyen versiyon oluşturulur (örn. YaklasikMaliyet.versiyon).
- **Pasif**: `is_active` alanı false yapılır (örn. TedarikciTeklifi.is_active = False).

### 16.2 Notlar
- Fiziksel DELETE, veri bütünlüğü ve geçmiş takibi açısından risklidir ve kullanılmaz.
- Tüm değişiklikler, audit trail ile takip edilir.

## 17. FRONTEND GERÇEK TEKNOLOJİSİNİ DOĞRULA

Mevcut frontend dosya yapısı kontrol edilmiştir.

### 17.1 Frontend Yapısı
- **Konum**: `frontend/` dizini
- **Teknolojiler**:
  - `package.json`: React, TypeScript, Vite kullanılıyor.
  - `tsconfig.json`: TypeScript yapılandırması.
  - `postcss.config.js` ve `tailwind.config.js`: Tailwind CSS kullanılıyor.
  - `index.html`: Ana HTML dosyası.
- **Sonuç**: Frontend, React/Tailwind tabanlı bir kullanıcı arayüzüne sahiptir.

### 17.2 FAZ 3 İçin Frontend Tasarımı
- FAZ 3 özellikleri, mevcut React mimarisiyle uyumlu olarak tasarlanacaktır.
- Yeni sayfa ve komponentler:
  - Satın Alma Talebi listesi ve oluşturma formu
  - Satın Alma Siparişi listesi ve oluşturma formu
  - Mal Kabul listesi ve oluşturma formu
  - Stok Hareketi listesi ve oluşturma formu
  - Gerçek Maliyet raporu sayfası
- State yönetimi: React Context veya Redux (mevcut projeye uygun) kullanılacaktır.
- API entegrasyonu: Django REST Framework üzerinden mevcut API endpoints'leri genişletilecektir.

## 18. FAZ 3 SINIRLARI

FAZ 3'nın kapsamı aşağıdaki şekilde kesinleştirilmiştir:

| Faz   | Adı                     | Yeni Model                     | Mevcut Model Bağlantısı                     | Frontend                     | API                     | Migration                     | Test                     | Bağımlılık                     |
|-------|-------------------------|--------------------------------|---------------------------------------------|------------------------------|-------------------------|-------------------------------|--------------------------|--------------------------------|
| FAZ 3A| Satın Alma Çekirdeği    | SatınAlmaTalebi, SatınAlmaTalebiKalemi, SatınAlmaSiparisi, SatınAlmaSiparisiKalemi | Proje, Malzeme, Poz, Tedarikci, TedarikciTeklifi | Satın alma talebi ve sipariş sayfaları | `/api/v1/purchase-requests/`, `/api/v1/purchase-orders/` | Yeni modeller için migration | Yeni modeller için test | FAZ 2'nin tamamı (özellikle construction modelleri) |
| FAZ 3B| Mal Kabul + Stok        | Depo, DepoSantiyeIlkisi, StokHareketi, MalKabul, MalKabulKalemi | Malzeme, SatınAlmaSiparisi | Stok yönetimi ve mal kabul sayfaları | `/api/v1/stock-movements/`, `/api/v1/receipts/` | Yeni modeller için migration | Yeni modeller için test | FAZ 3A (satın alma siparişi) |
| FAZ 3C| Poz/Mahal Gerçek Tüketim| (Yeni model gerekmez, StokHareketi.CIKIS kullanılır) | StokHareketi, Depo, Malzeme, Poz, Mahal | Poz/Mahal tüketim takibi sayfaları | `/api/v1/consumption/` (StokHareketi filtresi) | Mevcut modelde değişiklik yok | Stok tüketimi testleri | FAZ 3B (stok girişi) |
| FAZ 3D| Gerçekleşen Maliyet     | (Yeni model gerekmez, StokHareketi.maliyet kullanılır) | StokHareketi, SatınAlmaSiparisi, Finance.Fatura, CariHareket | Gerçek maliyet raporu sayfası | `/api/v1/real-cost/` (StokHareketi agregasyonu) | Mevcut modelde değişiklik yok | Maliyet raporu testleri | FAZ 3A, FAZ 3B, FAZ 3C |

## 19. SON NİHAİ MİMARİ

### 19.1 Ana Akış Diyagramı
```
Mevcut Tedarikci
    ↓
Mevcut TedarikciTeklifi
    ↓
Satın Alma Talebi
    ↓
Satın Alma Siparişi
    ↓
Mal Kabul
    ↓
Stok Hareketi
    ↓
Poz/Mahal Tüketimi
    ↓
Gerçek Maliyet
```

### 19.2 Paralel Finans Akışı
```
Satın Alma Siparişi
    ↓
Fatura
    ↓
Cari Hareket
    ↓
Muhasebe / Finance
```

### 19.3 Plan vs Gerçek
```
Plan maliyeti
    ↓
PozPlan / YaklaşıkMaliyet

Gerçek maliyet
    ↓
Stok + Tüketim + Fatura

Plan vs Gerçek
    ↓
Raporlama
```

## 20. ÇIKTI

Bu rapor, FAZ 3 implementation öncesi tek referans dokümanıdır.

### 20.1 FAZ 3 Implementation İçin Hazırlık Durumu
**FAZ 3 implementation için hazır değil.**

### 20.2 Eksik Kararlar
1. **Stok Maliyetleme Yöntemi**: Hareket bazlı maliyet seçildi ancak ekip tarafından onaylanması gerekiyor.
2. **Fatura Farkı Modeli**: Fatura tutarı ile sipariş tutarı arasındaki farkın nasıl takip edileceği (model mi, service mi) karar verilmemiş.
3. **Mal Kabul Durum Makinesi**: Mal kabul durum makinesinin detaylı tanımları (KISMI durumunun ne anlama gelmesi) tartışılmalı.
4. **Numaralandırma Servisi**: Numara üretimi için merkezi bir servis mi yoksa model save metodu içinde mi yapılacak karar verilmemiş.
5. **Frontend State Yönetimi**: React Context mi yoksa Redux mi kullanılacak karar verilmemiş (proje mevcut state yönetimine göre).
6. **API Sürümleme**: FAZ 3 API'leri mevcut API sürümüne eklenecek mi yoksa yeni sürüm mü açılacak karar verilmemiş.
7. **Test Stratejisi**: Entegrasyon testleri ve birim testleri için kapsam ve araçlar (pytest, pytest-django, playwright) finalize edilmemiş.
8. **Performans Önemli Sorgu**: Stok maliyet raporu gibi karmaşık agregasyon sorguları için performans optimizasyonu planlanmamış.
9. **Güvenlik ve Yetkilendirme**: Yeni modeller için izin roller ve yetkilendirme politikaları tanımlanmamış.
10. **Dağıtım Planı**: FAZ 3 özelliklerinin üretime dağıtımı için blue-green veya canary dağıtım planı hazırlanmamış.

Bu kararlar alınmadan ve ilgili tasarımlar tamamlanmadan FAZ 3 implementation başlanmamalıdır.