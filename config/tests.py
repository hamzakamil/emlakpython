"""İskelet smoke testleri — sağlık + JWT uç noktaları."""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class HealthTestCase(TestCase):
    def test_health_is_ok(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_health_ssl_redirect_muaf(self):
        # FAZ 6F-4: problar SECURE_SSL_REDIRECT altında 301 yememeli.
        from django.middleware.security import SecurityMiddleware
        from django.test import RequestFactory

        fabrika = RequestFactory()
        with self.settings(
            SECURE_SSL_REDIRECT=True,
            SECURE_REDIRECT_EXEMPT=[r"^api/v1/health/"],
        ):
            ara = SecurityMiddleware(lambda istek: None)
            self.assertIsNone(ara.process_request(fabrika.get("/api/v1/health/")))
            self.assertIsNone(ara.process_request(fabrika.get("/api/v1/health/ready/")))
            yon = ara.process_request(fabrika.get("/api/v1/finance/faturalar/"))
            self.assertEqual(yon.status_code, 301)

    def test_prod_redirect_muaf_tanimli(self):
        # FAZ 6F-4: prod ayarları health muafiyetini gerçekten taşır.
        import os
        import sys
        from unittest import mock

        for mod in [m for m in sys.modules if m == "config.settings.prod"]:
            del sys.modules[mod]
        with mock.patch.dict(
            os.environ,
            {
                "DJANGO_SECRET_KEY": "z" * 64,
                "DATABASE_URL": "postgres://u:p@localhost:5432/db",
                "DJANGO_ALLOWED_HOSTS": "ornek.test",
            },
            clear=False,
        ):
            from config.settings import prod

            self.assertIn(r"^api/v1/health/", prod.SECURE_REDIRECT_EXEMPT)

    def test_ready_db_ile_200(self):
        response = self.client.get(reverse("health-ready"))
        self.assertEqual(response.status_code, 200)
        veri = response.json()["data"]
        self.assertEqual(veri["status"], "ok")
        self.assertEqual(veri["db"], "ok")

    def test_ready_db_kapaliysa_503_ve_guvenli(self):
        from unittest.mock import patch

        from django.db import OperationalError

        with patch(
            "django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection",
            side_effect=OperationalError("kapali"),
        ):
            response = self.client.get(reverse("health-ready"))
            canli = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(canli.status_code, 200)
        self.assertEqual(response.status_code, 503)
        govde = response.content.decode()
        self.assertIn("unavailable", govde)
        for iz in ("Traceback", "kapali", "OperationalError", ".py"):
            self.assertNotIn(iz, govde)


class AuthTokenTestCase(TestCase):
    def test_token_requires_valid_credentials(self):
        client = APIClient()
        response = client.post(
            reverse("token_obtain_pair"),
            {"username": "olmayan", "password": "yanlis"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_swagger_schema_generated(self):
        response = self.client.get(reverse("schema"))
        self.assertEqual(response.status_code, 200)