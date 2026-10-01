"""Tüm başarılı DRF yanıtlarını {success, data, message} zarfına saran renderer.

API kuralı: docs/proje-kurallari/01-GELISTIRME-KURALLARI.md §6
    Başarılı → { "success": true, "data": {}, "message": "..." }
    Hata    → { "success": false, "message": "...", "errors": {} }

drf-spectacular'ın kendi doküman üretimleri (schema/docs/redoc) zarflanmaz.
"""

from rest_framework.renderers import JSONRenderer

SCHEMA_VIEWS = {"SpectacularAPIView", "SpectacularSwaggerView", "SpectacularRedocView"}


class EnvelopeJSONRenderer(JSONRenderer):
    """DRF yanıtlarını ortak zarf yapısına dönüştürür."""

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        view = renderer_context.get("view")
        view_name = view.__class__.__name__ if view else ""
        if view_name in SCHEMA_VIEWS or getattr(view, "swagger_fake_view", False):
            return super().render(data, accepted_media_type, renderer_context)

        response = renderer_context.get("response")
        status_code = getattr(response, "status_code", 200)
        if 200 <= status_code < 300:
            # Token veya veri — hepsi data alanına taşınır.
            data = {"success": True, "data": data, "message": ""}
        return super().render(data, accepted_media_type, renderer_context)