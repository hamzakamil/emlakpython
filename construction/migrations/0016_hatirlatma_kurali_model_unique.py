from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("construction", "0015_hatirlatma_kural_sablonlari")]

    operations = [
        migrations.RemoveConstraint(
            model_name="hatirlatmakurali",
            name="uniq_hatirlatma_kurali_tenant_tetik",
        ),
        migrations.AddConstraint(
            model_name="hatirlatmakurali",
            constraint=models.UniqueConstraint(
                fields=("tenant", "ilgili_modul", "ilgili_model", "tetikleyici", "once_gun_sayisi"),
                name="uniq_hatirlatma_kurali_tenant_tetik",
            ),
        ),
    ]
