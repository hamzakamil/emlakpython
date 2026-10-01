"""Finans modülü rol kontrolü — okuma herkes, yazma finans/admin rolleri."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import UserRole

EDITOR_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.TENANT_ADMIN,
    UserRole.FIRMA_ADMIN,
    UserRole.FINANS,
    UserRole.MUHASEBE,
}


class IsFinansEditor(BasePermission):
    """Kasa/banka + finansal işlem yazma yetkisi."""

    message = "Bu işlem için finans yetkisi gerekir."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if request.method in SAFE_METHODS:
            return True
        return user.role in EDITOR_ROLES
