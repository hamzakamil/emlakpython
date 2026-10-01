from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("construction", "0005_malzemehareketi_santiyecheckin_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="TedarikciTeklifi",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("miktar", models.DecimalField(decimal_places=4, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal("0.0001"))], verbose_name="Miktar")),
                ("birim_fiyat", models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))], verbose_name="Birim Fiyat (₺)")),
                ("toplam_tutar", models.DecimalField(blank=True, decimal_places=2, help_text="Miktar x birim fiyat; kayıtta otomatik hesaplanır.", max_digits=16, null=True, verbose_name="Toplam Tutar (₺)")),
                ("durum", models.CharField(choices=[("taslak", "Taslak"), ("istendi", "İstendi"), ("geldi", "Teklif Alındı"), ("degerlendiriliyor", "Değerlendiriliyor"), ("kabul", "Kabul Edildi"), ("red", "Reddedildi"), ("iptal", "İptal")], default="taslak", max_length=24, verbose_name="Durum")),
                ("gecerlilik_tarihi", models.DateField(blank=True, null=True, verbose_name="Geçerlilik Tarihi")),
                ("notlar", models.TextField(blank=True, verbose_name="Notlar")),
                ("secildi", models.BooleanField(default=False, verbose_name="Kazanan teklif")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktif")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Güncellenme")),
                ("malzeme", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="tedarikci_teklifleri", to="construction.malzeme", verbose_name="Malzeme")),
                ("proje", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="tedarikci_teklifleri", to="construction.proje", verbose_name="Proje")),
                ("tedarikci", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="teklifler", to="construction.tedarikci", verbose_name="Tedarikçi")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant", verbose_name="Tenant")),
            ],
            options={"verbose_name": "Tedarikçi Teklifi", "verbose_name_plural": "Tedarikçi Teklifleri", "ordering": ["-secildi", "birim_fiyat", "-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="tedarikciteklifi",
            constraint=models.CheckConstraint(condition=models.Q(miktar__gt=0), name="check_tedarikci_teklifi_miktar_pozitif"),
        ),
        migrations.AddConstraint(
            model_name="tedarikciteklifi",
            constraint=models.CheckConstraint(condition=models.Q(birim_fiyat__gt=0), name="check_tedarikci_teklifi_fiyat_pozitif"),
        ),
        migrations.AddConstraint(
            model_name="tedarikciteklifi",
            constraint=models.UniqueConstraint(condition=models.Q(is_active=True), fields=("tenant", "proje", "malzeme", "tedarikci"), name="uniq_aktif_tedarikci_teklifi"),
        ),
    ]
