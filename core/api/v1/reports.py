from rest_framework import viewsets
from .models import RaporTipi, Rapor


class RaporTipiViewSet(viewsets.ModelViewSet):
    """Rapor tipleri API - Kural 36 & Kural 37 raporlama"""
    
    queryset = RaporTipi.objects.all().order_by("ad")
    serializer_class = None


class RaporViewSet(viewsets.ModelViewSet):
    """Raporlar API - Kural 36 denetim izi ve Kural 37 dashboard entegrasyonu"""
    
    queryset = Rapor.objects.all().order_by("-yil", "-ay")
    serializer_class = None