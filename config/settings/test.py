"""Test ayarları — İzole test veritabanı, hızlı çalışma."""

from .dev import *  # noqa: F401,F403

import os

# Test ortamı: DEBUG kapalı, hız için
DEBUG = False
ALLOWED_HOSTS = ["testserver"]

# Test veritabanı — .env.test'ten DATABASE_URL alınır
# docker-compose.test.yml'de ayrı PostgreSQL konteyneri (port 5434) tanımlanmalı

# Cache — Bellek içi, testler arası izolasyon
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# JWT — Testlerde kısa ömürlü token
import datetime
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = datetime.timedelta(minutes=5)
SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"] = datetime.timedelta(minutes=10)

# E-posta ve dosya depolama — Bellek içi / geçici
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    },
}
DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"
MEDIA_ROOT = "/tmp/test_media"
MEDIA_URL = "/media/"

# Celery — Eager mode (senkron çalışır, broker gerekmez)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# CORS — Testlerde kapalı
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = []

# Logging — Testlerde sessiz
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"level": "WARNING"},
        "django.db.backends": {"level": "WARNING"},
    },
}

# Password hashing — Testlerde hızlı (MD5 yerine PBKDF2 çok yavaş)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Migrations — Testlerde çalıştır
# MIGRATION_MODULES = DisableMigrations()