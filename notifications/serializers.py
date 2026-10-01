from rest_framework import serializers

from .models import Hatirlatma, HatirlatmaKurali


class HatirlatmaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hatirlatma
        fields = (
            "id", "baslik", "aciklama", "ilgili_app", "ilgili_model",
            "ilgili_kayit_id", "hatirlatma_tarihi", "seviye", "durum",
            "sorumlu_kullanici", "tekrarlama", "tekrarlama_gun", "tenant", "created_at", "updated_at",
        )
        read_only_fields = ("id", "tenant", "created_at", "updated_at")


class HatirlatmaKuraliSerializer(serializers.ModelSerializer):
    class Meta:
        model = HatirlatmaKurali
        fields = (
            "id", "ilgili_app", "ilgili_model", "tetikleyici_alan",
            "once_gun", "seviye", "baslik_sablonu", "aktif_mi", "tenant",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "tenant", "created_at", "updated_at")
