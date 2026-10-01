"""İnşaat modülü API serializer'ları — Faz 1 + Faz 2 (poz planı, hakediş)."""

from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from tenants.serializers import TenantAwareModelSerializer, fk_kapsam_kontrol

from .imports import normalize_yapi_sinifi
from .models import (
    Hakedis,
    HakedisSatiri,
    KaliteKontrol,
    Malzeme,
    MalzemeFiyat,
    Poz,
    PozFiyat,
    PozGrubu,
    PozMalzemeIliskisi,
    PozPlan,
    Proje,
    ProjeMalzeme,
    ProjeMalzemeFiyat,
    ProjePozMalzeme,
    ProjePozFiyat,
    SantiyeGunlugu,
    TaseronSozlesi,
    Tedarikci,
    YapiSinifiBirimMaliyet,
    ContractTemplate,
    RiskStructure,
    LeaseAssistance,
    KaliteKabulTeminati,
    MalzemeTedarikciIliskisi,
    SantiyeCheckIn,
    MalzemeHareketi,
    TedarikciTeklifi,
    EKB,
    IFCImportJob,
    IFCQuantityDraft,
    Mahal,
    MahalElemani,
    YaklasikMaliyet,
    YaklasikMaliyetSatiri,
    Metraj,
    PozAnaliz,
    NakliyeMesafe,
    Hatirlatma,
    HatirlatmaKurali,
    YfkPozVersiyon,
    YfkFiyat,
    YfkRayic,
    YfkAnaliz,
    YfkGuncellemeGecmisi,
)
from .services import poz_birim_fiyati


class MetrajSerializer(TenantAwareModelSerializer):
    class Meta:
        model = Metraj
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at")


class PozAnalizSerializer(TenantAwareModelSerializer):
    class Meta:
        model = PozAnaliz
        fields = "__all__"
        read_only_fields = ("id", "tenant", "tutar")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("poz",))
        return attrs


class NakliyeMesafeSerializer(TenantAwareModelSerializer):
    class Meta:
        model = NakliyeMesafe
        fields = "__all__"
        read_only_fields = ("id", "tenant")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje", "poz"))
        return attrs


class HatirlatmaSerializer(TenantAwareModelSerializer):
    class Meta:
        model = Hatirlatma
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("sorumlu_kullanici",))
        return attrs


class HatirlatmaKuraliSerializer(TenantAwareModelSerializer):
    class Meta:
        model = HatirlatmaKurali
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at")


class PozGrubuSerializer(TenantAwareModelSerializer):
    class Meta:
        model = PozGrubu
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("ust_grup",))
        return attrs


class PozSerializer(TenantAwareModelSerializer):
    grup_bilgisi = serializers.CharField(source="grup.kod", read_only=True)

    class Meta:
        model = Poz
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("grup",))
        return attrs


class MalzemeSerializer(TenantAwareModelSerializer):
    class Meta:
        model = Malzeme
        fields = "__all__"
        read_only_fields = ("id", "qr_kodu", "created_at", "updated_at")


class PozMalzemeIliskisiSerializer(TenantAwareModelSerializer):
    class Meta:
        model = PozMalzemeIliskisi
        fields = "__all__"
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("poz", "malzeme"))
        return attrs


class YapiSinifiBirimMaliyetSerializer(ModelSerializer):
    class Meta:
        model = YapiSinifiBirimMaliyet
        fields = "__all__"
        read_only_fields = ("id", "created_at")


class PozFiyatSerializer(ModelSerializer):
    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("poz",))
        return attrs

    class Meta:
        model = PozFiyat
        fields = "__all__"
        read_only_fields = ("id", "created_at", "ice_aktarma_tarihi")

    def validate_donem(self, value):
        if value:
            valid_months = [
                "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
            ]
            if value not in valid_months:
                raise ValidationError("Geçerli bir Türkçe ay adı olmalıdır.")
        return value


