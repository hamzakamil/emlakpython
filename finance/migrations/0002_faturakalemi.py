from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):
    dependencies = [
        ("cari", "0001_initial"),
        ("finance", "0001_initial"),
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Fatura",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("No", models.CharField(max_length=30, unique=True, verbose_name="Fatura No")),
                ("durum", models.CharField(choices=[("taslak", "Taslak"), ("aktif", "Aktif"), ("odendi", "Ödendi"), ("iptal", "İptal")], default="taslak", max_length=20, verbose_name="Durum")),
                ("tarih", models.DateField(verbose_name="Fatura Tarihi")),
                ("vade_tarihi", models.DateField(blank=True, null=True, verbose_name="Vade Tarihi")),
                ("tutar", models.DecimalField(decimal_places=2, max_digits=15, verbose_name="Toplam Tutar")),
                ("alacakli", models.BooleanField(default=False, verbose_name="Alacaklı mı?")),
                ("aciklama", models.CharField(blank=True, max_length=255, verbose_name="Açıklama")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Güncellenme")),
                ("cari", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="faturalar", to="cari.cari", verbose_name="Cari")),
                ("kasa_banka_hesabi", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="faturalar", to="finance.kasabankahesabi", verbose_name="Kasa/Banka Hesabı")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant", verbose_name="Tenant")),
            ],
            options={"verbose_name": "Fatura", "verbose_name_plural": "Faturalar", "ordering": ["-tarih", "-id"]},
        ),
        migrations.CreateModel(
            name="FaturaKalemi",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("aciklama", models.CharField(max_length=255, verbose_name="Kalem Açıklaması")),
                ("miktar", models.DecimalField(decimal_places=4, max_digits=14, verbose_name="Miktar")),
                ("birim", models.CharField(default="ADET", max_length=20, verbose_name="Birim")),
                ("birim_fiyat", models.DecimalField(decimal_places=2, max_digits=15, verbose_name="Birim Fiyat")),
                ("kdv_orani", models.DecimalField(decimal_places=2, default=Decimal("20"), max_digits=5, verbose_name="KDV (%)")),
                ("tevkifat_orani", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=5, verbose_name="Tevkifat (%)")),
                ("fatura", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="kalemler", to="finance.fatura")),
            ],
            options={"ordering": ["id"]},
        ),
    ]
