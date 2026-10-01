"""Geliştirme ayarları (varsayılan DJANGO_SETTINGS_MODULE)."""

from .base import *  # noqa: F401,F403

import datetime

DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

# JWT — geliştirmede geniş, prod'da site-spec madde güvenlik kuralları geçerli.
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = datetime.timedelta(hours=8)  # noqa: F405
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = datetime.timedelta(days=7)  # noqa: F405