class ProjePozFiyatSerializer(TenantAwareModelSerializer):
    poz_no = serializers.CharField(source="poz.poz_no", read_only=True)
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)

    class Meta:
        model = ProjePozFiyat
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at", "poz_no", "proje_kodu")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje", "poz"))
        return attrs


class YapiSinifiBirimMaliyetSerializer(TenantAwareModelSerializer):
    class Meta:
        model = YapiSinifiBirimMaliyet
        fields = "__all__"
        read_only_fields = ("id", "created_at")

    def validate_sinif_kodu(self, value: str) -> str:
        """readme §52.6 madde 5: "4A" / "IV A" girişleri resmî "IV-A" gösterimine
        normalize edilir; geçersiz kod reddedilir."""
        try:
            return normalize_yapi_sinifi(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))


class ProjeSerializer(TenantAwareModelSerializer):
    yapisinif_kodu = serializers.CharField(
        source="yapisinif_maliyet.sinif_kodu", read_only=True, default=None
    )

    class Meta:
        model = Proje
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("yapisinif_maliyet",))
        return attrs


class MahalElemaniSerializer(TenantAwareModelSerializer):
    class Meta:
        model = MahalElemani
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("mahal",))
        return attrs


class MahalSerializer(TenantAwareModelSerializer):
    elemanlar = MahalElemaniSerializer(many=True, read_only=True)
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)

    class Meta:
        model = Mahal
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "created_at", "updated_at", "elemanlar", "proje_kodu",
        )

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje",))
        return attrs


class YaklasikMaliyetSatiriSerializer(TenantAwareModelSerializer):
    poz_no = serializers.CharField(source="poz.poz_no", read_only=True)
    satir_tutari = serializers.DecimalField(
        source="toplam_tutar", max_digits=18, decimal_places=2, read_only=True
    )

    class Meta:
        model = YaklasikMaliyetSatiri
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "birim_fiyat_snapshot", "toplam_tutar",
            "created_at", "updated_at", "poz_no", "satir_tutari",
        )

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("poz", "mahal", "yaklasik_maliyet", "metraj"))
        return attrs


class YaklasikMaliyetSerializer(TenantAwareModelSerializer):
    satirlar = YaklasikMaliyetSatiriSerializer(many=True, read_only=True)
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)

    class Meta:
        model = YaklasikMaliyet
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "versiyon", "onceki", "toplam_tutar",
            "created_at", "updated_at", "satirlar", "proje_kodu",
        )

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje",))
        return attrs


