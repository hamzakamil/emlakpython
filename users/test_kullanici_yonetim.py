"""Kullanıcı yönetimi endpoint testleri — 400 kök neden regresyonu."""

import uuid

from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User, UserRole

URL = "/api/v1/kullanicilar/"


class KullaniciYonetimTests(TestCase):
    def setUp(self):
        unique = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name="Yönetim A.Ş.", slug=f"ynt-{unique}")
        self.admin = User.objects.create_superuser(
            username=f"root_{unique}", password="Kok-Sifre-123",
            email=f"root_{unique}@example.com",
        )
        self.normal = User.objects.create_user(
            username=f"duz_{unique}", password="Duz-Sifre-123",
            email=f"duz_{unique}@example.com",
            tenant=self.tenant, role=UserRole.FINANS,
        )
        self.istemci = APIClient()
        self.istemci.force_authenticate(user=self.admin)

    def _veri(self, **ek):
        tag = uuid.uuid4().hex[:6]
        veri = {
            "username": f"yk_{tag}", "email": f"yk_{tag}@example.com",
            "role": "kullanici", "tenant": self.tenant.pk,
            "is_active": True, "password": "Guclu-Sifre-456",
        }
        veri.update(ek)
        return veri

    def test_gecerli_veri_201(self):
        yanit = self.istemci.post(URL, self._veri(), format="json")
        self.assertEqual(yanit.status_code, 201, yanit.content[:300])
        self.assertTrue(
            User.objects.get(username=yanit.json()["data"]["username"])
            .check_password("Guclu-Sifre-456")
        )

    def test_duplicate_username_400(self):
        veri = self._veri()
        self.assertEqual(self.istemci.post(URL, veri, format="json").status_code, 201)
        veri["email"] = f"farkli_{uuid.uuid4().hex[:6]}@example.com"
        yanit = self.istemci.post(URL, veri, format="json")
        self.assertEqual(yanit.status_code, 400)
        self.assertIn("username", yanit.json().get("errors", {}))

    def test_duplicate_email_400(self):
        veri = self._veri()
        self.assertEqual(self.istemci.post(URL, veri, format="json").status_code, 201)
        veri["username"] = f"yk_{uuid.uuid4().hex[:6]}"
        yanit = self.istemci.post(URL, veri, format="json")
        self.assertEqual(yanit.status_code, 400)
        self.assertIn("email", yanit.json().get("errors", {}))

    def test_zayif_parola_400(self):
        yanit = self.istemci.post(
            URL, self._veri(password="123"), format="json"
        )
        self.assertEqual(yanit.status_code, 400)
        self.assertIn("password", yanit.json().get("errors", {}))

    def test_eksik_username_400(self):
        veri = self._veri()
        del veri["username"]
        self.assertEqual(
            self.istemci.post(URL, veri, format="json").status_code, 400
        )

    def test_normal_kullanici_403(self):
        istemci = APIClient()
        istemci.force_authenticate(user=self.normal)
        self.assertEqual(
            istemci.post(URL, self._veri(), format="json").status_code, 403
        )
        self.assertEqual(istemci.get(URL).status_code, 403)
