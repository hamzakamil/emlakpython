"""FAZ 3A rol bazlı yetkilendirme — construction IsConstructionEditor kalıbı."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import UserRole

# Okuma herkes (logged-in); yazma yalnızca aşağıdaki roller.
# FAZ 6C SoD: FINANS/MUHASEBE satın alma yazamaz (onay dahil). Okuma
# SAFE_METHODS dalıyla herkese açık kalır; finans rolleri finance/cari
# modüllerindeki yetkilerini korur.
EDITOR_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.TENANT_ADMIN,
    UserRole.FIRMA_ADMIN,
    UserRole.MALIYET_MUHENDISI,
    UserRole.PROJE_YONETICISI,
}


class IsPurchasingEditor(BasePermission):
    """Satın alma modülünde yazma işlemleri için rol kısıtı."""

    message = "Bu işlem için yetkiniz yok (satın alma yetkisi gerekir)."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.role in EDITOR_ROLES
