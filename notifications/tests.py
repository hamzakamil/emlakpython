from datetime import date, timedelta

from django.test import TestCase

from construction.models import Proje
from tenants.models import Tenant

from .models import Hatirlatma, HatirlatmaKurali
from .services.hatirlatma import gunluk_getir, hatirlatmalari_uret


class MerkeziHatirlatmaTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Bildirim Test", slug="bildirim-test")

    def test_rules_are_seeded_without_duplicates(self):
        hatirlatmalari_uret(self.tenant.id, date(2026, 9, 18))
        hatirlatmalari_uret(self.tenant.id, date(2026, 9, 18))
        self.assertEqual(HatirlatmaKurali.objects.filter(tenant_id=self.tenant.id).count(), 13)

    def test_project_reminder_is_idempotent_and_daily(self):
        bugun = date(2026, 9, 18)
        Proje.objects.create(
            tenant=self.tenant,
            proje_kodu="P-1",
            ad="Test Projesi",
            sozlesme_bitis_tarihi=bugun + timedelta(days=30),
        )
        self.assertEqual(hatirlatmalari_uret(self.tenant.id, bugun), 1)
        self.assertEqual(hatirlatmalari_uret(self.tenant.id, bugun), 0)
        self.assertEqual(gunluk_getir(type("Kullanici", (), {"tenant_id": self.tenant.id})(), bugun).count(), 1)

    def test_tenant_isolation(self):
        other = Tenant.objects.create(name="Başka Firma", slug="baska-firma")
        Hatirlatma.objects.create(
            tenant_id=other.id,
            baslik="Başka firma",
            ilgili_app="construction",
            ilgili_model="Proje",
            hatirlatma_tarihi=date(2026, 9, 18),
            seviye="bilgi",
            durum="bekliyor",
            tekrarlama="yok",
            tekrarlama_gun=0,
        )
        self.assertEqual(gunluk_getir(type("Kullanici", (), {"tenant_id": self.tenant.id})(), date(2026, 9, 18)).count(), 0)
