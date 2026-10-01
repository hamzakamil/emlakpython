"""Ortak Django ayarları — Emlak ERP (base).

Detay: docs/proje-kurallari/00-TEKNOLOJI-STACK.md, 01-GELISTIRME-KURALLARI.md
"""

from pathlib import Path

import environ

# Build paths: BASE_DIR / 'subdir' → proje kökü (config/settings/base.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

# ⚠ SECURITY: production'da mutlaka environment variable ile verilmelidir.
SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-dev-only-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# ── Uygulamalar ────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3. parti
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    # yerel modüller
    "tenants",
    "users",
    "real_estate",
    "construction",
    "cari",
    "finance",
    "accounting",
    "database_admin",
    "audit",  # Kural 36: Audit trail
    "notifications",
    "purchasing",  # FAZ 3A: Satın alma çekirdeği
    "rest_framework_simplejwt.token_blacklist",  # FAZ 6F-1: refresh revoke
]

MIDDLEWARE = [
    "tenants.middleware.IstekBaglamMiddleware",  # FAZ 6F-2: korelasyon + erişim logu (en dışta)
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # RLS zemini: her istekte app.current_tenant GUC'sü (bkz. docs/rls-plani.md).
    # AuthenticationMiddleware'den SONRA olmalı (session auth → request.user).
    "tenants.middleware.TenantBaglamMiddleware",
    "tenants.middleware.TenantAuditMiddleware",  # Kural 36: Audit trail middleware
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ── Veritabanı (PostgreSQL, bkz. docker-compose.yml) ────────────────────────
DATABASES = {
    "default": env.db(
        default="postgres://emlak:emlak_dev_password@localhost:5432/emlak_erp"
    )
}
DATABASES["default"]["TEST"] = {
    "TEMPLATE": "template0",
}

# Özel kullanıcı modeli — auth sistemi users.User üzerinden çalışır.
AUTH_USER_MODEL = "users.User"

# ── Parola doğrulama ────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Yerelleştirme: Türkçe + Europe/Istanbul (01-GELISTIRME-KURALLARI.md §2) ─
LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

# ── Statik / medya ──────────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── DRF ─────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "users.authentication.TenantJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Yanıt zarfı + Türkçe hata mesajları (config/renderers.py, config/exceptions.py)
    "DEFAULT_RENDERER_CLASSES": [
        "config.renderers.EnvelopeJSONRenderer",
    ],
    "EXCEPTION_HANDLER": "config.exceptions.exception_handler",
}

# ── JWT — erişim 15 dk, yenileme 7 gün + rotation (site-specification.json) ─
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": None,  # dev override altında
    "REFRESH_TOKEN_LIFETIME": None,  # dev override altında
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# ── OpenAPI / Swagger ───────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "EMLAK ERP API",
    "DESCRIPTION": "Emlak + Muhasebe + Finans çok kiracılı ERP — Django + DRF.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ── CORS (bkz. site-specification.json) ─────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)

# ── E-posta (dev'de konsol) ─────────────────────────────────────────────────
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

# FAZ 6F-1 güvenlik politikası (toplanabilir sabitler).
# Başarısız login eşiği + kilit süresi (DB destekli sayaç; users.LoginDenemesi).
LOGIN_KILIT_ESIGI = 5
LOGIN_KILIT_SURESI_SN = 900
# IFC upload üst sınırı (bytes; ENV ile ezilebilir).
IFC_UPLOAD_MAX_BYTES = env.int("IFC_UPLOAD_MAX_BYTES", default=50 * 1024 * 1024)
# FAZ 6F-2: yavaş istek eşiği (ms; üstü WARNING loglanır).
SLOW_REQUEST_MS = 1000
# FAZ 6F-4: yavaş DB eşiği (istek-başı toplam sorgu süresi; üstü WARNING).
SLOW_DB_MS = 500

# ── FAZ 6F-2 production logging (console; hassas veri loglanmaz) ─────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "erp": {
            "format": (
                "%(asctime)s %(levelname)-7s %(name)s "
                "[cid=%(correlation_id)s tenant=%(tenant_id)s user=%(user_id)s] "
                "%(message)s | op=%(operation)s res=%(resource_id)s path=%(request_path)s"
            ),
        },
    },
    "filters": {
        "baglam": {"()": "tenants.middleware.BaglamFiltresi"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "erp",
            "filters": ["baglam"],
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"level": "WARNING"},
        "django.request": {"level": "ERROR"},
        "django.db.backends": {"level": "ERROR"},
        "erp": {"level": "INFO"},
    },
}

# FAZ 6F-3 yedekleme politikası (toplanabilir sabitler; ENV ile ezilebilir).
# Saklama günü + tazelik eşiği + off-site dizini + şifreleme anahtarı.
BACKUP_SAKLAMA_GUN = env.int("BACKUP_SAKLAMA_GUN", default=30)
BACKUP_MAX_YAS_SAAT = env.int("BACKUP_MAX_YAS_SAAT", default=26)
BACKUP_OFFSITE_DIR = env("BACKUP_OFFSITE_DIR", default="")
BACKUP_ENCRYPTION_KEY = env("BACKUP_ENCRYPTION_KEY", default="")

# Veritabanı yönetimi: yedekler uygulama kökünün altında, web kökünden ayrı tutulur.
DB_BACKUP_DIR = BASE_DIR / "backups"
PG_DUMP_PATH = env("PG_DUMP_PATH", default="")
PSQL_PATH = env("PSQL_PATH", default="")