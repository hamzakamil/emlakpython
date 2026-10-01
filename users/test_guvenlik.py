"""FAZ 6F-1 — auth güvenliği: kilit, inactive, logout, rotation, prod fail-closed."""

import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import LoginDenemesi, User, UserRole


class LoginGuvenlikTests(TestCase):
    def setUp(self):
        unique = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name="Güvenlik A.Ş.", slug=f"guv-{unique}")
        self.username = f"guv_{unique}"
        self.user = User.objects.create_user(
            username=self.username, password="dogru-sifre",
            email=f"{self.username}@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )

    def _login(self, username=None, password="dogru-sifre"):
        return APIClient().post(
            "/api/v1/auth/token/",
            {"username": username or self.username, "password": password},
            format="json",
        )

    def test_dogru_parola_login_basarili(self):
        yanit = self._login()
        self.assertEqual(yanit.status_code, 200)
        veri = yanit.json()["data"]
        self.assertIn("access", veri)
        self.assertIn("refresh", veri)

    def test_yanlis_parola_sayaci_artar(self):
        self.assertEqual(self._login(password="yanlis").status_code, 401)
        kayit = LoginDenemesi.objects.get(kullanici_adi=self.username)
        self.assertEqual(kayit.basarisiz_sayisi, 1)
        self.assertIsNone(kayit.kilit_bitis)

    def test_bes_basarisiz_deneme_kilitler(self):
        for _ in range(5):
            self.assertEqual(self._login(password="yanlis").status_code, 401)
        kayit = LoginDenemesi.objects.get(kullanici_adi=self.username)
        self.assertEqual(kayit.basarisiz_sayisi, 5)
        self.assertIsNotNone(kayit.kilit_bitis)

    def test_kilitliyken_dogru_parola_reddedilir(self):
        for _ in range(5):
            self._login(password="yanlis")
        self.assertEqual(self._login().status_code, 401)

    def test_kilit_suresi_dolunca_tekrar_denenebilir(self):
        for _ in range(5):
            self._login(password="yanlis")
        kayit = LoginDenemesi.objects.get(kullanici_adi=self.username)
        kayit.kilit_bitis = timezone.now() - timedelta(seconds=1)
        kayit.save(update_fields=["kilit_bitis"])
        self.assertEqual(self._login().status_code, 200)

    def test_basarili_login_sayaci_sifirlar(self):
        for _ in range(4):
            self._login(password="yanlis")
        self.assertEqual(self._login().status_code, 200)
        self.assertFalse(
            LoginDenemesi.objects.filter(kullanici_adi=self.username).exists()
        )
        self.assertEqual(self._login(password="yanlis").status_code, 401)
        self.assertEqual(
            LoginDenemesi.objects.get(kullanici_adi=self.username).basarisiz_sayisi, 1
        )

    def test_inactive_user_login_reddedilir(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.assertEqual(self._login().status_code, 401)

    def test_inactive_tenant_login_reddedilir(self):
        self.tenant.is_active = False
        self.tenant.save(update_fields=["is_active"])
        self.assertEqual(self._login().status_code, 401)

    def test_brute_force_kullanici_var_yok_ayirt_etmez(self):
        gercek = self._login(password="yanlis")
        sahte = self._login(username="olmayan-kullanici-xyz", password="yanlis")
        self.assertEqual(gercek.status_code, sahte.status_code)
        self.assertEqual(gercek.json(), sahte.json())

    def test_hata_govdesi_sizinti_icermez(self):
        govde = self._login(password="yanlis").content.decode()
        for iz in ("Traceback", ".py", "SECRET", "password", "DATABASES"):
            self.assertNotIn(iz, govde)


class TokenYasamTests(TestCase):
    def setUp(self):
        unique = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name="Token A.Ş.", slug=f"tok-{unique}")
        self.username = f"tok_{unique}"
        self.user = User.objects.create_user(
            username=self.username, password="dogru-sifre",
            email=f"{self.username}@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )
        veri = APIClient().post(
            "/api/v1/auth/token/",
            {"username": self.username, "password": "dogru-sifre"},
            format="json",
        ).json()["data"]
        self.access = veri["access"]
        self.refresh = veri["refresh"]

    def _kimlikli(self, token=None):
        istemci = APIClient()
        istemci.credentials(HTTP_AUTHORIZATION=f"Bearer {token or self.access}")
        return istemci

    def test_inactive_user_token_reddedilir(self):
        self.assertEqual(self._kimlikli().get("/api/v1/auth/me/").status_code, 200)
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.assertEqual(self._kimlikli().get("/api/v1/auth/me/").status_code, 401)

    def test_inactive_tenant_token_reddedilir(self):
        self.assertEqual(self._kimlikli().get("/api/v1/auth/me/").status_code, 200)
        self.tenant.is_active = False
        self.tenant.save(update_fields=["is_active"])
        yanit = self._kimlikli().get("/api/v1/auth/me/")
        self.assertIn(yanit.status_code, (401, 403))

    def test_refresh_inactive_user_reddedilir(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        yanit = APIClient().post(
            "/api/v1/auth/token/refresh/", {"refresh": self.refresh}, format="json"
        )
        self.assertEqual(yanit.status_code, 401)

    def test_logout_refreshi_iptal_eder(self):
        yanit = self._kimlikli().post(
            "/api/v1/auth/logout/", {"refresh": self.refresh}, format="json"
        )
        self.assertEqual(yanit.status_code, 200)
        tekrar = APIClient().post(
            "/api/v1/auth/token/refresh/", {"refresh": self.refresh}, format="json"
        )
        self.assertEqual(tekrar.status_code, 401)

    def test_refresh_rotation_eski_token_reddedilir(self):
        ilk = APIClient().post(
            "/api/v1/auth/token/refresh/", {"refresh": self.refresh}, format="json"
        )
        self.assertEqual(ilk.status_code, 200)
        self.assertIn("refresh", ilk.json()["data"])
        eski = APIClient().post(
            "/api/v1/auth/token/refresh/", {"refresh": self.refresh}, format="json"
        )
        self.assertEqual(eski.status_code, 401)


class ProdAyarTestleri(TestCase):
    """Prod fail-closed mantığı (in-process; secret yazılmaz)."""

    @classmethod
    def _prod_modulu(cls):
        import os
        import sys
        from unittest import mock

        for mod in [m for m in sys.modules if m == "config.settings.prod"]:
            del sys.modules[mod]
        with mock.patch.dict(
            os.environ,
            {
                "DJANGO_SECRET_KEY": "x" * 64,
                "DATABASE_URL": "postgres://u:p@localhost:5432/db",
                "DJANGO_ALLOWED_HOSTS": "ornek.test",
            },
            clear=False,
        ):
            from config.settings import prod

            return prod

    def _ortamla(self, degisim, sil=()):
        import os
        from unittest import mock

        return mock.patch.dict(os.environ, degisim, clear=False)

    def test_secret_yoksa_hata(self):
        import os

        from django.core.exceptions import ImproperlyConfigured

        prod = self._prod_modulu()
        with self._ortamla({}):
            os.environ.pop("DJANGO_SECRET_KEY", None)
            with self.assertRaises(ImproperlyConfigured) as ctx:
                prod._uretimi_dogrula()
        self.assertIn("DJANGO_SECRET_KEY", str(ctx.exception))

    def test_dev_secret_ile_prod_acilmaz(self):
        from django.core.exceptions import ImproperlyConfigured

        prod = self._prod_modulu()
        with self._ortamla({"DJANGO_SECRET_KEY": "dev-only-key-xyz"}):
            with self.assertRaises(ImproperlyConfigured):
                prod._uretimi_dogrula()

    def test_db_yoksa_hata(self):
        import os

        from django.core.exceptions import ImproperlyConfigured

        prod = self._prod_modulu()
        with self._ortamla({"DJANGO_SECRET_KEY": "x" * 64}):
            os.environ.pop("DATABASE_URL", None)
            with self.assertRaises(ImproperlyConfigured) as ctx:
                prod._uretimi_dogrula()
        self.assertIn("DATABASE_URL", str(ctx.exception))

    def test_gecerli_env_prod_dogrulamayi_gecer(self):
        prod = self._prod_modulu()
        with self._ortamla(
            {
                "DJANGO_SECRET_KEY": "y" * 64,
                "DATABASE_URL": "postgres://u:p@localhost:5432/db",
            }
        ):
            prod._uretimi_dogrula()
        self.assertTrue(prod.SECURE_CONTENT_TYPE_NOSNIFF)
        self.assertFalse(getattr(prod, "CORS_ALLOW_ALL_ORIGINS", False))
