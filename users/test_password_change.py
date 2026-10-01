"""FAZ 7Q — self-service şifre değiştirme: doğruluk + güvenlik."""

import uuid

from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User, UserRole

URL = "/api/v1/auth/password/change/"


class SifreDegistirmeTests(TestCase):
    def setUp(self):
        unique = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name="Profil A.Ş.", slug=f"prf-{unique}")
        self.user = User.objects.create_user(
            username=f"prf_{unique}", password="Eski-Sifre-123",
            email=f"prf_{unique}@example.com",
            tenant=self.tenant, role=UserRole.FINANS,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _degistir(self, **veri):
        return self.client.post(URL, veri, format="json")

    def test_basariyla_degisir_ve_yeniyle_login_olur(self):
        yanit = self._degistir(
            mevcut_sifre="Eski-Sifre-123", yeni_sifre="Yeni-Sifre-456",
            yeni_sifre_tekrar="Yeni-Sifre-456",
        )
        self.assertEqual(yanit.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Yeni-Sifre-456"))
        self.assertFalse(self.user.check_password("Eski-Sifre-123"))

    def test_yanlis_mevcut_reddedilir(self):
        yanit = self._degistir(
            mevcut_sifre="yalnis", yeni_sifre="Yeni-Sifre-456",
            yeni_sifre_tekrar="Yeni-Sifre-456",
        )
        self.assertEqual(yanit.status_code, 400)

    def test_eslesmeyen_tekrar_reddedilir(self):
        yanit = self._degistir(
            mevcut_sifre="Eski-Sifre-123", yeni_sifre="Yeni-Sifre-456",
            yeni_sifre_tekrar="Farkli-789",
        )
        self.assertEqual(yanit.status_code, 400)

    def test_zayif_sifre_reddedilir(self):
        yanit = self._degistir(
            mevcut_sifre="Eski-Sifre-123", yeni_sifre="123",
            yeni_sifre_tekrar="123",
        )
        self.assertEqual(yanit.status_code, 400)

    def test_eksik_alan_reddedilir(self):
        self.assertEqual(self._degistir(yeni_sifre="Yeni-Sifre-456").status_code, 400)

    def test_girissiz_401(self):
        yanit = APIClient().post(URL, {
            "mevcut_sifre": "x", "yeni_sifre": "Yeni-Sifre-456",
            "yeni_sifre_tekrar": "Yeni-Sifre-456",
        }, format="json")
        self.assertEqual(yanit.status_code, 401)
