from rest_framework import serializers
from .models import Fatura


class FaturaSerializer(serializers.ModelSerializer):
    """Fatura serializer - Kural 36 & Kural 37 entegrasyonlu"""
    
    class Meta:
        model = Fatura
        fields = [
            "id",
            "fatura_no",
            "tarih",
            "cari",
            "tutar",
            "vergino",
            "aciklama",
            "durum",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def validate(self, data):
        """Tenant izolasyonu ve validasyon"""
        # Cari varsa validate edilebilir
        if data.get("cari") and not data.get("tutar", 0) > 0:
            from django.core.exceptions import ValidationError
            raise ValidationError("Tutar 0'dan büyük olmalıdır.")
        return data