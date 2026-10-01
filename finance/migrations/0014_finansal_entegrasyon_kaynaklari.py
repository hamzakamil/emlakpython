from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0008_100_smoke_kasa_hesabi"),
        ("cari", "0002_carihareket_fatura"),
        ("finance", "0013_finansal_olay_cekirdegi"),
    ]

    operations = [
        migrations.AddField(
            model_name="finansalislem",
            name="muhasebe_fisi",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="finansal_islemler",
                to="accounting.muhasebefisi",
                verbose_name="Muhasebe Fişi",
            ),
        ),
    ]
