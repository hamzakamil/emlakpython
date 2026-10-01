from django.test import TestCase
from rest_framework.test import APIClient

from cari.models import Cari
from finance.models import Fatura
from tenants.models import Tenant
from users.models import User, UserRole


class FaturaApiTest(TestCase):
    def setUp(self):
        import uuid
        unique = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name="Fatura A.S.", slug=f"fatura-as-{unique}")
        self.user = User.objects.create_user(
            username=f"fatura-finans-{unique}", password="test", tenant=self.tenant,
            role=UserRole.FINANS, email=f"fatura-finans-{unique}@example.com",
        )
        self.cari = Cari.objects.create(tenant=self.tenant, ad="Test Cari")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_fatura_olusturulur_ve_listelenir(self):
        response = self.client.post(
            "/api/v1/finance/faturalar/",
            {
                "No": "FAT-001",
                "tarih": "2026-01-15",
                "cari": self.cari.id,
                "tutar": "1000.00",
                "durum": "aktif",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["No"], "FAT-001")
        self.assertEqual(Fatura.objects.count(), 1)

    def test_zero_tutar_reddedilir(self):
        response = self.client.post(
            "/api/v1/finance/faturalar/",
            {"No": "FAT-002", "tarih": "2026-01-15", "tutar": "0"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_satirli_fatura_kdv_tevkifat_hesaplar(self):
        payload = {
            "No": "FAT-SATIR-001",
            "tarih": "2026-01-15",
            "cari": self.cari.id,
            "tutar": "2100.00",
            "kalemler": [
                {
                    "aciklama": "Beton hizmeti",
                    "miktar": "2",
                    "birim": "M3",
                    "birim_fiyat": "1000",
                    "kdv_orani": "20",
                    "tevkifat_orani": "50",
                }
            ],
        }
        response = self.client.post(
            "/api/v1/finance/faturalar/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["tutar"], "2200.00")
        self.assertEqual(response.json()["data"]["ara_toplam"], "2000.00")
