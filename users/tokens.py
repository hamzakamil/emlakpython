"""Kullanıcı/tenant auth çekirdeği — JWT claim zenginleştirme.

simplejwt'nin varsayılan ``TokenObtainPairSerializer``'ı yalnızca
``access``/``refresh`` döner. Bu modül token gövdesine tenant bağlamını ekler:

- ``tenant_id``: kullanıcının bağlı olduğu tenant pk'sı (süper kullanıcıda None)
- ``role``: ``UserRole`` değeri (frontend rol-gating için — bkz. ``utils/yetki.ts``)

İzolasyon kuralı değişmez: normal kullanıcı token'ı her zaman kendi tenant'ına
sabitlenir; başka tenant seçimi yalnızca ``X-Tenant-Id`` başlığı + süper
kullanıcı kombinasyonunda kabul edilir (bkz. tenants/api.py).
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed as DrfAuthenticationFailed
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings

from .models import LoginDenemesi


def _kilitli_mi(kayit, simdi) -> bool:
    return bool(kayit and kayit.kilit_bitis and kayit.kilit_bitis > simdi)


def _ayni_hata() -> DrfAuthenticationFailed:
    """Kullanıcı var/yok ayrımı yapmayan standart login hatası."""
    return DrfAuthenticationFailed(
        "No active account found with the given credentials.",
        code="no_active_account",
    )


class TenantTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Access/refresh token'ına tenant bağlamı ekleyen serializer."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["tenant_id"] = user.tenant_id
        token["role"] = "super_admin" if user.is_superuser else user.role
        token["username"] = user.username
        return token

    def validate(self, attrs):
        """FAZ 6F-1 — hesap kilidi + başarısız sayaç (kalıcı, kullanıcı bazlı)."""
        anahtar = (attrs.get("username") or "").strip().lower()
        simdi = timezone.now()
        kayit = (
            LoginDenemesi.objects.filter(kullanici_adi=anahtar).first()
            if anahtar
            else None
        )
        if _kilitli_mi(kayit, simdi):
            import logging

            logging.getLogger("erp.auth").warning(
                "event=login_lockout kullanici=%s", anahtar,
                extra={"tenant_id": "-", "operation": "auth.login",
                       "resource_id": "-"},
            )
            raise _ayni_hata()
        try:
            veri = super().validate(attrs)
        # NOT: simplejwt serializer DRF'nin AuthenticationFailed'ını fırlatır.
        except DrfAuthenticationFailed:
            if anahtar:
                kayit, _ = LoginDenemesi.objects.get_or_create(
                    kullanici_adi=anahtar
                )
                kayit.basarisiz_sayisi += 1
                if kayit.basarisiz_sayisi >= settings.LOGIN_KILIT_ESIGI:
                    kayit.kilit_bitis = simdi + timedelta(
                        seconds=settings.LOGIN_KILIT_SURESI_SN
                    )
                kayit.save(update_fields=["basarisiz_sayisi", "kilit_bitis", "guncellendi"])
            raise
        else:
            if anahtar:
                LoginDenemesi.objects.filter(kullanici_adi=anahtar).delete()
            # FAZ 6F-1: pasif firma ile login yok (request katmanı da kilitli).
            tenant = getattr(self.user, "tenant", None)
            if tenant is not None and not tenant.is_active:
                raise _ayni_hata()
            return veri


class TenantTokenRefreshSerializer(TokenRefreshSerializer):
    """FAZ 6F-1 — refresh anında da aktiflik kontrolü."""

    def validate(self, attrs):
        veri = super().validate(attrs)
        from rest_framework_simplejwt.tokens import RefreshToken

        from .models import User

        # super() token'ı doğruladı (imza/süre/blacklist); burada verify
        # tekrarlanmaz — yalnızca kullanıcı kimliği okunur.
        token = RefreshToken(attrs["refresh"], verify=False)
        try:
            user = User.objects.select_related("tenant").get(
                **{api_settings.USER_ID_FIELD: token[api_settings.USER_ID_CLAIM]}
            )
        except (User.DoesNotExist, KeyError):
            raise AuthenticationFailed(
                "User not found", code="user_not_found"
            )
        if not user.is_active:
            raise AuthenticationFailed("User is inactive", code="user_inactive")
        tenant = getattr(user, "tenant", None)
        if tenant is not None and not tenant.is_active:
            raise AuthenticationFailed(
                "Firma aktif değil.", code="tenant_inactive"
            )
        return veri
