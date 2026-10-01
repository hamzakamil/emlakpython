from decimal import Decimal

from django.test import TestCase

from tenants.models import Tenant

from .models import Poz, PozFiyat, PozGrubu, Proje, YaklasikMaliyet, YaklasikMaliyetSatiri
from .services.yaklasik_maliyet import hesapla, revize


class YaklasikMaliyetTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="A", slug="a")
        self.other_tenant = Tenant.objects.create(name="B", slug="b")
        self.grup = PozGrubu.objects.create(tenant=self.tenant, kod="G", ad="Grup")
        self.poz = Poz.objects.create(
            tenant=self.tenant, poz_no="P-1", ad="İş", birim="m", grup=self.grup
        )
        PozFiyat.objects.create(
            tenant=self.tenant, poz=self.poz, yil=2026, birim_fiyat=Decimal("12.50")
        )
        self.proje = Proje.objects.create(tenant=self.tenant, proje_kodu="PR-1", ad="Proje")

    def test_totals_and_active_price_snapshot(self):
        maliyet = YaklasikMaliyet.objects.create(tenant=self.tenant, proje=self.proje, yil=2026)
        satir = YaklasikMaliyetSatiri.objects.create(
            tenant=self.tenant, yaklasik_maliyet=maliyet, poz=self.poz, miktar=Decimal("4")
        )
        self.assertEqual(satir.birim_fiyat_snapshot, Decimal("12.50"))
        self.assertEqual(hesapla(maliyet).toplam_tutar, Decimal("50.00"))
        PozFiyat.objects.filter(pk__isnull=False).update(birim_fiyat=Decimal("99.00"))
        satir.refresh_from_db()
        self.assertEqual(satir.birim_fiyat_snapshot, Decimal("12.50"))

    def test_revision_copies_lines_and_keeps_original(self):
        maliyet = YaklasikMaliyet.objects.create(tenant=self.tenant, proje=self.proje, yil=2026)
        YaklasikMaliyetSatiri.objects.create(
            tenant=self.tenant, yaklasik_maliyet=maliyet, poz=self.poz, miktar=Decimal("2")
        )
        yeni = revize(maliyet)
        self.assertEqual(yeni.versiyon, 2)
        self.assertEqual(yeni.satirlar.count(), 1)
        self.assertEqual(maliyet.satirlar.count(), 1)
        self.assertEqual(yeni.toplam_tutar, Decimal("25.00"))

    def test_tenant_isolation_is_enforced_by_queryset(self):
        YaklasikMaliyet.objects.create(
            tenant=self.tenant, proje=self.proje, yil=2026
        )
        diger_proje = Proje.objects.create(
            tenant=self.other_tenant, proje_kodu="PR-2", ad="Diğer"
        )
        YaklasikMaliyet.objects.create(
            tenant=self.other_tenant, proje=diger_proje, yil=2026
        )
        self.assertEqual(
            YaklasikMaliyet.objects.filter(tenant=self.tenant).count(), 1
        )
