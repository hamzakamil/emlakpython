# EMLAK ERP - İNŞAAT MALİYET HESAPLAMA MODÜLÜ
## MEVCUT SİSTEM ANALİZ RAPORU

**Tarih:** 2026-09-21  
**Hazırlayan:** AI Analiz Asistanı  
**Amaç:** Mevcut sistemi koruyarak yeni hedefe (IV-A yapı sınıfına göre proje bazlı inşaat maliyeti hesaplama) kademeli genişletme planı hazırlamak

---

## 1. MEVCUT TEKNOLOJİ YIĞINI

### Backend
| Teknoloji | Versiyon | Kullanım Alanı |
|-----------|----------|----------------|
| Python | 3.11+ | Ana dil |
| Django | 6.1.1 | Web framework |
| Django REST Framework | 3.18.1 | API |
| PostgreSQL | 18.6 | Veritabanı |
| psycopg | 3.3.5 | DB driver |
| drf-spectacular | 0.30.0 | OpenAPI/Swagger |
| django-filter | 26.1 | Filtreleme |
| django-environ | 0.14.0 | Config yönetimi |
| django-cors-headers | 4.9.0 | CORS |
| openpyxl | 3.1.5 | Excel import/export |
| pytest | 9.1.1 | Test |

### Frontend
| Teknoloji | Versiyon | Kullanım Alanı |
|-----------|----------|----------------|
| Vue | 3.4 | UI Framework |
| TypeScript | 5.3 | Tip güvenliği |
| Vite | 5.0 | Build tool |
| Tailwind CSS | 3.4 | Styling |
| Pinia | 2.1 | State management |
| TanStack Vue Query | 5.0 | Server state |
| TanStack Vue Table | 8.11 | Tablolar |
| Vue Router | 4.3 | Routing |
| Axios | 1.6 | HTTP client |
| Zod | 3.22 | Validation |
| Chart.js | 4.4 | Grafikler |
| Lucide Vue Next | 0.33 | İkonlar |

### Mimari Desenler
- **Multi-tenant (Çok kiracılı):** Tüm modeller `TenantAwareModel` miras alır
- **Soft Delete:** Fiziksel silme yok, `is_active` flag ile arşivleme
- **Snapshot Pricing:** Fiyatlar kayıt anında kopyalanır (`birim_fiyat_snapshot`)
- **Decimal-only:** Para/miktar her zaman `Decimal`, asla `float`
- **Versioning:** YaklasikMaliyet, YFK verileri versiyonlu
- **Audit Trail:** YfkGuncellemeGecmisi, outbox pattern

---

## 2. FRONTEND MİMARİSİ

### Klasör Yapısı
```
frontend/src/
├── components/          # Yeniden kullanılabilir bileşenler
│   ├── VeriTablosu.vue  # Genel tablo bileşeni
│   ├── KayitModal.vue   # CRUD modal
│   ├── Sayfalama.vue    # Sayfalama
│   ├── ExcelAktarim.vue # Excel import/export
│   └── ...
├── composables/         # Vue composables
├── config/              # Uygulama config
├── data/                # Statik veriler
├── hooks/               # Custom hooks
│   ├── useKayitListesi.ts    # Listeleme + sayfalama + arama
│   ├── useKayitFormu.ts      # Form yönetimi + validasyon
│   └── ...
├── layouts/             # Layout bileşenleri (AppLayout.vue)
├── router/              # Vue Router (index.ts)
├── services/            # API servisleri
│   ├── apiClient.ts     # Axios instance + interceptors
│   ├── insaatApi.ts     # İnşaat modülü API'leri
│   └── ...
├── stores/              # Pinia stores
│   └── auth.ts          # Auth + tenant yönetimi
├── themes/              # Tema dosyaları
├── types/               # TypeScript tipleri
│   └── insaat.ts        # İnşaat modülü tipleri
├── utils/               # Yardımcı fonksiyonlar
│   └── yetki.ts         # Yetki kontrolü
└── views/               # Sayfa bileşenleri
    ├── insaat/          # İnşaat modülü sayfaları
    ├── cari/, finans/, muhasebe/, yonetim/, gayrimenkul/
    └── ...
```

### Routing Yapısı (İnşaat Modülü)
| Yol | Bileşen | Açıklama |
|-----|---------|----------|
| `/insaat/poz-gruplari` | PozGruplariView | Poz grupları CRUD |
| `/insaat/pozlar` | PozlarView | Pozlar CRUD |
| `/insaat/yapi-sinifi` | YapiSinifiView | Yapı sınıfı birim maliyetleri |
| `/insaat/poz-planlari` | PozPlanlariView | Poz planları + S-eğrisi + Gantt |
| `/insaat/yfk/*` | YFK alt sayfaları | YFK veri güncelleme |
| `/insaat/mahaller` | MahalListesiView | Mahal listesi |
| `/insaat/analiz-kitabi` | AnalizKitabiView | Poz analiz kitabı |
| `/insaat/yaklasik-maliyet` | YaklasikMaliyetView | Yaklaşık maliyet + revizyon |
| `/insaat/ifc-import` | IFCImportView | IFC içe aktarma |
| `/insaat/gantt` | GanttView | Gantt şeması |
| `/insaat/rayicler` | RayiclerView | YFK rayıç listesi |
| `/insaat/projeler` | ProjelerView | Projeler CRUD |
| `/insaat/hakedisler` | HakedislerView | Hakedişler |
| `/insaat/poz-fiyatlari` | PozFiyatlariView | Poz fiyatları |
| `/insaat/poz-analizleri` | PozAnalizleriView | Poz analizleri |
| `/insaat/malzeme-tedarik` | MalzemeTedarikPlaniView | Malzeme tedarik planı |
| `/insaat/tedarikci-teklifleri` | TedarikciTeklifleriView | Tedarikçi teklifleri |
| `/insaat/kalite-kontrolleri` | KaliteKontrolleriView | Kalite kontrolleri |
| `/insaat/sozlesme-sablonlari` | ContractTemplatesView | Sözleşme şablonları |
| `/insaat/riskli-yapi` | RiskStructuresView | Riskli yapı takibi |
| `/insaat/kira-yardimi` | LeaseAssistanceView | Kira yardımı |
| `/insaat/ekb` | EKBView | EKB süreç takibi |
| `/insaat/nakit-akisi` | NakitAkisiView | Nakit akışı raporu |
| `/insaat/kar-zarar` | KarZararView | Kâr/zarar raporu |
| `/insaat/portfoy-karsilastirma` | PortfoyKarsilastirmaView | Portföy karşılaştırma |
| `/insaat/teknik-sartname` | TeknikSartnameView | Teknik şartname taslağı |

### State Management
- **Pinia (auth store):** Kullanıcı, tenant, roller, yetkiler
- **TanStack Query:** Server state caching, invalidation
- **Local component state:** Form verileri, UI durumu
- **Custom hooks:** `useKayitListesi`, `useKayitFormu` - CRUD pattern'leri soyutlar

### UI Bileşen Kütüphanesi
- **Headless UI:** Accessible unstyled components
- **Heroicons / Lucide:** İkon setleri
- **Tailwind Merge + clsx:** Class birleştirme
- **Vue Sonner:** Toast bildirimleri
- **TipTap:** Rich text editor

---

## 3. BACKEND MİMARİSİ

