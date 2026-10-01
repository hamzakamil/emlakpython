from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("construction", "0017_riskstructure_proje")]

    operations = [
        migrations.AddField(
            model_name="leaseassistance",
            name="banka_iban",
            field=models.CharField(blank=True, max_length=34, verbose_name="Banka IBAN"),
        ),
        migrations.AddField(
            model_name="leaseassistance",
            name="banka_adi",
            field=models.CharField(blank=True, max_length=150, verbose_name="Banka Adı"),
        ),
        migrations.AddField(
            model_name="leaseassistance",
            name="odeme_notu",
            field=models.TextField(blank=True, verbose_name="Ödeme Notu"),
        ),
    ]
