"""/auth/me endpoint testleri — oturum sahibinin bilgisi."""

from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User, UserRole


class MeViewTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Me A.Ş.", slug="me-firma")
        self.user = User.objects.create_user(
            username="meuser", password="x", email="me@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )

    def _token(self) -> str:
        response = APIClient().post(
            "/api/v1/auth/token/",
            {"username": "meuser", "password": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["data"]["access"]

    def test_jwt_ile_me_kullanici_bilgisini_verir(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self._token()}")
        response = client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["username"], "meuser")
        self.assertEqual(body["data"]["role"], UserRole.MALIYET_MUHENDISI)
        self.assertEqual(body["data"]["tenant"], self.tenant.pk)
        self.assertNotIn("password", body["data"])

    def test_anonim_me_401(self):
        response = APIClient().get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])