### Klasör Yapısı
```
construction/
├── models.py              # Tüm modeller (1000+ satır)
├── views.py               # ViewSet'ler (1200+ satır)
├── serializers.py         # Serializer'lar (600+ satır)
├── urls.py                # Router kayıtları
├── permissions.py         # IsConstructionEditor
├── services.py            # Ana servisler (maliyet motoru, raporlar)
├── services/              # Alt servis modülleri
│   ├── analiz.py          # Poz analiz + nakliye
│   ├── hatirlatma.py      # Hatırlatma motoru
│   ├── mahal_metraj.py    # Mahal metraj + maliyet üretimi
│   ├── metraj.py          # Güvenli metraj hesaplayıcı (AST-based)
│   ├── yaklasik_maliyet.py # Yaklaşık maliyet hesaplama/revizyon
│   └── __init__.py
├── imports.py             # CSV/PDF import (ÇŞİDB)
├── ifc.py                 # IFC parsing (IfcOpenShell)
├── management/            # Django management commands
├── migrations/            # 20 migration dosyası
├── tests.py               # Testler
└── api/                   # (boş - views.py kullanılıyor)
```

### ViewSet Mimarisi
- **TenantScopedViewSet:** Tenant izolasyonu sağlayan base class
- **IsConstructionEditor:** İnşaat modülü yazma izni
- **Custom Actions:** Raporlar, hesaplamalar, işlemler için `@action` decorator'ları

### API Endpoint Örnekleri
```
GET    /api/v1/construction/pozlar/                    # Poz listesi
POST   /api/v1/construction/pozlar/                    # Poz oluştur
GET    /api/v1/construction/poz-planlari/s-egrisi/     # S-eğrisi raporu
GET    /api/v1/construction/poz-planlari/gantt/        # Gantt verisi
GET    /api/v1/construction/poz-planlari/nakit-akisi/  # Nakit akışı
GET    /api/v1/construction/poz-planlari/kar-zarar/    # Kâr/zarar
GET    /api/v1/construction/poz-planlari/metraj-kontrolu/ # Akıllı metraj kontrolü
GET    /api/v1/construction/poz-planlari/fiyat-anomalileri/ # Fiyat anomali taraması
POST   /api/v1/construction/yaklasik-maliyetler/{id}/hesapla/  # Maliyet hesapla
POST   /api/v1/construction/yaklasik-maliyetler/{id}/revize/   # Yeni revizyon
POST   /api/v1/construction/yaklasik-maliyetler/{id}/mahal-listesinden-olustur/ # Mahallerden üret
POST   /api/v1/construction/mahaller/{id}/metraj-uret/         # Mahal metraj üret
POST   /api/v1/construction/metrajlar/hesapla/                 # Metraj önizleme
POST   /api/v1/construction/imports/upload/                    # CSV/PDF import
POST   /api/v1/construction/ifc-import-jobs/{id}/process/      # IFC işle
POST   /api/v1/construction/ifc-import-jobs/{id}/approve/      # IFC onayla → PozPlan
```

---

## 4. DATABASE MİMARİSİ

### Veritabanı Türü
- **PostgreSQL 18.6** (production)
- **SQLite** (test/development)

### Temel Prensipler
- **Tenant İzolasyonu:** Her tablo `tenant_id` FK'sı ile başlar
- **Soft Delete:** `is_active` boolean, fiziksel DELETE yok
- **Decimal Precision:** Para = 14,2 / Miktar = 14,4 / Metraj = 18,6
- **Unique Constraints:** Tenant + business key kombinasyonları
- **Check Constraints:** Pozitif değer zorunluluğu, tarih sıralaması
- **Indexes:** Tenant + sık filtrelenen alanlar için composite index'ler

### Ana Tablolar (Construction Modülü)

| Tablo | Açıklama | Ana Alanlar |
|-------|----------|-------------|
| `construction_pozgrubu` | Poz grupları (hiyerarşik) | kod, ad, ust_grup_id |
| `construction_poz` | Poz kartları | poz_no, ad, birim, grup_id, tip |
| `construction_malzeme` | Malzeme kartları | malzeme_kodu, ad, birim, ts_no, qr_kodu |
| `construction_pozmalzemeiliskisi` | Poz-Malzeme (through) | poz_id, malzeme_id, miktar |
| `construction_pozfiyat` | Poz birim fiyatları (yıl/dönem) | poz_id, yil, donem, birim_fiyat, kaynak |
| `construction_yapisinifibirimmaliyet` | Yapı sınıfı birim maliyetleri | sinif_kodu, yil, birim_maliyet |
| `construction_proje` | İnşaat projeleri | proje_kodu, ad, yapisinif_maliyet_id, durum |
| `construction_mahal` | Proje mahalleri | proje_id, kod, ad, mahal_tipi, kat, alan |
| `construction_mahalelemani` | Mahal elemanları | mahal_id, eleman_tipi, miktar, birim |
| `construction_yaklasikmaliyet` | Yaklaşık maliyet başlığı | proje_id, yil, versiyon, toplam_tutar, onceki_id |
| `construction_yaklasikmaliyetsatiri` | Yaklaşık maliyet satırları | yaklasik_maliyet_id, poz_id, mahal_id, miktar, birim_fiyat_snapshot |
| `construction_pozplan` | Poz maliyet planı | proje_id, poz_id, yil, planlanan_miktar, gercek_miktar, birim_fiyat_snapshot |
| `construction_pozanaliz` | Poz analiz satırları | poz_id, satir_no, malzeme, birim, miktar, birim_fiyat, analiz_tipi |
| `construction_nakliyemesafe` | Proje-poz nakliye mesafesi | proje_id, poz_id, mesafe_km, k_katsayisi |
| `construction_metraj` | Hesaplanmış metraj kayıtları | ad, metraj_tipi, ifade, sonuc, birim |
| `construction_hakedis` | Hakedişler | proje_id, donem, durum, cari_id |
| `construction_hakedissatiri` | Hakediş satırları | hakedis_id, poz_id, miktar, birim_fiyat |
| `construction_yfkpozversiyon` | YFK poz versiyonları | poz_no, ad, birim, grup_kodu, versiyon |
| `construction_yfkfiyat` | YFK fiyatları | poz_versiyon_id, yil, donem, birim_fiyat |
| `construction_yfkrayic` | YFK rayıç (katsayı) | poz_versiyon_id, malzeme_tipi, malzeme_kodu, katsayi |
| `construction_yfkanaliz` | YFK analiz detayları | poz_versiyon_id, malzeme_tipi, malzeme_kodu, miktar, birim_fiyat |
| `construction_ifcimportjob` | IFC içe aktarma işleri | project_id, year, status, file |
| `construction_ifcquantitydraft` | IFC miktar taslakları | job_id, poz_id, source_name, quantity, mapping_status |

### İlişki Şeması (Özet)
```
YapiSinifiBirimMaliyet (1) ←→ (N) Proje
Proje (1) ←→ (N) Mahal
Mahal (1) ←→ (N) MahalElemani
Proje (1) ←→ (N) PozPlan
PozPlan (N) ←→ (1) Poz
Poz (1) ←→ (N) PozFiyat (yıl/dönem bazlı)
Poz (1) ←→ (N) PozMalzemeIliskisi ←→ (N) Malzeme
Poz (1) ←→ (N) PozAnaliz
YaklasikMaliyet (1) ←→ (N) YaklasikMaliyetSatiri
YaklasikMaliyetSatiri (N) ←→ (1) Poz
YaklasikMaliyetSatiri (N) ←→ (1) Mahal (opsiyonel)
Proje (1) ←→ (N) NakliyeMesafe ←→ (1) Poz
```

---

## 5. MEVCUT TABLOLAR - DETAYLI

### 5.1 Poz Yapısı
**Model:** `Poz` (`construction_poz`)
- `poz_no`: ÇŞİDB formatında (örn. 15.110.1001)
- `ad`: Poz açıklaması
- `birim`: m², m³, m, kg, adet, lt
- `grup`: PozGrubu FK (hiyerarşik)
- `tip`: yapim/iscilik/nakliye/makine/diger

