from django.test import TestCase

"""Tenant izolasyonu + API zarf yapısı testleri."""

from django.test import TestCase
from rest_framework.test import APIClient

from construction.models import Poz, PozGrubu
from tenants.models import Tenant
from users.models import User, UserRole


class TenantIsolationTestCase(TestCase):
    def setUp(self):
        self.t1 = Tenant.objects.create(name="Firma 1", slug="firma-1")
        self.t2 = Tenant.objects.create(name="Firma 2", slug="firma-2")
        self.u1 = User.objects.create_user(
            username="u1", password="x", email="u1@example.com",
            tenant=self.t1, role=UserRole.MALIYET_MUHENDISI,
        )
        self.u2 = User.objects.create_user(
            username="u2", password="x", email="u2@example.com",
            tenant=self.t2, role=UserRole.MALIYET_MUHENDISI,
        )
        self.g1 = PozGrubu.objects.create(tenant=self.t1, kod="BT1", ad="Beton T1")
        self.g2 = PozGrubu.objects.create(tenant=self.t2, kod="BT2", ad="Beton T2")
        self.p1 = Poz.objects.create(tenant=self.t1, poz_no="P-101", ad="Poz T1", birim="m³", grup=self.g1)
        self.p2 = Poz.objects.create(tenant=self.t2, poz_no="P-101", ad="Poz T2", birim="m³", grup=self.g2)

    def _auth(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_tenant_baska_tenanta_erisemez(self):
        response = self._auth(self.u1).get("/api/v1/construction/pozlar/")
        self.assertEqual(response.status_code, 200)
        results = response.json()["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["ad"], "Poz T1")

    def test_diger_tenant_kendi_verisini_gorur(self):
        response = self._auth(self.u2).get("/api/v1/construction/pozlar/")
        results = response.json()["data"]["results"]
        self.assertEqual([p["ad"] for p in results], ["Poz T2"])

    def test_ayni_poz_no_farkli_tenlarda_ayri_kayit(self):
        # Veri erişimi değil; iki tenant aynı poz no kullanabiliyor (izolasyon).
        self.assertEqual(Poz.objects.filter(poz_no="P-101").count(), 2)

    def test_yazmada_tenant_kullanicidan_gelir(self):
        response = self._auth(self.u1).post(
            "/api/v1/construction/pozlar/",
            {"poz_no": "P-202", "ad": "Yeni Poz", "birim": "m", "grup": self.g1.pk},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["tenant"], self.t1.pk)

    def test_success_zarf_yapisi(self):
        response = self._auth(self.u1).get("/api/v1/construction/pozlar/")
        body = response.json()
        self.assertTrue(body["success"])
        self.assertIn("data", body)
        self.assertIn("message", body)

    def test_hata_zarf_yapisi_404(self):
        response = self._auth(self.u1).get("/api/v1/construction/pozlar/99999/")
        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertTrue(body["message"])

    def test_unauth_401_zarf_yapisi(self):
        response = APIClient().get("/api/v1/construction/pozlar/")
        self.assertEqual(response.status_code, 401)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertIn("message", body)


class TenantBaglamMiddlewareTests(TestCase):
    """RLS zemini: middleware'in app.current_tenant GUC'sünü ayarladığını doğrular.

    Not: Test DB'sinde RLS policy'leri yoktur (pytest --no-migrations); burada
    yalnızca bağlam değişkeninin doğru değerle yazıldığı denetlenir.
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Bağlam A.Ş.", slug="baglam")
        self.user = User.objects.create_user(
            username="baglam", password="x", email="baglam@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )

    def _token(self) -> str:
        response = APIClient().post(
            "/api/v1/auth/token/",
            {"username": "baglam", "password": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["data"]["access"]

    def _guc(self) -> str:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('app.current_tenant', true)")
            return cursor.fetchone()[0]

    def test_jwt_isteginde_tenant_baglami_ayarlanir(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._token()}")
        response = client.get("/api/v1/construction/pozlar/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._guc(), str(self.tenant.pk))

    def test_anonim_istekte_baglam_bos(self):
        response = APIClient().get("/api/v1/construction/pozlar/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self._guc(), "")

    def test_gecersiz_token_baglami_bos_birakir(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer gecersiz.token.degeri")
        response = client.get("/api/v1/construction/pozlar/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self._guc(), "")
