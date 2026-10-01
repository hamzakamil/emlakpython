from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from decimal import Decimal
import construction.models

class Migration(migrations.Migration):
    dependencies = [
        ('construction', '0004_hakedis_donem_compatibility'),
        ('tenants', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(
            model_name='malzeme', name='qr_kodu',
            field=models.CharField(default=construction.models.yeni_malzeme_qr_kodu, help_text='Malzeme etiketi için gizli bilgi içermeyen opak kod.', max_length=40, verbose_name='QR Kodu'),
        ),
        migrations.AddConstraint(
            model_name='malzeme',
            constraint=models.UniqueConstraint(fields=('tenant', 'qr_kodu'), name='uniq_malzeme_tenant_qr'),
        ),
        migrations.CreateModel(
            name='MalzemeHareketi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('yon', models.CharField(choices=[('giris', 'Giriş'), ('cikis', 'Çıkış')], max_length=10, verbose_name='Hareket')),
                ('miktar', models.DecimalField(decimal_places=4, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal('0.0001'))], verbose_name='Miktar')),
                ('birim', models.CharField(max_length=20, verbose_name='Birim')),
                ('qr_kodu', models.CharField(max_length=40, verbose_name='QR / Manuel Kod')),
                ('gerceklesme_zamani', models.DateTimeField(verbose_name='Gerçekleşme Zamanı')),
                ('notlar', models.TextField(blank=True, verbose_name='Notlar')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktif')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Güncellenme')),
                ('kaydeden', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='malzeme_hareketleri', to=settings.AUTH_USER_MODEL, verbose_name='Kaydeden')),
                ('malzeme', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='hareketler', to='construction.malzeme', verbose_name='Malzeme')),
                ('proje', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='malzeme_hareketleri', to='construction.proje', verbose_name='Proje')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='tenants.tenant', verbose_name='Tenant')),
            ],
            options={'verbose_name': 'Malzeme Hareketi', 'verbose_name_plural': 'Malzeme Hareketleri', 'ordering': ['-gerceklesme_zamani', '-id']},
        ),
        migrations.CreateModel(
            name='SantiyeCheckIn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('giris_zamani', models.DateTimeField(verbose_name='Giriş Zamanı')),
                ('cikis_zamani', models.DateTimeField(blank=True, null=True, verbose_name='Çıkış Zamanı')),
                ('notlar', models.TextField(blank=True, verbose_name='Notlar')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktif')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Güncellenme')),
                ('kullanici', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='santiye_checkinleri', to=settings.AUTH_USER_MODEL, verbose_name='Kullanıcı')),
                ('proje', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='checkinler', to='construction.proje', verbose_name='Proje')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='tenants.tenant', verbose_name='Tenant')),
            ],
            options={'verbose_name': 'Şantiye Giriş Çıkış', 'verbose_name_plural': 'Şantiye Giriş Çıkışları', 'ordering': ['-giris_zamani', '-id']},
        ),
        migrations.AddConstraint(
            model_name='santiyecheckin',
            constraint=models.CheckConstraint(condition=models.Q(('cikis_zamani__isnull', True), ('cikis_zamani__gte', models.F('giris_zamani')), _connector='OR'), name='check_santiye_cikis_giris_sonrasi'),
        ),
    ]
