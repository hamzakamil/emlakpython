from django.db import migrations


EK_TDHP_GRUPLARI = [
    ("17", "Yıllara Yaygın İnşaat ve Onarım Maliyetleri", "aktif", "borc"),
    ("35", "Yıllara Yaygın İnşaat ve Onarım Hakediş Bedelleri", "pasif", "alacak"),
]


def yukle_td_hp_gruplari(apps, schema_editor):
    HesapPlani = apps.get_model("accounting", "HesapPlani")
    Tenant = apps.get_model("tenants", "Tenant")

    for tenant in Tenant.objects.all().iterator():
        for kod, ad, tip, normal in EK_TDHP_GRUPLARI:
            HesapPlani.objects.update_or_create(
                tenant=tenant,
                kod=kod,
                defaults={
                    "ad": ad,
                    "tip": tip,
                    "seviye": 2,
                    "normal_bakiye": normal,
                    "detay_hesap_mi": False,
                    "is_active": True,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0004_td_hesaplari_tamamla"),
    ]

    operations = [
        migrations.RunPython(yukle_td_hp_gruplari, migrations.RunPython.noop),
    ]
