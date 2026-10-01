"""Finans modülü API serializer'ları (tenant izole)."""

from decimal import Decimal

from rest_framework import serializers

from tenants.serializers import TenantAwareModelSerializer, fk_kapsam_kontrol

from .models import CekSenet, FinansalIslem, KasaBankaHesabi, Fatura, FaturaKalemi, VergiProfili, Rapor, Ayar
from .services.fatura_hesaplama import fatura_toplam_hesapla, kalem_hesapla


class KasaBankaHesabiSerializer(TenantAwareModelSerializer):
    iban_maskeli = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = KasaBankaHesabi
        fields = "__all__"
        read_only_fields = ("id", "iban_maskeli", "created_at")
        extra_kwargs = {"iban": {"write_only": True}}

    @staticmethod
    def _maskele(deger: str) -> str | None:
        if not deger:
            return None
        if len(deger) <= 8:
            return "*" * len(deger)
        return f"{deger[:4]}{'*' * (len(deger) - 8)}{deger[-4:]}"

    def get_iban_maskeli(self, obj: KasaBankaHesabi) -> str | None:
        return self._maskele(obj.iban or "")


class FinansalIslemSerializer(TenantAwareModelSerializer):
    hesap_kodu = serializers.CharField(source="hesap.kod", read_only=True, default=None)

    class Meta:
        model = FinansalIslem
        fields = "__all__"
        read_only_fields = ("id", "hesap_kodu", "created_at")

    def validate(self, attrs):
        if self.instance and self.instance.is_cancelled:
            raise serializers.ValidationError("İptal edilmiş işlem değiştirilemez.")
        if self.instance and "is_cancelled" not in attrs and set(attrs) - {"aciklama"}:
            raise serializers.ValidationError(
                "Kayıtlı işlemin yalnızca açıklaması güncellenebilir (iptal için iptal endpoint'i)."
            )
        fk_kapsam_kontrol(self, attrs, ("hesap", "cari", "muhasebe_fisi"))
        return attrs


class CekSenetSerializer(TenantAwareModelSerializer):
    class Meta:
        model = CekSenet
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        if attrs.get("tutar", 0) <= 0:
            raise serializers.ValidationError({"tutar": "Tutar sıfırdan büyük olmalıdır."})
        fk_kapsam_kontrol(self, attrs, ("cari", "hesap", "proje"))
        return attrs


class FaturaKalemiSerializer(serializers.ModelSerializer):
    ara_toplam = serializers.SerializerMethodField(read_only=True)
    kdv_tutari = serializers.SerializerMethodField(read_only=True)
    tevkifat_tutari = serializers.SerializerMethodField(read_only=True)
    stopaj_tutari = serializers.SerializerMethodField(read_only=True)
    satir_toplami = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FaturaKalemi
        fields = "__all__"
        read_only_fields = ("id", "fatura", "ara_toplam", "kdv_tutari", "tevkifat_tutari", "stopaj_tutari", "satir_toplami")

    def validate(self, attrs):
        if attrs.get("miktar", 0) <= 0 or attrs.get("birim_fiyat", 0) < 0:
            raise serializers.ValidationError("Miktar pozitif, birim fiyat negatif olamaz.")
        if any(not 0 <= attrs.get(alan, 0) <= 100 for alan in ("kdv_orani", "tevkifat_orani", "stopaj_orani")):
            raise serializers.ValidationError("KDV, tevkifat ve stopaj oranları 0-100 arasında olmalıdır.")
        if not 0 <= attrs.get("iskonto_orani", 0) <= 100:
            raise serializers.ValidationError({"iskonto_orani": "İskonto oranı 0-100 arasında olmalıdır."})
        return attrs

    def _hesap(self, obj):
        # FAZ 6E: kalem başına tek hesaplama + nested bağlamda parent fatura
        # passthrough (kalem.fatura tekrar sorgulanmaz).
        cached = getattr(obj, "_hesap_cache", None)
        if cached is None:
            parent = getattr(getattr(getattr(self, "parent", None), "parent", None), "instance", None)
            cached = kalem_hesapla(
                obj, fatura=parent if isinstance(parent, Fatura) else None
            )
            obj._hesap_cache = cached
        return cached
    def get_ara_toplam(self, obj): return self._hesap(obj)["matrah"]
    def get_kdv_tutari(self, obj): return self._hesap(obj)["kdv"]
    def get_tevkifat_tutari(self, obj): return self._hesap(obj)["tevkifat"]
    def get_stopaj_tutari(self, obj): return self._hesap(obj)["stopaj"]
    def get_satir_toplami(self, obj): return self._hesap(obj)["satir_toplami"]


class VergiProfiliSerializer(TenantAwareModelSerializer):
    class Meta:
        model = VergiProfili
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        if any(not 0 <= attrs.get(alan, 0) <= 100 for alan in ("kdv_orani", "tevkifat_orani", "stopaj_orani")):
            raise serializers.ValidationError("Vergi profili oranları 0-100 arasında olmalıdır.")
        return attrs


