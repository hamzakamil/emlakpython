from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("construction", "0016_hatirlatma_kurali_model_unique")]

    operations = [
        migrations.AddField(
            model_name="riskstructure",
            name="proje",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="riskli_yapi_surecleri",
                to="construction.proje",
                verbose_name="Proje",
            ),
        ),
    ]