**İlişkiler:**
- `PozGrubu` (üst grup/alt gruplar hiyerarşisi)
- `PozFiyat` (yıl/dönem bazlı fiyatlar)
- `PozMalzemeIliskisi` → `Malzeme` (analiz malzemeleri)
- `PozAnaliz` (detaylı analiz satırları)
- `PozPlan` (proje bazlı plan/gerçekleşen)

### 5.2 Malzeme Yapısı
**Model:** `Malzeme` (`construction_malzeme`)
- `malzeme_kodu`: Benzersiz kod
- `ad`: Malzeme adı
- `birim`: Ölçü birimi
- `ts_no`: TS/TS EN referansı
- `qr_kodu`: Otomatik üretilen EML-XXXX kodu

### 5.3 Fiyat Yapısı
**Model:** `PozFiyat` (`construction_pozfiyat`)
- `poz_id` + `yil` + `donem` (ay) = unique
- `birim_fiyat`: Decimal(14,2)
- `kaynak`: Örn. "ÇŞİDB 2026 tebliği"
- `kaynak_url`, `yayin_tarihi`, `gecerlilik_tarihi`
- **Snapshot mantığı:** PozPlan, YaklasikMaliyetSatiri, HakedisSatiri → `birim_fiyat_snapshot` kopyalar

**YFK Fiyatları:** `YfkFiyat` ayrı tabloda, `YfkPozVersiyon` üzerinden versiyonlu

