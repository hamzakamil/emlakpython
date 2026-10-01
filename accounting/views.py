"""Muhasebe API view'ları (tenant izole, fiş satırı değişmezliği)."""

from decimal import Decimal

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tenants.api import TenantScopedViewSet, tenant_kapsamli_queryset

from .models import FisSatiri, HesapPlani, MuhasebeFisi
from .permissions import IsMuhasebeEditor
from .serializers import HesapPlaniSerializer, MuhasebeFisiSerializer


class HesapPlaniViewSet(TenantScopedViewSet):
    queryset = HesapPlani.objects.all()
    serializer_class = HesapPlaniSerializer
    permission_classes = [IsAuthenticated, IsMuhasebeEditor]
    search_fields = ("kod", "ad")
    filterset_fields = ("tip", "is_active")


class MuhasebeFisiViewSet(TenantScopedViewSet):
    """Fiş — satırlar oluşturma anında yazılır, sonra değişmez (405/400 korumalı)."""

    queryset = MuhasebeFisi.objects.prefetch_related("satirlar__hesap").all()
    serializer_class = MuhasebeFisiSerializer
    permission_classes = [IsAuthenticated, IsMuhasebeEditor]
    search_fields = ("fis_no", "aciklama")
    filterset_fields = ("durum",)

    def destroy(self, request, *args, **kwargs):
        fis = self.get_object()
        if fis.durum == MuhasebeFisi.Durum.KAYITLI:
            raise ValidationError({"detail": "Kayıtlı fiş silinemez (iptal kaydı açınız)."})
        fis.durum = MuhasebeFisi.Durum.IPTAL
        fis.save(update_fields=["durum"])
        # Renderer zaten zarflar — elle sarma yapılırsa çift zarf oluşur.
        return Response(self.get_serializer(fis).data)

    @action(detail=False, methods=["get"], url_path="mizan")
    def mizan(self, request):
        """Hesap bazlı borç/alacak/bakiye özeti (kayıtlı + taslak fişler).

        FAZ 6E: toplama DB'de (SUM/GROUP BY); sonuç eskiyle birebir aynı.
        """
        from django.db.models import Sum

        kapsamli_fisler = tenant_kapsamli_queryset(
            request, MuhasebeFisi.objects.exclude(durum=MuhasebeFisi.Durum.IPTAL)
        )
        satirlar = (
            FisSatiri.objects.filter(fis__in=kapsamli_fisler)
            .values("hesap__kod", "hesap__ad")
            .annotate(borc=Sum("borc"), alacak=Sum("alacak"))
            .order_by("hesap__kod")
        )
        # PG SUM ölçeği girdiye göre değişebilir; sözleşme için 2 haneye sabitle
        # (eski Python toplamlarıyla birebir aynı dizeler).
        sonuc = []
        for s in satirlar:
            borc = (s["borc"] or Decimal("0")).quantize(Decimal("0.00"))
            alacak = (s["alacak"] or Decimal("0")).quantize(Decimal("0.00"))
            sonuc.append(
                {
                    "hesap_kodu": s["hesap__kod"],
                    "hesap_adi": s["hesap__ad"],
                    "borc": str(borc),
                    "alacak": str(alacak),
                    "bakiye": str(borc - alacak),
                }
            )
        return Response(sonuc)

