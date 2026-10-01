from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0010_fatura_iade_faturasi"),
    ]

    operations = [
        migrations.AddField(
            model_name="faturakalemi",
            name="iskonto_orani",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0"),
                max_digits=5,
                verbose_name="İskonto (%)",
            ),
        ),
        migrations.AddField(
            model_name="faturakalemi",
            name="poz_no",
            field=models.CharField(
                blank=True,
                default="",
                max_length=50,
                verbose_name="Poz No",
            ),
        ),
    ]
