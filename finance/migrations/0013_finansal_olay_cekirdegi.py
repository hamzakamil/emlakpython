from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0008_100_smoke_kasa_hesabi"),
        ("finance", "0012_idempotencykey"),
    ]

    operations = [
        migrations.CreateModel(
            name="FinansalOlay",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("olay_turu", models.CharField(max_length=50)),
                ("kaynak_turu", models.CharField(max_length=100)),
                ("kaynak_id", models.PositiveBigIntegerField()),
                ("olay_anahtari", models.CharField(max_length=255)),
                ("tarih", models.DateField()),
                ("aciklama", models.CharField(blank=True, max_length=255)),
                (
                    "durum",
                    models.CharField(
                        choices=[("taslak", "Taslak"), ("kayitli", "Kayıtlı"), ("iptal", "İptal")],
                        default="taslak",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="tenants.tenant",
                        verbose_name="Tenant",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["tenant", "kaynak_turu", "kaynak_id"], name="finance_fin_tenant__7e4ca2_idx"),
                    models.Index(fields=["tenant", "olay_turu", "tarih"], name="finance_fin_tenant__be0f04_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="FinansalOlayLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("islem", models.CharField(max_length=50)),
                ("durum", models.CharField(max_length=20)),
                ("veri", models.JSONField(blank=True, default=dict)),
                ("hata", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "olay",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="loglar", to="finance.finansalolay"),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="tenants.tenant",
                        verbose_name="Tenant",
                    ),
                ),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.CreateModel(
            name="FinansalOlaySatiri",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("borc", models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ("alacak", models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ("aciklama", models.CharField(blank=True, max_length=255)),
                (
                    "hesap",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="finansal_olay_satirlari", to="accounting.hesapplani"),
                ),
                (
                    "olay",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="satirlar", to="finance.finansalolay"),
                ),
            ],
            options={},
        ),
        migrations.AddConstraint(
            model_name="finansalolay",
            constraint=models.UniqueConstraint(fields=("tenant", "olay_anahtari"), name="uniq_finansal_olay_tenant_key"),
        ),
        migrations.AddConstraint(
            model_name="finansalolaysatiri",
            constraint=models.CheckConstraint(
                condition=models.Q(("borc__gte", 0), ("alacak__gte", 0)),
                name="fin_olay_satiri_nonnegative",
            ),
        ),
    ]