class PozPlanSerializer(TenantAwareModelSerializer):
    """Poz maliyet planı — proje/poz/yıl bazlı planlanan vs gerçekleşen metraj.

    `birim_fiyat_snapshot` kayıt anında `PozFiyat`'tan otomatik doldurulur
    (snapshot; değişmez) ve istemciden kabul edilmez. Model `clean()`'i
    ValidationError fırlattığı için API'de 400 dönebilmesi adına doğrulama
    burada da tekrarlanır.
    """

    poz_no = serializers.CharField(source="poz.poz_no", read_only=True)
    grup_kodu = serializers.CharField(source="poz.grup.kod", read_only=True)
    plan_deger = serializers.SerializerMethodField(read_only=True)
    gercek_deger = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PozPlan
        fields = "__all__"
        read_only_fields = (
            "id", "birim_fiyat_snapshot", "created_at", "updated_at",
            "poz_no", "grup_kodu", "plan_deger", "gercek_deger",
        )

    def validate(self, attrs):
        planlanan = attrs.get(
            "planlanan_miktar", getattr(self.instance, "planlanan_miktar", None)
        )
        gercek = attrs.get("gercek_miktar", getattr(self.instance, "gercek_miktar", None))
        baslangic = attrs.get(
            "planlanan_baslangic", getattr(self.instance, "planlanan_baslangic", None)
        )
        bitis = attrs.get("planlanan_bitis", getattr(self.instance, "planlanan_bitis", None))
        poz = attrs.get("poz", getattr(self.instance, "poz", None))
        yil = attrs.get("yil", getattr(self.instance, "yil", None))

        if planlanan is not None and planlanan <= 0:
            raise serializers.ValidationError(
                {"planlanan_miktar": "Planlanan metraj 0'dan büyük olmalıdır."}
            )
        if gercek is not None and gercek < 0:
            raise serializers.ValidationError(
                {"gercek_miktar": "Gerçekleşen metraj negatif olamaz."}
            )
        if baslangic and bitis and bitis < baslangic:
            raise serializers.ValidationError(
                {"planlanan_bitis": "Planlanan bitiş tarihi başlangıçtan önce olamaz."}
            )
        if poz is not None and yil and poz_birim_fiyati(poz, yil) is None:
            raise serializers.ValidationError(
                {
                    "poz": (
                        f"{poz.poz_no} pozunun {yil} yılı için aktif birim fiyatı "
                        "bulunamadı. Önce PozFiyat kaydı oluşturun."
                    )
                }
            )
        fk_kapsam_kontrol(self, attrs, ("proje", "poz", "metraj"))
        return attrs

    def get_plan_deger(self, obj: PozPlan) -> str:
        tutar = (obj.planlanan_miktar * obj.birim_fiyat_snapshot).quantize(Decimal("0.01"))
        return str(tutar)

    def get_gercek_deger(self, obj: PozPlan) -> str:
        tutar = (obj.gercek_miktar * obj.birim_fiyat_snapshot).quantize(Decimal("0.01"))
        return str(tutar)


class IFCQuantityDraftSerializer(TenantAwareModelSerializer):
    poz_no = serializers.CharField(source="poz.poz_no", read_only=True, default=None)

    class Meta:
        model = IFCQuantityDraft
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at", "poz_no")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("job", "project", "poz"))
        return attrs


class IFCImportJobSerializer(TenantAwareModelSerializer):
    draft_rows = IFCQuantityDraftSerializer(many=True, read_only=True)
    project_code = serializers.CharField(source="project.proje_kodu", read_only=True)

    class Meta:
        model = IFCImportJob
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "file_name", "file_size", "content_type", "checksum",
            "status", "parser_mode", "validation_errors", "processing_message",
            "uploaded_by", "started_at", "finished_at", "created_at", "updated_at",
            "draft_rows", "project_code",
        )

    def validate(self, attrs):
        request = self.context.get("request")
        tenant_id = getattr(getattr(request, "user", None), "tenant_id", None)
        project = attrs.get("project", getattr(self.instance, "project", None))
        if tenant_id and project and project.tenant_id != tenant_id:
            raise serializers.ValidationError({"project": "Seçilen proje bu firma kapsamına ait değil."})
        year = attrs.get("year", getattr(self.instance, "year", None))
        if year is not None and not 2000 <= year <= 2100:
            raise serializers.ValidationError({"year": "Yıl 2000 ile 2100 arasında olmalıdır."})
        return attrs


class HakedisSatiriSerializer(serializers.ModelSerializer):
    """Hakediş satırı — poz + miktar + birim fiyat (tutar salt okunur)."""

    poz_no = serializers.CharField(source="poz.poz_no", read_only=True)
    satir_tutar = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HakedisSatiri
        fields = ("id", "poz", "poz_no", "miktar", "birim_fiyat", "satir_tutar")
        read_only_fields = ("id", "poz_no", "satir_tutar")

    def get_satir_tutar(self, obj: HakedisSatiri) -> str:
        return str(obj.satir_tutar)

    def validate(self, attrs):
        # FAZ 6C: onaylı/iptal hakedişin satırı serializer katmanında da kilitli.
        if self.instance is not None:
            hakedis = getattr(self.instance, "hakedis", None)
            if hakedis is not None and hakedis.durum != Hakedis.Durum.TASLAK:
                from audit.loglama import reddedilen_islemi_kaydet

                reddedilen_islemi_kaydet(
                    self.context.get("request"), "construction.HakedisSatiri",
                    getattr(self.instance, "pk", None), dict(attrs),
                    neden="Onaylı/iptal hakediş satır değişikliği reddedildi.",
                )
                raise serializers.ValidationError(
                    "Onaylanmış/iptal hakedişin satırları değiştirilemez."
                )
        return attrs


