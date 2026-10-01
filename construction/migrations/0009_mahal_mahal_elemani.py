from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("construction", "0008_ifc_import"),
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Mahal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kod", models.CharField(max_length=30, verbose_name="Mahal Kodu")),
                ("ad", models.CharField(max_length=255, verbose_name="Mahal Adı")),
                ("mahal_tipi", models.CharField(blank=True, max_length=50, verbose_name="Mahal Tipi")),
                ("kat", models.CharField(blank=True, max_length=30, verbose_name="Kat")),
                ("alan", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="Alan (m²)")),
                ("aciklama", models.TextField(blank=True, verbose_name="Açıklama")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktif")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Güncellenme")),
                ("proje", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mahaller", to="construction.proje", verbose_name="Proje")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant", verbose_name="Tenant")),
            ],
            options={
                "verbose_name": "Mahal",
                "verbose_name_plural": "Mahaller",
                "ordering": ["proje", "kod"],
            },
        ),
        migrations.CreateModel(
            name="MahalElemani",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("eleman_tipi", models.CharField(max_length=50, verbose_name="Eleman Tipi")),
                ("ad", models.CharField(blank=True, max_length=255, verbose_name="Eleman Adı")),
                ("miktar", models.DecimalField(decimal_places=2, default=1, max_digits=12, verbose_name="Miktar")),
                ("birim", models.CharField(default="adet", max_length=20, verbose_name="Birim")),
                ("aciklama", models.TextField(blank=True, verbose_name="Açıklama")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktif")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Güncellenme")),
                ("mahal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="elemanlar", to="construction.mahal", verbose_name="Mahal")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant", verbose_name="Tenant")),
            ],
            options={
                "verbose_name": "Mahal Elemanı",
                "verbose_name_plural": "Mahal Elemanları",
                "ordering": ["mahal", "eleman_tipi", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="mahal",
            constraint=models.UniqueConstraint(fields=("tenant", "proje", "kod"), name="uniq_mahal_tenant_proje_kod"),
        ),
        migrations.AddConstraint(
            model_name="mahalelemani",
            constraint=models.UniqueConstraint(fields=("tenant", "mahal", "eleman_tipi", "ad"), name="uniq_mahal_elemani_tenant_tip_ad"),
        ),
        migrations.AddIndex(
            model_name="mahal",
            index=models.Index(fields=["tenant", "proje"], name="mahal_tenant_proje_idx"),
        ),
        migrations.AddIndex(
            model_name="mahalelemani",
            index=models.Index(fields=["tenant", "mahal"], name="mahalel_tenant_mahal_idx"),
        ),
    ]
