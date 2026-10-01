"""import_yapi_sinifi — yapı sınıfı birim maliyetlerini içe aktarır.

Kullanım örneği::

    python manage.py import_yapi_sinifi --tenant insaat --dosya yapi_sinifi.csv

Sütunlar (bkz. docs/ornekler/import_yapi_sinifi_ornek.csv):
sinif_kodu;yil;birim_maliyet
"""

from django.core.management.base import BaseCommand, CommandError

from tenants.models import Tenant
from tenants.utils import tenant_baglam

from construction.imports import ImportHatasi, csv_satirlari_oku, import_yapi_sinifi_verisi


class Command(BaseCommand):
    help = (
        "Yapı sınıfı (I-A … V-E) yıllık birim maliyetlerini CSV'den içe aktarır. "
        "Girişler normalize edilir (örn. '4A' → 'IV-A'); aynı yıl+sinif güncellenir, "
        "hiçbir kayıt silinmez."
    )

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="Tenant slug (örn. insaat)")
        parser.add_argument("--dosya", required=True, help="CSV dosya yolu")
        parser.add_argument(
            "--ayrac", default=";", help="CSV ayraç karakteri (varsayılan: ';')"
        )

    def handle(self, *args, **options):
        slug = options["tenant"]
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant bulunamadı: {slug!r}")

        try:
            satirlar = csv_satirlari_oku(options["dosya"], ayrac=options["ayrac"])
        except OSError as exc:
            raise CommandError(f"CSV dosyası okunamadı: {exc}")

        try:
            with tenant_baglam(tenant):
                ozet = import_yapi_sinifi_verisi(tenant, satirlar)
        except (ImportHatasi, ValueError) as exc:
            raise CommandError(
                f"İçe aktarma başarısız (tüm değişiklikler geri alındı): {exc}"
            )

        self.stdout.write(self.style.SUCCESS("İçe aktarma tamamlandı."))
        self.stdout.write(ozet.ozet_metni())
