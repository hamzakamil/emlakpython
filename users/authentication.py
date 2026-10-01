"""FAZ 6F-1 — JWT doğrulamada aktiflik kontrolü.

simplejwt akışı birebir korunur (tek kullanıcı sorgusu; `tenant`
join'lenir, ek sorgu yok):

- `User.is_active = False` → 401 (kütüphanenin `CHECK_USER_IS_ACTIVE` kuralı)
- `Tenant.is_active = False` (kullanıcının tenant'ı) → 401
- Süper kullanıcı (tenant'sız) yalnızca kullanıcı kontrolüne tabidir.

simplejwt 5.5.1 `get_user` karşılığıdır (requirements'ta pinned).
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.utils import get_md5_hash_password

from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme


class TenantJWTScheme(SimpleJWTScheme):
    """Schema'da stok JWT ile aynı bearer şeması (yeni uyarı üretmez)."""

    target_class = "users.authentication.TenantJWTAuthentication"


class TenantJWTAuthentication(JWTAuthentication):
    """Aktiflik kontrollü JWT authentication (sorgu sayısı aynı)."""

    def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError as exc:
            raise InvalidToken(
                "Token contained no recognizable user identification"
            ) from exc

        try:
            user = self.user_model.objects.select_related("tenant").get(
                **{api_settings.USER_ID_FIELD: user_id}
            )
        except self.user_model.DoesNotExist as exc:
            raise AuthenticationFailed(
                "User not found", code="user_not_found"
            ) from exc

        if api_settings.CHECK_USER_IS_ACTIVE and not user.is_active:
            raise AuthenticationFailed("User is inactive", code="user_inactive")

        if api_settings.CHECK_REVOKE_TOKEN:
            if validated_token.get(
                api_settings.REVOKE_TOKEN_CLAIM
            ) != get_md5_hash_password(user.password):
                raise AuthenticationFailed(
                    "The user's password has been changed.", code="password_changed"
                )

        tenant = getattr(user, "tenant", None)
        if tenant is not None and not tenant.is_active:
            raise AuthenticationFailed(
                "Firma aktif değil.", code="tenant_inactive"
            )
        # FAZ 6F-2: log bağlamı (tenant/kullanıcı kimliği; hassas veri yok).
        from tenants.middleware import baglam_kullanici, baglam_tenant

        baglam_kullanici.set(str(user.pk))
        baglam_tenant.set(str(getattr(user, "tenant_id", None) or "-"))
        return user
