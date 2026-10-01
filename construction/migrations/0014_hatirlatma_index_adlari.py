from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("construction", "0013_hatirlatma_tarih_alanlari")]

    operations = [
        migrations.RenameIndex(
            model_name="hatirlatma",
            new_name="constructio_tenant__e99bad_idx",
            old_name="construction_hatirlatma_tarih_idx",
        ),
        migrations.RenameIndex(
            model_name="hatirlatma",
            new_name="constructio_tenant__f9a992_idx",
            old_name="construction_hatirlatma_kayit_idx",
        ),
    ]
