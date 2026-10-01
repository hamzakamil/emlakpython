"""Cari modülü API serializer'ları (tenant izole)."""

from rest_framework import serializers

from tenants.serializers import TenantAwareModelSerializer, fk_kapsam_kontrol

from .models import Cari, CariHareket


class CariSerializer(TenantAwareModelSerializer):
    telefon_maskeli = serializers.SerializerMethodField(read_only=True)
    iban_maskeli = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Cari
        fields = "__all__"
        read_only_fields = (
            "id", "telefon_maskeli", "iban_maskeli", "created_at", "updated_at",
        )
        extra_kwargs = {"telefon": {"write_only": True}, "iban": {"write_only": True}}

    def validate(self, attrs):
        if "ad" in attrs:
            ad = (attrs.get("ad") or "").strip()
            if not ad:
                raise serializers.ValidationError({"ad": "Ad / unvan zorunludur."})
            attrs["ad"] = ad

        vergi_no = (attrs.get("vergi_no") if "vergi_no" in attrs else getattr(self.instance, "vergi_no", "")) or ""
        vergi_no = vergi_no.strip()
        tc_kimlik_no = (attrs.get("tc_kimlik_no") if "tc_kimlik_no" in attrs else getattr(self.instance, "tc_kimlik_no", "")) or ""
        tc_kimlik_no = tc_kimlik_no.strip()
        if vergi_no and (not vergi_no.isdigit() or len(vergi_no) != 10):
            raise serializers.ValidationError(
                {"vergi_no": "Vergi kimlik no 10 hane rakam olmalıdır."}
            )
        if tc_kimlik_no and (not tc_kimlik_no.isdigit() or len(tc_kimlik_no) != 11):
            raise serializers.ValidationError(
                {"tc_kimlik_no": "T.C. kimlik no 11 hane rakam olmalıdır."}
            )
        if vergi_no and tc_kimlik_no:
            raise serializers.ValidationError("VKN ve T.C. kimlik no aynı anda girilemez.")
        telefon = (attrs.get("telefon") or "").strip()
        if "adres" in attrs and self.instance and attrs["adres"].strip() != (self.instance.adres or "").strip():
            if self.instance.adres:
                attrs["eski_adres"] = self.instance.adres
        iban = (attrs.get("iban") or "").replace(" ", "").upper()
        if telefon:
            attrs["telefon"] = telefon
        if iban:
            if not iban.startswith("TR") or len(iban) != 26 or not iban[2:].isdigit():
                raise serializers.ValidationError(
                    {"iban": "IBAN, TR ile başlayan 26 karakter olmalıdır."}
                )
            attrs["iban"] = iban
        if "vergi_no" in attrs:
            attrs["vergi_no"] = vergi_no
        if "vergi_dairesi" in attrs:
            attrs["vergi_dairesi"] = (attrs.get("vergi_dairesi") or "").strip()
        if "adres" in attrs:
            attrs["adres"] = (attrs.get("adres") or "").strip()
        if "tc_kimlik_no" in attrs:
            attrs["tc_kimlik_no"] = tc_kimlik_no
        if "web_sitesi" in attrs:
            attrs["web_sitesi"] = (attrs.get("web_sitesi") or "").strip()
        if "ulke" in attrs:
            attrs["ulke"] = (attrs.get("ulke") or "Türkiye").strip() or "Türkiye"
        for alan in ("telefonlar", "cep_telefonlari", "epostalar"):
            if alan in attrs and not isinstance(attrs[alan], list):
                raise serializers.ValidationError({alan: "Bu alan liste olarak gönderilmelidir."})
        if "yetkili_kisiler" in attrs:
            if not isinstance(attrs["yetkili_kisiler"], list):
                raise serializers.ValidationError({"yetkili_kisiler": "Bu alan liste olarak gönderilmelidir."})
            kisiler = [
                {"ad": str(item.get("ad", "")).strip(), "telefon": str(item.get("telefon", "")).strip()}
                for item in attrs["yetkili_kisiler"]
                if isinstance(item, dict) and str(item.get("ad", "")).strip()
            ]
            attrs["yetkili_kisiler"] = kisiler
            if kisiler:
                attrs["yetkili_kisi"] = kisiler[0]["ad"]
                attrs["yetkili_telefon"] = kisiler[0]["telefon"]
        for alan in ("telefonlar", "cep_telefonlari", "epostalar"):
            if alan in attrs:
                attrs[alan] = [str(item).strip() for item in attrs[alan] if str(item).strip()]
        if "telefonlar" in attrs and attrs["telefonlar"]:
            attrs["telefon"] = attrs["telefonlar"][0]
        if "cep_telefonlari" in attrs and attrs["cep_telefonlari"]:
            attrs["cep_telefonu"] = attrs["cep_telefonlari"][0]
        if "epostalar" in attrs and attrs["epostalar"]:
            attrs["eposta"] = attrs["epostalar"][0]
        fk_kapsam_kontrol(self, attrs, ("proje",))
        return attrs

    def validate_vade_gunu(self, value):
        if value < 0 or value > 365:
            raise serializers.ValidationError("Vade günü 0 ile 365 arasında olmalıdır.")
        return value

    def validate_iskonto_orani(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("İskonto oranı 0 ile 100 arasında olmalıdır.")
        return value

    def validate_risk_limiti(self, value):
        if value < 0:
            raise serializers.ValidationError("Risk limiti 0'dan küçük olamaz.")
        return value

    @staticmethod
    def _maskele(deger: str, bastan: int = 2, sondan: int = 2) -> str | None:
        if not deger:
            return None
        if len(deger) <= bastan + sondan:
            return "*" * len(deger)
        return f"{deger[:bastan]}{'*' * (len(deger) - bastan - sondan)}{deger[-sondan:]}"

    def get_telefon_maskeli(self, obj: Cari) -> str | None:
        return self._maskele(obj.telefon or "")

    def get_iban_maskeli(self, obj: Cari) -> str | None:
        return self._maskele(obj.iban or "", bastan=4, sondan=4)


class CariHareketSerializer(TenantAwareModelSerializer):
    cari_ad = serializers.CharField(source="cari.ad", read_only=True, default=None)
    muhasebelesti = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CariHareket
        fields = "__all__"
        read_only_fields = (
            "id", "cari_ad", "muhasebelesti", "muhasebe_fisi", "created_at",
        )

    def get_muhasebelesti(self, obj):
        return obj.muhasebe_fisi_id is not None

    def validate(self, attrs):
        if attrs.get("tutar", 0) <= 0:
            raise serializers.ValidationError({"tutar": "Tutar 0'dan büyük olmalıdır."})
        if self.instance and self.instance.is_cancelled:
            raise serializers.ValidationError("İptal edilmiş hareket değiştirilemez.")
        if self.instance and "is_cancelled" not in attrs and set(attrs) - {"aciklama"}:
            raise serializers.ValidationError(
                "Kayıtlı hareketin yalnızca açıklaması güncellenebilir (iptal için iptal endpoint'i)."
            )
        fk_kapsam_kontrol(self, attrs, ("cari", "fatura", "muhasebe_fisi"))
        return attrs
