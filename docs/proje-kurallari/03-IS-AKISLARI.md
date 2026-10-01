# İş Akışları (Business Flows)

> Kaynak: Benzer bir gayrimenkul/inşaat ERP projesinin iş akışları, bu projenin
> kapsamına (Emlak + Muhasebe + Finans) göre sadeleştirilip Django service-layer
> yaklaşımına uyarlanmıştır.

---

## 1. Kira Yönetim Akışı

```
1. GAYRİMENKUL TANIMLAMA
   RealEstate oluştur → bina, blok, kat, daire no, m², tapu bilgileri
   Durum: available | rented | sold | reserved | maintenance

2. CARİ (KİRACI / MALİK) TANIMLAMA
   Cari oluştur → Bireysel / Kurumsal
   Roller: Kiracı, Kefil, Malik
   İletişim, adres, banka bilgileri

3. KİRA SÖZLEŞMESİ OLUŞTURMA
   RentalContract oluştur → RealEstate + Cari (kiracı) bağlantısı
   Başlangıç/bitiş tarihi, aylık kira, depozito
   Artış tipi: TÜFE / Sabit / Pazarlık
   Ödeme periyodu: Aylık / 3 Aylık / 6 Aylık / Yıllık, ödeme günü

4. ÖDEME PLANI OTOMASYONU
   Sözleşme tarih aralığına göre otomatik ödeme planı oluştur
   Her dönem: vade tarihi, tutar, ödendi mi, ödenen tarih/tutar, gecikme faizi

   ├──► Vade yaklaştığında: FinanceReminder oluştur
   ├──► Vade geçtiğinde: Notification + gecikme faizi hesaplama
   └──► Ödeme yapıldığında: CariHareket + Invoice + AccountingVoucher (tek transaction içinde)

5. FATURALAMA
   Invoice → direction: out (satış) | in (alış)
   status: draft → issued → sent → paid → overdue → cancelled
   KDV hesaplama (varsayılan %20)

6. MUHASEBE ENTEGRASYONU
   Her finansal işlem için otomatik AccountingVoucher (çift kayıt)
   Hesap kodları ChartOfAccount referanslı

7. RAPORLAMA
   Kira Gelir Raporu, Birim Doluluk Raporu, Gecikmiş Tahsilat Raporu, Kasa/Banka Özeti
```

**Django service önerisi:** `services/rental.py` içinde
`create_rental_contract()`, `generate_payment_schedule()`,
`mark_payment_received()` gibi fonksiyonlar — her biri `transaction.atomic()`
içinde CariHareket + Invoice + AccountingVoucher'ı birlikte oluşturmalı.

---

## 2. Finans Yönetim Akışı

```
1. HESAP PLANI TANIMLAMA
   ChartOfAccount: '100 Kasa', '102 Bankalar', '120 Alıcılar' vb.

2. KASA / BANKA HESABI AÇMA
   TreasuryAccount: type (bank | cash | credit_card | check), IBAN, hesap kodu, para birimi

3. FİNANSAL İŞLEM KAYDI
   Transaction: type (income | expense | transfer), tutar, hesap, cari
   ├──► Otomatik CariHareket oluşturma
   ├──► Otomatik Invoice oluşturma (isteğe bağlı)
   ├──► Otomatik AccountingVoucher (fiş) oluşturma
   └──► FinanceReminder oluşturma (vade takibi)

4. BANKA EKSTRESİ EŞLEŞTİRME
   Excel import → BankMovement (pending)
   ├──► Açıklama parsing, cari önerisi, işlem eşleştirme
   └──► Eşleşince: status → processed, ilgili Transaction'a bağlanır

5. MUHASEBE FİŞİ (ÇİFT KAYIT)
   AccountingVoucher.lines = [
     { account_code: '100', debit: 1000, credit: 0 },
     { account_code: '600', debit: 0, credit: 1000 },
   ]
   total_debit == total_credit  (zorunlu doğrulama)

6. MİZAN / RAPORLAMA
   Trial Balance (Mizan): tüm hesapların borç/alacak toplamı, dönemsel filtreleme
```

---

## 3. Satış CRM Akışı *(opsiyonel modül — proje kapsamına göre eklenebilir)*

```
1. LEAD (POTANSİYEL MÜŞTERİ) OLUŞTURMA
   source: website | referral | social | advertisement | walk_in
   status: new, ilgilendiği gayrimenkuller, atanan kullanıcı, bütçe aralığı

2. AKTİVİTE TAKİBİ
   call | meeting | email | visit | note
   status akışı: new → contacted → qualified → proposal → negotiation

3. LEAD → CARİ DÖNÜŞÜMÜ
   Lead onaylanınca Cari oluşturulur, Lead.cari_id güncellenir

4. BİRİM / GAYRİMENKUL SATIŞI
   RealEstate.status = 'sold', buyer_id, sale_price, sale_date
   Otomatik Transaction + Invoice oluşturma
```

---

## 4. Bildirim ve Hatırlatıcı Akışı

```
1. HATIRLATICI TİPLERİ
   invoice_due     → Fatura vadesi geldiğinde
   payment_due     → Ödeme vadesi geçtiğinde
   credit_card     → Kredi kartı ödeme günü yaklaştığında
   manual          → Kullanıcı tarafından manuel oluşturulan

2. PERİYODİK TARAMA (Celery periodic task, örn. saatlik)
   run_finance_reminder_sweep()
   ├──► Yaklaşan/gecikmiş ödemeler ve faturalar taranır
   └──► Her biri için Notification oluşturulur ve dağıtılır

3. BİLDİRİM DAĞITIMI
   create_and_broadcast_notification(tenant, recipient_users, title, message, type, ...)
   ├──► Notification.objects.create() (DB kaydı)
   ├──► WebSocket / push bildirimi (gerekirse, ileri aşamada eklenir)
   └──► E-posta (opsiyonel)
```

**Not:** Kaynak projede bu akış Node.js + Socket.IO ile senkron/anlık
çalışıyordu. Django + Celery stack'inde bu, **periyodik görev (Celery beat)
+ bildirim tablosu** ile başlanıp, gerçek zamanlı ihtiyaç netleşirse Django
Channels / WebSocket ile genişletilebilir (bkz. `06-ILHAM-OZELLIKLER.md`).

---

## 5. Muhasebe Entegrasyonunda Genel Kural

Kaynak projenin özeti şu zincire dayanıyordu ve bu proje için de doğrudan
geçerlidir:

> **Gayrimenkul → Cari → Sözleşme → Ödeme Planı → Fatura → Muhasebe Fişi**

Bu zincirdeki her adım birbirine bağlı olmalı ve tek bir finansal olay
(örn. bir tahsilat), zincirdeki ilgili tüm kayıtları **tek bir transaction
içinde** güncellemelidir. Ara adımlardan biri başarısız olursa tüm işlem
rollback edilmelidir (bkz. `01-GELISTIRME-KURALLARI.md` Bölüm 4).
