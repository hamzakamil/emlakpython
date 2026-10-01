"""API hata sarmalayıcısı — Türkçe mesajlarla {success, data, message, errors}.

Kullanıcıya ham teknik hata gösterilmez (01-GELISTIRME-KURALLARI.md §6).
"""

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.views import exception_handler as drf_handler


def exception_handler(exc, context):
    response = drf_handler(exc, context)
    if response is None:
        return None

    status_code = response.status_code
    message = "İstek işlenemedi."
    errors = None

    if status_code == 404:
        message = "İstenen kaynak bulunamadı."
    elif isinstance(exc, PermissionDenied) or status_code == 403:
        message = "Bu işlem için yetkiniz yok."
    elif status_code == 401:
        message = "Kimlik doğrulama başarısız. Geçerli bir oturum açın."
    elif isinstance(exc, drf_exceptions.ValidationError):
        message = "Doğrulama hatası. Girilen bilgileri kontrol edin."
        errors = exc.detail
    elif isinstance(exc, drf_exceptions.MethodNotAllowed):
        message = "Bu uç nokta için kullanılan HTTP yöntemi geçersiz."
    else:
        # 4xx klasmanındaki diğer DRF hataları
        detail = getattr(exc, "detail", None)
        if isinstance(detail, str):
            message = detail

    payload = {"success": False, "message": message}
    if errors:
        payload["errors"] = errors
    response.data = payload
    return response