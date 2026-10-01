from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("construction", "0018_leaseassistance_odeme_bilgileri"),
    ]

    operations = [
        migrations.AddField(
            model_name="pozfiyat",
            name="donem",
            field=models.CharField(
                blank=True,
                help_text="Örn. Ocak, Şubat ... boş bırakılırsa yıl bazlı kabul edilir.",
                max_length=20,
                verbose_name="Dönem (Ay)",
            ),
        ),
        migrations.AddField(
            model_name="pozfiyat",
            name="kaynak_url",
            field=models.URLField(
                blank=True,
                help_text="Fiyatın duyurulduğu bağlantı",
                max_length=250,
                verbose_name="Kaynak URL",
            ),
        ),
        migrations.AddField(
            model_name="pozfiyat",
            name="yayin_tarihi",
            field=models.DateField(
                blank=True,
                null=True,
                help_text="Fiyatın yayımlandığı tarih",
                verbose_name="Yayın Tarihi",
            ),
        ),
        migrations.AddField(
            model_name="pozfiyat",
            name="gecerlilik_tarihi",
            field=models.DateField(
                blank=True,
                null=True,
                help_text="Fiyatın geçerli olduğu tarih",
                verbose_name="Geçerlilik Tarihi",
            ),
        ),
        migrations.AddField(
            model_name="pozfiyat",
            name="ice_aktarma_tarihi",
            field=models.DateTimeField(
                auto_now_add=True,
                help_text="Kayıt sisteme eklenme tarihi",
                verbose_name="İçe Aktarma Tarihi",
            ),
        ),
    ]
