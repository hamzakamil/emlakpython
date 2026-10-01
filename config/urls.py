"""URL yapılandırması — Emlak ERP API.

API prefix: api/v1/ — endpoint ve RBAC detayı: docs/proje-kurallari/04-API-VE-ROLLER.md
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from tenants.views import TenantSecimViewSet, TenantViewSet
from users.views import (
    LogoutView,
    MeView,
    PasswordChangeView,
    TenantTokenObtainPairView,
    TenantTokenRefreshView,
    UserViewSet,
)

API_V1 = "api/v1"


def health(_request):
    """Liveness: process çalışıyor (DB sorgusu yok)."""
    return JsonResponse({"success": True, "data": {"status": "ok"}})


def ready(_request):
    """Readiness: DB erişimi + bekleyen migration yoksa 200, yoksa 503.

    Yanıt güvenli tutulur (exception/SQL/path dönülmez).
    """
    import logging

    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        bekleyen = _bekleyen_migration_sayisi()
        if bekleyen:
            return JsonResponse(
                {"success": False,
                 "data": {"status": "unavailable", "db": "ok",
                          "bekleyen_migration": bekleyen}},
                status=503,
            )
        return JsonResponse(
            {"success": True,
             "data": {"status": "ok", "db": "ok", "bekleyen_migration": 0}}
        )
    except Exception:  # noqa: BLE001 — readiness sebebini dışa sızdırma
        logging.getLogger("erp.health").exception("readiness başarısız")
        return JsonResponse(
            {"success": False,
             "data": {"status": "unavailable", "db": "unavailable"}},
            status=503,
        )


def _bekleyen_migration_sayisi() -> int:
    """Uygulanmamış migration sayısı (salt-okunur)."""
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    return len(plan)


tenant_router = DefaultRouter()
tenant_router.register(r"tenants", TenantSecimViewSet, basename="tenant")
tenant_router.register(r"tenants-yonetim", TenantViewSet, basename="tenant-yonetim")
tenant_router.register(r"kullanicilar", UserViewSet, basename="kullanici")


urlpatterns = [
    path("admin/", admin.site.urls),
    # Sağlık / auth
    path(f"{API_V1}/health/", health, name="health"),
    path(f"{API_V1}/health/ready/", ready, name="health-ready"),
    path(f"{API_V1}/auth/token/", TenantTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(f"{API_V1}/auth/token/refresh/", TenantTokenRefreshView.as_view(), name="token_refresh"),
    path(f"{API_V1}/auth/logout/", LogoutView.as_view(), name="auth_logout"),
    path(f"{API_V1}/auth/me/", MeView.as_view(), name="auth_me"),
    path(f"{API_V1}/auth/password/change/", PasswordChangeView.as_view(), name="password_change"),
    # Tenant seçici (yalnızca süper admin) — /api/v1/tenants/
    path(f"{API_V1}/", include(tenant_router.urls)),
    # Modüller
    path(f"{API_V1}/construction/", include("construction.urls")),
    path(f"{API_V1}/notifications/", include("notifications.urls")),
    path(f"{API_V1}/real-estate/", include("real_estate.urls")),
    path(f"{API_V1}/cari/", include("cari.urls")),
    path(f"{API_V1}/accounting/", include("accounting.urls")),
    path(f"{API_V1}/finance/", include("finance.urls")),
    path(f"{API_V1}/database/", include("database_admin.urls")),
    # FAZ 3A: Satın alma — /api/v1/purchase-requests/, /api/v1/purchase-orders/
    path(f"{API_V1}/", include("purchasing.urls")),
    # OpenAPI dokümantasyonu
    path(f"{API_V1}/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(f"{API_V1}/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path(f"{API_V1}/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]