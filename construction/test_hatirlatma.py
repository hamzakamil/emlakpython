from datetime import date, timedelta

from django.test import TestCase

from tenants.models import Tenant

from .models import Hatirlatma, HatirlatmaKurali, Proje
from .services.hatirlatma import gunluk_getir, hatirlatmalari_uret


class HatirlatmaTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Hatırlatma", slug="hatirlatma")

    def test_default_rules_are_seeded_idempotently(self):
        hatirlatmalari_uret(self.tenant.id, date(2026, 1, 1))
        self.assertEqual(HatirlatmaKurali.objects.filter(tenant=self.tenant).count(), 10)
        hatirlatmalari_uret(self.tenant.id, date(2026, 1, 1))
        self.assertEqual(HatirlatmaKurali.objects.filter(tenant=self.tenant).count(), 10)

    def test_daily_generation_is_idempotent(self):
        tarih = date(2026, 2, 1)
        Proje.objects.create(
            tenant=self.tenant,
            proje_kodu="P-1",
            ad="Proje",
            sozlesme_bitis_tarihi=tarih + timedelta(days=30),
        )
        self.assertEqual(hatirlatmalari_uret(self.tenant.id, tarih), 1)
        self.assertEqual(hatirlatmalari_uret(self.tenant.id, tarih), 0)
        self.assertEqual(gunluk_getir(self.tenant.id, tarih).count(), 1)

    def test_reminders_are_tenant_isolated(self):
        diger = Tenant.objects.create(name="Diğer", slug="diger")
        Hatirlatma.objects.create(
            tenant=diger,
            baslik="Diğer",
            ilgili_modul="proje",
            hatirlatma_tarihi=date(2026, 1, 1),
        )
        self.assertEqual(gunluk_getir(self.tenant.id, date(2026, 1, 1)).count(), 0)