class HakedisSerializer(TenantAwareModelSerializer):
    """Hakediş — dönemsel hakediş (taslak → onaylandı / iptal)."""

    satirlar = HakedisSatiriSerializer(many=True, required=False)
    toplam_tutar = serializers.SerializerMethodField(read_only=True)
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True, default=None)

    class Meta:
        model = Hakedis
        fields = "__all__"
        read_only_fields = (
            "id", "toplam_tutar", "proje_kodu", "cari_hareket", "muhasebe_fisi",
            "onaylayan", "onay_tarihi", "created_at", "updated_at",
        )

    def get_toplam_tutar(self, obj: Hakedis) -> str:
        return str(obj.toplam_tutar.quantize(Decimal("0.01")))

    def create(self, validated_data):
        satirlar = validated_data.pop("satirlar", [])
        hakedis = Hakedis.objects.create(**validated_data)
        HakedisSatiri.objects.bulk_create(
            [HakedisSatiri(hakedis=hakedis, **satir) for satir in satirlar]
        )
        return hakedis

    def validate_donem(self, value: str) -> str:
        import re

        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value or ""):
            raise serializers.ValidationError("Dönem YYYY-MM biçiminde olmalıdır (örn. 2026-03).")
        return value

    def validate(self, attrs):
        if self.instance and self.instance.durum != Hakedis.Durum.TASLAK:
            if (set(attrs) - {"aciklama", "durum"}):
                from audit.loglama import reddedilen_islemi_kaydet

                reddedilen_islemi_kaydet(
                    self.context.get("request"), "construction.Hakedis",
                    getattr(self.instance, "pk", None), dict(attrs),
                    neden="Onaylı/iptal hakediş alan değişikliği reddedildi.",
                )
                raise serializers.ValidationError(
                    "Onaylanmış/iptal hakedişte yalnızca açıklama güncellenebilir."
                )
            if attrs.get("durum") == Hakedis.Durum.TASLAK:
                raise serializers.ValidationError("Onaylanmış/iptal hakediş taslağa döndürülemez.")
        fk_kapsam_kontrol(self, attrs, ("proje", "cari"))
        for satir in attrs.get("satirlar", []) or []:
            poz = satir.get("poz") if isinstance(satir, dict) else getattr(satir, "poz", None)
            if poz is not None:
                request = self.context.get("request")
                tenant_id = getattr(getattr(request, "user", None), "tenant_id", None)
                if tenant_id and poz.tenant_id != tenant_id:
                    raise serializers.ValidationError(
                        {"satirlar": "Satırdaki poz bu firma kapsamına ait değil."}
                    )
        return attrs


class ContractTemplateSerializer(TenantAwareModelSerializer):
    class Meta:
        model = ContractTemplate
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class RiskStructureSerializer(TenantAwareModelSerializer):
    class Meta:
        model = RiskStructure
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje",))
        return attrs


class LeaseAssistanceSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)

    class Meta:
        model = LeaseAssistance
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "proje_kodu")

    def validate(self, attrs):
        if self.instance:
            allowed = {"banka_iban", "banka_adi", "odeme_notu", "aciklama"}
            if set(attrs) - allowed:
                raise serializers.ValidationError(
                    "Otomatik oluşturulan kira yardımında yalnızca ödeme bilgileri düzenlenebilir."
                )
        fk_kapsam_kontrol(self, attrs, ("proje",))
        return attrs


class EKBSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    proje_adi = serializers.CharField(source="proje.ad", read_only=True)
    gecerlilik_durumu = serializers.SerializerMethodField()
    kalan_gun = serializers.SerializerMethodField()

    class Meta:
        model = EKB
        fields = "__all__"
        read_only_fields = (
            "id", "created_at", "updated_at", "proje_kodu", "proje_adi",
            "gecerlilik_durumu", "kalan_gun",
        )

    def validate(self, attrs):
        if "belge_no" in attrs:
            attrs["belge_no"] = attrs["belge_no"].strip()
            if not attrs["belge_no"]:
                raise serializers.ValidationError({"belge_no": "Belge numarası boş bırakılamaz."})
        issue = attrs.get("duzenlenme_tarihi", getattr(self.instance, "duzenlenme_tarihi", None))
        expiry = attrs.get("gecerlilik_tarihi", getattr(self.instance, "gecerlilik_tarihi", None))
        if issue and expiry and expiry <= issue:
            raise serializers.ValidationError(
                {"gecerlilik_tarihi": "Geçerlilik tarihi düzenlenme tarihinden sonra olmalıdır."}
            )
        fk_kapsam_kontrol(self, attrs, ("proje",))
        return attrs

    def _kalan_gun(self, obj):
        if not obj.gecerlilik_tarihi:
            return None
        return (obj.gecerlilik_tarihi - timezone.localdate()).days

    def get_kalan_gun(self, obj):
        return self._kalan_gun(obj)

    def get_gecerlilik_durumu(self, obj):
        kalan = self._kalan_gun(obj)
        if kalan is None:
            return "tarih_yok"
        if kalan < 0:
            return "suresi_doldu"
        if kalan <= 30:
            return "yaklasiyor"
        return "gecerli"


class SantiyeGunluguSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)

    class Meta:
        model = SantiyeGunlugu
        fields = "__all__"
        read_only_fields = ("id", "created_by", "created_at", "updated_at", "proje_kodu")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje",))
        return attrs


class SantiyeCheckInSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    kullanici_adi = serializers.CharField(source="kullanici.username", read_only=True)

    class Meta:
        model = SantiyeCheckIn
        fields = "__all__"
        read_only_fields = ("id", "kullanici", "created_at", "updated_at", "proje_kodu", "kullanici_adi")

    def validate(self, attrs):
        giris = attrs.get("giris_zamani", getattr(self.instance, "giris_zamani", None))
        cikis = attrs.get("cikis_zamani", getattr(self.instance, "cikis_zamani", None))
        if cikis and giris and cikis < giris:
            raise serializers.ValidationError({"cikis_zamani": "Çıkış zamanı girişten önce olamaz."})
        fk_kapsam_kontrol(self, attrs, ("proje",))
        return attrs


class MalzemeHareketiSerializer(TenantAwareModelSerializer):
    malzeme_adi = serializers.CharField(source="malzeme.ad", read_only=True)
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    kaydeden_adi = serializers.CharField(source="kaydeden.username", read_only=True)

    class Meta:
        model = MalzemeHareketi
        fields = "__all__"
        read_only_fields = ("id", "birim", "kaydeden", "created_at", "updated_at", "malzeme_adi", "proje_kodu", "kaydeden_adi")
        extra_kwargs = {"malzeme": {"required": False, "allow_null": True}}

    def validate(self, attrs):
        malzeme = attrs.get("malzeme")
        qr_kodu = attrs.get("qr_kodu", "").strip()
        if not malzeme and qr_kodu:
            tenant = self.context["request"].user.tenant_id
            try:
                malzeme = Malzeme.objects.get(tenant_id=tenant, qr_kodu=qr_kodu, is_active=True)
            except Malzeme.DoesNotExist:
                raise serializers.ValidationError({"qr_kodu": "Bu QR/manüel kod aktif bir malzeme ile eşleşmiyor."})
            attrs["malzeme"] = malzeme
        if not malzeme:
            raise serializers.ValidationError({"malzeme": "Malzeme veya QR/manüel kodu zorunludur."})
        attrs["qr_kodu"] = qr_kodu or malzeme.qr_kodu
        attrs["birim"] = malzeme.birim
        fk_kapsam_kontrol(self, attrs, ("proje", "malzeme"))
        return attrs


class KaliteKontrolSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    poz_no = serializers.CharField(source="poz.poz_no", read_only=True, default=None)

    class Meta:
        model = KaliteKontrol
        fields = "__all__"
        read_only_fields = (
            "id", "kontrol_eden", "onaylayan", "onay_tarihi", "created_at",
            "updated_at", "proje_kodu", "poz_no",
        )

    def validate(self, attrs):
        kriter = attrs.get("kriter", getattr(self.instance, "kriter", ""))
        if not kriter or not kriter.strip():
            raise serializers.ValidationError({"kriter": "Kontrol kriteri zorunludur."})
        fk_kapsam_kontrol(self, attrs, ("proje", "poz"))
        return attrs
class TedarikciSerializer(TenantAwareModelSerializer):
    class Meta:
        model = Tedarikci
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("cari",))
        return attrs


class MalzemeTedarikciIliskisiSerializer(TenantAwareModelSerializer):
    class Meta:
        model = MalzemeTedarikciIliskisi
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("malzeme", "tedarikci"))
        return attrs


class TedarikciTeklifiSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    proje_adi = serializers.CharField(source="proje.ad", read_only=True)
    malzeme_adi = serializers.CharField(source="malzeme.ad", read_only=True)
    malzeme_birimi = serializers.CharField(source="malzeme.birim", read_only=True)
    tedarikci_adi = serializers.CharField(source="tedarikci.firma_adi", read_only=True)

    class Meta:
        model = TedarikciTeklifi
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "toplam_tutar", "created_at", "updated_at",
            "proje_kodu", "proje_adi", "malzeme_adi", "malzeme_birimi", "tedarikci_adi",
        )

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje", "malzeme", "tedarikci"))
        miktar = attrs.get("miktar", getattr(self.instance, "miktar", None))
        fiyat = attrs.get("birim_fiyat", getattr(self.instance, "birim_fiyat", None))
        if miktar is not None and miktar <= 0:
            raise serializers.ValidationError({"miktar": "Miktar 0'dan büyük olmalıdır."})
        if fiyat is not None and fiyat <= 0:
            raise serializers.ValidationError({"birim_fiyat": "Birim fiyat 0'dan büyük olmalıdır."})
        return attrs


class TaseronSozlesiSerializer(TenantAwareModelSerializer):
    class Meta:
        model = TaseronSozlesi
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje",))
        baslangic = attrs.get("tarih_baslangic", getattr(self.instance, "tarih_baslangic", None))
        bitis = attrs.get("tarih_bitis", getattr(self.instance, "tarih_bitis", None))
        if bitis and baslangic and bitis < baslangic:
            raise serializers.ValidationError(
                {"tarih_bitis": "Bitiş tarihi başlangıç tarihinden önce olamaz."}
            )
        if "taseron_firma" in attrs and not attrs["taseron_firma"].strip():
            raise serializers.ValidationError({"taseron_firma": "Taşeron firma zorunludur."})
        return attrs


class KaliteKabulTeminatiSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    poz_no = serializers.CharField(source="poz.poz_no", read_only=True, default=None)

    class Meta:
        model = KaliteKabulTeminati
        fields = "__all__"
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "proje_kodu",
            "poz_no",
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje", "poz"))
        return attrs


