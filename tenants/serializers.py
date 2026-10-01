"""TenantAwareModelSerializer — tenant alanını istemciden kapatan ortak serializers tabanı.

02-VERI-MODELI.md §1: kullanıcı asla kendi tenant'ı dışında bir kayda sahiplik
veremez; tenant değeri ViewSet (TenantScopedViewSet) tarafından atanır.
"""

from rest_framework import serializers


class TenantAwareModelSerializer(serializers.ModelSerializer):
    """Tenant alanı read-only + required=False yapan taban sınıf."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tenant_field = self.fields.get("tenant")
        if tenant_field:
            tenant_field.read_only = True
            tenant_field.required = False


def fk_kapsam_kontrol(serializer, attrs, alanlar):
    """Tenant bağımlı FK'lerin istek sahibinin tenant'ına ait olduğunu doğrular.

    purchasingdesindeki `_kapsam_kontrol` ile aynı kural: tenant request
    context'inden (kullanıcı) alınır, asla istek gövdesinden okunmaz.
    POST ve PATCH'te de çalışır (instance değerleriyle birleşir).
    """
    request = serializer.context.get("request")
    user = getattr(request, "user", None)
    tenant_id = getattr(user, "tenant_id", None)
    for alan in alanlar:
        nesne = attrs.get(alan, getattr(serializer.instance, alan, None))
        if nesne is not None and tenant_id and nesne.tenant_id != tenant_id:
            raise serializers.ValidationError(
                {alan: "Seçilen kayıt bu firma kapsamına ait değil."}
            )