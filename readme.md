# EMLAK ERP — GELİŞTİRME, AI KODLAMA KURALLARI

# 2. Önceden varolan, doğrudan kullanıma yarayan modüllerden farklı bir özellik veya fonksiyonla ilgili bir AI kodlama işi olduğunda, o zaman gereken düzenlemeyi değiştirmeye gerek olur.
# 3. Herhangi bir yeni özellik veya fonksiyon eklenmeden önce, projenin tasarımına, mimariya ve modüllerine dikkat edilmesi gerekir.
# 4. Geliştiriciler, AI kodlamayı yaptıktan sonra projenin iyileştirmesi ve performansını en iyi şekilde sağlayacak şekilde optimize etmesi gerekir.
# 5. Projede AI kullanan tüm modüllerin belgelerine dikkat edilmelidir.
>
> AI ajanı kod yazmaya başlamadan önce bu README'yi okumalı ve burada belirtilen kurallara uymalıdır.

---

# 1. PROJE TANIMI

Bu proje; gayrimenkul, inşaat, cari hesap, finans, muhasebe, personel, kira, tahsilat, ödeme, banka, çek/senet, fatura, stok ve raporlama süreçlerini yönetebilen çok kiracılı (**multi-tenant**) bir ERP/SaaS uygulamasıdır.

Projenin temel hedefleri:

- Güvenli ve ölçeklenebilir ERP altyapısı
- Çoklu firma / tenant desteği
- Finans ve muhasebe işlemlerinde veri bütünlüğü
- Çift taraflı muhasebe mantığı
- Kullanıcı ve rol bazlı yetkilendirme
- Denetlenebilir işlem geçmişi
- Türkçe dil ve karakter desteği
- Güvenli kişisel veri yönetimi
- Modüler ve sürdürülebilir yazılım mimarisi

---

# 2. TÜRKÇE DİL, KARAKTER VE UTF-8 KULLANIMI

Türkçe karakter ve Türkçe dil desteği projenin **zorunlu gereksinimidir**.

Desteklenmesi gereken Türkçe karakterler:

```text
ç Ç
ğ Ğ
ı İ
ö Ö
ş Ş
ü Ü
```

## 2.1 UTF-8

Projenin tüm katmanlarında UTF-8 kullanılmalıdır:

- Frontend
- Backend
- API
- PostgreSQL
- JSON
- HTML
- CSV
- Excel import/export
- PDF
- E-posta
- Bildirimler
- Raporlar
- Loglar

Türkçe karakterler hiçbir aşamada ASCII'ye dönüştürülmemelidir.

Örneğin:

```text
Şahin → Sahin
Çağrı → Cagri
İstanbul → Istanbul
Ümit → Umit
```

şeklinde veri kaybına izin verilmez.

Doğru:

```text
ŞAHİN
ÇAĞRI
İSTANBUL
ÜMİT
```

## 2.2 Kullanıcı verilerinde Türkçe karakterler korunmalıdır

Aşağıdaki bilgiler Türkçe karakterleri desteklemelidir:

- Ad
- Soyad
- Firma adı
- Şirket adı
- Tenant adı
- Müşteri adı
- Tedarikçi adı
- Personel adı
- Adres
- İl
- İlçe
- Mahalle
- Sokak
- Bina adı
- Gayrimenkul adı
- Proje adı
- Daire açıklaması
- Fatura açıklaması
- Muhasebe açıklaması
- Notlar
- Açıklamalar
- Bildirimler
- Rapor başlıkları

## 2.3 Türkçe büyük/küçük harf dönüşümü

Türkçe büyük/küçük harf dönüşümü yapılırken:

```text
i → İ
ı → I
ş → Ş
ğ → Ğ
ç → Ç
ö → Ö
ü → Ü
```

kurallarına dikkat edilmelidir.

Özellikle:

```text
istanbul → İSTANBUL
izmir → İZMİR
ışık → IŞIK
içel → İÇEL
```

dönüşümleri doğru yapılmalıdır.

JavaScript veya Python'un İngilizce/ASCII odaklı basit `toUpperCase()` / `upper()` davranışına körü körüne güvenilmemelidir.

Türkçe locale gerektiren işlemler için uygun locale-aware yöntem kullanılmalıdır.

## 2.4 Teknik alan isimleri

Kod içerisindeki teknik alanlar İngilizce olabilir:

```text
tenant_id
company_id
user_id
created_at
updated_at
invoice_id
```

Ancak kullanıcıya gösterilen metinler ve kullanıcı tarafından girilen veriler Türkçe karakterleri korumalıdır.

---

# 3. VERİ FORMATLARI VE KİŞİSEL BİLGİ STANDARDI

AI ajanları yeni model, form, API, servis veya validasyon oluştururken aşağıdaki veri standartlarını **otomatik olarak uygulamalıdır**.

---

## 3.1 T.C. Kimlik Numarası

T.C. Kimlik No:

- Tam olarak **11 hane** olmalıdır.
- Yalnızca rakamlardan oluşmalıdır.
- Harf kabul edilmemelidir.
- Boşluk kabul edilmemelidir.
- Nokta, tire veya başka özel karakter kabul edilmemelidir.

Örnek:

```text
12345678901
```

Geçersiz:

```text
123 456 789 01
123-456-789-01
1234567890
123456789012
ABC12345678
```

Frontend validasyonu yeterli değildir.

Kontrol:

1. Frontend
2. Backend
3. API
4. Database seviyesinde uygun constraint/index

şeklinde mümkün olan tüm katmanlarda uygulanmalıdır.

