# API Endpoint Tasarımı ve Rol Hiyerarşisi

> Kaynak: Benzer bir gayrimenkul/inşaat ERP projesinin route yapısı ve rol
> modeli, bu projenin kapsamına göre sadeleştirilip DRF ViewSet/Router
> yaklaşımına uyarlanmıştır.

---

## 1. Rol Hiyerarşisi

README'deki (`01-GELISTIRME-KURALLARI.md`) örnek roller ile kaynak rapordaki
roller birleştirilerek önerilen hiyerarşi:

| Rol | Yetki Seviyesi |
|---|---|
| **Süper Admin** | Tüm tenant'lara erişim, sistem yönetimi |
| **Tenant Admin** | Tenant yönetimi, kullanıcı CRUD, finansal onaylar |
| **Firma Admin** | Firma bazlı yönetim (tenant altında birden çok firma varsa) |
| **Muhasebe** | Muhasebe modülü tam erişim (fiş, hesap planı, mizan) |
| **Finans** | Kasa/banka, tahsilat/ödeme, cari hareket erişimi |
| **Proje/Emlak Yöneticisi** | Gayrimenkul, sözleşme, cari CRUD |
| **Satış** *(opsiyonel)* | CRM, lead yönetimi, satış raporları |
| **Kullanıcı / Görüntüleyici** | Salt okunur veya sınırlı erişim |

Yetkiler yalnızca frontend'de gizlenmemeli; her endpoint DRF `permission_classes`
ile backend'de de korunmalıdır (bkz. `01-GELISTIRME-KURALLARI.md` Bölüm 5).

---

## 2. Önerilen API Kaynak (Resource) Yapısı

Kaynak projedeki route mount noktaları, bu projenin kapsamına göre
sadeleştirilerek DRF router yapısına uyarlanmıştır:

```
/api/auth/                     → login, refresh, logout, me
/api/users/                    → kullanıcı yönetimi
/api/tenants/                  → tenant yönetimi (yalnızca süper admin)

/api/real-estate/              → gayrimenkul CRUD
/api/real-estate/{id}/photos/  → fotoğraf yükleme
/api/real-estate/{id}/documents/ → tapu/belge yükleme

/api/cari/                     → cari (kiracı/malik/tedarikçi) CRUD
/api/cari/{id}/hareketler/     → cari hesap hareketleri
/api/cari/{id}/bagli-mulkler/  → cariye bağlı gayrimenkuller

/api/rental-contracts/         → kira sözleşmesi CRUD
/api/rental-contracts/{id}/payments/{payment_id}/  → ödeme işaretleme
/api/rental-contracts/{id}/rent-increase/          → kira artışı uygulama
/api/rental-contracts/{id}/terminate/              → sözleşme fesih

/api/invoices/                 → fatura CRUD
/api/finance/accounts/         → kasa/banka hesapları
/api/finance/transactions/     → finansal işlemler
/api/finance/bank-statement/upload/  → banka ekstresi import
/api/finance/trial-balance/    → mizan raporu

/api/accounting/chart-of-accounts/  → hesap planı
/api/accounting/vouchers/           → muhasebe fişleri

/api/reports/kira-gelir/
/api/reports/birim-durum/
/api/reports/gecikmis-tahsilat/
/api/reports/treasury-ozeti/
```

*(Satış CRM modülü eklenirse `/api/leads/` kaynağı bu listeye eklenebilir.)*

---

## 3. API Cevap Formatı

Tüm endpoint'ler tutarlı bir zarf (envelope) formatı döndürmelidir
(bkz. `01-GELISTIRME-KURALLARI.md` Bölüm 6):

```json
{ "success": true, "data": {}, "message": "İşlem başarılı." }
```

```json
{ "success": false, "message": "Muhasebe fişinde borç ve alacak eşit olmalıdır.", "errors": {} }
```

Bu, DRF'de ortak bir `BaseAPIView` / `exception_handler` ile merkezi olarak
uygulanabilir; her view'da tekrar yazılmamalıdır (DRY).

---

## 4. Yetkilendirme Katmanları (Middleware Zinciri)

Kaynak projedeki katmanlı yaklaşım Django/DRF karşılığıyla:

```
1. JWTAuthentication         → token doğrulama, kullanıcı/tenant çözümleme
2. TenantIsolationMiddleware → tüm sorgulara tenant_id filtresi (+ PostgreSQL RLS)
3. DRF permission_classes    → rol bazlı erişim kontrolü (RBAC)
4. Serializer validation     → alan/format doğrulama (TC Kimlik, IBAN, Decimal vb.)
5. Service layer             → iş kuralı doğrulaması (örn. borç=alacak, transaction.atomic)
```
