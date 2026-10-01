"""FAZ 3A ViewSet'leri — TenantScopedViewSet + IsPurchasingEditor.

Desen: construction TedarikciTeklifiViewSet (destroy→arşiv) ve HakedisViewSet
(destroy→iptal, onayla action + DjangoValidationError çevrimi).
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tenants.api import TenantScopedViewSet

from .models import (
    Depo,
    MalKabul,
    MalKabulKalemi,
    SatinAlmaSiparisi,
    StokHareketi,
    SatinAlmaSiparisiKalemi,
    SatinAlmaTalebi,
    SatinAlmaTalebiKalemi,
    StokHesapEsleme,
)
from .permissions import IsPurchasingEditor
from .serializers import (
    DepoSerializer,
    MalKabulKalemiSerializer,
    MalKabulSerializer,
    SatinAlmaSiparisiKalemiSerializer,
    SatinAlmaSiparisiSerializer,
    SatinAlmaTalebiKalemiSerializer,
    SatinAlmaTalebiSerializer,
    StokHareketiSerializer,
    StokHesapEslemeSerializer,
)
from .services import (
    belge_numarasi_uret,
    depo_bakiyeleri,
    mal_kabul_durum_gecis,
    mal_kabul_olustur,
    siparis_durum_gecis,
    stok_bakiye,
    stok_iade,
    stok_transfer,
    stok_tuketim,
    talep_durum_gecis,
    talepten_siparis_olustur,
)

PERMISSIONS = [IsAuthenticated, IsPurchasingEditor]


def _servis_hatasi(exc: DjangoValidationError):
    raise ValidationError({"detail": str(exc)})


def _anahtari_basarisiz_yap(
    tenant_id: int, operation: str, key: str, payload: dict
) -> None:
    """Çöken denemenin anahtarını FAILED'a çeker (yeniden deneme açılsın).

    Not: başarısız denemenin kendi transaction'ı geri alınır; bu yüzden kayıt
    burada taze transaction içinde get_or_create ile bulunur/oluşturulur.
    Digest gerçek payload'dan yazılır ki retry hash kontrolünden geçsin.
    """
    from finance.models import IdempotencyKey
    from finance.services.idempotency import request_hash

    try:
        with transaction.atomic():
            kayit, _ = IdempotencyKey.objects.select_for_update().get_or_create(
                tenant_id=tenant_id, operation=operation, key=key,
                defaults={"request_hash": request_hash(payload)},
            )
            if kayit.status == IdempotencyKey.Durum.PROCESSING:
                kayit.status = IdempotencyKey.Durum.FAILED
                kayit.save(update_fields=["status"])
    except Exception:  # noqa: BLE001 — kurtarma başarısızsa asıl hata yükseliyor
        pass


def _idempotent_post(request, *, tenant_id: int, operation: str, payload: dict,
                     kaynak_turu: str = "", kaynak_id: int | None = None,
                     islem) -> Response:
    """Opsiyonel Idempotency-Key sarmalı (anahtar yoksa doğrudan çalışır)."""
    from finance.services.idempotency import (
        IdempotencyConflict,
        complete_operation,
        idempotent_operation,
    )

    key = request.headers.get("Idempotency-Key")
    if not key:
        return islem()
    try:
        with idempotent_operation(
            tenant_id=tenant_id, operation=operation, key=key, payload=payload
        ) as kayit:
            if kayit.status == kayit.Durum.COMPLETED:
                return Response(kayit.response_data)
            yanit = islem()
            complete_operation(
                kayit, response_data=yanit.data,
                resource_type=kaynak_turu, resource_id=kaynak_id,
            )
            return yanit
    except IdempotencyConflict as exc:
        raise ValidationError({"Idempotency-Key": str(exc)}) from exc
    except Exception:
        import logging

        logging.getLogger("erp.idempotency").warning(
            "event=failed_retry operation=%s", operation,
            extra={"tenant_id": tenant_id, "operation": operation,
                   "resource_id": kaynak_id if kaynak_id is not None else "-"},
        )
        _anahtari_basarisiz_yap(tenant_id, operation, key, payload)
        raise


class SatinAlmaTalebiViewSet(TenantScopedViewSet):
    """Satın alma talepleri — taslak → onaya gönderildi → onaylandı/reddedildi
    → siparişe dönüştü / iptal. Fiziksel DELETE kapalı."""

    queryset = SatinAlmaTalebi.objects.select_related(
        "tenant", "proje", "talep_sahibi"
    ).prefetch_related("kalemler").all()
    serializer_class = SatinAlmaTalebiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("talep_no", "proje__proje_kodu", "proje__ad", "aciklama")
    filterset_fields = ("proje", "durum", "is_active")

    def perform_create(self, serializer):
        from .models import BelgeTipi
        from .services import belge_numarasi_uret

        tenant_id = self.request.user.tenant_id
        serializer.save(
            tenant_id=tenant_id,
            talep_no=belge_numarasi_uret(tenant_id, BelgeTipi.TALEP),
            talep_sahibi=self.request.user,
        )

    def destroy(self, request, *args, **kwargs):
        """Fiziksel silme yok: uygun durumdaki talep iptale çekilir."""
        talep = self.get_object()
        if talep.durum in (SatinAlmaTalebi.Durum.SIPARISE_DONUSTU, SatinAlmaTalebi.Durum.IPTAL):
            raise ValidationError({"detail": "Siparişe dönüşmüş/iptal talep silinemez."})
        try:
            talep = talep_durum_gecis(
                talep.pk, SatinAlmaTalebi.Durum.IPTAL, tenant_id=talep.tenant_id
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(self.get_serializer(talep).data)

    @action(detail=True, methods=["post"], url_path="onaya-gonder")
    def onaya_gonder(self, request, pk=None):
        talep = self.get_object()
        try:
            talep = talep_durum_gecis(
                talep.pk,
                SatinAlmaTalebi.Durum.ONAYA_GONDERILDI,
                tenant_id=talep.tenant_id,
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(self.get_serializer(talep).data)

    @action(detail=True, methods=["post"], url_path="onayla")
    def onayla(self, request, pk=None):
        talep = self.get_object()
        try:
            talep = talep_durum_gecis(
                talep.pk, SatinAlmaTalebi.Durum.ONAYLANDI, tenant_id=talep.tenant_id
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(self.get_serializer(talep).data)

    @action(detail=True, methods=["post"], url_path="reddet")
    def reddet(self, request, pk=None):
        talep = self.get_object()
        try:
            talep = talep_durum_gecis(
                talep.pk, SatinAlmaTalebi.Durum.REDDEDILDI, tenant_id=talep.tenant_id
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(self.get_serializer(talep).data)

    @action(detail=True, methods=["post"], url_path="iptal-et")
    def iptal_et(self, request, pk=None):
        talep = self.get_object()
        try:
            talep = talep_durum_gecis(
                talep.pk, SatinAlmaTalebi.Durum.IPTAL, tenant_id=talep.tenant_id
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(self.get_serializer(talep).data)

    @action(detail=True, methods=["post"], url_path="talepten-siparis-olustur")
    def talepten_siparis_olustur(self, request, pk=None):
        """Onaylı talebi siparişe dönüştürür (atomic, tek seferlik)."""
        talep = self.get_object()
        try:
            siparis = talepten_siparis_olustur(
                talep.pk,
                tenant_id=talep.tenant_id,
                tedarikci_id=request.data.get("tedarikci"),
                para_birimi=request.data.get("para_birimi", "TRY"),
                kur=request.data.get("kur", "1"),
                teslim_tarihi=request.data.get("teslim_tarihi"),
                aciklama=request.data.get("aciklama", ""),
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(SatinAlmaSiparisiSerializer(siparis, context={"request": request}).data)


class SatinAlmaTalebiKalemiViewSet(TenantScopedViewSet):
    """Talep kalemleri — yalnızca taslak talebe yazılır."""

    queryset = SatinAlmaTalebiKalemi.objects.select_related(
        "tenant", "talep", "malzeme", "poz", "mahal", "secili_teklif"
    ).all()
    serializer_class = SatinAlmaTalebiKalemiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("malzeme__ad", "malzeme__malzeme_kodu", "aciklama")
    filterset_fields = ("talep", "malzeme", "is_active")

    def destroy(self, request, *args, **kwargs):
        kalem = self.get_object()
        if kalem.talep.durum != SatinAlmaTalebi.Durum.TASLAK:
            raise ValidationError({"detail": "Yalnızca taslak talebin kalemi arşivlenebilir."})
        kalem.is_active = False
        kalem.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(kalem).data)


class SatinAlmaSiparisiViewSet(TenantScopedViewSet):
    """Satın alma siparişleri — taslak → onay bekliyor → onaylandı →
    kısmi teslim / tamamlandı / iptal. Fiziksel DELETE kapalı."""

    queryset = SatinAlmaSiparisi.objects.select_related(
        "tenant", "proje", "tedarikci", "kaynak_talep"
    ).prefetch_related("kalemler").all()
    serializer_class = SatinAlmaSiparisiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("siparis_no", "proje__proje_kodu", "tedarikci__firma_adi", "aciklama")
    filterset_fields = ("proje", "tedarikci", "durum", "is_active")

    def perform_create(self, serializer):
        from .models import BelgeTipi
        from .services import belge_numarasi_uret

        tenant_id = self.request.user.tenant_id
        serializer.save(
            tenant_id=tenant_id,
            siparis_no=belge_numarasi_uret(tenant_id, BelgeTipi.SIPARIS),
        )

    def destroy(self, request, *args, **kwargs):
        """Fiziksel silme yok: uygun durumdaki sipariş iptale çekilir."""
        siparis = self.get_object()
        if siparis.durum in (SatinAlmaSiparisi.Durum.TAMAMLANDI, SatinAlmaSiparisi.Durum.IPTAL):
            raise ValidationError({"detail": "Tamamlanmış/iptal sipariş silinemez."})
        try:
            siparis = siparis_durum_gecis(
                siparis.pk, SatinAlmaSiparisi.Durum.IPTAL, tenant_id=siparis.tenant_id
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(self.get_serializer(siparis).data)

    @action(detail=True, methods=["post"], url_path="onaya-gonder")
    def onaya_gonder(self, request, pk=None):
        siparis = self.get_object()
        try:
            siparis = siparis_durum_gecis(
                siparis.pk,
                SatinAlmaSiparisi.Durum.ONAY_BEKLIYOR,
                tenant_id=siparis.tenant_id,
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(self.get_serializer(siparis).data)

    @action(detail=True, methods=["post"], url_path="onayla")
    def onayla(self, request, pk=None):
        siparis = self.get_object()
        try:
            siparis = siparis_durum_gecis(
                siparis.pk, SatinAlmaSiparisi.Durum.ONAYLANDI, tenant_id=siparis.tenant_id
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(self.get_serializer(siparis).data)

    @action(detail=True, methods=["post"], url_path="iptal-et")
    def iptal_et(self, request, pk=None):
        siparis = self.get_object()
        try:
            siparis = siparis_durum_gecis(
                siparis.pk, SatinAlmaSiparisi.Durum.IPTAL, tenant_id=siparis.tenant_id
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(self.get_serializer(siparis).data)


class SatinAlmaSiparisiKalemiViewSet(TenantScopedViewSet):
    """Sipariş kalemleri — yalnızca taslak siparişe yazılır; birim_fiyat sabittir."""

    queryset = SatinAlmaSiparisiKalemi.objects.select_related(
        "tenant", "siparis", "malzeme", "poz", "mahal", "kaynak_teklif"
    ).all()
    serializer_class = SatinAlmaSiparisiKalemiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("malzeme__ad", "malzeme__malzeme_kodu", "aciklama")
    filterset_fields = ("siparis", "malzeme", "is_active")

    def destroy(self, request, *args, **kwargs):
        kalem = self.get_object()
        if kalem.siparis.durum != SatinAlmaSiparisi.Durum.TASLAK:
            raise ValidationError({"detail": "Yalnızca taslak siparişin kalemi arşivlenebilir."})
        kalem.is_active = False
        kalem.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(kalem).data)


class DepoViewSet(TenantScopedViewSet):
    """Depo kartları."""

    queryset = Depo.objects.all()
    serializer_class = DepoSerializer
    permission_classes = PERMISSIONS
    search_fields = ("kod", "ad")
    filterset_fields = ("is_active",)


class MalKabulViewSet(TenantScopedViewSet):
    """Mal kabul belgeleri — taslak → onaylandı/kısmi teslim/tamamlandı/iptal.

    Onayda GİRİŞ stok hareketleri üretilir; iptalde ters hareket açılır.
    Fiziksel DELETE kapalı.
    """

    queryset = MalKabul.objects.select_related(
        "tenant", "siparis", "proje", "depo", "created_by"
    ).prefetch_related("kalemler").all()
    serializer_class = MalKabulSerializer
    permission_classes = PERMISSIONS
    search_fields = ("belge_no", "proje__proje_kodu", "aciklama")
    filterset_fields = ("siparis", "proje", "depo", "durum", "is_active")

    def perform_create(self, serializer):
        from .models import BelgeTipi

        tenant_id = self.request.user.tenant_id
        serializer.save(
            tenant_id=tenant_id,
            belge_no=belge_numarasi_uret(tenant_id, BelgeTipi.MAL_KABUL),
            created_by=self.request.user,
        )

    def destroy(self, request, *args, **kwargs):
        """Fiziksel silme yok: taslak kabul iptale çekilir."""
        mal_kabul = self.get_object()
        if mal_kabul.durum != MalKabul.Durum.TASLAK:
            raise ValidationError({"detail": "Yalnızca taslak mal kabul iptal edilebilir."})
        try:
            mal_kabul = mal_kabul_durum_gecis(
                mal_kabul.pk, MalKabul.Durum.IPTAL, tenant_id=mal_kabul.tenant_id
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(self.get_serializer(mal_kabul).data)

    @action(detail=True, methods=["post"], url_path="onayla")
    def onayla(self, request, pk=None):
        mal_kabul = self.get_object()
        return _idempotent_post(
            request,
            tenant_id=mal_kabul.tenant_id,
            operation="mal-kabul.onayla",
            payload={"mal_kabul_id": mal_kabul.pk},
            kaynak_turu="purchasing.MalKabul",
            kaynak_id=mal_kabul.pk,
            islem=lambda: self._onayla_ve_zarf(mal_kabul, request),
        )

    @action(detail=True, methods=["post"], url_path="muhasebelestir")
    def muhasebelestir(self, request, pk=None):
        """Onaylı ama muhasebesiz kabulü sonradan muhasebeleştir (retry).

        Cari sonradan bağlanmış kabuller için eksik fatura/cari/fişi üretir.
        Idempotent: kayıtlar deterministik anahtarlarla bulunur/oluşturulur.
        """
        from finance.services.satin_alma_muhasebe import satin_alma_muhasebe_olustur

        kabul = self.get_object()
        if kabul.durum != MalKabul.Durum.ONAYLANDI:
            raise ValidationError({"detail": "Yalnızca onaylı kabul muhasebeleştirilebilir."})
        try:
            satin_alma_muhasebe_olustur(kabul.pk, tenant_id=kabul.tenant_id)
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        kabul.refresh_from_db()
        return Response(self.get_serializer(kabul).data)

    def _onayla_ve_zarf(self, mal_kabul, request):
        from finance.services.satin_alma_muhasebe import _muhasebe_ozeti

        try:
            mal_kabul = mal_kabul_durum_gecis(
                mal_kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=mal_kabul.tenant_id
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        veri = self.get_serializer(mal_kabul).data
        veri["muhasebe"] = _muhasebe_ozeti(mal_kabul.pk, tenant_id=mal_kabul.tenant_id)
        return Response(veri)

    @action(detail=True, methods=["post"], url_path="iptal-et")
    def iptal_et(self, request, pk=None):
        mal_kabul = self.get_object()
        try:
            mal_kabul = mal_kabul_durum_gecis(
                mal_kabul.pk, MalKabul.Durum.IPTAL, tenant_id=mal_kabul.tenant_id
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        return Response(self.get_serializer(mal_kabul).data)


class MalKabulKalemiViewSet(TenantScopedViewSet):
    """Mal kabul kalemleri — yalnızca taslak kabule yazılır."""

    queryset = MalKabulKalemi.objects.select_related(
        "tenant", "mal_kabul", "siparis_kalemi", "malzeme"
    ).all()
    serializer_class = MalKabulKalemiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("malzeme__ad", "malzeme__malzeme_kodu", "aciklama")
    filterset_fields = ("mal_kabul", "malzeme", "is_active")

    def destroy(self, request, *args, **kwargs):
        kalem = self.get_object()
        if kalem.mal_kabul.durum != MalKabul.Durum.TASLAK:
            raise ValidationError({"detail": "Yalnızca taslak kabulün kalemi arşivlenebilir."})
        kalem.is_active = False
        kalem.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(kalem).data)


class StokHareketiViewSet(TenantScopedViewSet):
    """Stok hareketleri — salt okunur liste; kayıtlar mal kabul onayıyla üretilir.

    Doğrudan yazma/silme kapalı (hareket bütünlüğü servis katmanında korunur).
    """

    queryset = StokHareketi.objects.select_related(
        "tenant", "depo", "malzeme", "proje"
    ).all()
    serializer_class = StokHareketiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("malzeme__ad", "malzeme__malzeme_kodu", "depo__kod", "aciklama")
    filterset_fields = ("depo", "malzeme", "proje", "hareket_tipi", "is_active")

    def create(self, request, *args, **kwargs):
        raise ValidationError(
            {"detail": "Stok hareketleri doğrudan oluşturulamaz; mal kabul onayıyla üretilir."}
        )

    def update(self, request, *args, **kwargs):
        raise ValidationError({"detail": "Stok hareketleri değiştirilemez."})

    def partial_update(self, request, *args, **kwargs):
        raise ValidationError({"detail": "Stok hareketleri değiştirilemez."})

    def destroy(self, request, *args, **kwargs):
        raise ValidationError(
            {"detail": "Stok hareketleri silinemez; ters hareket kaydı açınız."}
        )

    @action(detail=False, methods=["get"], url_path="stok-bakiye")
    def stok_bakiye(self, request):
        """Depo bakiyesi: ?depo=<id>[&malzeme=<id>] — malzeme yoksa tüm depo özeti."""
        from tenants.api import etkin_tenant_id

        tenant_id = etkin_tenant_id(request) or getattr(request.user, "tenant_id", None)
        depo_id = request.query_params.get("depo")
        if not depo_id:
            raise ValidationError({"depo": "Depo parametresi zorunludur."})
        malzeme_id = request.query_params.get("malzeme")
        try:
            if malzeme_id:
                bakiye = stok_bakiye(
                    tenant_id=tenant_id, depo_id=int(depo_id), malzeme_id=int(malzeme_id)
                )
                return Response({"depo": int(depo_id), "malzeme": int(malzeme_id), "bakiye": str(bakiye)})
            return Response(
                {
                    "depo": int(depo_id),
                    "kalemler": depo_bakiyeleri(tenant_id=tenant_id, depo_id=int(depo_id)),
                }
            )
        except DjangoValidationError as exc:
            _servis_hatasi(exc)
        except (TypeError, ValueError):
            raise ValidationError({"depo": "Geçersiz depo/malzeme parametresi."})

    @action(detail=False, methods=["post"], url_path="transfer-olustur")
    def transfer_olustur(self, request, pk=None):
        """Depolar arası transfer (atomik ÇIKIŞ+GİRİŞ)."""
        def _islem():
            try:
                cikis, giris = stok_transfer(
                    tenant_id=request.user.tenant_id,
                    kaynak_depo_id=request.data.get("kaynak_depo"),
                    hedef_depo_id=request.data.get("hedef_depo"),
                    malzeme_id=request.data.get("malzeme"),
                    miktar=request.data.get("miktar"),
                    aciklama=request.data.get("aciklama", ""),
                    created_by_id=request.user.pk,
                )
            except DjangoValidationError as exc:
                _servis_hatasi(exc)
            return Response(
                {
                    "cikis": self.get_serializer(cikis).data,
                    "giris": self.get_serializer(giris).data,
                }
            )

        return _idempotent_post(
            request,
            tenant_id=request.user.tenant_id,
            operation="stok.transfer-olustur",
            payload=dict(request.data),
            islem=_islem,
        )

    @action(detail=False, methods=["post"], url_path="tuketim-olustur")
    def tuketim_olustur(self, request, pk=None):
        """Projeye/mahale tüketim (proje+mahal zorunlu ÇIKIŞ)."""
        def _islem():
            try:
                hareket = stok_tuketim(
                    tenant_id=request.user.tenant_id,
                    depo_id=request.data.get("depo"),
                    malzeme_id=request.data.get("malzeme"),
                    miktar=request.data.get("miktar"),
                    proje_id=request.data.get("proje"),
                    mahal_id=request.data.get("mahal"),
                    aciklama=request.data.get("aciklama", ""),
                    created_by_id=request.user.pk,
                )
            except DjangoValidationError as exc:
                _servis_hatasi(exc)
            return Response(self.get_serializer(hareket).data)

        return _idempotent_post(
            request,
            tenant_id=request.user.tenant_id,
            operation="stok.tuketim-olustur",
            payload=dict(request.data),
            islem=_islem,
        )

    @action(detail=False, methods=["post"], url_path="iade-olustur")
    def iade_olustur(self, request, pk=None):
        """Tedarikçiye iade: stok ÇIKIŞ + iade faturası tek transaction'da."""
        from finance.services.satin_alma_muhasebe import stok_iade_muhasebelestir

        def _islem():
            try:
                with transaction.atomic():
                    hareket = stok_iade(
                        tenant_id=request.user.tenant_id,
                        mal_kabul_kalemi_id=request.data.get("mal_kabul_kalemi"),
                        miktar=request.data.get("miktar"),
                        aciklama=request.data.get("aciklama", ""),
                        created_by_id=request.user.pk,
                    )
                    muhasebe = stok_iade_muhasebelestir(
                        hareket.pk, tenant_id=request.user.tenant_id
                    )
            except DjangoValidationError as exc:
                _servis_hatasi(exc)
            veri = self.get_serializer(hareket).data
            veri["iade_fatura_no"] = muhasebe["fatura"].No
            veri["iade_fis_no"] = muhasebe["fis"].fis_no
            return Response(veri)

        return _idempotent_post(
            request,
            tenant_id=request.user.tenant_id,
            operation="stok.iade-olustur",
            payload=dict(request.data),
            islem=_islem,
        )


class StokHesapEslemeViewSet(TenantScopedViewSet):
    """FAZ 7R — malzeme bazında stok/KDV hesap eşlemesi (salt yapılandırma).

    Malzeme boşsa tenant varsayılanıdır (uniq kısmi constraint'ler modelde).
    """

    queryset = StokHesapEsleme.objects.select_related(
        "tenant", "malzeme", "hesap"
    ).all()
    serializer_class = StokHesapEslemeSerializer
    permission_classes = PERMISSIONS
    search_fields = ("hesap__kod", "hesap__ad", "malzeme__malzeme_kodu", "malzeme__ad")
    filterset_fields = ("hesap_turu", "malzeme", "hesap", "is_active")



