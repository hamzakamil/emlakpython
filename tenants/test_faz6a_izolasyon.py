"""FAZ 6A — Tenant izolasyon testleri: cross-tenant FK POST/PATCH/GET/action."""

import uuid
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounting.models import HesapPlani
from cari.models import Cari
from construction.models import Poz, PozFiyat, PozGrubu, PozPlan, Proje
from tenants.models import Tenant
from users.models import User, UserRole


class Faz6aIzolasyonBase(TestCase):
    def setUp(self):
        unique = uuid.uuid4().hex[:8]
        self.tenant_a = Tenant.objects.create(name="Firma A", slug=f"firma-a-{unique}")
        self.tenant_b = Tenant.objects.create(name="Firma B", slug=f"firma-b-{unique}")
        self.user_a = User.objects.create_user(
            username=f"a_{unique}", password="x", email=f"a_{unique}@example.com",
            tenant=self.tenant_a, role=UserRole.MALIYET_MUHENDISI,
        )
        self.finans_a = User.objects.create_user(
            username=f"fin_{unique}", password="x", email=f"fin_{unique}@example.com",
            tenant=self.tenant_a, role=UserRole.FINANS,
        )
        self.muhasebe_a = User.objects.create_user(
            username=f"muh_{unique}", password="x", email=f"muh_{unique}@example.com",
            tenant=self.tenant_a, role=UserRole.MUHASEBE,
        )
        grup_a = PozGrubu.objects.create(tenant=self.tenant_a, kod="A", ad="A")
        grup_b = PozGrubu.objects.create(tenant=self.tenant_b, kod="B", ad="B")
        self.poz_a = Poz.objects.create(
            tenant=self.tenant_a, poz_no="A-1", ad="A Pozu", birim="m", grup=grup_a
        )
        PozFiyat.objects.create(
            tenant=self.tenant_a, poz=self.poz_a, yil=2026, birim_fiyat=Decimal("10")
        )
        self.proje_a = Proje.objects.create(
            tenant=self.tenant_a, proje_kodu="PA", ad="Proje A"
        )
        self.proje_b = Proje.objects.create(
            tenant=self.tenant_b, proje_kodu="PB", ad="Proje B"
        )
        self.cari_b = Cari.objects.create(tenant=self.tenant_b, ad="Yabancı Cari")
        self.hesap_b = HesapPlani.objects.create(
            tenant=self.tenant_b, kod="100", ad="Kasa", tip="aktif"
        )
        self.plan_a = PozPlan.objects.create(
            tenant=self.tenant_a, proje=self.proje_a, poz=self.poz_a, yil=2026,
            planlanan_miktar=Decimal("5"),
        )

    def _istemci(self, kullanici=None):
        istemci = APIClient()
        istemci.force_authenticate(user=kullanici or self.user_a)
        return istemci


class CrossTenantPostTests(Faz6aIzolasyonBase):
    def test_poz_plan_b_projesi_400(self):
        yanit = self._istemci().post(
            "/api/v1/construction/poz-planlari/",
            {"proje": self.proje_b.pk, "poz": self.poz_a.pk, "yil": 2026,
             "planlanan_miktar": "5"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 400)
        self.assertEqual(
            PozPlan.objects.filter(
                tenant=self.tenant_a, proje=self.proje_b
            ).count(),
            0,
        )

    def test_fatura_b_carisi_400(self):
        from finance.models import Fatura

        yanit = self._istemci(self.finans_a).post(
            "/api/v1/finance/faturalar/",
            {"No": f"YZ-{uuid.uuid4().hex[:6]}", "tarih": "2026-01-15",
             "cari": self.cari_b.pk, "tutar": "100.00"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 400)
        self.assertFalse(Fatura.objects.filter(tenant=self.tenant_a).exists())

    def test_fis_b_hesabi_400(self):
        from accounting.models import MuhasebeFisi

        yanit = self._istemci(self.muhasebe_a).post(
            "/api/v1/accounting/fisler/",
            {"fis_no": "F-YABANCI", "fis_tarihi": "2026-03-01",
             "satirlar": [
                 {"hesap": self.hesap_b.pk, "borc": "100.00", "alacak": "0.00"},
                 {"hesap": self.hesap_b.pk, "borc": "0.00", "alacak": "100.00"},
             ]},
            format="json",
        )
        self.assertEqual(yanit.status_code, 400)
        self.assertFalse(MuhasebeFisi.objects.filter(tenant=self.tenant_a).exists())

    def test_cari_hareket_b_carisi_400(self):
        from cari.models import CariHareket

        yanit = self._istemci(self.muhasebe_a).post(
            "/api/v1/cari/cari-hareketler/",
            {"cari": self.cari_b.pk, "yon": "borc", "tutar": "10.00",
             "islem_tarihi": "2026-03-01"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 400)
        self.assertFalse(CariHareket.objects.filter(tenant=self.tenant_a).exists())


class CrossTenantPatchGetActionTests(Faz6aIzolasyonBase):
    def test_patch_kendi_kaydi_b_projeye_400(self):
        yanit = self._istemci().patch(
            f"/api/v1/construction/poz-planlari/{self.plan_a.pk}/",
            {"proje": self.proje_b.pk},
            format="json",
        )
        self.assertEqual(yanit.status_code, 400)
        self.plan_a.refresh_from_db()
        self.assertEqual(self.plan_a.proje_id, self.proje_a.pk)

    def test_get_b_kaydi_404(self):
        poz_b = Poz.objects.create(
            tenant=self.tenant_b, poz_no="B-9", ad="B", birim="m",
            grup=PozGrubu.objects.create(tenant=self.tenant_b, kod="B9", ad="B9"),
        )
        PozFiyat.objects.create(
            tenant=self.tenant_b, poz=poz_b, yil=2026, birim_fiyat=Decimal("10")
        )
        plan_b = PozPlan.objects.create(
            tenant=self.tenant_b, proje=self.proje_b, poz=poz_b,
            yil=2026, planlanan_miktar=Decimal("1"),
        )
        yanit = self._istemci().get(f"/api/v1/construction/poz-planlari/{plan_b.pk}/")
        self.assertEqual(yanit.status_code, 404)

    def test_action_b_talebi_404(self):
        from purchasing.models import SatinAlmaTalebi

        talep_b = SatinAlmaTalebi.objects.create(
            tenant=self.tenant_b, proje=self.proje_b, talep_no="B-001",
            talep_sahibi=User.objects.create_user(
                username=f"b_{uuid.uuid4().hex[:8]}", password="x",
                email=f"b_{uuid.uuid4().hex[:8]}@example.com",
                tenant=self.tenant_b, role=UserRole.MALIYET_MUHENDISI,
            ),
        )
        yanit = self._istemci().post(
            f"/api/v1/purchase-requests/{talep_b.pk}/onayla/"
        )
        self.assertEqual(yanit.status_code, 404)
        talep_b.refresh_from_db()
        self.assertEqual(talep_b.durum, SatinAlmaTalebi.Durum.TASLAK)
