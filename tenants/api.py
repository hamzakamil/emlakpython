"""Tenant izolasyon çekirdeği — DRF ViewSet tabanı.

Tüm tenant'a bağlı modeller bu sınıftan türemelidir (02-VERI-MODELI.md §1):
- Görünen veri yalnızca istek sahibinin tenant'ından gelir (superuser hariç).
- Yeni kayıtlarda tenant isteği yapan kullanıcıdan otomatik alınır; değiştirilemez.
- Süper admin, ``X-Tenant-Id`` başlığıyla kapsamını tek tenant'a daraltabilir
  (tenant seçici). Başlık yoksa global görünüm korunur; normal kullanıcıların
  başlığı yok sayılır (izolasyon kuralı 5 — asla gevşetilmez).
"""

from rest_framework import serializers, viewsets


#: Süper admin kapsam daraltma başlığı (frontend tenant seçici kullanır).
TENANT_KAPSAM_BASLIGI = "X-Tenant-Id"


def etkin_tenant_id(request):
    """İstek için etkin tenant pk'sı.

    - Normal kullanıcı → kendi ``tenant_id``'si (başlık ne olursa olsun).
    - Süper kullanıcı + geçerli ``X-Tenant-Id`` → başlıktaki tenant.
    - Süper kullanıcı + başlık yok/geçersiz → None (global görünüm).
    - Anonim → None.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None
    if not getattr(user, "is_superuser", False):
        return getattr(user, "tenant_id", None)
    ham = request.headers.get(TENANT_KAPSAM_BASLIGI) if hasattr(request, "headers") else None
    if ham is None:
        ham = request.META.get("HTTP_X_TENANT_ID")
    try:
        return int(ham) if ham not in (None, "") else None
    except (TypeError, ValueError):
        return None


def tenant_kapsamli_queryset(request, queryset):
    """Verilen tenant-aware queryset'i istek sahibinin etkin kapsamına daraltır.

    ``TenantScopedViewSet.get_queryset`` ile aynı kuralı uygular; bu sayede
    ViewSet dışındaki sorgular (örn. rapor endpoint'leri) da DRY biçimde izole
    edilebilir.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return queryset.none()
    if getattr(user, "is_superuser", False):
        kapsam = etkin_tenant_id(request)
        return queryset.filter(tenant_id=kapsam) if kapsam else queryset
    if not getattr(user, "tenant_id", None):
        return queryset.none()
    return queryset.filter(tenant_id=user.tenant_id)


class TenantScopedViewSet(viewsets.ModelViewSet):
    """Multi-tenant izole ModelViewSet tabanı."""

    def get_queryset(self):
        return tenant_kapsamli_queryset(self.request, super().get_queryset())

    def get_object(self):
        """FAZ 6F-2: audit before-state için nesne görüntüsünü isteğe iliştirir."""
        nesne = super().get_object()
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            try:
                from audit.loglama import guvenli_snapshot

                etiket = f"{nesne._meta.app_label}.{nesne.__class__.__name__}"
                # DRF sarmalayıcı değil, ham Django isteği (middleware aynı nesneyi görür).
                ham = getattr(self.request, "_request", self.request)
                ham._audit_onceki = (
                    etiket, nesne.pk, guvenli_snapshot(nesne)
                )
            except Exception:  # noqa: BLE001 — snapshot alınamazsa denetimsiz devam
                import logging

                logging.getLogger("erp.audit").exception(
                    "audit ön-görüntü alınamadı"
                )
        return nesne

    def perform_create(self, serializer):
        tenant_id = self.request.user.tenant_id
        if tenant_id is None:
            # Superuser gibi tenant'sız kullanıcı: kapsam başlığı öncelikli,
            # yoksa istek gövdesinden alabilir.
            kapsam = etkin_tenant_id(self.request)
            tenant_id = kapsam if kapsam else serializer.validated_data.get("tenant_id")
        if tenant_id is None:
            raise serializers.ValidationError(
                {"tenant": "Kayıt oluşturmak için aktif bir tenant seçmelisiniz."}
            )
        serializer.save(tenant_id=tenant_id)

    def perform_update(self, serializer):
        # Kaydın tenant'ı, istek sırasında değiştirilemez.
        serializer.save(tenant_id=serializer.instance.tenant_id)