T.C. Kimlik No kişisel veri olduğundan yetkisiz kullanıcıya açık şekilde gösterilmemelidir.

Örnek maskeleme:

```text
123******01
```

---

# 4. TELEFON VE CEP TELEFONU STANDARDI

Telefon numaraları farklı formatlarla girilse bile sistem içerisinde normalize edilmelidir.

Örneğin:

```text
0532 123 45 67
05321234567
+90 532 123 45 67
+905321234567
```

aynı telefon numarasını temsil ediyorsa sistem bunu mümkün olduğunca tek standartta değerlendirmelidir.

## 4.1 Veritabanında

Telefon numarasının normalize edilmiş hali saklanmalıdır.

Örneğin:

```text
905321234567
```

veya proje içerisinde belirlenen tek standart format kullanılmalıdır.

Aynı telefon numarasının farklı yazım şekilleri nedeniyle mükerrer kayıt oluşturulmasına izin verilmemelidir.

## 4.2 Kullanıcı arayüzünde

Telefon numarası kullanıcıya okunabilir ve gerektiğinde maskeli gösterilmelidir.

Örnek:

```text
0532 *** ** 67
```

veya:

```text
+90 532 *** ** 67
```

## 4.3 Yetkilendirme

Telefon numarasının tamamı sadece yetkili kullanıcılar tarafından görüntülenebilmelidir.

Liste ekranlarında mümkün olduğunca maskeli gösterim kullanılmalıdır.

---

# 5. AD, SOYAD VE KİŞİSEL İSİM STANDARDI

Ad ve soyad alanlarında:

- Türkçe karakterler korunmalıdır.
- Gereksiz baş/son boşluklar temizlenmelidir.
- Birden fazla boşluk normalize edilmelidir.
- Kullanıcı verisi kaybedilmemelidir.

Kullanıcı girişinde:

```text
Ahmet Şahin
```

girilebilir.

Sistemin standart gösteriminde:

```text
AHMET ŞAHİN
```

kullanılabilir.

Ancak orijinal veri anlamını değiştirecek ASCII dönüşümü yapılmamalıdır.

Yanlış:

```text
AHMET SAHIN
```

Doğru:

```text
AHMET ŞAHİN
```

---

# 6. ŞEHİR, İL, İLÇE VE ADRES STANDARDI

Aşağıdaki alanlarda Türkçe karakterler korunmalıdır:

- İl
- İlçe
- Mahalle
- Köy
- Cadde
- Sokak
- Bulvar
- Bina
- Kapı No
- Daire No
- Adres açıklaması

Örneğin:

```text
İSTANBUL
ANKARA
İZMİR
ŞANLIURFA
KAHRAMANMARAŞ
ÇANAKKALE
MUĞLA
```

gibi değerler doğru şekilde saklanmalı ve gösterilmelidir.

Şehir/il/ilçe gibi standart sözlük alanlarında farklı yazımların mükerrer kayıt oluşturması engellenmelidir.

Örneğin:

```text
istanbul
İstanbul
İSTANBUL
```

aynı standart şehir kaydına karşılık gelmelidir.

---

# 7. VERGİ KİMLİK NUMARASI

Vergi Kimlik No:

- **10 hane** olmalıdır.
- Yalnızca rakamlardan oluşmalıdır.
- Harf ve özel karakter kabul edilmemelidir.

Örnek:

```text
1234567890
```

Format kontrolü hem frontend hem backend tarafında yapılmalıdır.

---

# 8. VERGİ DAİRESİ

Vergi dairesi adlarında Türkçe karakterler korunmalıdır.

Örneğin:

```text
KOCASİNAN VERGİ DAİRESİ
ERCİYES VERGİ DAİRESİ
MİMARSİNAN VERGİ DAİRESİ
```

ASCII dönüşümü yapılmamalıdır.

---

# 9. POSTA KODU

Posta kodu:

- 5 hane
- Yalnızca rakam

olmalıdır.

Örnek:

```text
34000
38000
06000
```

---

# 10. IBAN STANDARDI

IBAN veritabanında normalize edilmiş şekilde tutulmalıdır.

Örneğin:

```text
TR000000000000000000000000
```

kullanılabilir.

Kullanıcı arayüzünde okunabilir format:

```text
TR00 0000 0000 0000 0000 0000 00
```

olabilir.

IBAN karşılaştırılırken boşluklar dikkate alınmamalıdır.

---

# 11. PLAKA STANDARDI

Araç plakalarında Türk plakası formatı desteklenmelidir.

Örnek:

```text
38 ABC 123
34 ABC 1234
06 AB 123
```

Plaka karşılaştırmalarında gereksiz boşlukların ve büyük/küçük harf farklılıklarının mükerrer kayıt oluşturmaması sağlanmalıdır.

---

# 12. PARA VE MUHASEBE VERİLERİ

Para ve muhasebe işlemlerinde:

> **FLOAT / DOUBLE kullanılmayacaktır.**

Para alanlarında:

```text
Python Decimal
PostgreSQL NUMERIC / DECIMAL
```

kullanılmalıdır.

Örneğin:

```text
100.25
1250000.50
```

gibi değerlerde yuvarlama hataları oluşmamalıdır.

Para birimi ayrıca tutulmalıdır:

```text
TRY
USD
EUR
GBP
```

Muhasebe hesaplarında borç ve alacak toplamları matematiksel olarak kesin şekilde hesaplanmalıdır.

---

# 13. ÇİFT TARAFLI MUHASEBE KURALI

Muhasebe fişlerinde:

