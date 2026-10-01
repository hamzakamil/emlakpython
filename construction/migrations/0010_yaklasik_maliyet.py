from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):
    dependencies = [("construction", "0009_mahal_mahal_elemani")]

    operations = [
        migrations.CreateModel(
            name="YaklasikMaliyet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("yil", models.PositiveSmallIntegerField(verbose_name="Fiyat Yılı")),
                ("ad", models.CharField(default="Yaklaşık Maliyet", max_length=255, verbose_name="Ad")),
                ("aciklama", models.TextField(blank=True, verbose_name="Açıklama")),
                ("versiyon", models.PositiveIntegerField(default=1, verbose_name="Versiyon")),
                ("toplam_tutar", models.DecimalField(decimal_places=2, default=0, max_digits=18, verbose_name="Toplam Tutar (₺)")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktif")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Güncellenme")),
                ("onceki", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="revizyonlar", to="construction.yaklasikmaliyet", verbose_name="Önceki Versiyon")),
                ("proje", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="yaklasik_maliyetler", to="construction.proje", verbose_name="Proje")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant", verbose_name="Tenant")),
            ],
            options={"ordering": ["-yil", "proje", "-versiyon"], "verbose_name": "Yaklaşık Maliyet", "verbose_name_plural": "Yaklaşık Maliyetler"},
        ),
        migrations.CreateModel(
            name="YaklasikMaliyetSatiri",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("miktar", models.DecimalField(decimal_places=4, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal("0.0001"))], verbose_name="Miktar")),
                ("birim_fiyat_snapshot", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=14, verbose_name="Birim Fiyat Snapshot (₺)")),
                ("toplam_tutar", models.DecimalField(decimal_places=2, default=0, max_digits=18, verbose_name="Toplam Tutar (₺)")),
                ("aciklama", models.TextField(blank=True, verbose_name="Açıklama")),
                ("sira", models.PositiveIntegerField(default=0, verbose_name="Sıra")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Güncellenme")),
                ("mahal", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="yaklasik_maliyet_satirlari", to="construction.mahal", verbose_name="Mahal")),
                ("poz", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="yaklasik_maliyet_satirlari", to="construction.poz", verbose_name="Poz")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant", verbose_name="Tenant")),
                ("yaklasik_maliyet", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="satirlar", to="construction.yaklasikmaliyet", verbose_name="Yaklaşık Maliyet")),
            ],
            options={"ordering": ["sira", "id"], "verbose_name": "Yaklaşık Maliyet Satırı", "verbose_name_plural": "Yaklaşık Maliyet Satırları"},
        ),
        migrations.AddConstraint(
            model_name="yaklasikmaliyet",
            constraint=models.UniqueConstraint(fields=("tenant", "proje", "yil", "versiyon"), name="uniq_yaklasik_maliyet_tenant_proje_yil_ver"),
        ),
        migrations.AddConstraint(
            model_name="yaklasikmaliyet",
            constraint=models.CheckConstraint(condition=models.Q(("versiyon__gt", 0)), name="check_yaklasik_maliyet_versiyon_pozitif"),
        ),
        migrations.AddConstraint(
            model_name="yaklasikmaliyet",
            constraint=models.CheckConstraint(condition=models.Q(("toplam_tutar__gte", 0)), name="check_yaklasik_maliyet_toplam_pozitif"),
        ),
        migrations.AddConstraint(
            model_name="yaklasikmaliyetsatiri",
            constraint=models.CheckConstraint(condition=models.Q(("miktar__gt", 0)), name="check_yaklasik_maliyet_satiri_miktar_pozitif"),
        ),
        migrations.AddConstraint(
            model_name="yaklasikmaliyetsatiri",
            constraint=models.CheckConstraint(condition=models.Q(("birim_fiyat_snapshot__gte", 0)), name="check_yaklasik_maliyet_satiri_fiyat_pozitif"),
        ),
        migrations.AddConstraint(
            model_name="yaklasikmaliyetsatiri",
            constraint=models.CheckConstraint(condition=models.Q(("toplam_tutar__gte", 0)), name="check_yaklasik_maliyet_satiri_toplam_pozitif"),
        ),
    ]