class YfkPozVersiyonSerializer(TenantAwareModelSerializer):
    fiyatlar = serializers.SerializerMethodField()
    rayiclar = serializers.SerializerMethodField()
    analizler = serializers.SerializerMethodField()

    class Meta:
        model = YfkPozVersiyon
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at")

    def get_fiyatlar(self, obj):
        from .serializers import YfkFiyatSerializer
        fiyatlar = obj.fiyatlar.filter(is_active=True).order_by("-yil", "donem")
        return YfkFiyatSerializer(fiyatlar, many=True, context=self.context).data

    def get_rayiclar(self, obj):
        from .serializers import YfkRayicSerializer
        rayiclar = obj.rayiclar.filter(is_active=True).order_by("malzeme_tipi")
        return YfkRayicSerializer(rayiclar, many=True, context=self.context).data

    def get_analizler(self, obj):
        from .serializers import YfkAnalizSerializer
        analizler = obj.analizler.filter(is_active=True).order_by("malzeme_tipi", "sira_no")
        return YfkAnalizSerializer(analizler, many=True, context=self.context).data

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("onceki_versiyon",))
        return attrs


class YfkFiyatSerializer(TenantAwareModelSerializer):
    poz_no = serializers.CharField(source="poz_versiyon.poz_no", read_only=True)

    class Meta:
        model = YfkFiyat
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("poz_versiyon",))
        return attrs


class YfkRayicSerializer(TenantAwareModelSerializer):
    poz_no = serializers.CharField(source="poz_versiyon.poz_no", read_only=True)

    class Meta:
        model = YfkRayic
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("poz_versiyon",))
        return attrs


class YfkAnalizSerializer(TenantAwareModelSerializer):
    poz_no = serializers.CharField(source="poz_versiyon.poz_no", read_only=True)

    class Meta:
        model = YfkAnaliz
        fields = "__all__"
        read_only_fields = ("id", "tenant", "toplam_tutar", "created_at", "updated_at")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("poz_versiyon",))
        return attrs


class YfkGuncellemeGecmisiSerializer(TenantAwareModelSerializer):
    class Meta:
        model = YfkGuncellemeGecmisi
        fields = "__all__"
        read_only_fields = ("id", "tenant", "baslangic_zamani", "bitis_zamani")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("baslayan_kullanici",))
        return attrs


# =============================================================================
# FAZ 2 — Projeye Özel Malzeme Sistemi Serializer'ları
# =============================================================================

class ProjeMalzemeSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    malzeme_kodu = serializers.CharField(source="malzeme.malzeme_kodu", read_only=True)
    malzeme_adi = serializers.CharField(source="malzeme.ad", read_only=True)
    malzeme_birim = serializers.CharField(source="malzeme.birim", read_only=True)
    tedarikci_adi = serializers.CharField(source="tedarikci.firma_adi", read_only=True, default=None)
    cari_adi = serializers.CharField(source="cari.ad", read_only=True, default=None)
    selected_teklif_id = serializers.IntegerField(source="selected_teklif.id", read_only=True, default=None)
    selected_teklif_fiyat = serializers.DecimalField(source="selected_teklif.birim_fiyat", max_digits=14, decimal_places=2, read_only=True, default=None)
    etkin_fiyat = serializers.SerializerMethodField()
    etkin_fiyat_kaynak = serializers.SerializerMethodField()

    class Meta:
        model = ProjeMalzeme
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at",
                           "proje_kodu", "malzeme_kodu", "malzeme_adi", "malzeme_birim",
                           "tedarikci_adi", "cari_adi", "selected_teklif_id", "selected_teklif_fiyat",
                           "etkin_fiyat", "etkin_fiyat_kaynak")

    def get_etkin_fiyat(self, obj):
        from .services.malzeme_fiyat import malzeme_etkin_fiyati
        sonuc = malzeme_etkin_fiyati(obj.proje, obj.malzeme, obj.proje.yil if hasattr(obj.proje, 'yil') else 2026)
        return str(sonuc.fiyat) if sonuc.fiyat else None

    def get_etkin_fiyat_kaynak(self, obj):
        from .services.malzeme_fiyat import malzeme_etkin_fiyati
        sonuc = malzeme_etkin_fiyati(obj.proje, obj.malzeme, obj.proje.yil if hasattr(obj.proje, 'yil') else 2026)
        return sonuc.kaynak

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje", "malzeme", "tedarikci", "cari", "selected_teklif"))
        return attrs


class ProjeMalzemeFiyatSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    malzeme_kodu = serializers.CharField(source="malzeme.malzeme_kodu", read_only=True)
    malzeme_adi = serializers.CharField(source="malzeme.ad", read_only=True)
    malzeme_birim = serializers.CharField(source="malzeme.birim", read_only=True)

    class Meta:
        model = ProjeMalzemeFiyat
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at",
                           "proje_kodu", "malzeme_kodu", "malzeme_adi", "malzeme_birim")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje", "malzeme"))
        return attrs


class ProjePozMalzemeSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    poz_no = serializers.CharField(source="poz.poz_no", read_only=True)
    poz_adi = serializers.CharField(source="poz.ad", read_only=True)
    kaynak_malzeme_kodu = serializers.CharField(source="kaynak_malzeme.malzeme_kodu", read_only=True)
    kaynak_malzeme_adi = serializers.CharField(source="kaynak_malzeme.ad", read_only=True)
    kaynak_malzeme_birim = serializers.CharField(source="kaynak_malzeme.birim", read_only=True)
    etkin_malzeme_kodu = serializers.CharField(source="etkin_malzeme.malzeme_kodu", read_only=True)
    etkin_malzeme_adi = serializers.CharField(source="etkin_malzeme.ad", read_only=True)
    etkin_malzeme_birim = serializers.CharField(source="etkin_malzeme.birim", read_only=True)
    etkin_fiyat = serializers.SerializerMethodField()
    etkin_fiyat_kaynak = serializers.SerializerMethodField()

    class Meta:
        model = ProjePozMalzeme
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at",
                           "proje_kodu", "poz_no", "poz_adi",
                           "kaynak_malzeme_kodu", "kaynak_malzeme_adi", "kaynak_malzeme_birim",
                           "etkin_malzeme_kodu", "etkin_malzeme_adi", "etkin_malzeme_birim",
                           "etkin_fiyat", "etkin_fiyat_kaynak")

    def get_etkin_fiyat(self, obj):
        from .services.malzeme_fiyat import malzeme_etkin_fiyati
        sonuc = malzeme_etkin_fiyati(obj.proje, obj.etkin_malzeme, obj.proje.yil if hasattr(obj.proje, 'yil') else 2026)
        return str(sonuc.fiyat) if sonuc.fiyat else None

    def get_etkin_fiyat_kaynak(self, obj):
        from .services.malzeme_fiyat import malzeme_etkin_fiyati
        sonuc = malzeme_etkin_fiyati(obj.proje, obj.etkin_malzeme, obj.proje.yil if hasattr(obj.proje, 'yil') else 2026)
        return sonuc.kaynak

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("proje", "poz", "kaynak_malzeme", "etkin_malzeme"))
        # Kaynak ve etkin malzeme aynı olamaz
        kaynak = attrs.get("kaynak_malzeme", getattr(self.instance, "kaynak_malzeme", None))
        etkin = attrs.get("etkin_malzeme", getattr(self.instance, "etkin_malzeme", None))
        if kaynak and etkin and kaynak.id == etkin.id:
            raise serializers.ValidationError({"etkin_malzeme": "Kaynak malzeme ve etkin malzeme aynı olamaz."})
        return attrs


class MalzemeFiyatSerializer(TenantAwareModelSerializer):
    malzeme_kodu = serializers.CharField(source="malzeme.malzeme_kodu", read_only=True)
    malzeme_adi = serializers.CharField(source="malzeme.ad", read_only=True)
    malzeme_birim = serializers.CharField(source="malzeme.birim", read_only=True)

    class Meta:
        model = MalzemeFiyat
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at",
                           "malzeme_kodu", "malzeme_adi", "malzeme_birim")

    def validate(self, attrs):
        fk_kapsam_kontrol(self, attrs, ("malzeme",))
        return attrs