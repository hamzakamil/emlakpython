"""Cari modülü rol kontrolü — okuma herkes, yazma muhasebe/finans/admin rolleri."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import UserRole

EDITOR_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.TENANT_ADMIN,
    UserRole.FIRMA_ADMIN,
    UserRole.MUHASEBE,
    UserRole.FINANS,
}


class IsCariEditor(BasePermission):
    """Cari kartı + cari hareket yazma yetkisi."""

    message = "Bu işlem için cari yetkisi gerekir (muhasebe / finans / admin)."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if request.method in SAFE_METHODS:
            return True
        return user.role in EDITOR_ROLES
