"""Cari API view'ları (tenant izole, fiziksel DELETE yok)."""

from decimal import Decimal

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import IsCariEditor
from tenants.api import TenantScopedViewSet

from .models import Cari, CariHareket
from .serializers import CariHareketSerializer, CariSerializer
from .services import cari_hareketi_muhasebelestir


class CariViewSet(TenantScopedViewSet):
    queryset = Cari.objects.all()
    serializer_class = CariSerializer
    permission_classes = [IsAuthenticated, IsCariEditor]
    search_fields = ("ad", "vergi_dairesi")
    filterset_fields = ("tip", "tur", "is_active")

    @action(detail=True, methods=["get"], url_path="hareketler")
    def hareketler(self, request, pk=None):
        # FAZ 6E: sayfalı liste (standart pagination; sıralama/kapsam aynı).
        cari = self.get_object()
        queryset = cari.hareketler.select_related("cari").all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(
                CariHareketSerializer(page, many=True).data
            )
        return Response(CariHareketSerializer(queryset, many=True).data)

    @action(detail=True, methods=["get"], url_path="ozet")
    def ozet(self, request, pk=None):
        # FAZ 6E: toplama DB'de (SUM); formül ve çıktı birebir aynı.
        from django.db.models import Q, Sum

        cari = self.get_object()
        toplam = cari.hareketler.filter(is_cancelled=False).aggregate(
            borc=Sum("tutar", filter=Q(yon="borc")),
            alacak=Sum("tutar", filter=Q(yon="alacak")),
        )
        # Sözleşme için 2 haneye sabitle; satır yoksa eski davranış ("0") korunur.
        borc = toplam["borc"]
        alacak = toplam["alacak"]
        borc = str(borc.quantize(Decimal("0.00"))) if borc is not None else "0"
        alacak = (
            str(alacak.quantize(Decimal("0.00"))) if alacak is not None else "0"
        )
        bakiye = str(Decimal(borc) - Decimal(alacak))
        return Response({"borc": borc, "alacak": alacak, "bakiye": bakiye})


class CariHareketViewSet(TenantScopedViewSet):
    """Cari hareket — destroy yerine iptal (is_cancelled + neden)."""

    queryset = CariHareket.objects.select_related("cari").all()
    serializer_class = CariHareketSerializer
    permission_classes = [IsAuthenticated, IsCariEditor]
    search_fields = ("cari__ad", "aciklama")
    filterset_fields = ("cari", "yon", "is_cancelled")

    @action(detail=True, methods=["post"], url_path="muhasebelestir")
    def muhasebelestir(self, request, pk=None):
        hareket = cari_hareketi_muhasebelestir(
            int(pk), tenant_id=request.user.tenant_id
        )
        return Response(self.get_serializer(hareket).data)

    def destroy(self, request, *args, **kwargs):
        raise ValidationError({"detail": "Cari hareket silinemez; iptal endpoint'ini kullanın."})

    @action(detail=True, methods=["post"], url_path="iptal")
    def iptal(self, request, pk=None):
        hareket = self.get_object()
        if hareket.is_cancelled:
            raise ValidationError({"detail": "Hareket zaten iptal edilmiş."})
        neden = (request.data.get("iptal_nedeni") or "").strip()
        if not neden:
            raise ValidationError({"iptal_nedeni": "İptal nedeni zorunludur."})
        hareket.is_cancelled = True
        hareket.iptal_nedeni = neden
        hareket.save(update_fields=["is_cancelled", "iptal_nedeni"])
        # Renderer zaten zarflar — elle sarma yapılırsa çift zarf oluşur.
        return Response(self.get_serializer(hareket).data)
