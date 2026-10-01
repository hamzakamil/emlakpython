"""Üretim ayarları — DEBUG kapalı, güvenlik katı.

Kullanım: DJANGO_SETTINGS_MODULE=config.settings.prod

FAZ 6F-1: kritik değerler fail-closed — ENV eksikse startup patlar.
"""

import datetime
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403


def _uretimi_dogrula() -> None:
    """SECRET_KEY ve DATABASE_URL ENV'den zorunlu (dev fallback yasak)."""
    sk = os.environ.get("DJANGO_SECRET_KEY", "")
    if not sk or any(
        isaret in sk for isaret in ("django-insecure-", "dev-only", "change-me")
    ):
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY üretimde zorunludur; dev/default değerle "
            "uygulama başlatılamaz."
        )
    if not os.environ.get("DATABASE_URL"):
        raise ImproperlyConfigured(
            "DATABASE_URL üretimde zorunludur; development fallback yasaktır."
        )


_uretimi_dogrula()

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")  # noqa: F405

# JWT — kısa erişim, güvenli oturum (site-specification.json)
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = datetime.timedelta(minutes=15)  # noqa: F405
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = datetime.timedelta(days=7)  # noqa: F405

SECURE_SSL_REDIRECT = True
# FAZ 6F-4: liveness/readiness probları HTTP ile yoklar; redirect döngüsüne
# girmemeleri için muaf (problar auth'suz ve içeriksizdir).
SECURE_REDIRECT_EXEMPT = [r"^api/v1/health/"]
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_AGE = 28800
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "Lax"
# JWT API mimarisi CSRF gerektirmez; session tabanlı tarayıcı akışları
# varsa izinli origin'ler ENV'den tanımlanır (boş default = kapalı).
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405
SECURE_CONTENT_TYPE_NOSNIFF = True
# NOT: SECURE_PROXY_SSL_HEADER bilerek tanımlı değil — mevcut deployment'ta
# reverse-proxy header sözleşmesi yok; proxy yokken tanımlamak spoof riski
# oluşturur (FAZ 6F-1 §2.3).
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"