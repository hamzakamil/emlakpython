from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("construction", "0003_alter_hakedis_options_alter_kalitekontrol_options_and_more"),
    ]

    operations = [
        migrations.RemoveField(model_name="hakedis", name="donem_baslangic"),
        migrations.RemoveField(model_name="hakedis", name="donem_bitis"),
        migrations.RemoveField(model_name="hakedis", name="hakedis_no"),
        migrations.RemoveField(model_name="hakedis", name="kesinti_toplam"),
        migrations.RemoveField(model_name="hakedis", name="muhasebe_durumu"),
        migrations.RemoveField(model_name="hakedis", name="net_tutar"),
        migrations.RemoveField(model_name="hakedis", name="toplam_tutar"),
        migrations.RemoveField(model_name="hakedissatiri", name="bu_donem_miktar"),
        migrations.RemoveField(model_name="hakedissatiri", name="kumulatif_miktar"),
        migrations.RemoveField(model_name="hakedissatiri", name="onceki_miktar"),
        migrations.AddField(
            model_name="hakedis",
            name="donem",
            field=models.CharField(
                default="2026-01",
                help_text="Hakediş dönemi, örn. 2026-03.",
                max_length=7,
                verbose_name="Dönem (YYYY-MM)",
            ),
        ),
        migrations.AddConstraint(
            model_name="hakedis",
            constraint=models.UniqueConstraint(
                fields=("tenant", "proje", "donem"),
                name="uniq_hakedis_tenant_proje_donem",
            ),
        ),
    ]
