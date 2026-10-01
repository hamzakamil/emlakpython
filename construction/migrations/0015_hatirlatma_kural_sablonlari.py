from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("construction", "0014_hatirlatma_index_adlari")]

    operations = [
        migrations.AddField(
            model_name="hatirlatmakurali",
            name="ilgili_model",
            field=models.CharField(default="", max_length=120, blank=True, verbose_name="İlgili Model"),
        ),
        migrations.AddField(
            model_name="hatirlatmakurali",
            name="baslik_sablonu",
            field=models.CharField(default="", max_length=255, blank=True, verbose_name="Başlık Şablonu"),
        ),
    ]