```text
TOPLAM BORÇ = TOPLAM ALACAK
```

olmak zorundadır.

Örneğin:

```text
Borç  : 100.000 TL
Alacak: 100.000 TL
```

eşit olmalıdır.

Dengesiz muhasebe fişinin kaydedilmesine izin verilmemelidir.

Muhasebe işlemlerinde:

- Borç
- Alacak
- Bakiye
- Hesap
- Fiş
- Fiş satırı
- Cari hareket

ilişkileri korunmalıdır.

---

# 14. KAYIT SİLME POLİTİKASI

Muhasebe ve finansal kayıtlar için fiziksel DELETE kullanılmamalıdır.

Özellikle:

- Muhasebe fişi
- Fatura
- Tahsilat
- Ödeme
- Cari hareket
- Banka hareketi
- Kasa hareketi
- Çek
- Senet
- Finansal işlem

silinmemelidir.

Bunun yerine:

- İptal
- Ters kayıt
- Düzeltme
- İade
- Revizyon
- İptal tarihi
- İptal eden kullanıcı
- İptal nedeni

gibi mekanizmalar kullanılmalıdır.

---

# 15. MEVCUT SİSTEM VE HEDEF SİSTEM

## 15.1 Mevcut sistem

Mevcut proje:

```text
Frontend:
Vue 3
TypeScript
Pinia
Tailwind CSS

Backend:
Node.js
Express.js

Database:
Mevcut veritabanı (legacy)
```

üzerinde çalışmaktadır.

Bu mevcut sistem **silinmeyecek veya bir anda yeniden yazılmayacaktır.**

## 15.2 Hedef sistem

Hedef mimari:

```text
Frontend:
Vue 3
TypeScript
Pinia
Tailwind CSS

Backend:
Python
Django
Django REST Framework

Database:
PostgreSQL

ORM:
Django ORM

Authentication:
JWT + Refresh Token

Authorization:
RBAC + Django Permissions

Multi-Tenancy:
tenant_id + PostgreSQL RLS

API:
REST + OpenAPI / Swagger

Storage:
S3-compatible Object Storage
```

Gerektiğinde:

```text
Redis
Celery
```

kullanılabilir.

Ancak ihtiyaç olmayan teknolojiler projeye eklenmemelidir.

---

# 

# 19. MULTI-TENANT GÜVENLİĞİ

Her kullanıcı yalnızca yetkili olduğu tenant/company verilerini görebilmelidir.

Her tenant'a ait veri:

```text
tenant_id
```

ile ilişkilendirilmelidir.

Tenant izolasyonu:

1. Application level
2. Service level
3. Query level
4. Database level

olarak korunmalıdır.

PostgreSQL tarafında uygun yerlerde:

```text
Row Level Security (RLS)
```

kullanılmalıdır.

Bir tenant'ın başka tenant'ın verisine erişmesi kesinlikle mümkün olmamalıdır.

---

# 20. AUTHENTICATION VE AUTHORIZATION

Authentication:

```text
JWT
+
Refresh Token
```

ile yapılmalıdır.

Authorization:

```text
RBAC
+
Django Permissions
```

kullanmalıdır.

Örnek roller:

```text
Süper Admin
Bayi Admin
Şirket Admin
Muhasebe
Finans
Personel
Kullanıcı
```

Yetkiler sadece frontend üzerinden gizlenmemelidir.

Backend mutlaka yetki kontrolü yapmalıdır.

---

# 21. KİŞİSEL VERİLERİN GÜVENLİĞİ

Kişisel veriler gereksiz şekilde frontend'e gönderilmemelidir.

Özellikle:

- T.C. Kimlik No
- Telefon
- E-posta
- Adres
- IBAN
- Banka bilgileri
- Personel bilgileri

yetkilendirme kurallarına tabi olmalıdır.

Liste ekranlarında mümkün olduğunca maskeleme kullanılmalıdır.

Örneğin:

```text
T.C. Kimlik:
123******01

Telefon:
0532 *** ** 67

IBAN:
TR00 **** **** **** **** **** **
```

---

# 22. AUDIT LOG

Kritik işlemler kayıt altına alınmalıdır.

Örneğin:

```text
Kim yaptı?
Ne yaptı?
Hangi tenant?
Hangi kayıt?
Eski değer?
Yeni değer?
Ne zaman?
IP / teknik bilgiler?
```

gerektiğinde tutulmalıdır.

Özellikle:

- Kullanıcı değişiklikleri
- Yetki değişiklikleri
- Finans işlemleri
- Muhasebe işlemleri
- Fatura işlemleri
- İptal işlemleri
- Tenant işlemleri
- Kritik veri güncellemeleri

audit log kapsamına alınmalıdır.

---

# 23. TRANSACTION KULLANIMI

Bir işlem birden fazla tabloyu etkiliyorsa:

```python
transaction.atomic()
```

kullanılmalıdır.

Örneğin tahsilat işleminde:

```text
Cari hareket
+
Kasa/Banka hareketi
+
Muhasebe fişi
+
Audit log
```

birbirinden bağımsız şekilde kaydedilmemelidir.

Herhangi bir aşamada hata oluşursa işlem uygun şekilde rollback edilmelidir.

---

# 24. BUSINESS LOGIC SERVICE LAYER'DA OLMALI

Karmaşık iş kuralları doğrudan:

- View
- Serializer
- Component
- Controller

içerisine yığılmamalıdır.

İş mantığı mümkün olduğunca:

```text
services/
```

altında veya proje mimarisine uygun service katmanında tutulmalıdır.

Örneğin:

