"""Kullanıcı API görünümleri — token, /auth/me, tenant kapsamı, yönetim."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .permissions import IsSuperUser
from .serializers import KullaniciSerializer, KullaniciYonetimSerializer
from .tokens import (
    TenantTokenObtainPairSerializer,
    TenantTokenRefreshSerializer,
)


class TenantTokenObtainPairView(TokenObtainPairView):
    """POST /api/v1/auth/token/ - access/refresh + tenant claim'li token.

    Yanıt zarfı EnvelopeJSONRenderer ile sarılır; claim'ler gövdede değil,
    JWT içinde taşınır (frontend isterse localStorage'daki access'i çözer).
    """

    serializer_class = TenantTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        import logging

        yanit = super().post(request, *args, **kwargs)
        if yanit.status_code == 200:
            logging.getLogger("erp.auth").info(
                "event=login kullanici=%s",
                request.data.get("username"),
                extra={"tenant_id": "-", "operation": "auth.login",
                       "resource_id": "-"},
            )
        return yanit


class TenantTokenRefreshView(TokenRefreshView):
    """POST /api/v1/auth/token/refresh/ - aktiflik kontrollü yenileme."""

    serializer_class = TenantTokenRefreshSerializer


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ - refresh token'ı kara listeye alır.

    FAZ 6F-1: simplejwt native blacklist kullanılır. Refresh tekrar
    kullanılamaz; access token kısa ömrü (prod 15 dk) içinde kendiliğinden
    düşer (stateless JWT güvenlik modeli).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from rest_framework_simplejwt.exceptions import TokenError
        from rest_framework_simplejwt.tokens import RefreshToken

        ham = request.data.get("refresh")
        if not ham:
            return Response({"detail": "Refresh token zorunludur."}, status=400)
        try:
            RefreshToken(ham).blacklist()
        except TokenError:
            return Response({"detail": "Geçersiz veya süresi dolmuş token."}, status=400)
        import logging

        logging.getLogger("erp.auth").info(
            "event=logout kullanici=%s", request.user.username,
            extra={"tenant_id": getattr(request.user, "tenant_id", None) or "-",
                   "operation": "auth.logout", "resource_id": "-"},
        )
        return Response({"detail": "Çıkış yapıldı."})


class MeView(APIView):
    """GET /api/v1/auth/me/ — JWT/session ile doğrulanan kullanıcının bilgisi.

    Yanıt EnvelopeJSONRenderer ile {success, data, message} zarfına sarılır.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(KullaniciSerializer(request.user).data)


class PasswordChangeView(APIView):
    """POST /api/v1/auth/password/change/ — kendi şifreni değiştir.

    Girdi: mevcut_sifre + yeni_sifre + yeni_sifre_tekrar. Django password
    hashing + AUTH_PASSWORD_VALIDATORS kullanılır; parola asla loglanmaz.
    JWT/session davranışı değişmez (token'lara dokunulmaz).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError

        mevcut = request.data.get("mevcut_sifre", "") or ""
        yeni = request.data.get("yeni_sifre", "") or ""
        tekrar = request.data.get("yeni_sifre_tekrar", "") or ""
        if not mevcut or not yeni or not tekrar:
            return Response(
                {"detail": "Mevcut şifre, yeni şifre ve tekrarı zorunludur."},
                status=400,
            )
        if not request.user.check_password(mevcut):
            return Response({"detail": "Mevcut şifre hatalı."}, status=400)
        if yeni != tekrar:
            return Response({"detail": "Yeni şifreler eşleşmiyor."}, status=400)
        try:
            validate_password(yeni, request.user)
        except DjangoValidationError as exc:
            return Response({"detail": " ".join(exc.messages)}, status=400)
        request.user.set_password(yeni)
        request.user.save(update_fields=["password"])
        import logging

        logging.getLogger("erp.auth").info(
            "event=password_change kullanici=%s",
            request.user.username,
            extra={"tenant_id": getattr(request.user, "tenant_id", None) or "-",
                   "operation": "auth.password_change", "resource_id": "-"},
        )
        return Response({"detail": "Şifre değiştirildi."})


class UserViewSet(ModelViewSet):
    """Süper admin kullanıcı yönetimi — tam CRUD.

    Firma bazlı kullanıcı oluşturma (parola ile), rol/tenant atama, düzenleme
    ve silme yalnızca süper admin yetkisindedir (04-API-VE-ROLLER.md §2).
    """

    queryset = User.objects.select_related("tenant").order_by("username")
    serializer_class = KullaniciYonetimSerializer
    permission_classes = [IsSuperUser]


