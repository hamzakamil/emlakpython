from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("cari", "0001_initial"),
        ("finance", "0013_finansal_olay_cekirdegi"),
    ]

    operations = [
        migrations.AddField(
            model_name="carihareket",
            name="fatura",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cari_hareketleri",
                to="finance.fatura",
                verbose_name="Kaynak Fatura",
            ),
        ),
        migrations.AddConstraint(
            model_name="carihareket",
            constraint=models.UniqueConstraint(
                condition=Q(("fatura__isnull", False)),
                fields=("fatura",),
                name="uniq_cari_hareket_fatura",
            ),
        ),
    ]
