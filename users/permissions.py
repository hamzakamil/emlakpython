"""Paylaşımlı yetki sınıfları — kullanıcı/tenant yönetimi (yalnızca süper admin)."""

from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """Yalnızca is_superuser — is_staff (örn. tenant_admin) yetmez.

    04-API-VE-ROLLER.md §2: tenant ve kullanıcı yönetimi yalnızca süper admin.
    """

    message = "Bu işlem yalnızca süper admin yetkisindedir."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_superuser)