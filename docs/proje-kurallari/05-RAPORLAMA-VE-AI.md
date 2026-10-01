# Raporlama Modülü ve AI Özellikleri (Opsiyonel / İleri Seviye)

> Kaynak: Benzer bir gayrimenkul/inşaat ERP projesindeki raporlama ve AI
> modülleri. Bu bölüm **öncelikli MVP kapsamı değildir** — temel emlak +
> muhasebe + finans modülleri oturduktan sonra değerlendirilmesi önerilir.

---

## 1. Önerilen Temel Raporlar

| Rapor | İçerik |
|---|---|
| **Kira Gelir Raporu** | Dönemsel kira gelirleri, tahsilat oranları |
| **Birim Doluluk Raporu** | Gayrimenkul/birim bazında doluluk-kiralama durumu |
| **Gecikmiş Tahsilat Raporu** | Vadesi geçen ödemeler, gecikme günü |
| **Kasa / Banka Özeti** | Hesap bazında bakiyeler ve hareketler |
| **Kiracı Listesi Raporu** | Aktif kiracılar ve sözleşme detayları |
| **Mizan (Trial Balance)** | Tüm hesapların dönemsel borç/alacak toplamları |

Bu raporlar mümkün olduğunca backend/veritabanı tarafında (Django ORM
aggregation, PostgreSQL view'ları vb.) hesaplanmalı; tüm ham veri frontend'e
gönderilip orada hesaplanmamalıdır (bkz. `01-GELISTIRME-KURALLARI.md` Bölüm 8).

PDF çıktısı alınan raporlarda Türkçe karakter desteği zorunludur
(bkz. `01-GELISTIRME-KURALLARI.md` Bölüm 10).

---

## 2. AI Destekli Özellikler (İleri Seviye Fikirler)

Kaynak projede yer alan, bu proje için **gelecek fazlara** bırakılabilecek
fikirler:

| Özellik | Açıklama |
|---|---|
| Belge Analizi | OCR + AI ile tapu/sözleşme gibi evrakların içerik analizi |
| Gecikme/Risk Analizi | Kiracı ödeme geçmişine göre gecikme riski tahmini |
| Maliyet/Tutar Anomalisi Tespiti | Olağandışı işlem/tutar tespiti (dolandırıcılık/hata önleme) |
| Rapor Özeti Oluşturma | Uzun mizan/rapor verisinin AI ile özetlenmesi |

**Not:** Bu özellikler proje MVP'sinde önceliklendirilmemelidir; önce
temel emlak + muhasebe + finans akışlarının (bkz. `03-IS-AKISLARI.md`)
sağlam ve doğru çalışması önceliklidir (bkz. karar önceliği,
`01-GELISTIRME-KURALLARI.md` Bölüm 11).