```text
create_invoice()
post_payment()
cancel_invoice()
create_accounting_voucher()
transfer_tenant_data()
```

gibi işlemler service katmanında yönetilmelidir.

---

# 25. API KURALLARI

API:

```text
REST
```

prensiplerine uygun olmalıdır.

API cevapları tutarlı yapıda olmalıdır.

Örneğin:

```json
{
  "success": true,
  "data": {},
  "message": "İşlem başarılı."
}
```

Hatalar:

```json
{
  "success": false,
  "message": "Geçersiz T.C. Kimlik No.",
  "errors": {}
}
```

gibi anlaşılır yapıda dönmelidir.

API hata mesajları Türkçe olabilir ve Türkçe karakterleri doğru desteklemelidir.

---

# 26. FRONTEND KURALLARI

Frontend:

```text
Vue 3
TypeScript
Pinia
Tailwind CSS
```

kullanmalıdır.

Composition API tercih edilmelidir.

Gereksiz framework veya UI kütüphanesi eklenmemelidir.

Frontend'de:

- Form validation
- Loading state
- Error state
- Empty state
- Pagination
- Search
- Filter
- Permission control

uygun şekilde uygulanmalıdır.

Ancak frontend validation hiçbir zaman backend validation'ın yerine geçmez.

---

# 27. VERİTABANI KURALLARI

PostgreSQL ana hedef veritabanıdır.

Django ORM kullanılmalıdır.

