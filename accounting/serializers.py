"""Muhasebe modülü API serializer'ları — çift kayıt korumalı (tenant izole)."""

from decimal import Decimal

from rest_framework import serializers

from tenants.serializers import TenantAwareModelSerializer, fk_kapsam_kontrol

from .models import FisSatiri, HesapPlani, MuhasebeFisi


class HesapPlaniSerializer(TenantAwareModelSerializer):
    class Meta:
        model = HesapPlani
        fields = "__all__"
        read_only_fields = ("id",)


class FisSatiriSerializer(serializers.ModelSerializer):
    hesap_kodu = serializers.CharField(source="hesap.kod", read_only=True)

    class Meta:
        model = FisSatiri
        fields = ("id", "hesap", "hesap_kodu", "borc", "alacak", "aciklama")
        read_only_fields = ("id", "hesap_kodu")

    def validate(self, attrs):
        borc = attrs.get("borc", Decimal("0")) or Decimal("0")
        alacak = attrs.get("alacak", Decimal("0")) or Decimal("0")
        if borc > 0 and alacak > 0:
            raise serializers.ValidationError("Bir satırda hem borç hem alacak olamaz.")
        if borc == 0 and alacak == 0:
            raise serializers.ValidationError("Satır tutarı 0 olamaz.")
        return attrs


class MuhasebeFisiSerializer(TenantAwareModelSerializer):
    """Fiş — nested satırlar; kayıt öncesi borç == alacak zorunlu."""

    satirlar = FisSatiriSerializer(many=True)

    class Meta:
        model = MuhasebeFisi
        fields = "__all__"
        read_only_fields = ("id", "created_at")

    def validate_satirlar(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Fişte en az iki satır olmalıdır.")
        return value

    def validate(self, attrs):
        satirlar = attrs.get("satirlar", getattr(self.instance, "satirlar", None))
        if satirlar is not None and hasattr(satirlar, "all"):
            satirlar = None  # update'te satır değişimi kapalı — aşağıda kontrol ediliyor
        if satirlar:
            request = self.context.get("request")
            tenant_id = getattr(getattr(request, "user", None), "tenant_id", None)
            for satir in satirlar:
                hesap = satir.get("hesap") if isinstance(satir, dict) else getattr(satir, "hesap", None)
                if hesap is not None and tenant_id and hesap.tenant_id != tenant_id:
                    raise serializers.ValidationError(
                        {"satirlar": "Satırdaki hesap bu firma kapsamına ait değil."}
                    )
        if satirlar:
            toplam_borc = sum((s.get("borc") or Decimal("0") for s in satirlar), Decimal("0"))
            toplam_alacak = sum(
                (s.get("alacak") or Decimal("0") for s in satirlar), Decimal("0")
            )
            if toplam_borc != toplam_alacak:
                raise serializers.ValidationError(
                    "Muhasebe fişinde borç ve alacak eşit olmalıdır."
                )
            if toplam_borc <= 0:
                raise serializers.ValidationError("Fiş tutarı 0'dan büyük olmalıdır.")
        if self.instance and self.instance.durum != MuhasebeFisi.Durum.TASLAK:
            if set(attrs) - {"aciklama", "durum"}:
                raise serializers.ValidationError(
                    "Kayıtlı/iptal fişte yalnızca açıklama güncellenebilir."
                )
        return attrs

    def create(self, validated_data):
        from django.db import transaction

        satirlar = validated_data.pop("satirlar", [])
        with transaction.atomic():
            fis = MuhasebeFisi.objects.create(**validated_data)
            for satir in satirlar:
                FisSatiri.objects.create(fis=fis, **satir)
            fis.full_clean()
        return fis

    def update(self, instance, validated_data):
        if "satirlar" in validated_data:
            raise serializers.ValidationError("Fiş satırları sonradan değiştirilemez.")
        for alan, deger in validated_data.items():
            setattr(instance, alan, deger)
        instance.full_clean()
        instance.save()
        return instance
