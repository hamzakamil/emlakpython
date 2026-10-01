from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("cari", "0001_initial"),
        ("construction", "0004_hakedis_donem_compatibility"),
        ("finance", "0003_fatura_rapor_ayar"),
    ]

    operations = [
        migrations.CreateModel(
            name="CekSenet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tur", models.CharField(choices=[("cek", "Çek"), ("senet", "Senet")], max_length=10, verbose_name="Tür")),
                ("numara", models.CharField(max_length=50, verbose_name="Belge No")),
                ("tutar", models.DecimalField(decimal_places=2, max_digits=15, verbose_name="Tutar (₺)")),
                ("vade_tarihi", models.DateField(verbose_name="Vade Tarihi")),
                ("durum", models.CharField(choices=[("bekliyor", "Bekliyor"), ("tahsil_edildi", "Tahsil Edildi"), ("odendi", "Ödendi"), ("karsiliksiz", "Karşılıksız"), ("iptal", "İptal")], default="bekliyor", max_length=20)),
                ("aciklama", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("cari", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cek_senetler", to="cari.cari")),
                ("hesap", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cek_senetler", to="finance.kasabankahesabi")),
                ("proje", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cek_senetler", to="construction.proje")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant")),
            ],
            options={"ordering": ["durum", "vade_tarihi", "id"]},
        ),
        migrations.AddConstraint(
            model_name="ceksenet",
            constraint=models.UniqueConstraint(fields=("tenant", "tur", "numara"), name="uniq_cek_senet_tenant_numara"),
        ),
    ]