`

mekanizması üzerinden kontrollü şekilde yapılmalıdır.

Production veritabanında manuel ve kontrolsüz schema değişiklikleri yapılmamalıdır.

Foreign key ilişkileri doğru kurulmalıdır.

Gerekli alanlarda:

- Unique constraint
- Check constraint
- Index
- Foreign key
- Composite index

kullanılmalıdır.

---

# 28. PERFORMANS

N+1 query problemi oluşturulmamalıdır.

Django tarafında gerektiğinde:

```text
select_related()
prefetch_related()
```

kullanılmalıdır.

Büyük listelerde pagination uygulanmalıdır.

Tüm kayıtları gereksiz yere frontend'e göndermek yasaktır.

Raporlamalar mümkün olduğunca backend/database tarafında hesaplanmalıdır.

---

# 29. ARAMA VE TÜRKÇE SIRALAMA

Türkçe verilerde arama ve sıralama yapılırken:

```text
I
İ
ı
i
```

farkları dikkate alınmalıdır.

Özellikle:

```text
İstanbul
istanbul
ISTANBUL
Istanbul
```

gibi değerlerin aynı mantıksal kaydı temsil etmesi gereken yerlerde Türkçe locale/collation kuralları uygulanmalıdır.

Türkçe karakterler normalize edilirken veri kaybı yaşanmamalıdır.

---

# 30. SLUG VE URL KURALLARI

URL/slug teknik amaçlı normalize edilebilir.

Örneğin:

```text
Erciyes Konut Projesi
```

şuna dönüşebilir:

```text
erciyes-konut-projesi
```

Ancak bu dönüşüm yalnızca teknik slug içindir.

Asıl veri:

```text
Erciyes Konut Projesi
```

olarak korunmalıdır.

Slug oluşturmak için Türkçe karakterlerin orijinal veri alanından silinmesi yasaktır.

---

# 31. CSV / EXCEL IMPORT-EXPORT

CSV ve Excel işlemlerinde Türkçe karakterler korunmalıdır.

Özellikle Excel ile açılan CSV dosyalarında:

```text
Ç
Ğ
İ
Ö
Ş
Ü
```

karakterlerinin bozulmaması sağlanmalıdır.

Örnek:

```text
Şirket Adı
Çalışan Adı
İl
İlçe
Açıklama
```

verileri export/import sonrasında aynı şekilde kalmalıdır.

Import işlemlerinde:

- Format validation
- Duplicate kontrolü
- Required field kontrolü
- Türkçe karakter kontrolü
- Veri tipi kontrolü

yapılmalıdır.

---

# 32. PDF VE RAPORLAR

PDF oluşturulurken Türkçe karakterleri destekleyen font kullanılmalıdır.

Aşağıdaki karakterler PDF'de bozulmamalıdır:

```text
ç Ç ğ Ğ ı İ ö Ö ş Ş ü Ü
```

Özellikle:

- Fatura
- Muhasebe raporu
- Cari ekstre
- Mizan
- Bilanço
- Gelir tablosu
- Personel raporu
- Kira raporu

gibi çıktılar test edilmelidir.

---

# 33. AI KODLAMA AJANLARI İÇİN ZORUNLU KURAL

AI ajanı herhangi bir kod değişikliği yapmadan önce:

1. Mevcut dosyaları incelemeli.
2. Mevcut mimariyi anlamalı.
3. Mevcut model ve API ilişkilerini kontrol etmeli.
4. Mevcut veri yapısını anlamalı.
5. Mevcut çalışan özelliği gereksiz yere değiştirmemeli.

AI ajanı:

> **“Bu proje sıfırdan yapılıyor.” varsayımıyla hareket edemez.**

---

# 34. TOPLU REWRITE YASAKTIR

Aşağıdaki işlemler açık onay olmadan yapılamaz:

- Projeyi sıfırdan yazmak
- Backend'i komple silmek
- Frontend'i komple silmek
- Mevcut veritabanını silmek
- Mevcut modelleri topluca değiştirmek
- Mevcut API'leri topluca kaldırmak
- Kullanıcı verilerini silmek
- Tenant verilerini silmek
- Finansal kayıtları silmek

Değişiklikler mümkün olduğunca:

```text
küçük
kontrollü
modüler
geri alınabilir
```

olmalıdır.

---

# 35. NODE.JS / EXPRESS GEÇİŞ SÜRECİNDE

Mevcut:

```text
Node.js
Express.js
```


Bunlar:

> **yasak teknoloji değildir.**

Bunlar mevcut sistemin legacy/current bileşenleridir.

Ancak yeni ana backend mimarisi:

```text
Python
Django
Django REST Framework
PostgreSQL
```

olmalıdır.

--

# 36. YENİ MODÜL GELİŞTİRME KURALI

Yeni ve büyük bir modül geliştiriliyorsa öncelikle hedef mimariye uygun geliştirilmelidir:

```text
Django
+
PostgreSQL
```

Mevcut Node/Express sistemine yeni bağımlılık eklemek için geçerli bir teknik gerekçe bulunmalıdır.

AI ajanı mevcut sistemi sırf kolay olduğu için büyütmemelidir.

---


# 39. BACKUP KURALI

büyük schema değişikliğinden önce backup alınmalıdır.

Backup alınmadan:

- Database temizliği
- Model değişikliği
- Toplu veri güncellemesi


yapılmamalıdır.

---

# 40. TEST KURALLARI

Backend:

```text
Pytest
Django Test
```

Frontend:

```text
Vitest
Vue Test Utils
```

kullanmalıdır.

Özellikle aşağıdaki senaryolar test edilmelidir:

- Login
- Logout
- Tenant izolasyonu
- Yetki kontrolü
- Kullanıcı oluşturma
- Kullanıcı güncelleme
- T.C. Kimlik validation
- Telefon validation
- Türkçe karakter
- Büyük/küçük harf dönüşümü
- Cari oluşturma
- Fatura
- Tahsilat
- Ödeme
- Muhasebe fişi
- Borç/alacak eşitliği
- API hata yönetimi

---

# 41. KOD KALİTESİ

Kod:

- Açık
- Okunabilir
- Modüler
- Test edilebilir
- Tip güvenli
- Güvenli
- Gereksiz tekrar içermeyen

yapıda olmalıdır.

Gereksiz abstraction oluşturulmamalıdır.

Basit bir problem gereksiz şekilde karmaşıklaştırılmamalıdır.

---

# 42. DEĞİŞİKLİK YAPMADAN ÖNCE AI AJANI ŞUNLARI KONTROL ETMELİ

Her görev öncesinde:

```text
1. Bu özellik mevcut mu?
2. Hangi dosyada?
3. Hangi model kullanılıyor?
4. Hangi API kullanılıyor?
5. Mevcut veritabanı mı PostgreSQL mi kullanıyor?
6. Mevcut kullanıcı/tenant verisine etkisi var mı?
7. Finansal kayıtları etkiliyor mu?
8. Türkçe karakter/veri standardına etkisi var mı?
9. Geriye dönük uyumluluk bozulacak mı?
```

soruları değerlendirilmelidir.

---

# 43. AI AJANININ KENDİLİĞİNDEN YAPMAMASI GEREKENLER

Açık talimat olmadan:

```text
Mevcut veritabanını silme
Node.js backend'i silme
Express API'lerini topluca kaldırma
Frontend'i yeniden yazma
Kullanıcıları silme
Tenantları silme
Finansal kayıtları silme
Muhasebe kayıtlarını silme
Production verisini değiştirme
.env değerlerini değiştirme
Database'i sıfırlama
```

yasaktır.

---

# 44. KİŞİSEL VERİLERDE AI KURALI

AI ajanı kullanıcı verilerini işlerken:

- T.C. Kimlik No'yu gereksiz yere loglamamalı
- Telefon numarasını gereksiz yere loglamamalı
- IBAN'ı gereksiz yere loglamamalı
- Kişisel verileri debug çıktısına basmamalı
- API response'larında gereksiz kişisel veri göndermemeli
- Liste ekranlarında hassas verileri maskelemeli

ve mümkün olduğunca **veri minimizasyonu** prensibine uymalıdır.

---

# 45. UI DİL STANDARDI

Kullanıcı arayüzü Türkçe ise:

- Butonlar
- Menü isimleri
- Form alanları
- Hata mesajları
- Başarı mesajları
- Modal başlıkları
- Tablo başlıkları
- Filtreler
- Raporlar
- Bildirimler

tutarlı Türkçe kullanılmalıdır.

Örneğin:

```text
Kaydet
Güncelle
İptal
Sil
Düzenle
Ara
Filtrele
Temizle
Yeni Kayıt
Detay
Açıklama
```

gibi ifadeler aynı uygulama içerisinde tutarlı kullanılmalıdır.

---

# 46. TEKNİK İSİMLENDİRME

Kod içerisinde İngilizce teknik isimlendirme kullanılabilir:

```text
User
Tenant
Company
Invoice
Customer
Payment
Receipt
AccountingVoucher
```

Ancak kullanıcı arayüzünde bunların Türkçe karşılıkları kullanılmalıdır:

```text
Kullanıcı
Firma
Fatura
Cari
Tahsilat
Makbuz
Muhasebe Fişi
```

---

# 47. LOG VE HATA MESAJLARI

Loglarda teknik bilgiler İngilizce olabilir.

Ancak kullanıcıya gösterilen hata mesajları anlaşılır olmalıdır.

Örneğin:

```text
Geçersiz T.C. Kimlik No.
Telefon numarası 10 haneli olmalıdır.
Bu kullanıcı için yetkiniz bulunmamaktadır.
Bu kayıt başka bir tenant'a aittir.
Fatura kaydedilemedi.
Muhasebe fişinde borç ve alacak eşit olmalıdır.
```

gibi mesajlar tercih edilmelidir.

Kullanıcıya:

```text
TypeError
NullReferenceException
IntegrityError
```

gibi ham teknik hata mesajları gösterilmemelidir.

---

# 48. GÜVENLİK

Aşağıdaki konular zorunludur:

- JWT güvenliği
- Refresh token güvenliği
- Password hashing
- CORS
- CSRF gerektiği yerlerde
- SQL injection koruması
- XSS koruması
- Rate limiting gerektiği yerlerde
- Permission kontrolü
- Tenant isolation
- Input validation
- Output validation
- Secure headers

Şifreler kesinlikle düz metin olarak saklanmamalıdır.

---

# 49. PRODUCTION KURALLARI

Production ortamında:

```text
DEBUG = False
```

olmalıdır.

Secret bilgiler Git'e gönderilmemelidir.

Örneğin:

```text
SECRET_KEY
JWT_SECRET
DATABASE_PASSWORD
API_KEY
AWS_SECRET
```

gibi değerler source code içine yazılmamalıdır.

Environment variable kullanılmalıdır.

---

# 50. DEPLOYMENT HEDEFİ

Hedef deployment mimarisi:

```text
Ubuntu VPS
Docker
Nginx
PostgreSQL
Django
Vue
```

olmalıdır.

Gerektiğinde:

```text
Redis
Celery
S3
```

eklenebilir.

Ancak gereksiz servisler çalıştırılmamalıdır.

---

# 51. ÖNCELİK SIRASI

AI ajanı karar verirken aşağıdaki öncelik sırasını kullanmalıdır:

```text
1. Veri güvenliği
2. Finansal doğruluk
3. Tenant izolasyonu
4. Mevcut verinin korunması
5. İş kurallarının korunması
6. 
7. Backend doğrulaması
8. Frontend kullanıcı deneyimi
9. Performans
10. Kod estetiği
```

Kodun daha güzel görünmesi için veri güvenliği veya mevcut iş mantığı bozulamaz.

---

# 52. İNŞAAT MODÜLÜ — YAPI SINIFI (IV-A) VE POZ / MALZEME YÖNETİMİ

## 52.1 Amaç ve kapsam

Bu bölüm, projeye eklenecek **İnşaat** modülünü tanımlar. Modülün amacı; bir inşaat
projesinin (özellikle **IV. Sınıf (A) Grubu** yapı ölçeğindeki projelerin) maliyet,
metraj, poz, malzeme ve teknik şartname bilgilerini tek bir yapı üzerinde yönetmektir.

Bu bölüm, üst bölümlerde tanımlanan genel kuralları (Türkçe karakter desteği, çift
taraflı muhasebe, Decimal zorunluluğu, fiziksel DELETE yasağı, tenant izolasyonu vb.)
**geçersiz kılmaz**; İnşaat modülü de bu kurallara tabidir. Poz/malzeme/hakediş gibi
mali sonucu olan kayıtlar da 14. bölümdeki silme politikasına (iptal/ters kayıt) tabidir.

## 52.2 Yapı sınıfı ve grubu kavramı

Çevre, Şehircilik ve İklim Değişikliği Bakanlığı (ÇŞİDB), her yıl **"Yapı Yaklaşık
Birim Maliyetleri Tebliği"** ile yapıları **I. Sınıf → V. Sınıf** arasında, her sınıf
içinde de **A, B, C, D, E** grupları halinde sınıflandırır. Sınıf/grup; yapının
karmaşıklığına, kullanılan malzeme/işçilik kalitesine, taşıyıcı sistem türüne ve
(konutlarda) yapı yüksekliğine göre belirlenir ve TL/m² cinsinden bir "yapı yaklaşık
birim maliyeti" üretir.

**IV. Sınıf (A) Grubu**, ihtisas gerektiren, orta-üst nitelikli yapıları kapsar. Tipik
örnekler:

- Liman binaları
- Konferans/spor salonu gibi ek tesisleri olan büyük okul yapıları
- Poliklinikler (hastane hariç)
- Vergi dairesi, ilçe hükümet konağı gibi idari yapılar
- 1-2 yıldızlı oteller, yüksekokul yapıları
- Yapı yüksekliği 30,50 m'nin altındaki apartmanlar/iş merkezleri

Sistemde `YapiSinifi` bir **sabit sözlük (lookup) tablosu** olarak tutulmalıdır (I-A …
V-E), her yıl güncellenen tebliğ verisiyle (yıl, sınıf/grup kodu, TL/m² birim maliyet)
versiyonlanmalıdır. **Bu tabloya hard-coded sabit değer gömülmemelidir**; tebliğ yıllık
değiştiği için `YapiSinifiBirimMaliyet(yil, sinif_kodu, tl_m2)` şeklinde yıl bazlı
kayıt tutulmalı ve proje, hangi yılın tebliğine göre hesap yapıldığını saklamalıdır.

> **Not:** Yapı sınıfı/grubu, projeye özgü mimari ve statik verilere göre değişebilir;
> AI ajanı bir projeyi otomatik olarak "IV-A" gibi tek bir sınıfa sabitlememeli, bu
> alanı kullanıcı/mühendis onayına açık bırakmalıdır.

## 52.3 Poz veri modeli (ÇŞİDB birim fiyat entegrasyonu)

Türkiye'de kamu ve özel sektör yapım maliyeti, **ÇŞİDB (eski adıyla Bayındırlık/Çevre
ve Şehircilik Bakanlığı) Birim Fiyat Pozları** üzerinden hesaplanır. Poz numaraları
`KK.GGG.SSSS` biçiminde 3 bölmelidir (örnek gerçek pozlar):

```text
15.110.1001  → Kazı (makine ile, yumuşak zeminde)
15.245.1002  → 250 gr/m² geotekstil keçe serilmesi
15.250.1001  → 200 kg çimento dozlu tesviye tabakası
15.275.1102  → Kireç/çimento karışımı iç cephe sıvası
15.300.1001  → Ahşap oturtma çatı (tahta kaplamalı)
15.315.1003  → PVC yağmur borusu
```

Veri modelinde önerilen çekirdek tablolar:

```text
Poz
 - poz_no (unique, örn: "15.275.1102")
 - kitap / defter (İnşaat, Mekanik Tesisat, Elektrik Tesisat, Peyzaj vb.)
 - tanim (Türkçe açıklama, Türkçe karakter korunur)
 - birim (m2, m3, kg, adet, m, ton ...)
 - kaynak_kurum ("ÇŞİDB", "İSKİ", "Bakanlık - Elektrik" vb.)
 - yil (poz fiyatının ait olduğu yıl)
 - birim_fiyat (Decimal, FLOAT yasak — bkz. bölüm 12)
 - analiz_detayi (malzeme/işçilik/ekipman kırılımı, opsiyonel)
 - teknik_sartname_ref (bkz. 52.5)
 - aktif (poz güncel mi, yoksa eski yıl poz numarası mı)

