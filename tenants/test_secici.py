"""Tenant seçici testleri — JWT claim'leri, /tenants/ listesi, X-Tenant-Id kapsamı.

Kural 5 (multi-tenant izolasyonu) regresyon güvencesi:
- Normal kullanıcı başlık gönderse bile kendi tenant'ından çıkamaz.
- Süper admin başlıksız global görür; başlıkla tek tenant'a daralır.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from construction.models import Poz, PozGrubu
from tenants.models import Tenant
from users.models import User, UserRole


class TenantSeciciTests(TestCase):
    def setUp(self):
        self.t1 = Tenant.objects.create(name="Firma 1", slug="secici-1")
        self.t2 = Tenant.objects.create(name="Firma 2", slug="secici-2")
        self.g1 = PozGrubu.objects.create(tenant=self.t1, kod="S1", ad="Seçici T1")
        self.g2 = PozGrubu.objects.create(tenant=self.t2, kod="S2", ad="Seçici T2")
        Poz.objects.create(tenant=self.t1, poz_no="S-1", ad="Poz T1", birim="m", grup=self.g1)
        Poz.objects.create(tenant=self.t2, poz_no="S-2", ad="Poz T2", birim="m", grup=self.g2)
        self.superuser = User.objects.create_superuser(
            username="root", password="x", email="root@example.com",
        )
        self.normal = User.objects.create_user(
            username="normal", password="x", email="normal@example.com",
            tenant=self.t1, role=UserRole.MALIYET_MUHENDISI,
        )

    def _client(self, user) -> APIClient:
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    # --- JWT claim'leri ---

    def test_token_tenant_claimlerini_tasir(self):
        response = APIClient().post(
            "/api/v1/auth/token/",
            {"username": "normal", "password": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        access = response.json()["data"]["access"]
        payload = AccessToken(access).payload
        self.assertEqual(payload["tenant_id"], self.t1.pk)
        self.assertEqual(payload["role"], UserRole.MALIYET_MUHENDISI)

    def test_superuser_token_tenant_id_none(self):
        response = APIClient().post(
            "/api/v1/auth/token/",
            {"username": "root", "password": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = AccessToken(response.json()["data"]["access"]).payload
        self.assertIsNone(payload["tenant_id"])

    # --- /tenants/ listesi ---

    def test_tenants_listesi_superuser_acik(self):
        response = self._client(self.superuser).get("/api/v1/tenants/")
        self.assertEqual(response.status_code, 200)
        adlar = [t["slug"] for t in response.json()["data"]["results"]]
        self.assertIn("secici-1", adlar)
        self.assertIn("secici-2", adlar)

    def test_tenants_listesi_normal_kullaniciya_kapali(self):
        response = self._client(self.normal).get("/api/v1/tenants/")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["success"])

    def test_tenants_listesi_staff_olmayan_superuser_disi_kapali(self):
        # is_staff=True ama is_superuser=False (örn. tenant_admin) → 403.
        staff = User.objects.create_user(
            username="staff", password="x", email="staff@example.com",
            tenant=self.t1, role=UserRole.TENANT_ADMIN, is_staff=True,
        )
        response = self._client(staff).get("/api/v1/tenants/")
        self.assertEqual(response.status_code, 403)

    # --- X-Tenant-Id kapsam daraltma ---

    def _poz_adlari(self, client, **extra):
        response = client.get("/api/v1/construction/pozlar/", **extra)
        self.assertEqual(response.status_code, 200)
        return sorted(p["ad"] for p in response.json()["data"]["results"])

    def test_normal_kullanici_baslikla_baska_tenanta_gecemez(self):
        client = self._client(self.normal)
        adlar = self._poz_adlari(client, HTTP_X_TENANT_ID=str(self.t2.pk))
        self.assertEqual(adlar, ["Poz T1"])

    def test_superuser_basliksiz_global_gorur(self):
        self.assertEqual(
            self._poz_adlari(self._client(self.superuser)), ["Poz T1", "Poz T2"]
        )

    def test_superuser_baslikla_kapsam_daraltir(self):
        client = self._client(self.superuser)
        self.assertEqual(
            self._poz_adlari(client, HTTP_X_TENANT_ID=str(self.t1.pk)), ["Poz T1"]
        )
        self.assertEqual(
            self._poz_adlari(client, HTTP_X_TENANT_ID=str(self.t2.pk)), ["Poz T2"]
        )

    def test_superuser_gecersiz_baslikta_global_gorur(self):
        adlar = self._poz_adlari(self._client(self.superuser), HTTP_X_TENANT_ID="gecersiz")
        self.assertEqual(adlar, ["Poz T1", "Poz T2"])

    # --- /auth/me tenant_ad ---

    def test_me_tenant_adini_verir(self):
        response = self._client(self.normal).get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["tenant_ad"], "Firma 1")

    def test_me_tenantsiz_superuser_tenant_ad_none(self):
        response = self._client(self.superuser).get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["data"]["tenant_ad"])