### 5.4 Analiz Yapısı
**Model:** `PozAnaliz` (`construction_pozanaliz`)
- `poz_id` + `satir_no` = unique
- `analiz_tipi`: malzeme/iscilik/makine/nakliye/diger
- `malzeme`: Analiz kalemi adı (serbest metin, Malzeme FK'sı YOK)
- `miktar` × `birim_fiyat` = `tutar` (otomatik hesaplanır)

**YFK Analiz:** `YfkAnaliz` ayrı tabloda, `YfkPozVersiyon` + `malzeme_kodu` + `sira_no` unique

### 5.5 Proje Yapısı
**Model:** `Proje` (`construction_proje`)
- `proje_kodu`, `ad`
- `yapisinif_maliyet`: `YapiSinifiBirimMaliyet` FK (snapshot)
- `durum`: teklif/planlanan/devam/askida/tamamlandi/iptal
- Tarih alanları: baslangic, bitis, sozlesme_bitis, gecici_kabul, kesin_kabul

### 5.6 Mahal Yapısı
**Model:** `Mahal` (`construction_mahal`)
- `proje_id`, `kod`, `ad`, `mahal_tipi`, `kat`, `alan`
- `MahalElemani` (1-N): eleman_tipi, miktar, birim

**Mahal Tipleri:** oda, salon, mutfak, banyo, wc, balkon, koridor, antre, depo, diger
**Eleman Tipleri:** doseme, duvar, tavan, supurgelik, kapi, pencere, dograma

### 5.7 Metraj Yapısı
**Model:** `Metraj` (`construction_metraj`)
- `ad`, `metraj_tipi`, `ifade`, `sonuc`, `birim`
- Güvenli hesaplayıcı: `metraj/services/metraj.py` → AST parser (eval YOK)
- Özel fonksiyonlar: `demir_metraji`, `profil_metraji`, `pursantaj_hesapla`

### 5.8 Maliyet Yapısı
**YaklasikMaliyet** (Proje + Yıl + Versiyon bazlı)
- `versiyon` artan, `onceki` FK ile revizyon zinciri
- `toplam_tutar` = Σ satır toplamları
- Satırlar: `poz_id`, `mahal_id` (opsiyonel), `miktar`, `birim_fiyat_snapshot`

**PozPlan** (Proje + Poz + Yıl bazlı, unique)
- `planlanan_miktar` > 0, `gercek_miktar` ≥ 0
- `birim_fiyat_snapshot` kayıt anında PozFiyat'tan alınır
- S-eğrisi: PV = planlanan × snapshot, AV = gerçekleşen × snapshot

**Hakedis** (Dönemsel progress payment)
- `donem`: YYYY-MM formatında
- `durum`: taslak/onaylandi/iptal
- Onay → Cari Hareket + Muhasebe Fişi üretir

---

## 6. MEVCUT POZ YAPISI

### Mevcut Durum
✅ **Poz Grubu:** Hiyerarşik (üst/alt grup), kod+ad, tenant unique  
✅ **Poz Kartı:** poz_no, ad, birim, grup, tip (yapim/iscilik/nakliye/makine/diger)  
✅ **Poz Fiyatı:** Yıl/dönem bazlı, kaynak takibi, snapshot mantığı  
✅ **Poz-Malzeme İlişkisi:** Through model, miktar (poz birimi başına malzeme miktarı)  
✅ **Poz Analizi:** Satır bazlı, 5 analiz tipi, tutar otomatik  
✅ **YFK Pozları:** Versiyonlu, ayrı tablo seti (poz/fiyat/rayic/analiz)  

### Eksiklikler (Yeni Hedefe Göre)
❌ **İmalat Grubu:** PozGrubu var ama "İmalat Grubu" kavramı yok (Beton, Demir, Kalıp, İşçilik gibi)  
❌ **Yapı Sınıfı → Poz Filtresi:** IV-A sınıfı için poz seçimi otomatik değil  
❌ **Poz Kategorizasyonu:** Ana yapı / tamamlama / Tesisat ayrımı yok  

---

## 7. MEVCUT MALZEME YAPISI

### Mevcut Durum
✅ **Malzeme Kartı:** Kod, ad, birim, TS referansı, QR kod  
✅ **Poz-Malzeme İlişkisi:** Poz başına malzeme miktarı (birim başına)  
✅ **Tedarikçi İlişkisi:** `MalzemeTedarikciIliskisi` + `TedarikciTeklifi`  
✅ **Malzeme Hareketi:** QR kodlu giriş/çıkış, proje bazlı  

### Eksiklikler
❌ **Malzeme Kategorisi:** Beton, Çelik, Tuğla, İzolasyon gibi kategori yok  
❌ **Projeye Özel Malzeme:** Global malzeme kartı var, proje özel malzeme yok  
❌ **Malzeme Alternatifleri:** Aynı poz için farklı marka/model seçeneği yok  

---

## 8. MEVCUT FİYAT YAPISI

### Mevcut Durum
✅ **Genel Poz Fiyatı:** `PozFiyat` - Yıl/Ay bazlı, kaynaklı, snapshot  
✅ **YFK Fiyatları:** `YfkFiyat` - Versiyonlu, ayrı tablo  
✅ **Snapshot Mantığı:** PozPlan, YaklasikMaliyetSatiri, HakedisSatiri → fiyat kopyalanır  
✅ **Nakliye Fiyatı:** `NakliyeMesafe` - Proje+Poz bazlı mesafe + K katsayısı  

### Eksiklikler (Kritik)
❌ **Proje Bazlı Fiyat:** `PozFiyat` tenant+poz+yıl+dönem unique → **Aynı poz için farklı projelerde farklı fiyat YOK**  
❌ **Malzeme Bazlı Proje Fiyatı:** Malzeme fiyatı projeye özel değil  
❌ **Tedarikçi Fiyatı:** `TedarikciTeklifi` var ama PozPlan/YaklasikMaliyet'e entegre değil  

---

## 9. MEVCUT ANALİZ YAPISI

### Mevcut Durum
✅ **PozAnaliz:** Poz başına satırlar, 5 tip (malzeme/iscilik/makine/nakliye/diger)  
✅ **YfkAnaliz:** YFK versiyonlu analiz, malzeme_kodu referanslı  
✅ **Toplam Hesaplama:** `poz_analiz_toplam(poz_id)` servis fonksiyonu  
✅ **Nakliye Hesaplama:** `nakliye_hesapla(poz, mesafe, k)` - OSKA/AMP formülü  

### Eksiklikler
❌ **Analiz Şablonu:** Standart analiz şablonları yok (her poz için manuel)  
❌ **Projeye Özel Analiz:** Global analiz var, proje özel analiz yok  
❌ **Malzeme Değişimi:** Analizdeki malzeme projeye göre değiştirilemiyor  

---

## 10. MEVCUT PROJE YAPISI

### Mevcut Durum
✅ **Proje:** Kod, ad, durum, yapı sınıfı maliyeti, tarihler  
✅ **Yapı Sınıfı Maliyeti:** `YapiSinifiBirimMaliyet` - Yıl + Sınıf kodu (I-A ... V-E)  
✅ **Proje-Poz Planı:** `PozPlan` - Planlanan/Gerçekleşen metraj + snapshot fiyat  
✅ **Proje-Mahal:** Mahal listesi, kat, alan  
✅ **Proje-YaklasikMaliyet:** Versiyonlu, revizyonlu maliyet çalışmaları  

### Eksiklikler
❌ **Blok/Kat Hiyerarşisi:** Mahal'de `kat` var ama `blok` alanı yok (modelde `blok` yok, `kat` string)  
❌ **Proje Poz Şablonu:** IV-A için standart poz listesi otomatik gelmiyor  

---

## 11. MEVCUT MAHAL YAPISI

### Mevcut Durum
✅ **Mahal:** Proje+kod unique, ad, tip, kat, alan  
✅ **MahalElemani:** Kapı, pencere, duvar, tavan, döşeme, süpürgelik, doğrama  
✅ **Metraj Üretimi:** `mahal_metraj_uret()` - Ölçülerden 7 standart metraj üretir  
✅ **Maliyet Üretimi:** `mahal_elemanlarindan_yaklasik_maliyet_uret()` - Poz eşleştirme ile  

### Eksiklikler
❌ **Blok Alanı:** Modelde `blok` alanı YOK (sadece `kat` string)  
❌ **Mahal Şablonu:** Standart mahal tipleri için poz/malzeme şablonu yok  
❌ **Mahal Bazlı Malzeme:** Mahal elemanları poz'a bağlı, malzeme direkt bağlı değil  

---

## 12. MEVCUT METRAJ YAPISI

### Mevcut Durum
✅ **Metraj Modeli:** Ad, tip, ifade, sonuç, birim - güvenli AST hesaplayıcı  
✅ **Mahal Metrajı:** Uzunluk/genişlik/yükseklik → 7 metraj (döşeme, tavan, duvar, süpürgelik, kapı, pencere, doğrama)  
✅ **Demir/Profil Metrajı:** Çap/tablo bazlı kg hesaplama  
✅ **Pursantaj Hesaplama:** Tutar × oran  

### Eksiklikler
❌ **Poz+Metraj+Proje+Mahal Bağlantısı:** `PozPlan` proje+poz+yıl bazlı, mahal yok  
❌ **YaklasikMaliyetSatiri** mahal_id opsiyonel ama PozPlan'da mahal yok  

---

## 13. MEVCUT MALİYET YAPISI

### Maliyet Motoru (Mevcut)
**Dosya:** `construction/services.py` + `construction/services/*.py`

| Fonksiyon | Açıklama |
|-----------|----------|
| `poz_birim_fiyati(poz, yil)` | PozFiyat'tan aktif fiyat getirir |
| `poz_toplam_tutar(poz, yil, metraj)` | Metraj × birim fiyat |
| `yaklasik_maliyet_hesapla()` | Satır toplamları + başlık toplamı |
| `yaklasik_maliyet_revize()` | Versiyon artırarak kopyalar |
| `mahal_metraj_uret()` | Mahal ölçülerden metraj üretir |
| `mahal_elemanlarindan_yaklasik_maliyet_uret()` | Mahal metrajları → maliyet satırları |
| `s_egrisi_raporu()` | PV/AV/Sapma raporu |
| `proje_kar_zarar()` | Proje kâr/zarar |
| `proje_nakit_akisi()` | Aylık nakit akışı |
| `portfoy_karsilastirmasi()` | Multi-proje karşılaştırma |
| `teknik_sartname_taslagi()` | Poz+malzeme → şartname markdown |
| `metraj_kontrolu()` | Akıllı metraj kontrolleri (eşikler) |
| `fiyat_anomalilerini_bul()` | Yıllar arası fiyat sapması taraması |

### Hesaplama Formülleri
```
POZ MALİYETİ (Basit)     = METRAJ × BİRİM_FİYAT_SNAPSHOT
POZ MALİYETİ (Analizli)  = Σ (ANALİZ_MİKTARI × MALZEME_FİYATI)
YAKLASIK MALİYET TOPLAMI = Σ SATIR_TOPLAMLARI
S-EĞRİSİ PV              = PLANLANAN_MİKTAR × BİRİM_FİYAT_SNAPSHOT
S-EĞRİSİ AV              = GERÇEKLEŞEN_MİKTAR × BİRİM_FİYAT_SNAPSHOT
NAKLİYE                  = 0.00017 × K_KATSAYISI × MESAFE_KM × NAKLİYE_BİRİM_FİYAT
```

---

## 14. YENİ HEDEF İÇİN KORUNACAKLAR

| Bileşen | Korunacak mı? | Neden |
|---------|---------------|-------|
| PozGrubu / Poz / PozFiyat | ✅ EVET | Çalışan çekirdek, snapshot mantığı sağlam |
| Malzeme / PozMalzemeIliskisi | ✅ EVET | Malzeme kütüphanesi, TS referansları |
| PozAnaliz | ✅ EVET | Analiz motoru çalışıyor |
| YapiSinifiBirimMaliyet | ✅ EVET | IV-A başta sınıf maliyetleri var |
| Proje / Mahal / MahalElemani | ✅ EVET | Hiyerarşi mevcut, genişletilebilir |
| YaklasikMaliyet / Satırları | ✅ EVET | Revizyonlu maliyet çalışması motoru hazır |
| PozPlan / S-eğrisi / Gantt | ✅ EVET | Plan/gerçekleşen takibi çalışıyor |
| Metraj (AST hesaplayıcı) | ✅ EVET | Güvenli, genişletilebilir |
| Hakedis / Cari/Muhasebe entegrasyonu | ✅ EVET | Ödeme akışı çalışıyor |
| YFK Verileri (ayrı tablo seti) | ✅ EVET | Veri kaynağı olarak koru, sistem yapma |
| IFC Import / Draft / Approve | ✅ EVET | BIM miktar girişi çalışıyor |
| Tedarikci / Teklif / MalzemeHareketi | ✅ EVET | Tedarik zinciri hazır |
| Raporlar (nakit akışı, kâr/zarar, portföy) | ✅ EVET | Rapor altyapısı hazır |

---

## 15. DEĞİŞTİRİLECEKLER (Mevcut Yapı Üzerinde)

| Alan | Mevcut | Yeni | Etki |
|------|--------|------|------|
| **PozPlan** | Mahal alanı YOK | `mahal` FK opsiyonel eklenecek | Mahal bazlı metraj/maliyet |
| **PozFiyat** | Tenant+Poz+Yıl+Dönem unique | **Proje bazlı fiyat** için yeni tablo | Proje özel fiyatı |
| **Malzeme** | Global kart | **ProjeMalzeme** yeni tablo | Proje özel malzeme/fiyat |
| **PozAnaliz** | Global analiz | **ProjePozAnaliz** yeni tablo | Proje özel analiz/malzeme |
| **Mahal** | `blok` alanı yok | `blok` CharField eklenecek | Blok/Kat/Mahal hiyerarşisi |
| **YaklasikMaliyetSatiri** | Mahal opsiyonel | Zorunlu hale getirilebilir | Mahal bazlı maliyet zorunlu |

---

## 16. GENİŞLETİLECEKLER (Yeni Alanlar/Eklemeler)

### 16.1 Yeni Modeller/Tablolar

| Model | Amaç | Alanlar |
|-------|------|---------|
| `ImalatGrubu` | Poz gruplarını imalat bazlı kategorize etme | kod, ad, ust_grup, sira |
| `PozImalatGrubu` | Poz-İmalatGrubu many-to-many | poz_id, imalat_grubu_id |
| `ProjePozFiyat` | **Projeye özel poz fiyatı** | proje_id, poz_id, yil, birim_fiyat, kaynak |
| `ProjeMalzeme` | **Projeye özel malzeme/fiyat** | proje_id, malzeme_id, ad_override, birim_fiyat, tedarikci_id |
| `ProjePozAnaliz` | **Projeye özel poz analizi** | proje_id, poz_id, satir_no, malzeme_id/adi, miktar, birim_fiyat |
| `Blok` | Proje altına blok hiyerarşisi | proje_id, kod, ad, sira |
| `Mahal` (güncelleme) | Blok FK eklenecek | blok_id (FK) |
| `MetrajKaydi` | Poz+Proje+Mahal+Miktar birleşik | proje_id, poz_id, mahal_id, miktar, birim, birim_fiyat, kaynak |

### 16.2 Mevcut Modellerde Yeni Alanlar

| Model | Yeni Alanlar |
|-------|--------------|
| `Poz` | `imalat_grubu` (FK, nullable), `yapi_sinifi_uygunluk` (JSON: ["IV-A", "III-B"]), `kategori` (ana_yapi/tamamlama/tesisat) |
| `Proje` | `yapi_sinifi` (CharField: "IV-A"), `blok_sayisi`, `kat_sayisi`, `toplam_alan_m2` |
| `Mahal` | `blok` (FK), `mahal_sablonu` (FK - standart mahal tipleri) |
| `YaklasikMaliyetSatiri` | `metraj_kaydi_id` (FK - MetrajKaydi'ne bağla) |
| `PozPlan` | `mahal` (FK, nullable), `metraj_kaydi_id` (FK) |

---

## 17. YENİ EKLENMESİ GEREKENLER

### 17.1 Yapı Sınıfı → Poz Seçimi (IV-A Odaklı)
- **YapiSinifiPozSablonu** modeli: `sinif_kodu` + `poz_id` + `zorunlu_mu` + `varsayilan_miktar_katsayisi`
- IV-A için standart poz listesi (ÇŞİDB/YFK'ten filtrelenmiş)
- Proje oluşturulurken yapı sınıfı seçilince poz şablonu kopyalansın

### 17.2 İmalat Grubu Hiyerarşisi
```
YAPI SINIFI (IV-A)
  ↓
İMALAT GRUBU (Beton, Demir, Kalıp, İşçilik, Tuğla, İzolasyon, Tesisat, ...)
  ↓
POZ (15.110.1001 - Betonarme beton C30)
  ↓
POZ ANALİZİ (C30 Beton 0.45 m³, Çelik 45 kg, ...)
  ↓
MALZEME / İŞÇİLİK / MAKİNE
  ↓
FİYAT (Genel / Proje Özel / Tedarikçi)
```

### 17.3 Proje Bazlı Fiyat/Malzeme Motoru
```
Fiyat Çözümleme Sırası:
1. ProjePozFiyat (proje+poz+yıl) → varsa KULLAN
2. ProjeMalzeme (proje+malzeme) → analizli pozda malzeme fiyatı için KULLAN
3. TedarikciTeklifi (seçili/kazanan) → varsa KULLAN
4. PozFiyat (genel, tenant+poz+yıl) → FALLBACK
5. YfkFiyat (YFK referans) → SON FALLBACK
```

### 17.4 Mahal Bazlı Maliyet Hesaplama
```
PROJE
  ↓
BLOK (A, B, C...)
  ↓
KAT (Zemin, 1, 2, Kat...)
  ↓
MAHAL (Banyo, Mutfak, Salon, Yatak Odası...)
  ↓
MAHAL KALEMLERİ (Seramik, Klozet, Lavabo, Batarya, Kapı, Pencere, Parke, Boya...)
  ↓
POZ / MALZEME / MİKTAR / FİYAT
  ↓
MAHAL MALİYETİ = Σ (KALEM_MİKTARI × ETKİN_FİYAT)
```

### 17.5 Maliyet Hesaplama Motoru Genişletmesi
Yeni servis fonksiyonları:
- `proje_maliyeti_hesapla(proje_id, yil)` → Toplam + kırılım (imalat grubu / poz / malzeme / mahal / m²)
- `mahal_maliyeti_hesapla(mahal_id, yil)` → Mahal detay maliyeti
- `poz_etkin_fiyati(proje_id, poz_id, yil)` → Fiyat çözümleme zinciri
- `malzeme_etkin_fiyati(proje_id, malzeme_id, yil)` → ProjeMalzeme → TedarikciTeklifi → Genel

### 17.6 Raporlama Genişletmesi
- Proje toplam maliyeti (Özet + Detay)
- İmalat grubu maliyeti
- Poz maliyeti (Plan vs Gerçek)
- Malzeme maliyeti (Miktar × Fiyat + Tedarikçi karşılaştırma)
- Mahal maliyeti (Banyo X TL, Mutfak Y TL...)
- m² maliyeti (Toplam / Proje alanı)
- Proje maliyet kırılımı (Excel/PDF export)

---

## 18. ARTIK GEREKSİZ OLANLAR (Kullanılmayacak/Deprecate)

| Bileşen | Durum | Neden |
|---------|-------|-------|
| `YfkPozVersiyon` / `YfkFiyat` / `YfkRayic` / `YfkAnaliz` | **KORU** (Veri kaynağı) | Sistem olmasa da referans veri olarak kalacak |
| `YfkGuncellemeGecmisi` | **KORU** | Audit log |
| Mevcut `PozAnaliz` (global) | **KORU** | Fallback olarak kalacak, proje özel analiz öncelikli |
| Mevcut `PozFiyat` (genel) | **KORU** | Fallback fiyat kaynağı |

> **ÖNEMLİ:** Hiçbir mevcut tablo/veri SİLİNECEK DEĞİL. Yeni yapılar yanına eklenecek, fallback zinciri kurulacak.

---

## 19. GEREKLİ DATABASE MIGRATIONLARI

### 19.1 Yeni Tablolar (Migration Sırası)

```python
# 0021_imalat_grubu.py
ImalatGrubu (kod, ad, ust_grup, sira, is_active)
PozImalatGrubu (poz_id, imalat_grubu_id) - M2M through

# 0022_proje_poz_fiyat.py
ProjePozFiyat (proje_id, poz_id, yil, birim_fiyat, kaynak, is_active)
  Unique: tenant+proje+poz+yil

# 0023_proje_malzeme.py
ProjeMalzeme (proje_id, malzeme_id, ad_override, birim_fiyat, tedarikci_id, is_active)
  Unique: tenant+proje+malzeme

# 0024_proje_poz_analiz.py
ProjePozAnaliz (proje_id, poz_id, satir_no, malzeme_id, malzeme_adi, birim, miktar, birim_fiyat, analiz_tipi)
  Unique: tenant+proje+poz+satir_no+malzeme_id

# 0025_blok.py
Blok (proje_id, kod, ad, sira, is_active)
  Unique: tenant+proje+kod

# 0026_mahal_blok.py
Mahal.blok_id FK (nullable, PROTECT)
Mahal.mahal_sablonu_id FK (nullable)

# 0027_metraj_kaydi.py
MetrajKaydi (proje_id, poz_id, mahal_id, miktar, birim, birim_fiyat, kaynak, aciklama)
  Unique: tenant+proje+poz+mahal (opsiyonel)

# 0028_poz_ek_alanlari.py
Poz.imalat_grubu_id FK (nullable)
Poz.yapi_sinifi_uygunluk JSONField (default=list)
Poz.kategori CharField (choices: ana_yapi/tamamlama/tesisat)

# 0029_proje_ek_alanlari.py
Proje.yapi_sinifi CharField (max_length=10, "IV-A" formatında)
Proje.blok_sayisi, kat_sayisi, toplam_alan_m2

# 0030_yapi_sinifi_poz_sablonu.py
YapiSinifiPozSablonu (sinif_kodu, poz_id, zorunlu_mu, varsayilan_miktar_katsayisi, aciklama)
```

### 19.2 Veri Migrasyon Stratejisi (Mevcut Verileri Koruma)

```python
# Her migration'da RunPython ile:
# 1. Mevcut PozPlan kayıtları → MetrajKaydi'ye kopyala (mahal=null)
# 2. Mevcut YaklasikMaliyetSatiri → MetrajKaydi'ye kopyala (mahal varsa)
# 3. Mevcut PozFiyat → ProjePozFiyat'e kopyala (her proje için, snapshot olarak)
# 4. Mevcut PozAnaliz → ProjePozAnaliz'e kopyala (her proje için)
# 5. Mahal.blok = NULL (mevcut kayıtlar blok'suz kalacak, yeni kayıtlarda zorunlu)
```

---

## 20. GEREKLİ API DEĞİŞİKLİKLERİ

### 20.1 Yeni Endpoint'ler

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/api/v1/construction/imalat-gruplari/` | CRUD | İmalat grupları yönetimi |
| `/api/v1/construction/proje-poz-fiyatlari/` | CRUD | Proje özel poz fiyatları |
| `/api/v1/construction/proje-malemeler/` | CRUD | Proje özel malzemeler/fiyatlar |
| `/api/v1/construction/proje-poz-analizleri/` | CRUD | Proje özel poz analizleri |
| `/api/v1/construction/bloklar/` | CRUD | Blok yönetimi |
| `/api/v1/construction/metraj-kayitlari/` | CRUD | Birleşik metraj kayıtları |
| `/api/v1/construction/yapi-sinifi-poz-sablonlari/` | CRUD | Yapı sınıfı poz şablonları |
| `/api/v1/construction/projeler/{id}/poz-sablonu-uygula/` | POST | Projeye IV-A poz şablonu uygula |
| `/api/v1/construction/projeler/{id}/maliyet-hesapla/` | POST | Proje toplam maliyet hesapla |
| `/api/v1/construction/projeler/{id}/maliyet-kirilimi/` | GET | Maliyet kırılım raporu |
| `/api/v1/construction/mahaller/{id}/maliyet/` | GET | Mahal maliyet detayı |
| `/api/v1/construction/projeler/{id}/m2-maliyeti/` | GET | m² maliyeti |

### 20.2 Mevcut Endpoint Güncellemeleri

| Endpoint | Değişiklik |
|----------|------------|
| `PozPlanViewSet` | `mahal` filtresi, `metraj_kaydi_id` dönüş alanında |
| `YaklasikMaliyetViewSet` | `mahal_listesinden_olustur` → `metraj_kayitlarindan_olustur` |
| `ProjeViewSet` | `poz_sablonu_uygula`, `maliyet_hesapla` action'ları |
| `PozViewSet` | `imalat_grubu`, `yapi_sinifi_uygunluk` alanları |
| `MahalViewSet` | `blok` filtresi, `mahal_sablonu` desteği |

### 20.3 Serializer Güncellemeleri
- `PozPlanSerializer`: `mahal`, `metraj_kaydi_id` alanları
- `ProjeSerializer`: `yapi_sinifi`, `bloklar` nested
- `MahalSerializer`: `blok`, `mahal_sablonu` alanları
- Yeni serializer'lar: `ProjePozFiyatSerializer`, `ProjeMalzemeSerializer`, `ProjePozAnalizSerializer`, `BlokSerializer`, `MetrajKaydiSerializer`, `ImalatGrubuSerializer`, `YapiSinifiPozSablonuSerializer`

---

## 21. GEREKLİ FRONTEND DEĞİŞİKLİKLERİ

### 21.1 Yeni Sayfalar/Bileşenler

| Sayfa/Bileşen | Yol | Açıklama |
|---------------|-----|----------|
| `ImalatGruplariView.vue` | `/insaat/imalat-gruplari` | İmalat grubu CRUD |
| `ProjePozFiyatlariView.vue` | `/insaat/proje-poz-fiyatlari` | Proje özel poz fiyatları |
| `ProjeMalzemelerView.vue` | `/insaat/proje-malemeler` | Proje özel malzemeler |
| `ProjePozAnalizleriView.vue` | `/insaat/proje-poz-analizleri` | Proje özel analizler |
| `BlokYonetimiView.vue` | `/insaat/bloklar` | Blok/Kat/Mahal hiyerarşisi |
| `MetrajKayitlariView.vue` | `/insaat/metraj-kayitlari` | Poz+Proje+Mahal metraj girişi |
| `YapiSinifiPozSablonuView.vue` | `/insaat/yapi-sinifi-poz-sablonu` | IV-A poz şablonu yönetimi |
| `ProjeMaliyetOzetiView.vue` | `/insaat/proje-maliyet-ozeti` | Proje maliyet dashboard |
| `MaliyetKirilimView.vue` | `/insaat/maliyet-kirilim` | Detaylı kırılım raporu |
| `MahalMaliyetView.vue` | `/insaat/mahal-maliyet` | Mahal bazlı maliyet |

### 21.2 Mevcut Sayfa Güncellemeleri

| Sayfa | Güncelleme |
|-------|------------|
| `PozlarView.vue` | İmalat grubu kolonu, filtresi, yapı sınıfı uygunluk badge'i |
| `PozPlanlariView.vue` | Mahal kolonu/filtresi, MetrajKaydi bağlantısı |
| `YaklasikMaliyetView.vue` | Mahal zorunlu, MetrajKaydi entegrasyonu |
| `ProjelerView.vue` | Yapı sınıfı seçimi (IV-A dropdown), blok/kat/alan alanları |
| `MahalListesiView.vue` | Blok hiyerarşisi tree view, mahal şablonu seçimi |
| `PozAnalizleriView.vue` | Proje özel analiz sekmesi |

### 21.3 Yeni TypeScript Tipleri (`types/insaat.ts`)

```typescript
// Yeni eklenecek tipler
export interface ImalatGrubu { id, kod, ad, ust_grup, sira, is_active }
export interface ProjePozFiyat { id, proje, poz, yil, birim_fiyat, kaynak, is_active }
export interface ProjeMalzeme { id, proje, malzeme, ad_override, birim_fiyat, tedarikci, is_active }
export interface ProjePozAnaliz { id, proje, poz, satir_no, malzeme, malzeme_adi, birim, miktar, birim_fiyat, analiz_tipi }
export interface Blok { id, proje, kod, ad, sira, is_active }
export interface MetrajKaydi { id, proje, poz, mahal, miktar, birim, birim_fiyat, kaynak }
export interface YapiSinifiPozSablonu { id, sinif_kodu, poz, zorunlu_mu, varsayilan_miktar_katsayisi }

// Rapor tipleri
export interface ProjeMaliyetOzeti { proje_kodu, yil, toplam_maliyet, m2_maliyet, imalat_grubu_kirilimi, poz_kirilimi, malzeme_kirilimi, mahal_kirilimi }
export interface MahalMaliyeti { mahal_id, mahal_adi, blok_adi, kat, alan_m2, kalemler: MahalKalemMaliyeti[], toplam }
export interface MahalKalemMaliyeti { poz_no, poz_adi, malzeme_adi, miktar, birim, birim_fiyat, tutar, kaynak }
```

### 21.4 API Servis Güncellemeleri (`services/insaatApi.ts`)

```typescript
// Yeni eklenecek API fonksiyonları
export const insaatApi = {
  // ... mevcutlar
  imalatGruplari: crud('/construction/imalat-gruplari/'),
  projePozFiyatlari: crud('/construction/proje-poz-fiyatlari/'),
  projeMalzemeler: crud('/construction/proje-malemeler/'),
  projePozAnalizleri: crud('/construction/proje-poz-analizleri/'),
  bloklar: crud('/construction/bloklar/'),
  metrajKayitlari: crud('/construction/metraj-kayitlari/'),
  yapiSinifiPozSablonlari: crud('/construction/yapi-sinifi-poz-sablonlari/'),
  
  // Proje özel action'lar
  pozSablonuUygula: (projeId, sinifKodu) => post(`/construction/projeler/${projeId}/poz-sablonu-uygula/`, { sinif_kodu: sinifKodu }),
  projeMaliyetHesapla: (projeId, yil) => post(`/construction/projeler/${projeId}/maliyet-hesapla/`, { yil }),
  projeMaliyetKirilimi: (projeId, yil) => get(`/construction/projeler/${projeId}/maliyet-kirilimi/`, { yil }),
  mahalMaliyeti: (mahalId, yil) => get(`/construction/mahaller/${mahalId}/maliyet/`, { yil }),
  m2Maliyeti: (projeId, yil) => get(`/construction/projeler/${projeId}/m2-maliyeti/`, { yil }),
}
```

### 21.5 UI/UX İyileştirmeleri
- **Blok/Kat/Mahal Tree View:** Sol panelde hiyerarşik navigasyon
- **Maliyet Dashboard:** Proje özet kartları (Toplam, m², İmalat grubu, Sapma)
- **Fiyat Karşılaştırma Tablosu:** Genel vs Proje vs Tedarikçi fiyatları yan yana
- **Mahal Maliyet Matrisi:** Satır=Mahal, Sütun=İmalat Grubu, Hücre=Maliyet
- **Sürükle-Bırak Poz Şablonu:** IV-A poz listesini projeye sürükle-bırak

---

## 22. DOSYA BAZLI UYGULAMA PLANI

### BACKEND DOSYALARI

| Dosya | Mevcut Görev | Yapılacak | Neden | Etkilenecek Tablolar | Etkilenecek API | Risk |
|-------|--------------|-----------|-------|---------------------|-----------------|------|
| `construction/models.py` | Tüm modeller | Yeni modeller ekle (ImalatGrubu, ProjePozFiyat, ProjeMalzeme, ProjePozAnaliz, Blok, MetrajKaydi, YapiSinifiPozSablonu), Mevcut modellerde FK/alan ekle | Yeni veri yapısı | Tüm yukarıda listelenenler | Tüm construction API | ORTA - Migration dikkatli yapılmalı |
| `construction/migrations/0021-0030` | - | 10 yeni migration dosyası | Veritabanı şeması | Yukarıdaki tablolar | - | YÜKSEK - Veri kaybı riski, test şart |
| `construction/serializers.py` | Serializer'lar | Yeni serializer'lar, mevcutlara alan ekle | API veri şekli | Yeni modeller + Poz, Proje, Mahal, PozPlan, YaklasikMaliyetSatiri | Tüm construction API | DÜŞÜK - Sadece serializer |
| `construction/views.py` | ViewSet'ler | Yeni ViewSet'ler, mevcutlara action ekle | API endpoint'leri | Yeni modeller + PozPlan, Proje, Mahal, YaklasikMaliyet | Yeni + mevcut endpoint'ler | ORTA - İş mantığı değişikliği |
| `construction/services.py` | Maliyet motoru, raporlar | `proje_maliyeti_hesapla`, `mahal_maliyeti_hesapla`, `poz_etkin_fiyati`, `malzeme_etkin_fiyati`, fiyat çözümleme zinciri | Yeni hesaplama motoru | ProjePozFiyat, ProjeMalzeme, ProjePozAnaliz, PozFiyat, YfkFiyat | Yeni rapor endpoint'leri | YÜKSEK - Çekirdek mantık değişimi |
| `construction/services/analiz.py` | Poz analiz + nakliye | Proje özel analiz desteği | Analiz motoru genişletme | ProjePozAnaliz | PozAnalizViewSet | ORTA |
| `construction/services/mahal_metraj.py` | Mahal metraj + maliyet | MetrajKaydi entegrasyonu | Mahal→Metraj→Maliyet zinciri | MetrajKaydi, YaklasikMaliyetSatiri | YaklasikMaliyetViewSet | ORTA |
| `construction/services/yaklasik_maliyet.py` | Yaklaşık maliyet hesapla/revizyon | Mahal zorunlu, MetrajKaydi bağlantısı | Veri bütünlüğü | YaklasikMaliyetSatiri, MetrajKaydi | YaklasikMaliyetViewSet | ORTA |
| `construction/urls.py` | Router kayıtları | Yeni ViewSet'ler register et | Routing | - | Tüm yeni endpoint'ler | DÜŞÜK |

### FRONTEND DOSYALARI

| Dosya | Mevcut Görev | Yapılacak | Neden | Etkilenecek API | Risk |
|-------|--------------|-----------|-------|-----------------|------|
| `frontend/src/types/insaat.ts` | Tip tanımları | Yeni interface'ler ekle | Type safety | Tüm yeni API | DÜŞÜK |
| `frontend/src/services/insaatApi.ts` | API çağrıları | Yeni fonksiyonlar ekle | API erişimi | Yeni endpoint'ler | DÜŞÜK |
| `frontend/src/views/insaat/ImalatGruplariView.vue` | - | Yeni sayfa | İmalat grubu CRUD | imalatGruplari API | DÜŞÜK |
| `frontend/src/views/insaat/ProjePozFiyatlariView.vue` | - | Yeni sayfa | Proje özel poz fiyatı | projePozFiyatlari API | ORTA |
| `frontend/src/views/insaat/ProjeMalzemelerView.vue` | - | Yeni sayfa | Proje özel malzeme/fiyat | projeMalzemeler API | ORTA |
| `frontend/src/views/insaat/ProjePozAnalizleriView.vue` | - | Yeni sayfa | Proje özel analiz | projePozAnalizleri API | ORTA |
| `frontend/src/views/insaat/BlokYonetimiView.vue` | - | Yeni sayfa (Tree view) | Blok/Kat/Mahal hiyerarşisi | bloklar, mahaller API | ORTA |
| `frontend/src/views/insaat/MetrajKayitlariView.vue` | - | Yeni sayfa | Poz+Proje+Mahal metraj girişi | metrajKayitlari, pozlar, mahaller API | YÜKSEK - Karmaşık form |
| `frontend/src/views/insaat/YapiSinifiPozSablonuView.vue` | - | Yeni sayfa | IV-A poz şablonu yönetimi | yapiSinifiPozSablonlari API | ORTA |
| `frontend/src/views/insaat/ProjeMaliyetOzetiView.vue` | - | Yeni sayfa (Dashboard) | Proje maliyet özeti | projeMaliyetHesapla, projeMaliyetKirilimi API | YÜKSEK - Rapor bileşenleri |
| `frontend/src/views/insaat/MaliyetKirilimView.vue` | - | Yeni sayfa | Detaylı kırılım raporu | projeMaliyetKirilimi API | ORTA |
| `frontend/src/views/insaat/MahalMaliyetView.vue` | - | Yeni sayfa | Mahal bazlı maliyet | mahalMaliyeti API | ORTA |
| `frontend/src/views/insaat/PozlarView.vue` | Poz CRUD | İmalat grubu, yapı sınıfı uygunluk kolonları | Yeni alanlar gösterimi | pozlar API (güncellenmiş) | DÜŞÜK |
| `frontend/src/views/insaat/PozPlanlariView.vue` | Poz planı + raporlar | Mahal filtresi, MetrajKaydi bağlantısı | Mahal bazlı planlama | pozPlanlari API (güncellenmiş) | ORTA |
| `frontend/src/views/insaat/YaklasikMaliyetView.vue` | Yaklaşık maliyet | Mahal zorunlu, MetrajKaydi entegrasyonu | Veri bütünlüğü | yaklasikMaliyet API (güncellenmiş) | ORTA |
| `frontend/src/views/insaat/ProjelerView.vue` | Proje CRUD | Yapı sınıfı dropdown (IV-A), blok/kat/alan | Yeni proje alanları | projeler API (güncellenmiş) | DÜŞÜK |
| `frontend/src/views/insaat/MahalListesiView.vue` | Mahal listesi | Blok tree view, mahal şablonu | Hiyerarşik navigasyon | mahaller, bloklar API | ORTA |
| `frontend/src/views/insaat/PozAnalizleriView.vue` | Poz analiz CRUD | Proje özel analiz sekmesi | Yeni analiz yapısı | pozAnalizleri, projePozAnalizleri API | ORTA |
| `frontend/src/router/index.ts` | Routing | Yeni route'lar ekle | Navigasyon | - | DÜŞÜK |
| `frontend/src/components/` | Bileşenler | TreeView, FiyatKarsilastirmaTablo, MaliyetDashboard, MahalMaliyetMatrisi | Yeni UI bileşenleri | - | ORTA |

---

## 23. UYGULAMA FAZLARI (ÖNERİLEN SIRALAMA)

### FAZ 1: Temel Altyapı (Hafta 1-2)
1. **Migration 0021-0023:** ImalatGrubu, ProjePozFiyat, ProjeMalzeme
2. **Models/Serializers/Views:** Yeni modeller için CRUD
3. **Fiyat Çözümleme Zinciri:** `poz_etkin_fiyati()` servis fonksiyonu
4. **Test:** Mevcut PozPlan/YaklasikMaliyet hâlâ çalışıyor mu?

### FAZ 2: Analiz ve Mahal Yapısı (Hafta 3-4)
1. **Migration 0024-0026:** ProjePozAnaliz, Blok, Mahal.blok
2. **Mahal Tree View Frontend:** Blok/Kat/Mahal hiyerarşisi
3. **Mahal Şablonu:** Standart mahal tipleri (banyo, mutfak, vb.)
4. **Test:** Mahal metraj üretimi hâlâ çalışıyor mu?

### FAZ 3: Metraj Kaydı ve Poz Şablonu (Hafta 5-6)
1. **Migration 0027-0028:** MetrajKaydi, Poz.imalat_grubu/yapi_sinifi_uygunluk
2. **IV-A Poz Şablonu:** YapiSinifiPozSablonu modeli + veri girişi
3. **Projeye Poz Şablonu Uygula:** Proje oluştururken IV-A pozları kopyala
4. **Metraj Kayıt Girişi:** Poz+Proje+Mahal+Miktar tek formda

### FAZ 4: Maliyet Motoru ve Raporlama (Hafta 7-8)
1. **Migration 0029-0030:** Proje ek alanlar, YapiSinifiPozSablonu
2. **Maliyet Hesaplama Motoru:** `proje_maliyeti_hesapla()` + kırılım raporları
3. **Dashboard:** ProjeMaliyetOzetiView, MaliyetKirilimView, MahalMaliyetView
4. **Fiyat Karşılaştırma:** Genel/Proje/Tedarikçi fiyatları tablosu

### FAZ 5: Entegrasyon ve Test (Hafta 9-10)
1. **YaklasikMaliyet ↔ MetrajKaydi** entegrasyonu
2. **PozPlan ↔ MetrajKaydi** entegrasyonu
3. **IFC Import → MetrajKaydi → PozPlan** akışı
4. **E2E Testler:** IV-A proje oluştur → poz şablonu uygula → metraj gir → maliyet hesapla → rapor al

---

## 24. RİSK ANALİZİ VE ÖNLEMLER

| Risk | Etki | Olasılık | Önlem |
|------|------|----------|-------|
| Migration sırasında veri kaybı | YÜKSEK | ORTA | Transaction içinde, backup al, test DB'de dene |
| Fiyat çözümleme zinciri hatası | YÜKSEK | ORTA | Unit testlerle her senaryo test et (fallback sırası) |
| Mevcut raporlar bozulur | YÜKSEK | DÜŞÜK | Mevcut endpoint'leri değiştirme, sadece yeni ekle |
| Frontend/Backend tip uyumsuzluğu | ORTA | ORTA | TypeScript tipleri backend serializer'la senkronize et |
| Performans (büyük projelerde) | ORTA | ORTA | Index'ler ekle, select_related/prefetch_related kullan |
| Kullanıcı adapte olamaz | DÜŞÜK | ORTA | Mevcut menüleri koru, yeni sekme/sayfa olarak ekle |

---

## 25. ÖZET VE SONRAKI ADIM

**Mevcut Sistem Durumu:** 
- ✅ Poz, Malzeme, Fiyat, Analiz, Proje, Mahal, YaklasikMaliyet, PozPlan, S-eğrisi, Gantt, Hakedis, YFK, IFC, Tedarikçi - **TÜMÜ ÇALIŞIYOR**
- ✅ Multi-tenant, snapshot pricing, versioning, audit trail - **MİMARİ SAĞLAM**

**Yeni Hedefe Ulaşmak İçin:**
1. **Proje bazlı fiyat/malzeme/analiz** tabloları ekle (fallback zinciriyle)
2. **İmalat Grubu** hiyerarşisi ekle (PozGrubu yanına)
3. **Blok/Kat/Mahal** hiyerarşisini tamamla
4. **MetrajKaydi** birleşik tablosu ile Poz+Proje+Mahal+Miktar+Fiyat tek yerde
5. **IV-A Poz Şablonu** ile proje başlangıcını hızlandır
6. **Maliyet Motoru** genişlet → kırılım raporları (imalat/poz/malzeme/mahal/m²)

**İLK ADIM:** `DEVAM ET` derseniz **FAZ 1** ile başlarız:
- Migration 0021 (ImalatGrubu), 0022 (ProjePozFiyat), 0023 (ProjeMalzeme)
- Models/Serializers/Views/API için CRUD
- `poz_etkin_fiyati()` servis fonksiyonu (fallback zinciri)
- Mevcut sistem testleri (regresyon kontrolü)

---

**NOT:** Bu rapor sadece analizdir. Hiçbir kod değiştirilmedi, dosya silinmedi, migration çalıştırılmadı. Onayınızla kademeli uygulama başlayacaktır.