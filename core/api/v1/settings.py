from rest_framework import viewsets
from .models import SistemAyarları, RaporTipi, Rapor


class SistemAyarlarViewSet(viewsets.ModelViewSet):
    """Sistem ayarları API - Kural 37: UI Status Display konfigürasyonu"""
    
    queryset = SistemAyarları.objects.all().order_by("anahtar")
    serializer_class = None  # Serializer will be created separately
    lookup_field = "anahtar"


class RaporTipiViewSet(viewsets.ModelViewSet):
    """Rapor tipleri API - Kural 36 & Kural 37 raporlama"""
    
    queryset = RaporTipi.objects.all().order_by("ad")
    serializer_class = None


class RaporViewSet(viewsets.ModelViewSet):
    """Raporlar API - Kural 36 denetim izi ve Kural 37 dashboard entegrasyonu"""
    
    queryset = Rapor.objects.all().order_by("-yil", "-ay")
    serializer_class = None