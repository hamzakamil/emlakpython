import decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("construction", "0011_metraj")]

    operations = [
        migrations.CreateModel(
            name="NakliyeMesafe",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("mesafe_km", models.DecimalField(decimal_places=3, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name="Mesafe Km")),
                ("k_katsayisi", models.DecimalField(decimal_places=4, default=decimal.Decimal("1"), max_digits=8, validators=[django.core.validators.MinValueValidator(0)], verbose_name="K Katsayısı")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant", verbose_name="Tenant")),
                ("poz", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="nakliye_mesafeleri", to="construction.poz", verbose_name="Poz")),
                ("proje", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="nakliye_mesafeleri", to="construction.proje", verbose_name="Proje")),
            ],
            options={"ordering": ["proje", "poz"], "verbose_name": "Nakliye Mesafesi", "verbose_name_plural": "Nakliye Mesafeleri"},
        ),
        migrations.CreateModel(
            name="PozAnaliz",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("satir_no", models.PositiveIntegerField(default=1, verbose_name="Satır No")),
                ("malzeme", models.CharField(max_length=255, verbose_name="Analiz Kalemi")),
                ("birim", models.CharField(max_length=20, verbose_name="Birim")),
                ("miktar", models.DecimalField(decimal_places=4, max_digits=14, validators=[django.core.validators.MinValueValidator(0.0001)])),
                ("birim_fiyat", models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(0)])),
                ("tutar", models.DecimalField(decimal_places=2, default=decimal.Decimal("0"), max_digits=18)),
                ("analiz_tipi", models.CharField(choices=[("malzeme", "Malzeme"), ("iscilik", "İşçilik"), ("makine", "Makine"), ("nakliye", "Nakliye"), ("diger", "Diğer")], default="malzeme", max_length=20)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant", verbose_name="Tenant")),
                ("poz", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="analizler", to="construction.poz", verbose_name="Poz")),
            ],
            options={"ordering": ["poz", "satir_no", "id"], "verbose_name": "Poz Analizi", "verbose_name_plural": "Poz Analizleri"},
        ),
        migrations.AddConstraint(
            model_name="nakliyemesafe",
            constraint=models.UniqueConstraint(fields=("tenant", "proje", "poz"), name="uniq_nakliye_mesafe_tenant_proje_poz"),
        ),
        migrations.AddConstraint(
            model_name="pozanaliz",
            constraint=models.UniqueConstraint(fields=("tenant", "poz", "satir_no"), name="uniq_poz_analiz_tenant_satir"),
        ),
        migrations.AddConstraint(
            model_name="pozanaliz",
            constraint=models.CheckConstraint(condition=models.Q(("tutar__gte", 0)), name="check_poz_analiz_tutar_pozitif"),
        ),
    ]
