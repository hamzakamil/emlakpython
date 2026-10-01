# Geliştirme Kuralları — Emlak + Muhasebe + Finans SaaS

> Bu kurallar Django + DRF + PostgreSQL + Vue 3 stack'i için bağlayıcıdır.
> Kod yazan her geliştirici / AI ajanı görev almadan önce bu dosyayı okumalıdır.
> (Kaynak: mevcut bir Node.js → Django migration projesinin kurallarından,
> migration'a özel kısımlar çıkarılarak, sıfırdan kurulacak bu proje için uyarlanmıştır.)

---

## 1. Kod Kalitesi: SOLID ve DRY

- Kod **SOLID** ilkelerine uygun yazılmalıdır:
  - **S**ingle Responsibility — her sınıf/servis tek bir sorumluluğa sahip olmalı.
  - **O**pen/Closed — mevcut kod değiştirilmeden genişletilebilir olmalı.
  - **L**iskov Substitution — alt sınıflar üst sınıfların yerine sorunsuz geçebilmeli.
  - **I**nterface Segregation — gereksiz geniş arayüzler/serializer'lar dayatılmamalı.
  - **D**ependency Inversion — üst seviye modüller somut detaylara değil soyutlamalara bağımlı olmalı.
- **DRY** (Don't Repeat Yourself) ihlal edilmemelidir; tekrar eden mantık ortak
  servis/yardımcı fonksiyonlara taşınmalıdır (bkz. Bölüm 7 — Service Layer).
- Gereksiz abstraction oluşturulmamalı; basit bir problem gereksiz yere
  karmaşıklaştırılmamalıdır (YAGNI ile dengelenmelidir).
- Kod: açık, okunabilir, modüler, test edilebilir, tip güvenli ve güvenli olmalıdır.

---

## 2. Türkçe Dil, Karakter ve UTF-8

Türkçe karakter ve dil desteği **zorunlu gereksinimdir**: `ç Ç ğ Ğ ı İ ö Ö ş Ş ü Ü`

- Projenin tüm katmanlarında (Frontend, Backend, API, PostgreSQL, JSON, HTML,
  CSV, Excel import/export, PDF, e-posta, bildirimler, raporlar, loglar) UTF-8
  kullanılmalıdır.
- Türkçe karakterler hiçbir aşamada ASCII'ye dönüştürülmemelidir
  (`Şahin → Sahin` gibi veri kaybına izin verilmez).
- Türkçe karakter desteği gereken alanlar: ad, soyad, firma/şirket/tenant adı,
  müşteri/tedarikçi/personel adı, il/ilçe/mahalle/sokak, bina/gayrimenkul/proje
  adı, daire/fatura/muhasebe açıklaması, notlar, bildirimler, rapor başlıkları.
- Türkçe büyük/küçük harf dönüşümünde (`i → İ`, `ı → I`, `ş → Ş` ...) İngilizce/
  ASCII odaklı basit `toUpperCase()`/`upper()` davranışına körü körüne
  güvenilmemeli; Türkçe locale-aware yöntemler kullanılmalıdır.
- Arama ve sıralamada `İstanbul / istanbul / ISTANBUL / Istanbul` gibi
  değerlerin aynı kaydı temsil ettiği yerlerde Türkçe locale/collation
  kuralları uygulanmalıdır.
- URL/slug üretimi için Türkçe karakterler teknik slug alanında normalize
  edilebilir (`Erciyes Konut Projesi → erciyes-konut-projesi`) ancak **asıl veri
  alanı orijinal Türkçe haliyle korunmalıdır**.
- Kod içindeki teknik alan adları İngilizce olabilir (`tenant_id`, `created_at`
  vb.) ama kullanıcıya gösterilen/kullanıcının girdiği veriler Türkçe
  karakterleri korumalıdır.

---

## 3. Kişisel Veri ve Format Standartları

Yeni model/form/API/validasyon oluştururken aşağıdaki standartlar otomatik uygulanmalıdır.

| Alan | Kural |
|---|---|
| **T.C. Kimlik No** | Tam 11 hane, yalnızca rakam, boşluk/tire kabul edilmez. Frontend + Backend + API + DB constraint ile doğrulanmalı. Yetkisiz kullanıcıya maskeli gösterilmeli (`123******01`). |
| **Telefon** | Farklı formatlarda girilse de (`0532 123 45 67`, `+90 532 123 45 67` vb.) normalize edilip tek standartta saklanmalı (örn. `905321234567`). Aynı numaranın farklı yazımları mükerrer kayıt oluşturmamalı. UI'da maskeli gösterim (`0532 *** ** 67`); tam hâli sadece yetkili kullanıcıya. |
| **Vergi Kimlik No** | 10 hane, yalnızca rakam. |
| **Vergi Dairesi** | Türkçe karakterler korunmalı, ASCII'ye çevrilmemeli. |
| **Posta Kodu** | 5 hane, yalnızca rakam. |
| **IBAN** | DB'de normalize (`TR000000000000000000000000`), UI'da gruplu (`TR00 0000 ...`). Karşılaştırmada boşluk yok sayılmalı. |
| **Plaka** | Türk plaka formatı desteklenmeli (`38 ABC 123` vb.); karşılaştırmada boşluk/büyük-küçük harf farkı mükerrer kayıt yaratmamalı. |
| **Ad/Soyad** | Türkçe karakterler korunur, baş/son ve çoklu boşluklar temizlenir; anlam değiştirecek ASCII dönüşümü yapılmaz. |

Kişisel veriler (T.C. Kimlik, telefon, IBAN, banka bilgileri, personel
bilgileri) yetkilendirme kurallarına tabi olmalı, gereksiz yere frontend'e
gönderilmemeli, liste ekranlarında mümkün olduğunca maskelenmelidir.
Bu veriler ayrıca gereksiz yere loglanmamalı, debug çıktısına basılmamalıdır
— **veri minimizasyonu** prensibine uyulmalıdır.

---

## 4. Muhasebe ve Finansal Veri Kuralları

- **FLOAT / DOUBLE kesinlikle kullanılmayacaktır.** Para alanlarında Python
  `Decimal` ve PostgreSQL `NUMERIC`/`DECIMAL` kullanılmalıdır (yuvarlama
  hatası kabul edilemez).
- Para birimi ayrıca tutulmalıdır (`TRY`, `USD`, `EUR`, `GBP`).
- **Çift taraflı muhasebe kuralı:** Her muhasebe fişinde `TOPLAM BORÇ =
  TOPLAM ALACAK` olmak zorundadır; dengesiz fiş kaydedilemez. Bu kural sistem
  seviyesinde (serializer/service validation) korunmalıdır.
- Borç, Alacak, Bakiye, Hesap, Fiş, Fiş Satırı, Cari Hareket ilişkileri
  bütünlük içinde korunmalıdır.
- **Silme politikası:** Muhasebe ve finansal kayıtlar (muhasebe fişi, fatura,
  tahsilat, ödeme, cari hareket, banka/kasa hareketi, çek, senet) için
  **fiziksel `DELETE` kullanılmaz.** Bunun yerine: iptal, ters kayıt,
  düzeltme, iade, revizyon mekanizmaları; iptal tarihi, iptal eden kullanıcı
  ve iptal nedeni alanları kullanılmalıdır.
- Bir işlem birden fazla tabloyu etkiliyorsa (örn. tahsilat → cari hareket +
  kasa/banka hareketi + muhasebe fişi + audit log) `transaction.atomic()`
  içinde, hep birlikte veya hiçbiri şeklinde kaydedilmelidir.

---

## 5. Güvenlik ve Multi-Tenant İzolasyonu

- Her kullanıcı yalnızca yetkili olduğu tenant/firma verisini görebilmelidir.
- Her tenant'a ait veri `tenant_id` ile ilişkilendirilmeli; izolasyon
  **application, service, query ve database** seviyelerinin tamamında
  korunmalıdır. PostgreSQL tarafında uygun yerlerde **Row Level Security
  (RLS)** kullanılmalıdır.
- **Authentication:** JWT + Refresh Token. **Authorization:** RBAC + Django
  Permissions. Yetkiler yalnızca frontend'de gizlenmemeli, backend her zaman
  yetki kontrolü yapmalıdır.
- Zorunlu güvenlik konuları: JWT güvenliği, refresh token güvenliği, password
  hashing, CORS, gerektiğinde CSRF, SQL injection koruması, XSS koruması,
  gerektiğinde rate limiting, permission kontrolü, tenant isolation, input/
  output validation, secure headers. Şifreler asla düz metin saklanmaz.
- **Audit log:** Kritik işlemler (kullanıcı/yetki değişiklikleri, finans/
  muhasebe/fatura işlemleri, iptal işlemleri, tenant işlemleri, kritik veri
  güncellemeleri) için kim/ne/hangi tenant/hangi kayıt/eski-yeni değer/ne
  zaman/IP bilgisi tutulmalıdır.
- Production ortamında `DEBUG = False` olmalı; `SECRET_KEY`, `JWT_SECRET`,
  `DATABASE_PASSWORD`, `API_KEY`, `AWS_SECRET` gibi bilgiler kesinlikle
  koda gömülmemeli, environment variable üzerinden yönetilmelidir.

---

## 6. API Kuralları

- API REST prensiplerine uygun olmalı, cevaplar tutarlı yapıda olmalıdır:

```json
// Başarılı
{ "success": true, "data": {}, "message": "İşlem başarılı." }

// Hata
{ "success": false, "message": "Geçersiz T.C. Kimlik No.", "errors": {} }
```

- Hata mesajları Türkçe ve anlaşılır olmalı; kullanıcıya ham teknik hata
  (`TypeError`, `IntegrityError` vb.) gösterilmemelidir.
- Teknik nesne isimleri kod içinde İngilizce (`User`, `Invoice`,
  `AccountingVoucher`), kullanıcı arayüzünde Türkçe karşılıkları
  (`Kullanıcı`, `Fatura`, `Muhasebe Fişi`) kullanılmalıdır.
- API dokümantasyonu OpenAPI/Swagger ile tutulmalıdır.

---

## 7. Business Logic ve Servis Katmanı

- Karmaşık iş kuralları doğrudan view/serializer/component içine
  yığılmamalı; `services/` katmanında tutulmalıdır
  (örn. `create_invoice()`, `post_payment()`, `cancel_invoice()`,
  `create_accounting_voucher()`).
- Bu yaklaşım hem DRY hem Single Responsibility ilkesini destekler.

---

## 8. Veritabanı ve Performans

- PostgreSQL ana veritabanıdır; **Migration KULLANILMAZ.** Şema `db/schema.sql`
  (pg_dump çıktısı) içinde version-controllu tutulur; şema değişiklikleri elle
  SQL ile uygulanır ve bu dosya güncellenir.
- Gerekli alanlarda unique constraint, check constraint, index, foreign key,
  composite index kullanılmalıdır.
- N+1 query problemi oluşturulmamalı; gerektiğinde `select_related()` /
  `prefetch_related()` kullanılmalıdır.
- Büyük listelerde pagination zorunludur; tüm kayıtları gereksiz yere
  frontend'e göndermek yasaktır. Raporlamalar mümkün olduğunca backend/
  database tarafında hesaplanmalıdır.

---

## 9. Frontend Kuralları

- Vue 3 Composition API tercih edilmelidir.
- Form validation, loading/error/empty state, pagination, arama, filtre ve
  yetki kontrolü uygun şekilde uygulanmalıdır.
- Frontend validasyonu **hiçbir zaman** backend validasyonunun yerine geçmez.

---

## 10. CSV / Excel / PDF

- CSV/Excel import-export işlemlerinde Türkçe karakterler (`Ç Ğ İ Ö Ş Ü`)
  bozulmamalıdır; import'ta format, duplicate, zorunlu alan, veri tipi ve
  Türkçe karakter kontrolü yapılmalıdır.
- PDF çıktılarında (fatura, muhasebe raporu, cari ekstre, mizan, bilanço,
  gelir tablosu) Türkçe karakterleri destekleyen font kullanılmalıdır.

---

## 11. Karar Önceliği

Belirsiz durumlarda aşağıdaki öncelik sırası izlenmelidir:

1. Veri güvenliği
2. Finansal doğruluk
3. Tenant izolasyonu
4. Mevcut verinin korunması
5. İş kurallarının korunması
6. Backend doğrulaması
7. Frontend kullanıcı deneyimi
8. Performans
9. Kod estetiği

Kodun daha "güzel" görünmesi uğruna veri güvenliği veya iş mantığı bozulamaz.