class FaturaSerializer(TenantAwareModelSerializer):
    cari_ad = serializers.CharField(source="cari.ad", read_only=True, default=None)
    hesap_ad = serializers.CharField(source="kasa_banka_hesabi.ad", read_only=True, default=None)
    kalemler = FaturaKalemiSerializer(many=True, required=False)
    ara_toplam = serializers.SerializerMethodField(read_only=True)
    kdv_tutari = serializers.SerializerMethodField(read_only=True)
    tevkifat_tutari = serializers.SerializerMethodField(read_only=True)
    stopaj_tutari = serializers.SerializerMethodField(read_only=True)
    matrah = serializers.SerializerMethodField(read_only=True)
    kdv = serializers.SerializerMethodField(read_only=True)
    tevkifat = serializers.SerializerMethodField(read_only=True)
    stopaj = serializers.SerializerMethodField(read_only=True)
    odenecek = serializers.SerializerMethodField(read_only=True)
    tl_karsiligi = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Fatura
        fields = "__all__"
        read_only_fields = ("id", "cari_ad", "hesap_ad", "ara_toplam", "kdv_tutari", "tevkifat_tutari", "stopaj_tutari", "created_at", "updated_at")

    def validate_tutar(self, value):
        if value <= 0:
            raise serializers.ValidationError("Fatura tutarı 0'dan büyük olmalıdır.")
        return value

    def validate(self, attrs):
        if self.instance and self.instance.durum != Fatura.DurumChoices.DRAFT and set(attrs) - {"durum", "aciklama"}:
            raise serializers.ValidationError("Aktif/ödenmiş fatura yalnızca açıklama veya durum alanından güncellenebilir.")
        kur = attrs.get("kur", getattr(self.instance, "kur", Decimal("1")))
        fatura_turu = attrs.get("fatura_turu", getattr(self.instance, "fatura_turu", "satis"))
        iade_faturasi = attrs.get("iade_faturasi", getattr(self.instance, "iade_faturasi", None))
        if kur <= 0:
            raise serializers.ValidationError({"kur": "Kur sıfırdan büyük olmalıdır."})
        if attrs.get("iskonto_tutari", getattr(self.instance, "iskonto_tutari", Decimal("0"))) < 0:
            raise serializers.ValidationError({"iskonto_tutari": "İskonto negatif olamaz."})
        if attrs.get("odenen_tutar", getattr(self.instance, "odenen_tutar", Decimal("0"))) < 0:
            raise serializers.ValidationError({"odenen_tutar": "Ödenen tutar negatif olamaz."})
        if fatura_turu == "iade" and not iade_faturasi:
            raise serializers.ValidationError({"iade_faturasi": "İade faturasında referans fatura zorunludur."})
        if fatura_turu != "iade" and iade_faturasi:
            raise serializers.ValidationError({"iade_faturasi": "Referans yalnızca iade faturasında kullanılabilir."})
        fk_kapsam_kontrol(self, attrs, ("cari", "kasa_banka_hesabi", "iade_faturasi"))
        return attrs

    def _toplamlar(self, obj):
        ozet = self._ozet(obj)
        return tuple(Decimal(ozet[alan]) for alan in ("matrah", "kdv", "tevkifat", "stopaj"))

    def get_ara_toplam(self, obj):
        # FAZ 6E: memoized özet kullanılır; kalemsiz faturada tutar döner
        # (davranış korunur, ek sorgu yok).
        ozet = self._ozet(obj)
        return str(Decimal(ozet["matrah"]) if ozet["kalem_detaylari"] else obj.tutar)

    def get_kdv_tutari(self, obj):
        return str(self._toplamlar(obj)[1])

    def get_tevkifat_tutari(self, obj):
        return str(self._toplamlar(obj)[2])

    def get_stopaj_tutari(self, obj):
        return str(self._toplamlar(obj)[3])

    def _ozet(self, obj):
        # FAZ 6E: aynı fatura için özet tek kez hesaplanır (alan başına
        # kalemler sorgusu engellenir). Önbellek istek-içi nesnededir.
        ozet = getattr(obj, "_ozet_cache", None)
        if ozet is None:
            ozet = fatura_toplam_hesapla(obj)
            obj._ozet_cache = ozet
        return ozet

    def get_matrah(self, obj): return self._ozet(obj)["matrah"]
    def get_kdv(self, obj): return self._ozet(obj)["kdv"]
    def get_tevkifat(self, obj): return self._ozet(obj)["tevkifat"]
    def get_stopaj(self, obj): return self._ozet(obj)["stopaj"]
    def get_odenecek(self, obj): return self._ozet(obj)["odenecek"]
    def get_tl_karsiligi(self, obj): return self._ozet(obj)["tl_karsiligi"]

    def create(self, validated_data):
        kalemler = validated_data.pop("kalemler", [])
        fatura = Fatura.objects.create(**validated_data)
        self._kalemleri_kaydet(fatura, kalemler)
        return fatura

    def update(self, instance, validated_data):
        kalemler = validated_data.pop("kalemler", None)
        fatura = super().update(instance, validated_data)
        if kalemler is not None:
            fatura.kalemler.all().delete()
            self._kalemleri_kaydet(fatura, kalemler)
        return fatura

    def _kalemleri_kaydet(self, fatura, kalemler):
        if not kalemler:
            return
        satirlar = [FaturaKalemi(fatura=fatura, **kalem) for kalem in kalemler]
        FaturaKalemi.objects.bulk_create(satirlar)
        fatura.tutar = Decimal(fatura_toplam_hesapla(fatura)["genel_toplam"])
        fatura.save(update_fields=["tutar", "updated_at"])


class RaporSerializer(TenantAwareModelSerializer):
    class Meta:
        model = Rapor
        fields = "__all__"
        read_only_fields = ("id", "created_by", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("cari", "kasa_banka_hesabi"))
        return attrs


class AyarSerializer(TenantAwareModelSerializer):
    class Meta:
        model = Ayar
        fields = "__all__"
        read_only_fields = ("id", "created_by", "created_at", "updated_at")
