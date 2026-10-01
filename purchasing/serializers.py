"""FAZ 3A serializer'ları — TenantAwareModelSerializer + tenant FK doğrulama.

Desen: construction TedarikciTeklifiSerializer (source read-only alanlar,
tenant kapsam kontrolü, miktar/fiyat validasyonu).
"""

from rest_framework import serializers

from decimal import Decimal

from tenants.serializers import TenantAwareModelSerializer

from .models import (
    Depo,
    MalKabul,
    MalKabulKalemi,
    SatinAlmaSiparisi,
    SatinAlmaSiparisiKalemi,
    SatinAlmaTalebi,
    SatinAlmaTalebiKalemi,
    StokHareketi,
    StokHesapEsleme,
)


def _kapsam_id(request):
    user = getattr(request, "user", None)
    return getattr(user, "tenant_id", None)


def _kapsam_kontrol(serializer, attrs, alanlar):
    request = serializer.context.get("request")
    tenant_id = _kapsam_id(request)
    for alan in alanlar:
        nesne = attrs.get(alan, getattr(serializer.instance, alan, None))
        if nesne is not None and tenant_id and nesne.tenant_id != tenant_id:
            raise serializers.ValidationError(
                {alan: "Seçilen kayıt bu firma kapsamına ait değil."}
            )


class SatinAlmaTalebiKalemiSerializer(TenantAwareModelSerializer):
    malzeme_adi = serializers.CharField(source="malzeme.ad", read_only=True)
    malzeme_kodu = serializers.CharField(source="malzeme.malzeme_kodu", read_only=True)
    poz_no = serializers.CharField(source="poz.poz_no", read_only=True, default=None)
    mahal_kodu = serializers.CharField(source="mahal.kod", read_only=True, default=None)

    class Meta:
        model = SatinAlmaTalebiKalemi
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "created_at", "updated_at",
            "malzeme_adi", "malzeme_kodu", "poz_no", "mahal_kodu",
        )

    def validate(self, attrs):
        _kapsam_kontrol(self, attrs, ("malzeme", "poz", "mahal", "secili_teklif"))
        miktar = attrs.get("miktar", getattr(self.instance, "miktar", None))
        if miktar is not None and miktar <= 0:
            raise serializers.ValidationError({"miktar": "Miktar 0'dan büyük olmalıdır."})
        fiyat = attrs.get("tahmini_birim_fiyat", getattr(self.instance, "tahmini_birim_fiyat", None))
        if fiyat is not None and fiyat <= 0:
            raise serializers.ValidationError(
                {"tahmini_birim_fiyat": "Tahmini birim fiyat 0'dan büyük olmalıdır."}
            )
        talep = attrs.get("talep", getattr(self.instance, "talep", None))
        if talep is not None and getattr(talep, "durum", None) not in (
            None,
            SatinAlmaTalebi.Durum.TASLAK,
        ):
            raise serializers.ValidationError(
                {"talep": "Yalnızca taslak talebe kalem eklenebilir/değiştirilebilir."}
            )
        return attrs


class SatinAlmaTalebiSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    proje_adi = serializers.CharField(source="proje.ad", read_only=True)
    talep_sahibi_adi = serializers.CharField(source="talep_sahibi.username", read_only=True)
    kalemler = SatinAlmaTalebiKalemiSerializer(many=True, read_only=True)

    class Meta:
        model = SatinAlmaTalebi
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "talep_no", "talep_sahibi", "durum",
            "created_at", "updated_at",
            "proje_kodu", "proje_adi", "talep_sahibi_adi", "kalemler",
        )

    def validate(self, attrs):
        _kapsam_kontrol(self, attrs, ("proje",))
        return attrs


class SatinAlmaSiparisiKalemiSerializer(TenantAwareModelSerializer):
    malzeme_adi = serializers.CharField(source="malzeme.ad", read_only=True)
    malzeme_kodu = serializers.CharField(source="malzeme.malzeme_kodu", read_only=True)
    poz_no = serializers.CharField(source="poz.poz_no", read_only=True, default=None)
    mahal_kodu = serializers.CharField(source="mahal.kod", read_only=True, default=None)

    class Meta:
        model = SatinAlmaSiparisiKalemi
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "toplam_tutar", "created_at", "updated_at",
            "malzeme_adi", "malzeme_kodu", "poz_no", "mahal_kodu",
        )

    def validate(self, attrs):
        _kapsam_kontrol(self, attrs, ("malzeme", "poz", "mahal", "kaynak_teklif"))
        miktar = attrs.get("miktar", getattr(self.instance, "miktar", None))
        if miktar is not None and miktar <= 0:
            raise serializers.ValidationError({"miktar": "Miktar 0'dan büyük olmalıdır."})
        fiyat = attrs.get("birim_fiyat", getattr(self.instance, "birim_fiyat", None))
        if fiyat is not None and fiyat <= 0:
            raise serializers.ValidationError({"birim_fiyat": "Birim fiyat 0'dan büyük olmalıdır."})
        siparis = attrs.get("siparis", getattr(self.instance, "siparis", None))
        if siparis is not None and getattr(siparis, "durum", None) not in (
            None,
            SatinAlmaSiparisi.Durum.TASLAK,
        ):
            raise serializers.ValidationError(
                {"siparis": "Yalnızca taslak siparişe kalem eklenebilir/değiştirilebilir."}
            )
        return attrs


class SatinAlmaSiparisiSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    proje_adi = serializers.CharField(source="proje.ad", read_only=True)
    tedarikci_adi = serializers.CharField(source="tedarikci.firma_adi", read_only=True)
    kalemler = SatinAlmaSiparisiKalemiSerializer(many=True, read_only=True)

    class Meta:
        model = SatinAlmaSiparisi
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "siparis_no", "durum",
            "created_at", "updated_at",
            "proje_kodu", "proje_adi", "tedarikci_adi", "kalemler",
        )

    def validate(self, attrs):
        _kapsam_kontrol(self, attrs, ("proje", "tedarikci", "kaynak_talep"))
        return attrs


class DepoSerializer(TenantAwareModelSerializer):
    class Meta:
        model = Depo
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at")


class MalKabulKalemiSerializer(TenantAwareModelSerializer):
    malzeme_adi = serializers.CharField(source="malzeme.ad", read_only=True)
    malzeme_kodu = serializers.CharField(source="malzeme.malzeme_kodu", read_only=True)

    class Meta:
        model = MalKabulKalemi
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "siparis_miktari", "birim_fiyat_snapshot",
            "created_at", "updated_at", "malzeme_adi", "malzeme_kodu",
        )

    def validate(self, attrs):
        _kapsam_kontrol(self, attrs, ("malzeme",))
        for alan in ("kabul_miktari", "red_miktari"):
            deger = attrs.get(alan, getattr(self.instance, alan, None))
            if deger is not None and deger < 0:
                raise serializers.ValidationError({alan: "Miktar negatif olamaz."})
        oran = attrs.get("kdv_orani", getattr(self.instance, "kdv_orani", None))
        if oran is not None and not Decimal("0") <= oran <= Decimal("100"):
            raise serializers.ValidationError({"kdv_orani": "KDV oranı 0-100 arasında olmalıdır."})
        return attrs

    def create(self, validated_data):
        # Snapshot alanları read-only'dir; sipariş kaleminden otomatik dolar.
        kalem = validated_data.get("siparis_kalemi")
        if kalem:
            validated_data.setdefault("siparis_miktari", kalem.miktar)
            validated_data.setdefault("birim", kalem.birim)
            validated_data.setdefault("birim_fiyat_snapshot", kalem.birim_fiyat)
        return super().create(validated_data)


class MalKabulSerializer(TenantAwareModelSerializer):
    proje_kodu = serializers.CharField(source="proje.proje_kodu", read_only=True)
    depo_kodu = serializers.CharField(source="depo.kod", read_only=True)
    kalemler = MalKabulKalemiSerializer(many=True, read_only=True)
    muhasebe = serializers.SerializerMethodField()

    class Meta:
        model = MalKabul
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "belge_no", "durum", "created_by", "updated_by",
            "created_at", "updated_at", "proje_kodu", "depo_kodu", "kalemler",
            "muhasebe",
        )

    def validate(self, attrs):
        _kapsam_kontrol(self, attrs, ("siparis", "proje", "depo"))
        return attrs

    def get_muhasebe(self, obj) -> dict:
        from finance.services.satin_alma_muhasebe import _muhasebe_ozeti

        return _muhasebe_ozeti(obj.pk, tenant_id=obj.tenant_id)


class StokHareketiSerializer(TenantAwareModelSerializer):
    malzeme_adi = serializers.CharField(source="malzeme.ad", read_only=True)
    depo_kodu = serializers.CharField(source="depo.kod", read_only=True)

    class Meta:
        model = StokHareketi
        fields = "__all__"
        read_only_fields = (
            "id", "tenant", "created_by", "created_at", "updated_at",
            "malzeme_adi", "depo_kodu",
        )


class StokHesapEslemeSerializer(TenantAwareModelSerializer):
    """FAZ 7R — stok/KDV hesap eşlemesi (malzeme boşsa tenant varsayılanı)."""

    malzeme_kodu = serializers.SerializerMethodField()
    malzeme_adi = serializers.SerializerMethodField()
    hesap_kodu = serializers.SerializerMethodField()
    hesap_adi = serializers.SerializerMethodField()

    class Meta:
        model = StokHesapEsleme
        fields = "__all__"
        read_only_fields = (
            "id", "created_at", "updated_at",
            "malzeme_kodu", "malzeme_adi", "hesap_kodu", "hesap_adi",
        )

    def get_malzeme_kodu(self, obj):
        return obj.malzeme.malzeme_kodu if obj.malzeme_id else None

    def get_malzeme_adi(self, obj):
        return obj.malzeme.ad if obj.malzeme_id else None

    def get_hesap_kodu(self, obj):
        return obj.hesap.kod

    def get_hesap_adi(self, obj):
        return obj.hesap.ad

    def validate(self, attrs):
        _kapsam_kontrol(self, attrs, ("malzeme", "hesap"))
        # Kısmi unique constraint'ler DRF UniqueValidator'a takılmaz (500 olur);
        # kullanıcı girdisini 400 ile karşıla (model değişikliği yok).
        from .models import StokHesapEsleme

        tenant_id = _kapsam_id(self.context.get("request"))
        tur = attrs.get("hesap_turu", getattr(self.instance, "hesap_turu", None))
        malzeme = attrs.get("malzeme", getattr(self.instance, "malzeme", None))
        if tenant_id and tur:
            sorgu = StokHesapEsleme.objects.filter(tenant_id=tenant_id, hesap_turu=tur)
            if malzeme is None:
                sorgu = sorgu.filter(malzeme__isnull=True)
            else:
                sorgu = sorgu.filter(malzeme=malzeme)
            if self.instance is not None:
                sorgu = sorgu.exclude(pk=self.instance.pk)
            if sorgu.exists():
                raise serializers.ValidationError(
                    "Bu kapsamda aynı türde eşleme zaten tanımlı."
                )
        return attrs



