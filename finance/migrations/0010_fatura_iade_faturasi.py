import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0009_fatura_enterprise_alanlari"),
    ]

    operations = [
        migrations.AddField(
            model_name="fatura",
            name="iade_faturasi",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="iadeler",
                to="finance.fatura",
                verbose_name="İade Edilen Fatura",
            ),
        ),
    ]
