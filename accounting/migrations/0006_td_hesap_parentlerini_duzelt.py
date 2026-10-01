from django.db import migrations


def duzelt_td_hp_parentleri(apps, schema_editor):
    HesapPlani = apps.get_model("accounting", "HesapPlani")
    Tenant = apps.get_model("tenants", "Tenant")

    for tenant in Tenant.objects.all().iterator():
        grup_17 = HesapPlani.objects.filter(tenant=tenant, kod="17").first()
        grup_35 = HesapPlani.objects.filter(tenant=tenant, kod="35").first()
        if grup_17:
            HesapPlani.objects.filter(
                tenant=tenant, kod__in=["170", "171", "172", "173", "174", "175", "176", "177", "178", "179"]
            ).update(ust_hesap=grup_17)
        if grup_35:
            HesapPlani.objects.filter(
                tenant=tenant, kod__in=["350", "351", "352", "353", "354", "355", "356", "357", "358", "359"]
            ).update(ust_hesap=grup_35)
        HesapPlani.objects.filter(tenant=tenant, kod="17").update(
            ust_hesap=HesapPlani.objects.filter(tenant=tenant, kod="1").first()
        )
        HesapPlani.objects.filter(tenant=tenant, kod="35").update(
            ust_hesap=HesapPlani.objects.filter(tenant=tenant, kod="3").first()
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0005_td_hesap_gruplari"),
    ]

    operations = [
        migrations.RunPython(duzelt_td_hp_parentleri, migrations.RunPython.noop),
    ]
