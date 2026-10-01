"""import_pozlar — ÇŞİDB CSV poz verisini içe aktarır (roadmap Faz 1).

Kullanım örneği::

    python manage.py import_pozlar --tenant insaat --dosya pozlar.csv ^
        --yil 2026 --kaynak "ÇŞİDB 2026 tebliği" --arsivle 2025

Sütunlar (bkz. docs/ornekler/import_poz_ornek.csv):
poz_no;grup_kodu;grup_adi;ad;birim;yil;birim_fiyat;tip;kaynak
"""

from django.core.management.base import BaseCommand, CommandError

from tenants.models import Tenant
from tenants.utils import tenant_baglam

from construction.imports import ImportHatasi, csv_satirlari_oku, import_poz_verisi


class Command(BaseCommand):
    help = (
        "ÇŞİDB poz verisini CSV'den içe aktarır (PozGrubu + Poz + yıl bazlı PozFiyat). "
        "Hiçbir kayıt silinmez; --arsivle verilen yıldaki aktif kayıtlar "
        "importta gelmezse is_active=False yapılır."
    )

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="Tenant slug (örn. insaat)")
        parser.add_argument("--dosya", required=True, help="CSV dosya yolu")
        parser.add_argument(
            "--yil", type=int, help="Satırlarda yıl sütunu yoksa kullanılır"
        )
        parser.add_argument(
            "--kaynak",
            default="",
            help="Satırlarda kaynak sütunu yoksa kullanılır (örn. 'ÇŞİDB 2026 tebliği')",
        )
        parser.add_argument(
            "--arsivle",
            type=int,
            metavar="YIL",
            help="Bu yıla ait aktif fiyatı olup importta gelmeyen pozlar arşivlenir",
        )
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
                ozet = import_poz_verisi(
                    tenant,
                    satirlar,
                    varsayilan_yil=options.get("yil"),
                    varsayilan_kaynak=options.get("kaynak", ""),
                    arsivlenecek_yil=options.get("arsivle"),
                )
        except (ImportHatasi, ValueError) as exc:
            raise CommandError(
                f"İçe aktarma başarısız (tüm değişiklikler geri alındı): {exc}"
            )

        self.stdout.write(self.style.SUCCESS("İçe aktarma tamamlandı."))
        self.stdout.write(ozet.ozet_metni())
