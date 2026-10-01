# Veri Modeli ve İlişkiler — Django Uyarlaması

> Kaynak: Benzer bir gayrimenkul/inşaat ERP projesinin mimari analiz raporundaki
> veri modeli, bu projenin Django + PostgreSQL stack'ine uyarlanmıştır. Burada
> kavramsal model ve ilişkiler Django modelleri (`app/models.py`) düzeyinde
> referans olarak sunulmuştur.

---

## 1. Multi-Tenancy Yaklaşımı

- **Single database + tenant isolation** (database-per-tenant değil).
- Her modelde `tenant_id` (FK → `Tenant`) alanı zorunlu olmalıdır. Bunu
  tekrarlamamak için ortak bir soyut model kullanılabilir:

```python
class TenantAwareModel(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT)

    class Meta:
        abstract = True
```

- Tenant izolasyonu bir middleware / DRF permission + queryset filtresi ile
  her istekte otomatik uygulanmalı, ayrıca PostgreSQL RLS ile veritabanı
  seviyesinde de garanti altına alınmalıdır (bkz. `01-GELISTIRME-KURALLARI.md`).
- JWT token içinde `tenant_id` taşınmalı; kullanıcı başka tenant'ın verisine
  hiçbir koşulda erişememelidir.
- Tenant başına limitler tanımlanabilir: `max_users`, `max_projects`,
  `max_storage_gb`.

---

## 2. Model Grupları ve Referans Listesi

Referans alınan projede 33 model bulunuyordu; bunlar işlevlerine göre
gruplanmış ve bu projenin kapsamına (Emlak + Muhasebe + Finans) göre
önceliklendirilmiştir.

### 2.1 Çekirdek / Kimlik

| Model | Amaç |
|---|---|
| `Tenant` | Çok kiracılı yapının kök entity'si |
| `Company` (Firma) | Tenant altında bir veya birden çok firma (gerekirse) |
| `User` | Sistem kullanıcıları, rol tabanlı |
| `Notification` | Sistem bildirimleri |

### 2.2 Gayrimenkul / Emlak

| Model | Amaç |
|---|---|
| `RealEstate` (Gayrimenkul) | Bina, blok, kat, daire no, m², tapu bilgileri; durum: `available \| rented \| sold \| reserved \| maintenance` |
| `Project` (Proje) *(opsiyonel)* | İnşaat/geliştirme projeleri, gayrimenkulleri gruplamak için |
| `Unit` (Birim/Daire) *(opsiyonel)* | Satış odaklı birim yönetimi, `RealEstate` ile birlikte veya onun yerine kullanılabilir |
| `RentalContract` (Kira Sözleşmesi) | Kiracı, mülk, başlangıç/bitiş tarihi, aylık kira, depozito, artış tipi, ödeme periyodu |
| `RentalPaymentSchedule` (Ödeme Planı) | Sözleşmeye bağlı dönemsel ödeme kalemleri (vade, tutar, ödendi mi, gecikme faizi) |

### 2.3 Cari / Finans

| Model | Amaç |
|---|---|
| `Cari` | Kiracı, malik, tedarikçi, taşeron vb. taraf; bireysel/kurumsal |
| `CariHareket` | Cari hesap hareketleri (borç/alacak) |
| `Invoice` (Fatura) | `direction: out \| in`, `status: draft → issued → sent → paid → overdue → cancelled`, KDV hesaplama |
| `TreasuryAccount` (Kasa/Banka Hesabı) | `type: bank \| cash \| credit_card \| check \| ...`, IBAN, hesap kodu, para birimi |
| `Transaction` (Finansal İşlem) | `type: income \| expense \| transfer`, tutar, hesap, cari |
| `BankMovement` (Banka Hareketi) | Excel/ekstre import ile gelen hareketler, eşleştirme durumu |
| `FinanceReminder` (Finansal Hatırlatıcı) | Fatura/ödeme/kredi kartı vade hatırlatıcıları |

### 2.4 Muhasebe

| Model | Amaç |
|---|---|
| `ChartOfAccount` (Hesap Planı) | `account_code`, `account_title`, `account_type`, `level` |
| `AccountingVoucher` (Muhasebe Fişi) | Çift kayıt; `voucher_no`, `voucher_date`, satırlar (`debit`/`credit`), `total_debit == total_credit` zorunlu |
| `AccountingVoucherLine` (Fiş Satırı) | Hesap kodu, borç, alacak, açıklama |

### 2.5 Satış CRM *(opsiyonel modül)*

| Model | Amaç |
|---|---|
| `Lead` (Potansiyel Müşteri) | `source`, `status: new → contacted → qualified → proposal → negotiation`, ilgilendiği birimler |
| `LeadActivity` | Görüşme/toplantı/e-posta/ziyaret notları |

### 2.6 Belge / Medya / Hukuki

| Model | Amaç |
|---|---|
| `ProjectDocument` (Belge) | Tapu, sözleşme, kimlik vb.; versiyonlama + onay akışı |
| `ProjectPhoto` (Fotoğraf) | Gayrimenkul/proje fotoğrafları |
| `LegalCase` (Hukuki Takip) | Dava/icra takibi, ilgili cari |

---

## 3. Temel İlişki Diyagramı (Kavramsal)

```
Tenant (Kök)
│
├── User [N:1] ──► rol: super_admin | tenant_admin | firma_admin |
│                  muhasebe | finans | proje_yoneticisi | satis | kullanici
│
├── RealEstate [N:1]
│   ├── RentalContract [N:1] ──► Cari (kiracı), RentalPaymentSchedule
│   │   └── Invoice [N:1] ──► CariHareket, AccountingVoucher
│   └── LegalCase [N:1] ──► Cari
│
├── Cari [N:1] ──► RealEstate (bağlı mülkler), RentalContract (bağlı sözleşmeler)
│   └── CariHareket [N:1] ──► TreasuryAccount (ödeme yeri)
│
├── TreasuryAccount [N:1]
│   └── BankMovement [N:1] ──► Cari, Transaction
│
├── Transaction [N:1] ──► Cari, TreasuryAccount
│   └── AccountingVoucher [N:1] ──► ChartOfAccount (satırlar üzerinden)
│
├── Lead [N:1] ──► RealEstate/Unit (ilgilendiği), User (atanan), Cari (dönüşünce)
│
└── Notification / FinanceReminder [N:1] ──► User
```

---

## 4. Django Modellemesine Dair Notlar

- Para alanları **her zaman** `DecimalField(max_digits=..., decimal_places=2)`
  ile tanımlanmalı, asla `FloatField` kullanılmamalıdır (bkz.
  `01-GELISTIRME-KURALLARI.md` Bölüm 4).
- `AccountingVoucher` kaydında toplam borç/alacak eşitliği bir
  `clean()`/serializer validation veya service-layer kontrolü ile
  **kayıt öncesi** doğrulanmalıdır.
- Finansal/muhasebesel modellerde fiziksel silme yerine `is_cancelled`,
  `cancelled_at`, `cancelled_by`, `cancel_reason` alanları ile iptal
  mekanizması kurulmalıdır — `delete()` override edilmemeli, ayrı bir
  `cancel()` metodu/service fonksiyonu tanımlanmalıdır.
- `RealEstate`, `RentalContract`, `Cari` gibi modellerde Türkçe alan
  isimlendirmesi UI tarafında (serializer `label` / frontend metinleri)
  yapılmalı, model/alan isimleri kod içinde İngilizce kalmalıdır.
