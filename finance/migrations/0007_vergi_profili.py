from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("finance", "0006_faturakalemi_stopaj")]

    operations = [
        migrations.CreateModel(
            name="VergiProfili",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kod", models.CharField(max_length=40, verbose_name="Profil Kodu")),
                ("ad", models.CharField(max_length=120, verbose_name="Profil Adı")),
                ("kdv_orani", models.DecimalField(decimal_places=2, default=20, max_digits=5)),
                ("tevkifat_orani", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("stopaj_orani", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktif")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant")),
            ],
            options={"ordering": ["ad"]},
        ),
        migrations.AddConstraint(
            model_name="vergiprofili",
            constraint=models.UniqueConstraint(fields=("tenant", "kod"), name="uniq_vergi_profili_tenant_kod"),
        ),
    ]
