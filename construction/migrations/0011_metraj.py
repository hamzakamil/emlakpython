from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("construction", "0010_yaklasik_maliyet")]

    operations = [
        migrations.CreateModel(
            name="Metraj",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ad", models.CharField(max_length=200, verbose_name="Metraj Adı")),
                ("metraj_tipi", models.CharField(default="genel", max_length=30, verbose_name="Metraj Tipi")),
                ("ifade", models.CharField(max_length=500, verbose_name="Hesap İfadesi")),
                ("sonuc", models.DecimalField(decimal_places=6, max_digits=18, verbose_name="Sonuç")),
                ("birim", models.CharField(default="miktar", max_length=20, verbose_name="Birim")),
                ("aciklama", models.TextField(blank=True, verbose_name="Açıklama")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktif")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Güncellenme")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant", verbose_name="Tenant")),
            ],
            options={"verbose_name": "Metraj", "verbose_name_plural": "Metrajlar", "ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="metraj",
            constraint=models.UniqueConstraint(fields=("tenant", "ad"), name="uniq_metraj_tenant_ad"),
        ),
        migrations.AddConstraint(
            model_name="metraj",
            constraint=models.CheckConstraint(condition=models.Q(("sonuc__gte", 0)), name="check_metraj_sonuc_pozitif"),
        ),
    ]
