# YOL HARİTASI — İnşaat Modülü (Yapı Sınıfı IV-A Odaklı)

> Bu yol haritası, `readme.md` içindeki **"52. İNŞAAT MODÜLÜ — YAPI SINIFI (IV-A) VE
> POZ / MALZEME YÖNETİMİ"** bölümünü esas alır. Mevcut Emlak + Muhasebe + Finans
> SaaS altyapısına (multi-tenant, Django + PostgreSQL hedef mimarisi) **ek modül**
> olarak eklenir; mevcut sistemi bozmaz (bkz. AGENTS.md / readme.md bölüm 33-34).

Sembol anahtarı: `☑` tamamlandı, `☐` yapılacak, `◐` kısmen / devam ediyor.

---

## Faz 1 — Temel (0-3 ay)

* ☑ ÇŞİDB poz parser (CSV içe aktarma: `import_pozlar` / `import_yapi_sinifi`
  management komutları; KK.GGG.SSSS doğrulama, `4A → IV-A` normalize,
  yıllık çalıştırılabilir, eski yıl `is_active=False` arşiv, fail-fast atomic;
  örnek şablonlar `docs/ornekler/*.csv`. PDF kaynaklı veri önce CSV'ye
  dönüştürülür — doğrudan PDF parser'ı ileri fazda değerlendirilir)
* ☑ Poz veri modeli (`Poz`, `PozGrubu`, `Malzeme`, `PozMalzemeIliskisi`) — `construction/`
* ☑ Yıl bazlı `YapiSinifiBirimMaliyet` tablosu (I-A … V-E, tebliğ yılı ile versiyonlu)
* ☑ Maliyet motoru (metraj → poz → fiyat, `birim_fiyat_snapshot` mantığı) — `services.py`
* ☑ Proje tanımlama modülü (Proje ↔ Gayrimenkul ↔ Yapı Sınıfı ilişkisi) — `Proje`
  + `RealEstate` (proje FK) + `/api/v1/real-estate/gayrimenkuller/`; Yapı Sınıfı
  ilişkisi `Proje.yapisinif_maliyet` üzerinden
* ☑ IV-A yapı sınıfı taban maliyet entegrasyonu (52.2'deki tipik yapı grupları) —
  model + `import_yapi_sinifi` CSV içe aktarma (normalize'lu) tamam; API/admin
  üzerinden elle giriş de mümkün
* ☑ Malzeme kartı + TS/TS EN referans alanı (52.5)
* ☑ Poz/metraj için Decimal zorunluluğu ve borç-alacak benzeri "metraj bütünlüğü"
  validasyonu (fazla/negatif metraj engeli) — DB check + service
* ☑ Rol bazlı yetkilendirme: Şantiye Şefi (okuma), Maliyet Mühendisi, Proje Yöneticisi
  (yazma) — `IsConstructionEditor`

## Faz 2 — İş Takibi (3-6 ay)

* ☑ Poz maliyet planı çekirdeği (planlanan/gerçekleşen metraj + `birim_fiyat_snapshot`) —
  `PozPlan` modeli, `/api/v1/construction/poz-planlari/` CRUD, admin, DB check/unique
  constraint, RLS policy; frontend "Poz Planları (Metraj)" ekranı
* ☑ Gantt şeması (iş kalemi / poz grubu bazlı zaman çizelgesi) —
  backend: `construction/services.py::gantt_verisi` +
  `GET /api/v1/construction/poz-planlari/gantt/?proje=<id>&yil=<yıl>` (tenant izole);
  frontend: Poz Planları ekranında görselleştirme paneli (Tailwind CSS çubukları,
  ilerleme bandı = gerçekleşen/planlanan metraj, tarihsiz pozlar işaretlenir;
  planlanan başlangıç/bitiş alanları modal'a eklendi)
* ☑ Hakediş takibi (dönemsel hakediş → Muhasebe Fişi/Cari Hareket entegrasyonu,
   bkz. 52.6 madde 4) — `Hakedis`/`HakedisSatiri` modelleri (tenant+proje+dönem unique),
   satır üretimi poz planlarından (`POST /hakedisler/{id}/satirlar-olustur/`), onay
   `POST /hakedisler/{id}/onayla/` (Cari Hareket + Muhasebe Fişi 740 borç/120 alacak,
   transaction.atomic + select_for_update), iptal (fiziksel DELETE yok);
   frontend "Hakedişler" ekranı (satır yönetimi + onay akışı)
* ☑ Şantiye günlüğü (mobil uyumlu kayıt ekranı, çevrimdışı taslak, fotoğraf/not alanları için temel altyapı)
* ☑ Malzeme/tedarik planı (Malzeme ↔ Tedarikçi ↔ sipariş/t teslim takibi; tenant izole CRUD + frontend)
* ☑ Alt yüklenici (taşeron) sözleşme ve hakediş modülü (sözleşme CRUD, durum akışı, iptal deseni ve hakediş ekranı bağlantısı)
* ☑ İş güvenliği / kalite kontrol kontrol listeleri (poz/proje bazlı kabul kriterleri, ölçüm-tolerans alanları, durum ve düzeltici faaliyet akışı)
* ☑ Poz bazlı gerçekleşen/planlanan maliyet karşılaştırma raporu (S-eğrisi) —
  `construction/services.py::s_egrisi_raporu` (PV/AV/sapma, Decimal+quantize) +
  `GET /api/v1/construction/poz-planlari/s-egrisi/?proje=<id>&yil=<yıl>` (tenant izole) +
  frontend S-eğrisi paneli

## Faz 3 — Kentsel Dönüşüm (6-9 ay)

* ☑ Ada/parsel ve imar modülü (tenant izole ada/parsel CRUD, alan/oran doğrulaması, imar durumu ve frontend ekranı; TKGM/e-Devlet entegrasyon noktaları için altyapı)
* ☑ Kat karşılığı senaryo simülasyonu (Decimal oran/alan doğrulaması, parsel bazlı senaryo ekranı ve bağımsız bölüm dağılımı)
* ☑ Malik mutabakatı takibi (çoklu malik, pay toplam kontrolü, oy/onay durumu ve not takibi; doküman arşivi sonraki e-belge paketinde)
* ☑ Sözleşme şablonları (kat karşılığı, hasılat paylaşımlı, taşeron, tedarik; tenant izole CRUD ve içerik önizleme)
* ☑ Riskli yapı tespiti/süreç takibi (6306 sayılı Kanun süreç adımları — bilgi
   amaçlı iş akışı, hukuki danışmanlık yerine geçmez; durum/tarih/not takibi)
* ☑ Kira yardımı / tahliye süreci takibi (mevcut LeaseAssistance modeliyle proje bazlı CRUD, arama ve süreç durumu)

## Faz 4 — Finans ve Muhasebe Derinleştirme (9-12 ay)

* ☑ Poz/hakediş verisinin çift taraflı muhasebeye tam otomatik yansıması (onay akışında Cari Hareket + 740/120 Muhasebe Fişi transaction içinde üretiliyor; tekrar onay ve tutar uyumsuzluğu korunuyor)
   (bölüm 12-13 kuralları çerçevesinde)
* ☑ Proje bazlı nakit akışı (yıllık planlanan poz gideri + onaylı hakedişlerin aylık gerçekleşen gider akışı; proje gelir ilişkisi mevcut modelde olmadığı için açık veri notu)
* ☑ Banka/çek/senet modülüyle taşeron ödeme planı entegrasyonu (proje bağlantılı çek/senet kayıtları, vade ve durum takibi)
* ☑ Proje bazlı kâr/zarar ve bütçe sapma raporu (bütçelenen poz maliyeti vs.
   onaylı hakediş gerçekleşmesi; proje gelir modeli bulunmadığı için kapsam notu)
* ◐ KDV/stopaj hesaplamalarında inşaat sektörüne özgü kurallar (KDV, KDV tevkifatı ve brüt matrah üzerinden stopaj satır bazlı hesaplanıyor; tenant bazlı vergi profili kataloğu eklendi, mevzuat oranlarının kurum bazlı yönetimi sonraki iterasyonda)
* ☑ Fiziksel DELETE yasağı kapsamına poz/metraj/hakediş kayıtlarının netleştirilmesi (poz planı pasife çekilir; hakediş iptal edilir; onaylı hakediş korunur)

## Faz 5 — Raporlama ve AI (12-15 ay, ileri seviye / opsiyonel)

* ◐ AI destekli metraj kontrolü (ilk sürümde açıklanabilir metraj eşik kontrolleri ve aksiyon önerileri; çizim/liste verisiyle poz eşleştirme entegrasyonu sonraki iterasyonda)
* ◐ Anomali tespiti (ilk sürümde proje snapshot fiyatı ile önceki yıl aktif fiyat karşılaştırması; piyasa ortalaması ve malzeme tedarik fiyatları sonraki iterasyonda)
* ◐ Doğal dilde raporlama (ilk sürümde tenant kapsamlı gelir/gider, cari bakiye ve mizan soruları; proje/hakediş doğal dil niyetleri sonraki iterasyonda)
* ☑ Yönetici paneli: çoklu proje portföyü, yapı sınıfı bazlı karşılaştırmalı maliyet
   analizi (yıl/durum/arama/yapı sınıfı filtreleri, bütçe-gerçekleşen-sapma KPI'ları)
* ☑ Teknik şartname otomatik doküman üretimi (poz + malzeme + TS referanslarından
   yazdırılabilir/PDF'e dönüştürülebilir taslak; teknik onay notu ve boş veri durumu dahil)

## Faz 6 — Esin Kaynağı / Opsiyonel Özellikler (planlama dışı, backlog)

* ☑ Mobil şantiye check-in / QR kod ile malzeme giriş-çıkış takibi
* ☑ Tedarikçi karşılaştırmalı teklif toplama modülü (uygulandı; Faz 1/2 satın
  alma ekranı ve karşılaştırmalı teklif API'si)
* ☑ Enerji kimlik belgesi (EKB) süreç takibi (tenant/proje bazlı belge, durum ve
  enerji sınıfı akışı, tarih doğrulama, arşivleme, filtreli API ve frontend)
* ☐ BIM/IFC dosya içe aktarma ile otomatik metraj taslağı (ileri araştırma konusu)

---

### Notlar

- Her fazın çıktısı, önceki fazın verisini **bozmadan** üzerine eklenmelidir
  (bkz. AGENTS.md ve readme.md — "toplu rewrite yasaktır").
- Poz/fiyat verileri her yıl ÇŞİDB tarafından güncellendiğinden, Faz 1'deki parser
  **yıllık çalıştırılabilir** şekilde tasarlanmalı; eski yıl pozları `aktif=false`
  olarak arşivlenmeli, silinmemelidir.
- Faz 3 (Kentsel Dönüşüm) hukuki bir süreçtir; modül yalnızca **takip ve doküman
  yönetimi** sağlar, hukuki/teknik danışmanlığın yerine geçmez.
