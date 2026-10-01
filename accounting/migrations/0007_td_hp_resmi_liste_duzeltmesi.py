from django.db import migrations


# Paylaşılan 1 Sıra No'lu MSUGT özetindeki eksik resmi hesaplar.
EK_HESAPLAR = [
    ("159", "Verilen Sipariş Avansları", "aktif", "borc"),
    ("178", "Yıllara Yaygın İnşaat Enflasyon Düzeltme Hesabı", "aktif", "borc"),
    ("23", "Diğer Alacaklar", "aktif", "borc"),
    ("230", "Ortaklardan Alacaklar", "aktif", "borc"),
    ("231", "İştiraklerden Alacaklar", "aktif", "borc"),
    ("232", "Bağlı Ortaklıklardan Alacaklar", "aktif", "borc"),
    ("235", "Personelden Alacaklar", "aktif", "borc"),
    ("236", "Diğer Çeşitli Alacaklar", "aktif", "borc"),
    ("237", "Diğer Alacak Senetleri Reeskontu (-)", "aktif", "alacak"),
    ("239", "Şüpheli Diğer Alacaklar Karşılığı (-)", "aktif", "alacak"),
    ("241", "Bağlı Menkul Kıymetler Değer Düşüklüğü Karşılığı (-)", "aktif", "alacak"),
    ("248", "Diğer Mali Duran Varlıklar", "aktif", "borc"),
    ("249", "Diğer Mali Duran Varlıklar Karşılığı (-)", "aktif", "alacak"),
    ("256", "Diğer Maddi Duran Varlıklar", "aktif", "borc"),
    ("269", "Verilen Avanslar", "aktif", "borc"),
    ("279", "Verilen Avanslar", "aktif", "borc"),
    ("398", "Sayım ve Tesellüm Fazlaları", "pasif", "alacak"),
    ("421", "Borç Senetleri", "pasif", "alacak"),
    ("422", "Borç Senetleri Reeskontu (-)", "pasif", "borc"),
    ("426", "Alınan Depozito ve Teminatlar", "pasif", "alacak"),
    ("429", "Diğer Ticari Borçlar", "pasif", "alacak"),
    ("438", "Kamuya Olan Ertelenmiş veya Taksitlendirilmiş Borçlar", "pasif", "alacak"),
    ("480", "Gelecek Yıllara Ait Gelirler", "pasif", "alacak"),
    ("520", "Hisse Senetleri İhraç Primleri", "pasif", "alacak"),
    ("521", "Hisse Senedi İptal Kârları", "pasif", "alacak"),
    ("641", "Bağlı Ortaklıklardan Temettü Gelirleri", "gelir", "alacak"),
    ("643", "Komisyon Gelirleri", "gelir", "alacak"),
    ("644", "Konusu Kalmayan Karşılıklar", "gelir", "alacak"),
    ("649", "Faaliyetle İlgili Diğer Gelir ve Kârlar", "gelir", "alacak"),
    ("652", "Reeskont Faiz Giderleri (-)", "gider", "borc"),
    ("680", "Çalışmayan Kısım Gider ve Zararları (-)", "gider", "borc"),
    ("700", "Maliyet Muhasebesi Bağlantı Hesabı", "gider", "borc"),
    ("723", "Direkt İşçilik Süre (Zaman) Farkları", "gider", "borc"),
    ("734", "Genel Üretim Giderleri Kapasite Farkları", "gider", "borc"),
    ("752", "Araştırma ve Geliştirme Gider Farkları", "gider", "borc"),
    ("762", "Pazarlama Satış ve Dağıtım Giderleri Fark Hesabı", "gider", "borc"),
    ("772", "Genel Yönetim Gider Farkları Hesabı", "gider", "borc"),
    ("782", "Finansman Giderleri Fark Hesabı", "gider", "borc"),
    ("791", "İşçi Ücret ve Giderleri", "gider", "borc"),
    ("792", "Memur Ücret ve Giderleri", "gider", "borc"),
]

# Paylaşılan listede resmi olarak tanımlı olmayan veya listede bulunmayan önceki
# seed kayıtları. Silinmez; fiş bağlantıları varsa korunur, kullanım dışı yapılır.
RESMI_DISI_KODLAR = {
    "8",
    "9",
    "104",
    "105",
    "106",
    "107",
    "109",
    "123",
    "124",
    "125",
    "127",
    "134",
    "140",
    "190",
    "171",
    "172",
    "173",
    "174",
    "175",
    "176",
    "177",
    "179",
    "223",
    "224",
    "227",
    "228",
    "265",
    "301",
    "302",
    "323",
    "324",
    "329",
    "351",
    "352",
    "353",
    "354",
    "355",
    "356",
    "357",
    "359",
    "362",
    "387",
    "389",
    "401",
    "402",
    "409",
    "470",
    "471",
    "473",
    "474",
    "603",
    "604",
    "605",
    "606",
    "613",
    "623",
    "633",
    "702",
    "900",
    "901",
    "910",
    "911",
}


def uygula_resmi_td_hp_duzeltmesi(apps, schema_editor):
    HesapPlani = apps.get_model("accounting", "HesapPlani")
    Tenant = apps.get_model("tenants", "Tenant")

    for tenant in Tenant.objects.all().iterator():
        for kod in RESMI_DISI_KODLAR:
            HesapPlani.objects.filter(tenant=tenant, kod=kod).update(is_active=False)

        for kod, ad, tip, normal in EK_HESAPLAR:
            ust_kod = kod[:-1] if len(kod) in (2, 3) else None
            ust_hesap = (
                HesapPlani.objects.filter(tenant=tenant, kod=ust_kod).first()
                if ust_kod
                else None
            )
            HesapPlani.objects.update_or_create(
                tenant=tenant,
                kod=kod,
                defaults={
                    "ad": ad,
                    "tip": tip,
                    "ust_hesap": ust_hesap,
                    "seviye": len(kod),
                    "normal_bakiye": normal,
                    "detay_hesap_mi": len(kod) >= 3,
                    "is_active": True,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0006_td_hesap_parentlerini_duzelt"),
    ]

    operations = [
        migrations.RunPython(uygula_resmi_td_hp_duzeltmesi, migrations.RunPython.noop),
    ]
