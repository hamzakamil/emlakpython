"""Standart poz grubu ağacını tenant bazında idempotent olarak oluşturur.

Bu komut resmi YFK poz/fiyat kaydı üretmez. Doğrulanabilir resmi veri için
``import_pozlar`` komutunun kaynak CSV akışı kullanılmalıdır.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from construction.models import PozGrubu
from tenants.models import Tenant
from tenants.utils import tenant_baglam


ANA_GRUPLAR = [
    ("01", "Hafriyat ve Zemin İşleri"), ("02", "Temel İşleri"),
    ("03", "Betonarme İşleri"), ("04", "Kalıp ve İskele İşleri"),
    ("05", "Donatı / Demir İşleri"), ("06", "Duvar İşleri"),
    ("07", "Çatı İşleri"), ("08", "Su Yalıtımı"), ("09", "Isı Yalıtımı"),
    ("10", "Ses Yalıtımı"), ("11", "Cephe İşleri"), ("12", "Sıva İşleri"),
    ("13", "Alçı ve Asma Tavan İşleri"), ("14", "Şap İşleri"),
    ("15", "Seramik ve Fayans İşleri"), ("16", "Mermer ve Doğal Taş İşleri"),
    ("17", "Parke ve Ahşap İşleri"), ("18", "Boya İşleri"),
    ("19", "Kapı İşleri"), ("20", "Pencere ve Doğrama İşleri"),
    ("21", "Cam İşleri"), ("22", "Sıhhi Tesisat"), ("23", "Isıtma Tesisatı"),
    ("24", "Soğutma ve Klima"), ("25", "Havalandırma"),
    ("26", "Yangın Tesisatı"), ("27", "Elektrik Tesisatı"),
    ("28", "Zayıf Akım Sistemleri"), ("29", "Asansör"),
    ("30", "Merdiven ve Korkuluklar"), ("31", "Metal İşleri"),
    ("32", "Sabit Mobilya ve Mutfak"), ("33", "Çevre Düzenleme"),
    ("34", "Peyzaj"), ("35", "Dış Altyapı"),
    ("36", "Test, Devreye Alma ve Teslim"), ("99", "Özel / Projeye Özel Pozlar"),
]

ALT_GRUPLAR = {
    "03": ["Beton", "Hazır Beton", "Betonarme Betonları", "Özel Betonlar"],
    "04": ["Ahşap Kalıp", "Plywood Kalıp", "Çelik Kalıp", "Özel Kalıplar", "İş İskelesi", "Kalıp Altı İskele"],
    "05": ["Nervürlü Donatı", "Düz Donatı", "Hasır Çelik", "Ankraj ve Gömme Parçalar"],
    "06": ["Tuğla Duvar", "Gazbeton Duvar", "Bims / Beton Blok", "Bölme Duvar"],
    "07": ["Ahşap Çatı", "Çelik Çatı", "Betonarme Çatı", "Çatı Örtüleri", "Kiremit", "Metal Çatı", "Sandviç Panel", "Çatı Yalıtımı", "Dere ve Yağmur İnişleri"],
    "08": ["Temel Su Yalıtımı", "Teras Yalıtımı", "Çatı Su Yalıtımı", "Islak Hacim Yalıtımı", "Sürme Yalıtım", "Membran Yalıtım", "Derz ve Dilatasyon Yalıtımı"],
    "09": ["Dış Cephe Isı Yalıtımı", "Mantolama", "Çatı Isı Yalıtımı", "Döşeme Isı Yalıtımı", "Temel / Perde Isı Yalıtımı", "Boru ve Tesisat Yalıtımı"],
    "12": ["Kaba Sıva", "İnce Sıva", "Çimento Esaslı Sıva", "Alçı Sıva", "Makine Sıvası", "Dekoratif Sıva"],
    "15": ["Duvar Seramiği", "Zemin Seramiği", "Fayans", "Granit Seramik", "Porselen", "Mozaik"],
    "18": ["İç Cephe Boya", "Dış Cephe Boya", "Tavan Boya", "Metal Boya", "Ahşap Boya", "Epoksi Boya"],
    "22": ["Temiz Su", "Pis Su", "Yağmur Suyu", "Sıcak Su", "Armatürler", "Vitrifiye", "Su Depoları", "Hidrofor"],
    "23": ["Kazan", "Kombi", "Merkezi Isıtma", "Radyatör", "Yerden Isıtma", "Borulama", "Pompa", "Kolektör", "Doğalgaz Tesisatı"],
    "27": ["Kuvvetli Akım", "Aydınlatma", "Priz Tesisatı", "Pano", "Kablo", "Topraklama", "Paratoner", "Jeneratör", "UPS"],
    "28": ["Data", "Telefon", "TV", "İnterkom", "Kamera", "Hırsız Alarm", "Yangın Algılama", "Access Kontrol", "Merkezi Uydu"],
    "33": ["Bahçe Duvarı", "İstinat Duvarı", "Kaldırım", "Bordür", "Beton Saha", "Otopark", "Yol İşleri"],
    "34": ["Toprak İşleri", "Bitkisel Toprak", "Çim", "Ağaç", "Çalı", "Sulama", "Peyzaj Donatıları"],
}


class Command(BaseCommand):
    help = "Standart poz grubu ve alt grup ağacını idempotent olarak oluşturur."

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="Tenant slug (örn. insaat)")

    def handle(self, *args, **options):
        try:
            tenant = Tenant.objects.get(slug=options["tenant"], is_active=True)
        except Tenant.DoesNotExist as exc:
            raise CommandError(f"Aktif tenant bulunamadı: {options['tenant']!r}") from exc

        created_main = created_sub = existing = 0
        with tenant_baglam(tenant), transaction.atomic():
            parents = {}
            for code, name in ANA_GRUPLAR:
                parent, created = PozGrubu.objects.get_or_create(
                    tenant=tenant, kod=code,
                    defaults={"ad": name, "is_active": True},
                )
                parents[code] = parent
                if created:
                    created_main += 1
                else:
                    existing += 1
                    updates = []
                    if parent.ad != name:
                        parent.ad = name
                        updates.append("ad")
                    if not parent.is_active:
                        parent.is_active = True
                        updates.append("is_active")
                    if updates:
                        parent.save(update_fields=[*updates, "updated_at"])

            for parent_code, names in ALT_GRUPLAR.items():
                parent = parents[parent_code]
                for index, name in enumerate(names, start=1):
                    _, created = PozGrubu.objects.get_or_create(
                        tenant=tenant,
                        kod=f"{parent_code}.{index:02d}",
                        defaults={"ad": name, "ust_grup": parent, "is_active": True},
                    )
                    if created:
                        created_sub += 1
                    else:
                        existing += 1

        self.stdout.write(self.style.SUCCESS("Poz Kütüphanesi grup aktarımı tamamlandı."))
        self.stdout.write(f"Ana gruplar oluşturulan: {created_main}")
        self.stdout.write(f"Alt gruplar oluşturulan: {created_sub}")
        self.stdout.write(f"Mevcut kayıtlar: {existing}")
        self.stdout.write("Yapı sınıfı IV-A: Poz grubu değildir; resmi maliyet verisi olmadan seed edilmedi.")
        self.stdout.write("Gerçek YFK pozları: 0; doğrulanabilir resmi veri dosyası verilmedi.")
