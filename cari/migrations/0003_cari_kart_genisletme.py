from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cari", "0002_carihareket_fatura"),
        ("construction", "0008_ifc_import"),
    ]

    operations = [
        migrations.AddField(
            model_name="cari",
            name="tc_kimlik_no",
            field=models.CharField(blank=True, max_length=11, verbose_name="T.C. Kimlik No"),
        ),
        migrations.AddField(
            model_name="cari",
            name="ticaret_sicil_no",
            field=models.CharField(blank=True, max_length=50, verbose_name="Ticaret Sicil No"),
        ),
        migrations.AddField(
            model_name="cari",
            name="mersis_no",
            field=models.CharField(blank=True, max_length=16, verbose_name="MERSİS No"),
        ),
        migrations.AddField(
            model_name="cari",
            name="vergi_mukellefiyeti",
            field=models.CharField(
                choices=[
                    ("kdv_mukellefi", "KDV Mükellefi"),
                    ("kdv_istisna", "KDV İstisna"),
                    ("basit_usul", "Basit Usul"),
                    ("vergi_mukellefi_degil", "Vergi Mükellefi Değil"),
                ],
                default="kdv_mukellefi",
                max_length=30,
                verbose_name="Vergi Mükellefiyeti",
            ),
        ),
        migrations.AddField(
            model_name="cari",
            name="fatura_adresi",
            field=models.TextField(blank=True, verbose_name="Fatura Adresi"),
        ),
        migrations.AddField(
            model_name="cari",
            name="sevk_adresi",
            field=models.TextField(blank=True, verbose_name="Sevk Adresi"),
        ),
        migrations.AddField(
            model_name="cari",
            name="il",
            field=models.CharField(blank=True, max_length=100, verbose_name="İl"),
        ),
        migrations.AddField(
            model_name="cari",
            name="ilce",
            field=models.CharField(blank=True, max_length=100, verbose_name="İlçe"),
        ),
        migrations.AddField(
            model_name="cari",
            name="posta_kodu",
            field=models.CharField(blank=True, max_length=10, verbose_name="Posta Kodu"),
        ),
        migrations.AddField(
            model_name="cari",
            name="yetkili_kisi",
            field=models.CharField(blank=True, max_length=150, verbose_name="Yetkili Kişi"),
        ),
        migrations.AddField(
            model_name="cari",
            name="yetkili_telefon",
            field=models.CharField(blank=True, max_length=20, verbose_name="Yetkili Telefon"),
        ),
        migrations.AddField(
            model_name="cari",
            name="cep_telefonu",
            field=models.CharField(blank=True, max_length=20, verbose_name="Cep Telefonu"),
        ),
        migrations.AddField(
            model_name="cari",
            name="eposta",
            field=models.EmailField(blank=True, max_length=254, verbose_name="E-posta"),
        ),
        migrations.AddField(
            model_name="cari",
            name="web_sitesi",
            field=models.URLField(blank=True, verbose_name="Web Sitesi"),
        ),
        migrations.AddField(
            model_name="cari",
            name="banka_adi",
            field=models.CharField(blank=True, max_length=150, verbose_name="Banka Adı"),
        ),
        migrations.AddField(
            model_name="cari",
            name="sube_adi",
            field=models.CharField(blank=True, max_length=150, verbose_name="Şube Adı"),
        ),
        migrations.AddField(
            model_name="cari",
            name="odeme_sekli",
            field=models.CharField(
                choices=[
                    ("nakit", "Nakit"), ("havale", "Havale"), ("cek", "Çek"),
                    ("senet", "Senet"), ("kredi_karti", "Kredi Kartı"), ("takas", "Takas"),
                ],
                default="havale",
                max_length=20,
                verbose_name="Ödeme Şekli",
            ),
        ),
        migrations.AddField(
            model_name="cari",
            name="vade_gunu",
            field=models.PositiveIntegerField(default=0, verbose_name="Vade Günü"),
        ),
        migrations.AddField(
            model_name="cari",
            name="iskonto_orani",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name="İskonto Oranı"),
        ),
        migrations.AddField(
            model_name="cari",
            name="risk_limiti",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name="Risk Limiti"),
        ),
        migrations.AddField(
            model_name="cari",
            name="para_birimi",
            field=models.CharField(
                choices=[("TRY", "TRY"), ("USD", "USD"), ("EUR", "EUR"), ("GBP", "GBP")],
                default="TRY",
                max_length=3,
                verbose_name="Para Birimi",
            ),
        ),
        migrations.AddField(
            model_name="cari",
            name="muhasebe_hesap_kodu",
            field=models.CharField(blank=True, max_length=30, verbose_name="Muhasebe Hesap Kodu"),
        ),
        migrations.AddField(
            model_name="cari",
            name="e_fatura_profili",
            field=models.CharField(
                choices=[("e_fatura", "e-Fatura"), ("e_arsiv", "e-Arşiv"), ("kagit", "Kağıt")],
                default="kagit",
                max_length=10,
                verbose_name="e-Fatura Profili",
            ),
        ),
        migrations.AddField(
            model_name="cari",
            name="grup",
            field=models.CharField(blank=True, max_length=150, verbose_name="Grup"),
        ),
        migrations.AddField(
            model_name="cari",
            name="proje",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cari_kartlari",
                to="construction.proje",
                verbose_name="Proje",
            ),
        ),
        migrations.AddField(
            model_name="cari",
            name="notlar",
            field=models.TextField(blank=True, verbose_name="Notlar"),
        ),
    ]
