import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("construction", "0012_poz_analiz_nakliye_mesafe")]

    operations = [
        migrations.CreateModel(
            name="Hatirlatma",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("baslik", models.CharField(max_length=255, verbose_name="Başlık")),
                ("aciklama", models.TextField(blank=True, verbose_name="Açıklama")),
                ("ilgili_modul", models.CharField(max_length=80, verbose_name="İlgili Modül")),
                ("ilgili_kayit_id", models.PositiveBigIntegerField(blank=True, null=True, verbose_name="İlgili Kayıt ID")),
                ("ilgili_kayit_tipi", models.CharField(blank=True, max_length=120, verbose_name="İlgili Kayıt Tipi")),
                ("hatirlatma_tarihi", models.DateField(verbose_name="Hatırlatma Tarihi")),
                ("seviye", models.CharField(choices=[("kritik", "Kritik"), ("uyari", "Uyarı"), ("bilgi", "Bilgi")], default="bilgi", max_length=10)),
                ("durum", models.CharField(choices=[("bekliyor", "Bekliyor"), ("okundu", "Okundu"), ("tamamlandi", "Tamamlandı"), ("iptal", "İptal")], default="bekliyor", max_length=12)),
                ("tekrarlama_tipi", models.CharField(choices=[("yok", "Tekrarsız"), ("gunluk", "Günlük"), ("haftalik", "Haftalık"), ("aylik", "Aylık")], default="yok", max_length=10)),
                ("tekrarlama_gun", models.PositiveSmallIntegerField(default=0, verbose_name="Tekrarlama Günü")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("sorumlu_kullanici", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="hatirlatmalar", to="users.user", verbose_name="Sorumlu Kullanıcı")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant", verbose_name="Tenant")),
            ],
            options={"ordering": ["hatirlatma_tarihi", "-created_at"]},
        ),
        migrations.CreateModel(
            name="HatirlatmaKurali",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ilgili_modul", models.CharField(max_length=80, verbose_name="İlgili Modül")),
                ("tetikleyici", models.CharField(max_length=80, verbose_name="Tetikleyici")),
                ("once_gun_sayisi", models.PositiveSmallIntegerField(default=0, verbose_name="Önce Gün Sayısı")),
                ("seviye", models.CharField(choices=[("kritik", "Kritik"), ("uyari", "Uyarı"), ("bilgi", "Bilgi")], default="uyari", max_length=10)),
                ("aktif_mi", models.BooleanField(default=True, verbose_name="Aktif")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant", verbose_name="Tenant")),
            ],
            options={"ordering": ["ilgili_modul", "once_gun_sayisi"]},
        ),
        migrations.AddField(model_name="hakedis", name="odeme_vadesi", field=models.DateField(blank=True, null=True, verbose_name="Ödeme Vadesi")),
        migrations.AddField(model_name="leaseassistance", name="aylik_odeme_gunu", field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Aylık Ödeme Günü")),
        migrations.AddField(model_name="leaseassistance", name="baslangic_tarihi", field=models.DateField(blank=True, null=True, verbose_name="Başlangıç Tarihi")),
        migrations.AddField(model_name="leaseassistance", name="bitis_tarihi", field=models.DateField(blank=True, null=True, verbose_name="Bitiş Tarihi")),
        migrations.AddField(model_name="leaseassistance", name="sure_ay", field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Süre (Ay)")),
        migrations.AddField(model_name="leaseassistance", name="tahliye_son_tarihi", field=models.DateField(blank=True, null=True, verbose_name="Tahliye Son Tarihi")),
        migrations.AddField(model_name="proje", name="gecici_kabul_tarihi", field=models.DateField(blank=True, null=True, verbose_name="Geçici Kabul Tarihi")),
        migrations.AddField(model_name="proje", name="kesin_kabul_tarihi", field=models.DateField(blank=True, null=True, verbose_name="Kesin Kabul Tarihi")),
        migrations.AddField(model_name="proje", name="sozlesme_bitis_tarihi", field=models.DateField(blank=True, null=True, verbose_name="Sözleşme Bitiş Tarihi")),
        migrations.AddField(model_name="riskstructure", name="asama", field=models.CharField(blank=True, max_length=100, verbose_name="Aşama")),
        migrations.AddField(model_name="riskstructure", name="baslangic_tarihi", field=models.DateField(blank=True, null=True, verbose_name="Başlangıç Tarihi")),
        migrations.AddField(model_name="riskstructure", name="hedef_bitis_tarihi", field=models.DateField(blank=True, null=True, verbose_name="Hedef Bitiş Tarihi")),
        migrations.AddField(model_name="riskstructure", name="sonraki_adim_tarihi", field=models.DateField(blank=True, null=True, verbose_name="Sonraki Adım Tarihi")),
        migrations.AddField(model_name="taseronsozlesi", name="teminat_bitis_tarihi", field=models.DateField(blank=True, null=True, verbose_name="Teminat Bitiş Tarihi")),
        migrations.AddConstraint(model_name="hatirlatma", constraint=models.UniqueConstraint(fields=("tenant", "ilgili_modul", "ilgili_kayit_id", "hatirlatma_tarihi"), name="uniq_hatirlatma_tenant_kayit_tarih")),
        migrations.AddConstraint(model_name="hatirlatmakurali", constraint=models.UniqueConstraint(fields=("tenant", "ilgili_modul", "tetikleyici", "once_gun_sayisi"), name="uniq_hatirlatma_kurali_tenant_tetik")),
        migrations.AddIndex(model_name="hatirlatma", index=models.Index(fields=("tenant", "hatirlatma_tarihi", "durum"), name="construction_hatirlatma_tarih_idx")),
        migrations.AddIndex(model_name="hatirlatma", index=models.Index(fields=("tenant", "ilgili_modul", "ilgili_kayit_id"), name="construction_hatirlatma_kayit_idx")),
    ]