PozGrubu
 - kod, ad (örn: "04-Kazı ve Zemin", "15-Kaba İnşaat", "16-İnce İnşaat",
   "17-Mekanik Tesisat", "18-Elektrik Tesisat", "19-Dış Cephe/Yalıtım",
   "20-Peyzaj ve Çevre Düzenleme")

Malzeme
 - kod, ad, birim, standart_ref (TS/TS EN no)
 - tedarikci (Cari ile ilişkili, bkz. mevcut Cari modeli)

PozMalzemeIliskisi (BOM — Bill of Materials)
 - poz_id → Poz
 - malzeme_id → Malzeme
 - miktar (Decimal, poz birimine göre malzeme sarfiyatı)

ProjeMetraj
 - proje_id → Project (mevcut Gayrimenkul/Proje modeliyle ilişkili)
 - poz_id → Poz
 - metraj_miktari (Decimal)
 - birim_fiyat_snapshot (o anki poz fiyatının donmuş kopyası — fiyat
   güncellemesi geçmiş projeleri değiştirmemeli)
 - tutar (metraj_miktari * birim_fiyat_snapshot)
```

`ProjeMetraj.birim_fiyat_snapshot` alanı **zorunludur**: Poz tablosundaki fiyat her yıl
değiştiği için, geçmişte onaylanmış bir maliyet kaydı, poz fiyatı güncellendiğinde
sessizce değişmemelidir (bkz. bölüm 12 — para/muhasebe verilerinde kesinlik ilkesi).

## 52.4 IV-A yapı sınıfıyla örtüşen başlıca poz grupları

Aşağıdaki gruplar, IV. Sınıf (A) Grubu ölçeğindeki bir yapının (asansörlü, kaloriferli/
mekanik tesisatlı, orta-üst nitelikte) tipik iş kalemi (poz) kategorileridir. Bunlar
gerçek poz listesi değil, modülün **kapsayacağı poz grubu iskeletidir**; gerçek poz
numaraları ve fiyatları projede ÇŞİDB'nin güncel "Yapı Yaklaşık Birim Maliyetleri" ve
"Birim Fiyat ve Tarifleri" tebliğlerinden (yıllık Resmî Gazete yayınları) içe
aktarılmalıdır (bkz. yol haritası, Faz 1 — "ÇŞİDB poz parser").

**A) Zemin ve Kazı İşleri**
- Zemin etüdü/sondaj kaydı (harici rapor referansı olarak, metraja girmez)
- Hafriyat/kazı (makine ile, el ile, derinlik zammı)
- Dolgu, sıkıştırma, tesviye
- Geotekstil/drenaj

- Temel betonu, radye/tekil/sürekli temel
- Kolon, kiriş, perde, döşeme betonarme imalatı
- Demir (nervürlü inşaat çeliği) işçiliği ve donatı
- Beton pompası ile dökme, kür, kalıp işleri
- Su yalıtımlı bodrum perde/temel detayları

**C) Duvar, Sıva, Şap**
- Tuğla/gazbeton duvar örgüsü
- İç/dış cephe sıvası (kireç/çimento harcı)
- Şap (tesviye betonu), zemin hazırlığı

**D) Çatı ve Yalıtım**
- Ahşap/çelik çatı taşıyıcı sistemi
- Isı yalıtımı (mantolama), su yalıtımı (membran)
- Çatı örtüsü (kiremit, membran, metal)

**E) İnce İşler**
- Seramik/fayans, doğal taş, laminat/parke kaplama
- İç/dış kapı-pencere doğraması (PVC, alüminyum, ahşap)
- Boya-badana, alçı sıva, asma tavan
- Merdiven, korkuluk, metal işleri

**F) Mekanik Tesisat**
- Sıhhi tesisat (temiz su, pis su, yağmur suyu)
- Isıtma/soğutma tesisatı (kombi/kalorifer, klima altyapısı)
- Doğalgaz iç tesisatı
- Yangın tesisatı (sprinkler, hidrant) — IV-A grubunda sıkça zorunlu
- Asansör altyapısı (IV-A grubu tipik olarak asansörlü yapıları kapsar)

**G) Elektrik Tesisatı**
- Kuvvetli akım (aydınlatma, priz, pano)
- Zayıf akım (data, TV, diyafon, yangın algılama)
- Topraklama, paratoner (yıldırımdan korunma tesisatı)
- Jeneratör/UPS altyapısı (özellikle idari/ticari IV-A yapılarında)

**H) Dış Cephe ve Çevre Düzenleme**
- Dış cephe kaplaması (taş, kompozit panel, sıva)
- Bahçe duvarı, ihata duvarı
- Peyzaj, sert/yumuşak zemin düzenlemesi, otopark

Her grup, sisteme `PozGrubu` olarak tanımlanmalı; her proje için bu gruplar üzerinden
**metraj → poz → malzeme → maliyet** zinciri kurulmalıdır.

## 52.5 Malzeme listesi (BOM) ve teknik şartname ilişkisi

Her poz, bir veya birden fazla malzeme ile ilişkilendirilir (`PozMalzemeIliskisi`).
Malzeme kartları, ilgili **Türk/Avrupa standardına (TS / TS EN)** referans vermelidir;
bu alan zorunlu değildir ama doluysa raporlarda/şartname belgelerinde gösterilir.
Sık kullanılan örnek referanslar (proje teknik şartnamesi hazırlanırken kullanılabilir):

```text
TS EN 206        → Beton (özellik, performans, imalat, uygunluk)
TS 500            → Betonarme yapıların tasarım ve yapım kuralları
TBDY (2018)       → Türkiye Bina Deprem Yönetmeliği
TS 825            → Binalarda ısı yalıtım kuralları
TS EN 998-1/998-2 → Örgü/sıva harcı şartnameleri
TS EN 1996        → Yığma yapılar tasarımı (Eurocode 6)
TS EN 13501       → Yapı malzemelerinde yangın sınıflandırması
TS EN 14351       → Pencere ve kapı performans şartnameleri
TS 12514           → Doğalgaz iç tesisat kuralları
```

AI ajanı bu standart numaralarını **sabit ve değişmez veri gibi kod içine gömmemeli**;
`Malzeme.standart_ref` alanında serbest metin/veri olarak tutmalı, ihtiyaç halinde
güncel mevzuata göre kullanıcı tarafından düzenlenebilmelidir.

## 52.6 AI ajanı için İnşaat modülüne özel kurallar

1. Poz/malzeme fiyatlarını **asla tahmini/uydurma değerle** doldurmamalı; ya kullanıcının
   sağladığı içe aktarma (import) verisinden almalı ya da alanı boş/manuel giriş olarak
   bırakmalıdır.
2. `YapiSinifi` ve poz fiyatları **yıl bazlı** olduğundan, "güncel" fiyat varsayımıyla
   sabit kod yazılmamalıdır; her zaman `yil` parametresi açık olmalıdır.
3. Poz/metraj/hakediş kayıtları finansal sonuç doğurduğundan bölüm 12-14'teki
   (Decimal zorunluluğu, çift taraflı muhasebe, silme yerine iptal) kurallara tabidir.
4. Hakediş (bölüm 52 kapsamındaki iş takibi) onaylandığında, ilgili tutar mevcut
   Muhasebe Fişi / Cari Hareket modelleriyle entegre edilmeli, ayrı bir "gölge muhasebe"
   oluşturulmamalıdır.
5. "4A yapı sınıfı" gibi kullanıcı ifadeleri, teknik olarak **IV. Sınıf (A) Grubu**
   anlamına geldiğinden, arayüz metinlerinde tutarlılık için resmî `IV-A` gösterimi
   tercih edilmeli, kullanıcı girişlerinde her iki yazımı da (4A / IV-A) eşleştiren bir
   normalize fonksiyonu kullanılmalıdır.

---

# 53. SON KURAL

Bu README'deki kurallar proje için bağlayıcıdır.

AI ajanı:

> **Mevcut sistemi anlamadan değiştirmemeli.**

> **Mevcut veriyi riske atmamalı.**


> **Node.js / Express mevcut sistem olduğu için bunları izinsiz silmemeli.**

> **Hedef backend mimarisinde Django + Django REST Framework + PostgreSQL kullanmalıdır.**

> **Türkçe karakterleri hiçbir aşamada bozmamalıdır.**

> **T.C. Kimlik No, telefon, IBAN ve diğer kişisel veriler için belirlenen format ve maskeleme kurallarına uymalıdır.**

> **Ad, soyad, şehir, ilçe ve diğer Türkçe bilgilerde Türkçe büyük/küçük harf kurallarını doğru uygulamalıdır.**

> **Finansal ve muhasebesel verilerde kesinlik ve veri bütünlüğünü korumalıdır.**

> **Silme yerine iptal/düzeltme/ters kayıt yaklaşımını kullanmalıdır.**

>
Bu proje **sıfırdan yazılacak bir projedir**.

Mimari:
```text
BAŞTAN TASARIM
     ↓
DJANGO + DJANGO REST FRAMEWORK + POSTGRESQL
     ↓
MODÜLER MİMARİ
     ↓
PROD'A ÇIKMIŞ PROJE
```

şeklinde ilerleyecektir.

**Veri kaybı, tenant izolasyonunun bozulması, finansal tutarsızlık, Türkçe karakter kaybı veya kontrolsüz toplu rewrite kabul edilemez.**