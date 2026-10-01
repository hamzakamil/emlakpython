export const menuHelp = {

  // ==================== GENEL ====================
  panel: {
    amac: "İşletmenin finansal ve operasyonel durumunu tek ekranda özetler.",
    yapilabilir: [
      "Günlük/aylık ciro, gider ve kâr KPI'larını görüntüleme",
      "Cari bakiye özetlerini ve vadesi geçen alacakları izleme",
      "Son işlemleri ve bekleyen görevleri hızlıca görme",
      "Sık kullanılan sayfalara kısayol ile erişim"
    ],
    ipucu: "Gün başında ilk açılacak sayfa burasıdır; kırmızı uyarıları öncelikle kontrol edin."
  },

  // ==================== GAYRİMENKUL ====================
  gayrimenkuller: {
    amac: "Sahip olunan veya yönetilen tüm mülklerin (bina, daire, arsa) kartlarını tek yerde tutar.",
    yapilabilir: [
      "Yeni mülk kartı ekleme, düzenleme, pasife alma",
      "Mülkü ada/parsel bilgisiyle ilişkilendirme",
      "Mülk durumu (satılık, kiralık, boş, dolu) takibi",
      "Mülk bazlı not ve belge ekleme"
    ],
    ipucu: "Mülk kartını oluşturmadan önce ada/parsel kaydının var olduğundan emin olun."
  },

  adaParsel: {
    amac: "Tapu ve imar bilgilerini (ada, parsel, KAKS, emsal, TAKS) yönetir.",
    yapilabilir: [
      "Yeni ada ve parsel kaydı oluşturma",
      "İmar durumu (konut, ticari, sanayi) ve emsal bilgisi girme",
      "Parsel üzerindeki gayrimenkulleri ilişkilendirme",
      "Kat karşılığı senaryolarını parsel bazında tanımlama"
    ],
    ipucu: "İmar durumu değişikliklerini güncel tutun; kat karşılığı hesapları bu bilgiye dayanır."
  },

  malikMutabakati: {
    amac: "Kat karşılığı veya satış görüşmelerinde maliklerle yapılan anlaşmaları takip eder.",
    yapilabilir: [
      "Malik bazlı mutabakat kaydı oluşturma (hisse oranı, daire sayısı)",
      "Görüşme durumu (imzalandı, beklemede, reddedildi) takibi",
      "Mutabakat belgelerini ve eklerini yükleme",
      "Parsel/gayrimenkul ile ilişkilendirme"
    ],
    ipucu: "Mutabakat oranlarını %100'e tamamlamadan inşaata başlamayın; eksik malik sonradan sorun çıkarır."
  },

  // ==================== İNŞAAT ====================
  pozGruplari: {
    amac: "Poz kütüphanesindeki iş kalemlerini düzenli ve tekrar kullanılabilir gruplar altında toplar.",
    yapilabilir: [
      "Ana ve alt poz grubu oluşturma",
      "Grup kodu ve adını düzenleme",
      "Grupları aktif veya pasif duruma alma"
    ],
    ipucu: "Önce poz grubunu oluşturun, ardından Pozlar ekranından yeni poz eklerken bu grubu seçin."
  },
  pozlar: {
    amac: "İnşaat iş kalemlerinin (poz) birim fiyat ve tanım kütüphanesini yönetir.",
    yapilabilir: [
      "Yeni poz tanımı ekleme, düzenleme",
      "Poz grubu bazlı filtreleme (kazı, beton, duvar vb.)",
      "Birim fiyat ve ölçü birimi tanımlama",
      "ÇŞB pozlarıyla eşleştirme"
    ],
    ipucu: "Pozları standart isimlendirmeyle girin; hakediş ve analizler bunlara bağlıdır. Excel ile veri dışa/İçe aktarma mümkün."
  },

  yapiSinifi: {
    amac: "4A, 4B, 5A gibi yapı sınıflarına göre m² birim maliyetlerini tanımlar.",
    yapilabilir: [
      "Yapı sınıfı bazlı birim maliyet güncelleme",
      "Yıllık tebliğ değişikliklerini işleme",
      "Yaklaşık maliyet hesabında referans olarak kullanma"
    ],
    ipucu: "Her yıl Ocak ayında Resmi Gazete'de yayımlanan yeni birim maliyetleri buraya işleyin. Excel ile veri dışa/İçe aktarma mümkün."
  },

projeler: {
    amac: "İnşaat/geliştirme projelerini oluşturur ve tüm süreçlerin ana kapsayıcısıdır.",
    yapilabilir: [
      "Yeni proje kartı açma (arsa, konut, ticari)",
      "Projeye mahal, poz, sözleşme bağlama",
      "Proje durum takibi (planlama, devam, tamamlandı)",
      "Proje bazlı raporlara erişim"
    ],
    ipucu: "Hakediş, şantiye günlüğü ve nakit akışı gibi tüm alt modüller bir projeye bağlıdır; önce projeyi açın. Excel ile veri dışa/İçe aktarma mümkün."
  },

  santiyeGunlukleri: {
    amac: "Proje bazlı günlük şantiye saha kayıtlarını (yapılan işler, işçi sayısı, hava durumu, malzeme giriş/çıkış, ekipmanlar, sorunlar) tutar.",
    yapilabilir: [
      "Yeni günlük şantiye kaydı oluşturma (tarih, proje seçimi)",
      "Hava durumu, sıcaklık, işçi sayısı ve çalışma saatleri girme",
      "Yapılan işler, malzeme giriş/çıkış, ekipmanlar ve sorunları not etme",
      "Günlük kayıtları proje ve tarih bazında listeleme, arama ve filtreleme",
      "Çevrimdışı taslak kaydetme ve internet geldiğinde gönderme"
    ],
    ipucu: "Günlük kayıtları aynı gün içinde girin; haftalık/aylık raporlamalarda referans olur. Benzersizlik kuralı: aynı projede aynı tarihte birden fazla kayıt oluşturulamaz."
  },

  pozPlanlari: {
    amac: "Bir projede hangi pozdan ne kadar, ne zaman yapılacağını planlar.",
    yapilabilir: [
      "Planlanan miktar ve tarih girme",
      "Gerçekleşen miktarla karşılaştırma",
      "İş kalemi bazlı ilerleme takibi",
      "Gantt şemasına veri sağlama"
    ],
    ipucu: "Planı haftalık güncelleyin; sapmalar erken görülürse maliyet artışı önlenir. Excel ile veri dışa/İçe aktarma mümkün."
  },

  mahalListesi: {
    amac: "Projedeki mekânları (blok, kat, daire, oda) tanımlar.",
    yapilabilir: [
      "Blok/kat/daire bazlı mahal tanımlama",
      "Mahal elemanlarını (duvar, zemin, tavan) tanımlama",
      "Her mahale özel poz ve metraj bağlama"
    ],
    ipucu: "Mahal isimlerini standartlaştırın (örn. 'A-Blok-3.Kat-Daire5-Salon') ki sonradan arama kolay olsun."
  },

  analizKitabi: {
    amac: "Pozların malzeme, işçilik ve makine bileşenlerini analiz eder.",
    yapilabilir: [
      "Poz bazlı birim fiyat analizi görüntüleme",
      "Malzeme/işçilik/makine dağılımını inceleme",
      "Nakliye analizi ekleme",
      "Analiz raporu alma"
    ],
    ipucu: "Yaklaşık maliyet ve hakediş hesaplarının doğruluğu bu analizlerin güncelliğine bağlıdır."
  },

  yaklasikMaliyet: {
    amac: "İhale veya fizibilite öncesi projenin tahmini maliyetini hesaplar.",
    yapilabilir: [
      "Poz miktarlarını girerek maliyet hesaplama",
      "Genel gider ve yüklenici kârı ekleme",
      "Farklı senaryoları karşılaştırma",
      "Rapor olarak dışa aktarma"
    ],
    ipucu: "Yapı sınıfı birim maliyetini referans alın; poz bazlı hesapla karşılaştırın."
  },

  ganttSemasi: {
    amac: "Projenin zaman planını görsel olarak sunar.",
    yapilabilir: [
      "İş kalemlerini zaman çizelgesinde görme",
      "Bağımlılıkları (öncül/ardıl) takip etme",
      "Gecikmeleri görsel olarak tespit etme",
      "Kritik yolu belirleme"
    ],
    ipucu: "Haftalık toplantı öncesi Gantt'ı inceleyin; kırmızı çubuklar gecikmeyi gösterir."
  },

  hakedisler: {
    amac: "Yüklenici ve taşeron hakedişlerini (ödeme taleplerini) yönetir.",
    yapilabilir: [
      "Dönemsel hakediş oluşturma (imalat, metraj, fiyat)",
      "Kesintileri (teminat, vergi, avans) otomatik hesaplama",
      "Hakediş onay akışını takip etme",
      "Ödeme ile ilişkilendirme"
    ],
    ipucu: "Hakedişi onaylamadan önce metrajları şantiye şefine doğrulatın."
  },

  taseronHakedisleri: {
    amac: "Alt yüklenicilere ait hakedişleri ayrı olarak takip eder.",
    yapilabilir: [
      "Taşeron bazlı hakediş oluşturma",
      "Sözleşme kapsamına göre kesinti uygulama",
      "Taşeron bazlı ödeme geçmişini görme",
      "Genel hakedişten ayırma"
    ],
    ipucu: "Taşeron hakedişini ana hakedişe bağlamayı ihmal etmeyin; çift ödeme riski doğar."
  },

  taseronSozlesmeleri: {
    amac: "Taşeronlarla yapılan sözleşmeleri arşivler ve takip eder.",
    yapilabilir: [
      "Yeni sözleşme oluşturma",
      "Sözleşme bedeli, süresi ve kapsamını girme",
      "Ek protokolleri (iş artışı) ekleme",
      "Sözleşme bitiş tarihini hatırlatma"
    ],
    ipucu: "Sözleşmeyi imzalamadan önce Sözleşme Şablonları menüsünden taslak oluşturun."
  },

  santiyeGunlugu: {
    amac: "Şantiyedeki günlük faaliyetleri (personel, hava, iş) kayıt altına alır.",
    yapilabilir: [
      "Günlük personel ve ekipman sayısı girme",
      "Yapılan işleri ve hava durumunu kaydetme",
      "Fotoğraflı kanıt ekleme",
      "Haftalık/aylık özet rapor alma"
    ],
    ipucu: "Günlüğü her akşam doldurun; sonradan hatırlamak zordur. Hukuki delil niteliği taşır."
  },
malzemeTedarikPlani: {
    amac: "Malzemelerin hangi tedarikçiden, ne zaman alınacağını planlar.",
    yapilabilir: [
      "Malzeme-tedarikçi ilişkisi tanımlama",
      "Sipariş miktarı ve teslim tarihi girme",
      "Alternatif tedarikçi belirleme",
      "Tedarik gecikmelerini izleme"
    ],
    ipucu: "Kritik malzemeler için en az 2 tedarikçi tanımlayın; tedarik riski azalır."
  },

  tedarikciTeklifleri: {
    amac: "Tedarikçilerden gelen fiyat tekliflerini karşılaştırır.",
    yapilabilir: [
      "Teklifleri sisteme girme",
      "Fiyat/teslim/vade bazında karşılaştırma",
      "Kazanan teklifi seçme ve siparişe dönüştürme",
      "Teklif geçmişini arşivleme"
    ],
    ipucu: "En düşük fiyat her zaman en iyi değildir; teslim süresi ve vadeyi de puanlayın."
  },

  satinAlmaTalepleri: {
    amac: "Satın alma taleplerini ve onay akışını yönetir.",
    yapilabilir: [
      "Talep oluşturma ve kalem ekleme",
      "Teklif seçimi ve uygunluk doğrulaması",
      "Onaya gönderme, onaylama ve reddetme",
      "Onaylı talebi siparişe dönüştürme"
    ],
    ipucu: "Siparişe dönüşen talep tekrar dönüştürülemez; fiyatlar dönüşüm anında sabitlenir."
  },

  satinAlmaSiparisleri: {
    amac: "Tedarikçilere verilen satın alma siparişlerini izler.",
    yapilabilir: [
      "Sipariş oluşturma ve kalem takibi",
      "Onay akışı (taslak, onay bekliyor, onaylandı)",
      "Talep bağlantılı sipariş görüntüleme",
      "Sipariş iptali"
    ],
    ipucu: "Bu fazda sipariş muhasebe fişi üretmez; entegrasyon sonraki fazdadır."
  },

  malKabuller: {
    amac: "Tedarikçiden gelen malzemelerin kabul ve red kayıtlarını yönetir.",
    yapilabilir: [
      "Onaylı siparişten mal kabul belgesi oluşturma",
      "Kısmi kabul ve red miktarı girme",
      "Onayda stok giriş hareketi üretme",
      "Kabul iptalinde ters hareket açma"
    ],
    ipucu: "Kabul miktarı kalan sipariş miktarını aşamaz; onay sonrası fiyatlar sabittir."
  },

  stokHareketleri: {
    amac: "Depo eksenli stok giriş/çıkış hareketlerini izler.",
    yapilabilir: [
      "Depo ve malzeme bazında hareket listeleme",
      "Mal kabul kaynaklı girişleri görme",
      "İptal kaynaklı ters hareketleri görme"
    ],
    ipucu: "Hareketler yalnızca mal kabul onayıyla üretilir; elle kayıt kapalıdır."
  },

  stokDurumu: {
    amac: "Depo ve malzeme bazında güncel stok bakiyelerini gösterir.",
    yapilabilir: [
      "Bakiye sorgulama",
      "Depolar arası transfer",
      "Projeye tüketim çıkışı",
      "Tedarikçiye iade"
    ],
    ipucu: "Bakiye = giriş - çıkış; negatif stoka izin verilmez."
  },

  depolar: {
    amac: "Stok tutulacak depo kartlarını yönetir.",
    yapilabilir: [
      "Depo tanımlama ve düzenleme"
    ],
    ipucu: "Depo kodları firma içinde benzersiz olmalıdır."
  },

  kaliteIsg: {
    amac: "Kalite kontrol ve iş güvenliği kayıtlarını yönetir.",
    yapilabilir: [
      "Malzeme ve imalat kalite kontrol formu doldurma",
      "Uygunsuzluk kaydı ve düzeltici faaliyet takibi",
      "İSG eğitim ve denetim kayıtları",
      "Kaza/ramak kala olay kaydı"
    ],
    ipucu: "Uygunsuzlukları kapatmadan yeni imalata geçmeyin; aksi halde kabul sorunu çıkar."
  },

  sozlesmeSablonlari: {
    amac: "Tekrar kullanılabilir sözleşme taslaklarını saklar.",
    yapilabilir: [
      "Yeni şablon oluşturma (taşeron, tedarik, kira vb.)",
      "Değişken alanları (firma, bedel, tarih) tanımlama",
      "Şablondan hızlı sözleşme üretme",
      "Sürüm takibi yapma"
    ],
    ipucu: "Şablonları yılda bir güncelleyin; mevzuat değişiklikleri yansımalıdır."
  },

  nakitAkisi: {
    amac: "Proje bazlı nakit giriş-çıkış projeksiyonunu gösterir.",
    yapilabilir: [
      "Aylık nakit akış tablosu görme",
      "Tahsilat ve ödeme planlarını izleme",
      "Nakit açığı/fazlası dönemlerini tespit etme",
      "Farklı senaryoları karşılaştırma"
    ],
    ipucu: "Nakit açığı olan ayları önceden görüp kredi veya tahsilat planı yapın."
  },

  karZararSapma: {
    amac: "Bütçelenen ile gerçekleşen maliyet/geliri karşılaştırır.",
    yapilabilir: [
      "Bütçe-gerçekleşen karşılaştırması",
      "Sapma oranlarını kalem bazında görme",
      "Kâr marjı analizi",
      "Proje bazlı kâr/zarar raporu alma"
    ],
    ipucu: "Sapma %10'u geçtiyse nedenini mutlaka araştırın; küçük sapmalar büyür."
  },

  portfoyKarsilastirma: {
    amac: "Birden fazla projeyi KPI bazında karşılaştırır.",
    yapilabilir: [
      "Projeleri kârlılık, nakit akışı, ilerleme bazında kıyaslama",
      "En iyi/en kötü performanslı projeleri belirleme",
      "Yatırım kararı için rapor alma",
      "Grafik ve tablo görünümü"
    ],
    ipucu: "Karşılaştırmayı aynı büyüklükteki projeler arasında yapın; aksi halde yanıltıcı olur."
  },

  teknikSartnameTaslagi: {
    amac: "Projeye özgü teknik şartname metni üretir.",
    yapilabilir: [
      "Proje bilgilerine göre otomatik şartname taslağı oluşturma",
      "Malzeme ve imalat standartlarını seçme",
      "Taslağı düzenleme ve PDF olarak dışa aktarma",
      "Şablon olarak kaydetme"
    ],
    ipucu: "Taslağı ihale öncesi mutlaka hukuk ve teknik ekibe onaylatın."
  },

  riskliYapiSureci: {
    amac: "Riskli yapı tespiti, başvuru ve yıkım süreçlerini takip eder.",
    yapilabilir: [
      "Riskli yapı başvurusu kaydı oluşturma",
      "Kurul kararı ve itiraz süreçlerini izleme",
      "Yıkım tarihi ve ruhsat takibi",
      "Malik bilgileriyle ilişkilendirme"
    ],
    ipucu: "6306 sayılı Kanun süreçlerini takip edin; süre aşımı hak kaybına yol açar."
  },

  ekbSurecTakibi: {
    amac: "Enerji Kimlik Belgesi (EKB) süreçlerini yönetir.",
    yapilabilir: [
      "EKB başvuru ve onay sürecini takip etme",
      "Enerji sınıfı (A-G) kaydı",
      "Belge geçerlilik tarihi hatırlatması",
      "Proje/gayrimenkul ile ilişkilendirme"
    ],
    ipucu: "EKB olmadan yapı kullanma izni alınamaz; süreci erken başlatın."
  },

  kiraYardimiTahliye: {
    amac: "Kentsel dönüşümde kira desteği ve tahliye süreçlerini takip eder.",
    yapilabilir: [
      "Kira yardımı başvurularını kaydetme",
      "Aylık ödeme planı ve tahsilat takibi",
      "Tahliye tarihi ve taahhütname kaydı",
      "Malik/kiracı bilgileriyle ilişkilendirme"
    ],
    ipucu: "Ödemeleri belgeleyin; denetimde en çok sorgulanan kalemdir."
  },

  cariKartlar: {
    amac: "Kiracı, malik, tedarikçi, taşeron gibi tüm tarafları tanımlar.",
    yapilabilir: [
      "Yeni cari kart açma (bireysel/kurumsal)",
      "VKN/TCKN, adres, iletişim bilgisi girme",
      "Cari tipi ve tür belirleme",
      "Cari hareketleri görüntüleme"
    ],
    ipucu: "Cari kartı açmadan fatura/işlem yapmayın; aksi halde muhasebe karışır."
  },

  cariHareketler: {
    amac: "Carilerin borç/alacak hareketlerini listeler.",
    yapilabilir: [
      "Cari bazlı hareket dökümü alma",
      "Borç/alacak bakiyesi görme",
      "Vadesi geçen işlemleri filtreleme",
      "Ekstre yazdırma"
    ],
    ipucu: "Ay sonu kapanışından önce tüm carilerin mutabakatını yapın."
  },

  finansalHesaplar: {
    amac: "Kasa ve banka hesaplarını tanımlar ve takip eder.",
    yapilabilir: [
      "Yeni kasa/banka hesabı açma",
      "IBAN ve şube bilgisi girme",
      "Hesap bakiyesi görme",
      "Hesap bazlı hareket dökümü alma"
    ],
    ipucu: "Her banka hesabı için ayrı kayıt açın; toplu kayıt mutabakatı zorlaştırır."
  },

  finansalIslemler: {
    amac: "Gelir, gider, transfer ve tahsilat işlemlerini kaydeder.",
    yapilabilir: [
      "Tahsilat/ödeme kaydı oluşturma",
      "Hesaplar arası transfer yapma",
      "İşlemi cari ve fatura ile ilişkilendirme",
      "Günlük kasa raporu alma"
    ],
    ipucu: "İşlemi kaydettikten sonra mutlaka makbuz/fiş yazdırın."
  },
cekSenetler: {
    amac: "Alınan ve verilen çek/senetlerin vade takibini yapar.",
    yapilabilir: [
      "Çek/senet kaydı oluşturma",
      "Vade tarihi hatırlatması",
      "Tahsil/ödeme durumu güncelleme",
      "Portföy raporu alma"
    ],
    ipucu: "Vadesi yaklaşan çekleri haftalık kontrol edin; karşılıksız riskini azaltır."
  },

  hesapPlani: {
    amac: "Muhasebe hesap planını (TDHP) yönetir.",
    yapilabilir: [
      "Hesap ekleme/düzenleme",
      "Hesap tipi ve normal bakiye tanımlama",
      "Alt hesap açma",
      "Hesap planını dışa aktarma"
    ],
    ipucu: "Hesap planını yılda bir gözden geçirin; gereksiz hesapları kapatın."
  },

  fislerMizan: {
    amac: "Muhasebe fişlerini (çift kayıt) oluşturur ve yönetir.",
    yapilabilir: [
      "Yeni fiş oluşturma (borç/alacak satırları)",
      "Fiş onaylama ve kilitleme",
      "Fiş bazlı belge ilişkilendirme",
      "Dönem sonu kapanışı yapma"
    ],
    ipucu: "Fişi onaylamadan önce borç=alacak kontrolünü yapın; sistem otomatik uyarır."
  },

  mizanRaporu: {
    amac: "Dönem sonu mizan (trial balance) raporunu üretir.",
    yapilabilir: [
      "Aylık/yöllık mizan görüntüleme",
      "Hesap bazlı borç/alacak toplamı",
      "Kapanmayan hesapları tespit etme",
      "PDF/Excel olarak dışa aktarma"
    ],
    ipucu: "Mizanı kapatmadan önce ters bakiye veren hesapları düzeltin."
  },

  faturalar: {
    amac: "Satış ve alış faturalarını oluşturur ve takip eder.",
    yapilabilir: [
      "Yeni fatura oluşturma (satış/alış)",
      "e-Fatura/e-Arşiv olarak gönderme",
      "Fatura durumu (taslak, onaylı, iptal) takibi",
      "Fatura bazlı ödeme eşleştirme"
    ],
    ipucu: "Faturayı cari kart olmadan kesmeyin; tahsilat takibi zorlaşır."
  },

  raporlar: {
    amac: "Finansal ve operasyonel raporları görüntüler.",
    yapilabilir: [
      "Hazır rapor şablonlarını çalıştırma",
      "Tarih/hesap/cari filtreleri uygulama",
      "Raporu PDF/Excel olarak dışa aktarma",
      "Özel rapor tanımlama"
    ],
    ipucu: "Raporları dönem sonunda arşivleyin; karşılaştırma için gerekir."
  },

  ayarlar: {
    amac: "Sistem ve firma bazlı ayarları yönetir.",
    yapilabilir: [
      "Firma bilgileri ve logo güncelleme",
      "Varsayılan para birimi ve KDV oranı tanımlama",
      "Belge numaralandırma serileri ayarlama",
      "Kullanıcı yetkilerini düzenleme"
    ],
    ipucu: "Ayarları değiştirmeden önce mevcut yapılandırmayı yedekleyin."
  },

  firmalar: {
    amac: "Çok-kiracılı (multi-tenant) yapıda firmaları yönetir.",
    yapilabilir: [
      "Yeni firma (tenant) oluşturma",
      "Firma bazlı yetkilendirme tanımlama",
      "Firma durumunu (aktif/pasif) yönetme",
      "Firma bazlı veri izolasyonu sağlama"
    ],
    ipucu: "Firma silmek yerine pasife alın; veri kaybı önlenir."
  },

  kullanicilar: {
    amac: "Kullanıcı hesaplarını ve rollerini yönetir.",
    yapilabilir: [
      "Yeni kullanıcı ekleme",
      "Rol atama (yönetici, muhasebe, şantiye vb.)",
      "Şifre sıfırlama ve hesap kilitleme",
      "Kullanıcı aktivite loglarını görme"
    ],
    ipucu: "Her kullanıcıya ayrı hesap açın; ortak hesap denetimde sorun olur."
  },

  veritabaniYonetimi: {
    amac: "Veritabanını görüntüler, yedekler ve Excel içeri/dışa işlemleri yapar.",
    yapilabilir: [
      "Tablo bazlı veri görüntüleme",
      "Excel şablonu indirme ve veri yükleme",
      "Veritabanı yedekleme ve geri yükleme",
      "Belirli kayıtları düzenleme"
    ],
    ipucu: "Yedek almadan toplu içeri aktarma yapmayın; hatalı veri tüm sistemi etkiler."
  },

  // ==================== FAZ 7 EK EKRANLAR ====================
  malzemeler: {
    amac: "İnşaat malzemelerinin kod, birim ve TS referanslı kartlarını tutar.",
    yapilabilir: [
      "Malzeme kartı oluşturma ve düzenleme",
      "Kod, ad veya TS no ile arama",
      "Aktif/pasif filtreleme",
      "Excel ile toplu içe aktarma"
    ],
    ipucu: "Poz ve siparişlerde kullanılacak malzemeyi önce burada tanımlayın."
  },
  metrajKesif: {
    amac: "Mahal, metraj, model ve analiz akışlarını tek ekranda toplar.",
    yapilabilir: [
      "Proje bazında mahal ve metraj özetini görme",
      "Mahal Listesi, IFC ve Analiz Kitabı ekranlarına geçiş"
    ],
    ipucu: "Üretim mevcut detay ekranlarında yapılır; burası izleme ve geçiş merkezidir."
  },
  maliyetHesabi: {
    amac: "Yaklaşık maliyet, poz planı ve S-eğrisi akışlarını tek ekranda toplar.",
    yapilabilir: [
      "Proje/yıl bazında maliyet özetini görme",
      "Yaklaşık Maliyet, Poz Planları ve Analiz Kitabı ekranlarına geçiş"
    ],
    ipucu: "Sapma analizi için poz planlarına gerçekleşen metraj girilmelidir."
  },
  genelBakis: {
    amac: "Portföy, nakit, kâr/zarar, ilerleme ve zaman çizelgesini tek ekranda izler.",
    yapilabilir: [
      "Proje/yıl seçerek tüm maliyet göstergelerini görme",
      "Portföy, Nakit Akışı, Kâr/Zarar ve Gantt ekranlarına geçiş"
    ],
    ipucu: "Boş görünen kartlar, ilgili modülde henüz veri girilmediğini gösterir."
  },
  insaatRaporlar: {
    amac: "Tüm inşaat raporlarına tek ekrandan erişim sağlar.",
    yapilabilir: [
      "Portföy, nakit, kâr/zarar, S-eğrisi, Gantt ve teknik raporlara geçiş",
      "Mizan ve şartname raporlarına geçiş"
    ],
    ipucu: "Hesaplama bu ekranda yapılmaz; her rapor kendi ekranında üretilir."
  },
  insaatAyarlar: {
    amac: "Firma, kullanıcı, proje ve muhasebe ayarlarına merkezi erişim sağlar.",
    yapilabilir: [
      "Firma bilgileri, kullanıcı, tenant, proje ve hesap planı ekranlarına geçiş",
      "Rol ve yetki matrisini görüntüleme"
    ],
    ipucu: "Yetki değişiklikleri backend kurallarıyla uygulanır; tablo bilgilendirme amaçlıdır."
  },
  profil: {
    amac: "Kendi profil bilgilerini görüntüler ve şifre değiştirmeyi sağlar.",
    yapilabilir: [
      "Kullanıcı, rol ve firma bilgisini görme",
      "Mevcut şifreyle yeni şifre belirleme"
    ],
    ipucu: "Şifre değişikliğinden sonra diğer cihazlardaki oturumlar kapanmaz; gerekiyorsa çıkış yapın."
  },
  vergiProfilleri: {
    amac: "Fatura kalemlerinde tekrar kullanılan KDV, tevkifat ve stopaj kurallarını tutar.",
    yapilabilir: [
      "Vergi profili oluşturma ve düzenleme",
      "Kod veya ad ile arama",
      "Fatura girişinde profili kaleme uygulama"
    ],
    ipucu: "Oranlar 0-100 arasında olmalıdır; profili silmek yerine pasife alın."
  },
  stokHesapEsleme: {
    amac: "Malzeme bazında stok ve KDV muhasebe hesap eşleşmelerini yönetir.",
    yapilabilir: [
      "Malzemeye özel veya tenant varsayılanı eşleme tanımlama",
      "Hesap türüne göre filtreleme"
    ],
    ipucu: "Malzeme seçilmezse kayıt tenant varsayılanı olur; aynı kapsamda tekrar tanımlanamaz."
  },
  hatirlatmaKurallari: {
    amac: "Modül tarihlerinden otomatik hatırlatma üreten kuralları yönetir.",
    yapilabilir: [
      "Modül ve tetikleyici bazında kural tanımlama",
      "Önce-gün sayısı, seviye ve aktiflik yönetimi"
    ],
    ipucu: "Aynı modül/tetikleyici/gün için tek kural tanımlanabilir."
  }
};