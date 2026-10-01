from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from tenants.api import TenantScopedViewSet

from .models import Hatirlatma, HatirlatmaKurali
from .serializers import HatirlatmaKuraliSerializer, HatirlatmaSerializer
from .services.hatirlatma import gunluk_getir, hatirlatmalari_uret


class HatirlatmaViewSet(TenantScopedViewSet):
    queryset = Hatirlatma.objects.all()
    serializer_class = HatirlatmaSerializer
    filterset_fields = ("ilgili_app", "ilgili_model", "seviye", "durum", "hatirlatma_tarihi")

    @action(detail=False, methods=["get"], url_path="gunluk")
    def gunluk(self, request):
        return Response(self.get_serializer(gunluk_getir(request.user), many=True).data)

    @action(detail=True, methods=["post"], url_path="tamamla")
    def tamamla(self, request, pk=None):
        hatirlatma = self.get_object()
        hatirlatma.durum = "tamamlandi"
        hatirlatma.updated_at = timezone.now()
        hatirlatma.save(update_fields=["durum", "updated_at"])
        return Response(self.get_serializer(hatirlatma).data)

    @action(detail=False, methods=["post"], url_path="uret")
    def uret(self, request):
        return Response({"uretilen": hatirlatmalari_uret(request.user.tenant_id)})


class HatirlatmaKuraliViewSet(TenantScopedViewSet):
    queryset = HatirlatmaKurali.objects.all()
    serializer_class = HatirlatmaKuraliSerializer
    filterset_fields = ("ilgili_app", "ilgili_model", "tetikleyici_alan", "aktif_mi")
