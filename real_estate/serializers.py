"""Gayrimenkul API serializer'ları."""

from rest_framework import serializers

from tenants.serializers import TenantAwareModelSerializer

from .models import Ada, KatKarsiligiSenaryo, MalikMutabakati, Parsel, RealEstate


class AdaSerializer(TenantAwareModelSerializer):
    class Meta:
        model = Ada
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_ada_no(self, value):
        if not value.strip():
            raise serializers.ValidationError("Ada numarası zorunludur.")
        return value.strip()


class ParselSerializer(TenantAwareModelSerializer):
    ada_no = serializers.CharField(source="ada.ada_no", read_only=True, default=None)
    ilce = serializers.CharField(source="ada.ilce", read_only=True, default=None)

    class Meta:
        model = Parsel
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        alan = attrs.get("alan_m2", getattr(self.instance, "alan_m2", None))
        oran = attrs.get("kat_karsiligi_orani", getattr(self.instance, "kat_karsiligi_orani", 0))
        if alan is not None and alan <= 0:
            raise serializers.ValidationError({"alan_m2": "Parsel alanı sıfırdan büyük olmalıdır."})
        if oran < 0 or oran > 100:
            raise serializers.ValidationError({"kat_karsiligi_orani": "Oran 0 ile 100 arasında olmalıdır."})
        return attrs


class KatKarsiligiSenaryoSerializer(TenantAwareModelSerializer):
    parsel_no = serializers.CharField(source="parsel.parsel_no", read_only=True, default=None)

    class Meta:
        model = KatKarsiligiSenaryo
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        for alan in ("arsa_pay_orani", "kat_karsiligi_orani"):
            deger = attrs.get(alan, getattr(self.instance, alan, 0))
            if deger < 0 or deger > 100:
                raise serializers.ValidationError({alan: "Oran 0 ile 100 arasında olmalıdır."})
        if attrs.get("bagimsiz_bolum_m2", getattr(self.instance, "bagimsiz_bolum_m2", 0)) <= 0:
            raise serializers.ValidationError({"bagimsiz_bolum_m2": "Bağımsız bölüm alanı sıfırdan büyük olmalıdır."})
        if attrs.get("toplam_birim_sayisi", getattr(self.instance, "toplam_birim_sayisi", 0)) <= 0:
            raise serializers.ValidationError({"toplam_birim_sayisi": "Birim sayısı sıfırdan büyük olmalıdır."})
        return attrs


class MalikMutabakatiSerializer(TenantAwareModelSerializer):
    senaryo_adi = serializers.CharField(source="senaryo.senaryo_adi", read_only=True, default=None)

    class Meta:
        model = MalikMutabakati
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        malik_adi = attrs.get("malik_adi", getattr(self.instance, "malik_adi", "")).strip()
        pay_orani = attrs.get("pay_orani", getattr(self.instance, "pay_orani", 0))
        senaryo = attrs.get("senaryo", getattr(self.instance, "senaryo", None))
        if not malik_adi:
            raise serializers.ValidationError({"malik_adi": "Malik adı zorunludur."})
        if pay_orani < 0 or pay_orani > 100:
            raise serializers.ValidationError({"pay_orani": "Pay oranı 0 ile 100 arasında olmalıdır."})
        if senaryo is not None:
            mevcutlar = MalikMutabakati.objects.filter(senaryo=senaryo)
            if self.instance is not None:
                mevcutlar = mevcutlar.exclude(pk=self.instance.pk)
            toplam = sum((kayit.pay_orani for kayit in mevcutlar), pay_orani)
            if toplam > 100:
                raise serializers.ValidationError({"pay_orani": "Aynı senaryodaki malik payları toplamı %100'ü aşamaz."})
        attrs["malik_adi"] = malik_adi
        return attrs


class RealEstateSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True, default=None)

    class Meta:
        model = RealEstate
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")