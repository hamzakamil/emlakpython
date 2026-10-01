from rest_framework import viewsets
from .models import Fatura
from .serializers import FaturaSerializer


class FaturaViewSet(viewsets.ModelViewSet):
    """Fatura ViewSet - Kural 36 & Kural 37 entegrasyonlu"""
    
    queryset = Fatura.objects.all().order_by("-tarih", "fatura_no")
    serializer_class = FaturaSerializer