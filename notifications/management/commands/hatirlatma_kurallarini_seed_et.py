from django.core.management.base import BaseCommand

from tenants.models import Tenant

from notifications.services.hatirlatma import kurallari_seed_et


class Command(BaseCommand):
    help = "Tüm tenantlar için merkezi hatırlatma kurallarını idempotent olarak oluşturur."

    def handle(self, *args, **options):
        toplam = 0
        for tenant in Tenant.objects.filter(is_active=True):
            kurallari_seed_et(tenant.id)
            toplam += 1
        self.stdout.write(self.style.SUCCESS(f"{toplam} tenant için hatırlatma kuralları hazırlandı."))
