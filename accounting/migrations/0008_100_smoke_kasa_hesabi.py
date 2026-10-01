from django.db import migrations


def yeniden_adlandir_kasa_hesabi(apps, schema_editor):
    HesapPlani = apps.get_model("accounting", "HesapPlani")
    HesapPlani.objects.filter(kod="100.SMOKE").update(
        ad="Kasa Hesabı",
        is_active=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0007_td_hp_resmi_liste_duzeltmesi"),
    ]

    operations = [
        migrations.RunPython(
            yeniden_adlandir_kasa_hesabi,
            migrations.RunPython.noop,
        ),
    ]
