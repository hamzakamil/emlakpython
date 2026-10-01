from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0008_alter_vergiprofili_tenant"),
    ]

    operations = [
        migrations.AddField(
            model_name="fatura",
            name="e_fatura_durum",
            field=models.CharField(
                choices=[
                    ("gonderilmedi", "Gönderilmedi"),
                    ("gonderildi", "Gönderildi"),
                    ("kabul", "Kabul"),
                    ("red", "Red"),
                ],
                default="gonderilmedi",
                max_length=20,
                verbose_name="e-Fatura Durumu",
            ),
        ),
        migrations.AddField(
            model_name="fatura",
            name="e_fatura_uuid",
            field=models.CharField(
                blank=True,
                default="",
                max_length=64,
                verbose_name="e-Fatura UUID",
            ),
        ),
        migrations.AddField(
            model_name="fatura",
            name="fatura_turu",
            field=models.CharField(
                choices=[
                    ("satis", "Satış"),
                    ("kira", "Kira"),
                    ("hakedis", "Hakediş"),
                    ("iade", "İade"),
                    ("aidat", "Aidat"),
                    ("hizmet", "Hizmet"),
                    ("proforma", "Proforma"),
                ],
                default="satis",
                max_length=20,
                verbose_name="Fatura Türü",
            ),
        ),
        migrations.AddField(
            model_name="fatura",
            name="iskonto_tutari",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0"),
                max_digits=15,
                verbose_name="Belge İskontosu",
            ),
        ),
        migrations.AddField(
            model_name="fatura",
            name="kdv_dahil_mi",
            field=models.BooleanField(default=False, verbose_name="KDV Dahil mi?"),
        ),
        migrations.AddField(
            model_name="fatura",
            name="kur",
            field=models.DecimalField(
                decimal_places=6,
                default=Decimal("1"),
                max_digits=15,
                verbose_name="Kur",
            ),
        ),
        migrations.AddField(
            model_name="fatura",
            name="odenen_tutar",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0"),
                max_digits=15,
                verbose_name="Ödenen Tutar",
            ),
        ),
        migrations.AddField(
            model_name="fatura",
            name="para_birimi",
            field=models.CharField(
                choices=[
                    ("TRY", "TRY"),
                    ("USD", "USD"),
                    ("EUR", "EUR"),
                    ("GBP", "GBP"),
                ],
                default="TRY",
                max_length=3,
                verbose_name="Para Birimi",
            ),
        ),
        migrations.AddField(
            model_name="fatura",
            name="senaryo",
            field=models.CharField(
                choices=[
                    ("e_fatura", "e-Fatura"),
                    ("e_arsiv", "e-Arşiv"),
                    ("kagit", "Kağıt"),
                ],
                default="kagit",
                max_length=20,
                verbose_name="e-Belge Senaryosu",
            ),
        ),
    ]
