from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="hesapplani",
            name="aciklama",
            field=models.TextField(blank=True, verbose_name="Açıklama"),
        ),
        migrations.AddField(
            model_name="hesapplani",
            name="detay_hesap_mi",
            field=models.BooleanField(
                default=True,
                help_text="Muhasebe fişi satırında doğrudan kullanılabilir alt hesap.",
                verbose_name="Detay Hesap mı?",
            ),
        ),
        migrations.AddField(
            model_name="hesapplani",
            name="normal_bakiye",
            field=models.CharField(
                blank=True,
                choices=[("borc", "Borç"), ("alacak", "Alacak")],
                max_length=6,
                null=True,
                verbose_name="Normal Bakiye",
            ),
        ),
        migrations.AddField(
            model_name="hesapplani",
            name="seviye",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="1 ana sınıf, 2 hesap grubu, 3 ana hesap ve alt seviyeler.",
                null=True,
                verbose_name="Hesap Seviyesi",
            ),
        ),
        migrations.AddField(
            model_name="hesapplani",
            name="ust_hesap",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="alt_hesaplar",
                to="accounting.hesapplani",
                verbose_name="Üst Hesap",
            ),
        ),
    ]
