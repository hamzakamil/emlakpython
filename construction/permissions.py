"""Faz 1 rol bazlı yetkilendirme (roadmap: Şantiye Şefi / Maliyet Mühendisi / Proje Yöneticisi)."""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.models import UserRole

# Okuma herkes (logged-in); yazma (POST/PUT/PATCH/DELETE) yalnızca aşağıdaki roller.
EDITOR_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.TENANT_ADMIN,
    UserRole.FIRMA_ADMIN,
    UserRole.MALIYET_MUHENDISI,
    UserRole.PROJE_YONETICISI,
}


class IsConstructionEditor(BasePermission):
    """İnşaat modülünde yazma işlemleri için rol kısıtı.

    Şantiye şefi (SANTIYE_SEFI) salt okur; maliyet mühendisi ve proje yöneticisi
    yazabilir. Tenant izolasyonu ileride ayrı katmanla netleştirilecek
    (bkz. memory-bank — tenant middleware).
    """

    message = "Bu işlem için yetkiniz yok (maliyet mühendisi / proje yöneticisi gerekir)."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.role in EDITOR_ROLES