"""Finans API view'ları (tenant izole, fiziksel DELETE yok)."""

from collections import defaultdict
from decimal import Decimal

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tenants.api import TenantScopedViewSet, etkin_tenant_id, tenant_kapsamli_queryset

from .models import CekSenet, FinansalIslem, KasaBankaHesabi, Fatura, VergiProfili, Rapor, Ayar
from .permissions import IsFinansEditor
from .serializers import CekSenetSerializer, FaturaSerializer, FinansalIslemSerializer, KasaBankaHesabiSerializer, VergiProfiliSerializer, RaporSerializer, AyarSerializer
from .services.fatura_hesaplama import fatura_toplam_hesapla
from .services.idempotency import (
    IdempotencyConflict,
    complete_operation,
    idempotent_operation,
)
from .services.state_machine import fatura_durum_gecis
from .services.shadow_posting import fatura_shadow_muhasebelestir


class KasaBankaHesabiViewSet(TenantScopedViewSet):
    queryset = KasaBankaHesabi.objects.all()
    serializer_class = KasaBankaHesabiSerializer
    permission_classes = [IsAuthenticated, IsFinansEditor]
    search_fields = ("kod", "ad")
    filterset_fields = ("tip", "para_birimi", "is_active")


class FinansalIslemViewSet(TenantScopedViewSet):
    """Finansal işlem — destroy yerine iptal (is_cancelled)."""

    queryset = FinansalIslem.objects.select_related("hesap", "cari").all()
    serializer_class = FinansalIslemSerializer
    permission_classes = [IsAuthenticated, IsFinansEditor]
    search_fields = ("hesap__kod", "aciklama", "cari__ad")
    filterset_fields = ("hesap", "cari", "yon", "is_cancelled")

    def perform_create(self, serializer):
        import logging

        super().perform_create(serializer)
        islem = serializer.instance
        logging.getLogger("erp.finans").info(
            "event=odeme hesap=%s tutar=%s", islem.hesap_id, islem.tutar,
            extra={"tenant_id": islem.tenant_id, "operation": "finansal-islem.ac",
                   "resource_id": islem.pk},
        )

    def destroy(self, request, *args, **kwargs):
        raise ValidationError({"detail": "Finansal işlem silinemez; iptal endpoint'ini kullanın."})

    @action(detail=True, methods=["post"], url_path="iptal")
    def iptal(self, request, pk=None):
        from django.core.exceptions import ValidationError as DjangoValidationError

        from .services.entegrasyon import finansal_islem_iptal

        islem = self.get_object()
        if islem.is_cancelled:
            raise ValidationError({"detail": "İşlem zaten iptal edilmiş."})
        try:
            finansal_islem_iptal(islem.pk, tenant_id=islem.tenant_id)
        except DjangoValidationError as exc:
            raise ValidationError({"detail": str(exc)})
        islem.refresh_from_db()
        # Renderer zaten zarflar — elle sarma yapılırsa çift zarf oluşur.
        return Response(self.get_serializer(islem).data)


class CekSenetViewSet(TenantScopedViewSet):
    queryset = CekSenet.objects.select_related("cari", "hesap", "proje").all()
    serializer_class = CekSenetSerializer
    permission_classes = [IsAuthenticated, IsFinansEditor]
    search_fields = ("numara", "aciklama", "cari__ad", "proje__proje_kodu")
    filterset_fields = ("tur", "durum", "cari", "proje")

    def destroy(self, request, *args, **kwargs):
        kayit = self.get_object()
        if kayit.durum == CekSenet.Durum.IPTAL:
            raise ValidationError({"detail": "Kayıt zaten iptal edilmiş."})
        kayit.durum = CekSenet.Durum.IPTAL
        kayit.save(update_fields=["durum", "updated_at"])
        return Response(self.get_serializer(kayit).data)


class FaturaViewSet(TenantScopedViewSet):
    """Fatura CRUD — borç/alacak takibi."""

    queryset = Fatura.objects.select_related("cari", "kasa_banka_hesabi").prefetch_related("kalemler").all()
    serializer_class = FaturaSerializer
    permission_classes = [IsAuthenticated, IsFinansEditor]
    search_fields = ("No", "cari__ad", "aciklama")
    filterset_fields = ("durum", "cari", "kasa_banka_hesabi", "alacakli", "fatura_turu")

    def destroy(self, request, *args, **kwargs):
        fatura = self.get_object()
        if fatura.durum == "iptal":
            raise ValidationError({"detail": "Fatura zaten iptal edilmiş."})
        fatura.durum = "iptal"
        fatura.save(update_fields=["durum", "updated_at"])
        return Response(self.get_serializer(fatura).data)

    @action(detail=True, methods=["post"], url_path="iptal")
    def iptal(self, request, pk=None):
        return self.destroy(request, pk=pk)

    @action(detail=True, methods=["post"], url_path="durum-gecis")
    def durum_gecis(self, request, pk=None):
        hedef_durum = request.data.get("durum")
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            raise ValidationError({"Idempotency-Key": "Bu işlem için Idempotency-Key zorunludur."})
        payload = {"fatura_id": pk, "durum": hedef_durum}
        try:
            with idempotent_operation(
                tenant_id=self.request.user.tenant_id,
                operation="fatura.durum-gecis",
                key=idempotency_key,
                payload=payload,
            ) as operation:
                if operation.status == operation.Durum.COMPLETED:
                    return Response(operation.response_data)
                fatura = fatura_durum_gecis(
                    int(pk),
                    hedef_durum,
                    tenant_id=self.request.user.tenant_id,
                )
                response_data = self.get_serializer(fatura).data
                complete_operation(
                    operation,
                    response_data=response_data,
                    resource_type="finance.Fatura",
                    resource_id=fatura.id,
                )
                return Response(response_data)
        except IdempotencyConflict as exc:
            raise ValidationError({"Idempotency-Key": str(exc)}) from exc

    @action(detail=True, methods=["post"], url_path="shadow-muhasebelestir")
    def shadow_muhasebelestir(self, request, pk=None):
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            raise ValidationError({"Idempotency-Key": "Bu işlem için Idempotency-Key zorunludur."})
        fatura = self.get_object()
        try:
            with idempotent_operation(
                tenant_id=request.user.tenant_id,
                operation="fatura.shadow-muhasebelestir",
                key=idempotency_key,
                payload={"fatura_id": fatura.pk},
            ) as operation:
                if operation.status == operation.Durum.COMPLETED:
                    return Response(operation.response_data)
                olay = fatura_shadow_muhasebelestir(
                    fatura,
                    tenant_id=request.user.tenant_id,
                )
                response_data = {
                    "id": olay.id,
                    "durum": olay.durum,
                    "olay_anahtari": olay.olay_anahtari,
                    "satir_sayisi": olay.satirlar.count(),
                }
                complete_operation(
                    operation,
                    response_data=response_data,
                    resource_type="finance.FinansalOlay",
                    resource_id=olay.id,
                )
                return Response(response_data, status=201)
        except IdempotencyConflict as exc:
            raise ValidationError({"Idempotency-Key": str(exc)}) from exc
    @action(detail=True, methods=["get"], url_path="hesap-ozeti")
    def hesap_ozeti(self, request, pk=None):
        fatura = self.get_object()
        veri = self.get_serializer(fatura).data
        veri.update(fatura_toplam_hesapla(fatura))
        return Response(veri)

    @action(detail=True, methods=["post"], url_path="e-fatura-gonder")
    def e_fatura_gonder(self, request, pk=None):
        fatura = self.get_object()
        if fatura.fatura_turu == "proforma":
            raise ValidationError({"detail": "Proforma fatura e-Fatura olarak gönderilemez."})
        if fatura.senaryo != "e_fatura":
            raise ValidationError({"detail": "Faturanın senaryosu e-Fatura olmalıdır."})
        fatura.e_fatura_durum = "gonderildi"
        fatura.save(update_fields=["e_fatura_durum", "updated_at"])
        return Response(self.get_serializer(fatura).data)

    @action(detail=True, methods=["post"], url_path="iade-olustur")
    def iade_olustur(self, request, pk=None):
        kaynak = self.get_object()
        if kaynak.durum == Fatura.DurumChoices.CANCELLED:
            raise ValidationError({"detail": "İptal edilmiş faturadan iade oluşturulamaz."})
        no = f"IADE-{kaynak.No}"
        sayac = 1
        while Fatura.objects.filter(No=no).exists():
            sayac += 1
            no = f"IADE-{kaynak.No}-{sayac}"
        iade = Fatura.objects.create(
            tenant=kaynak.tenant,
            No=no,
            cari=kaynak.cari,
            kasa_banka_hesabi=kaynak.kasa_banka_hesabi,
            durum=Fatura.DurumChoices.DRAFT,
            tarih=kaynak.tarih,
            vade_tarihi=kaynak.vade_tarihi,
            tutar=Decimal("0"),
            alacakli=not kaynak.alacakli,
            aciklama=f"{kaynak.No} numaralı faturanın iadesi",
            fatura_turu="iade",
            senaryo=kaynak.senaryo,
            para_birimi=kaynak.para_birimi,
            kur=kaynak.kur,
            kdv_dahil_mi=kaynak.kdv_dahil_mi,
            iade_faturasi=kaynak,
        )
        for kalem in kaynak.kalemler.all():
            from .models import FaturaKalemi
            FaturaKalemi.objects.create(
                fatura=iade,
                aciklama=kalem.aciklama,
                miktar=kalem.miktar,
                birim=kalem.birim,
                birim_fiyat=kalem.birim_fiyat,
                kdv_orani=kalem.kdv_orani,
                tevkifat_orani=kalem.tevkifat_orani,
                stopaj_orani=kalem.stopaj_orani,
                poz_no=kalem.poz_no,
                iskonto_orani=kalem.iskonto_orani,
            )
        iade.tutar = Decimal(fatura_toplam_hesapla(iade)["genel_toplam"])
        iade.save(update_fields=["tutar", "updated_at"])
        return Response(self.get_serializer(iade).data, status=201)


class VergiProfiliViewSet(TenantScopedViewSet):
    queryset = VergiProfili.objects.all()
    serializer_class = VergiProfiliSerializer
    permission_classes = [IsAuthenticated, IsFinansEditor]
    search_fields = ("kod", "ad")
    filterset_fields = ("is_active",)

    DEFAULT_PROFILLER = (
        ("STANDART-KDV", "Standart KDV", 20, 0, 0),
        ("INS-TEVKIFAT", "İnşaat hizmeti / %50 tevkifat", 20, 50, 0),
        ("STOPAJ-5", "Stopajlı ödeme / %5", 20, 0, 5),
    )

    def list(self, request, *args, **kwargs):
        tenant_id = etkin_tenant_id(request)
        if tenant_id:
            for kod, ad, kdv, tevkifat, stopaj in self.DEFAULT_PROFILLER:
                VergiProfili.objects.get_or_create(
                    tenant_id=tenant_id,
                    kod=kod,
                    defaults={
                        "ad": ad,
                        "kdv_orani": kdv,
                        "tevkifat_orani": tevkifat,
                        "stopaj_orani": stopaj,
                    },
                )
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        profil = self.get_object()
        if not profil.is_active:
            raise ValidationError({"detail": "Vergi profili zaten pasif."})
        profil.is_active = False
        profil.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(profil).data)


class RaporViewSet(TenantScopedViewSet):
    """Rapor CRUD - various business reports."""

    queryset = Rapor.objects.all()
    serializer_class = RaporSerializer
    permission_classes = [IsAuthenticated, IsFinansEditor]
    search_fields = ("baslik", "tip", "cari__ad")
    filterset_fields = ("tip", "cari", "kasa_banka_hesabi")

    @action(detail=False, methods=["post"], url_path="dogal-dil")
    def dogal_dil(self, request):
        """Desteklenen rapor niyetlerini açıklanabilir metne dönüştürür."""
        soru = str(request.data.get("soru", "")).strip()
        if not soru:
            raise ValidationError({"soru": "Bir rapor sorusu yazmalısınız."})
        soru_kucuk = soru.casefold()
        if not any(kelime in soru_kucuk for kelime in ("gelir", "gider", "nakit", "finans")):
            if any(kelime in soru_kucuk for kelime in ("cari", "bakiye", "müşteri", "tedarikçi")):
                veri = self.cari_ozeti(request).data
                borc = sum((Decimal(x["borc"]) for x in veri), Decimal("0"))
                alacak = sum((Decimal(x["alacak"]) for x in veri), Decimal("0"))
                return Response({
                    "soru": soru,
                    "rapor_tipi": "cari_ozeti",
                    "ozet": f"{len(veri)} cari hesapta toplam borç {borc:,.2f} ₺, toplam alacak {alacak:,.2f} ₺.",
                    "veri_notu": "Cari özeti, iptal edilmemiş cari hareketlerden ve seçili firma kapsamından üretildi.",
                    "satirlar": veri[:10],
                })
            if "mizan" in soru_kucuk or "hesap" in soru_kucuk:
                veri = self.mizan(request).data
                return Response({
                    "soru": soru,
                    "rapor_tipi": "mizan",
                    "ozet": f"Mizanda {len(veri)} hesap hareketi bulundu.",
                    "veri_notu": "İptal edilmemiş muhasebe fişleri kullanıldı.",
                    "satirlar": veri[:10],
                })
            raise ValidationError({
                "soru": "Şimdilik gelir/gider, cari bakiye veya mizan soruları destekleniyor."
            })
        veri = self.finans_ozeti(request).data
        gelir = Decimal(veri["gelir"])
        gider = Decimal(veri["gider"])
        net = gelir - gider
        return Response({
            "soru": soru,
            "rapor_tipi": "finans_ozeti",
            "ozet": f"Toplam gelir {gelir:,.2f} ₺, toplam gider {gider:,.2f} ₺. Net nakit sonucu {net:,.2f} ₺.",
            "veri_notu": "İptal edilmemiş finansal işlemler ve seçili firma kapsamı kullanıldı.",
            "metrikler": {"gelir": str(gelir), "gider": str(gider), "net": str(net)},
        })

    @action(detail=False, methods=["get"], url_path="finans-ozeti")
    def finans_ozeti(self, request):
        islemler = tenant_kapsamli_queryset(
            request, FinansalIslem.objects.filter(is_cancelled=False)
        )
        toplamlar = defaultdict(lambda: Decimal("0"))
        for islem in islemler:
            toplamlar[islem.yon] += islem.tutar
        return Response({kod: str(toplamlar[kod]) for kod in ("gelir", "gider", "transfer")})

    @action(detail=False, methods=["get"], url_path="cari-ozeti")
    def cari_ozeti(self, request):
        from cari.models import CariHareket

        hareketler = tenant_kapsamli_queryset(
            request, CariHareket.objects.filter(is_cancelled=False).select_related("cari")
        )
        ozet = defaultdict(lambda: {"borc": Decimal("0"), "alacak": Decimal("0")})
        adlar = {}
        for hareket in hareketler:
            adlar[hareket.cari_id] = hareket.cari.ad
            ozet[hareket.cari_id][hareket.yon] += hareket.tutar
        return Response([
            {
                "cari": cari_id,
                "cari_ad": adlar[cari_id],
                "borc": str(degerler["borc"]),
                "alacak": str(degerler["alacak"]),
                "bakiye": str(degerler["borc"] - degerler["alacak"]),
            }
            for cari_id, degerler in ozet.items()
        ])

    @action(detail=False, methods=["get"], url_path="mizan")
    def mizan(self, request):
        from accounting.models import FisSatiri, MuhasebeFisi

        fisler = tenant_kapsamli_queryset(
            request, MuhasebeFisi.objects.exclude(durum=MuhasebeFisi.Durum.IPTAL)
        )
        satirlar = FisSatiri.objects.filter(fis__in=fisler).select_related("hesap")
        ozet = defaultdict(lambda: {"borc": Decimal("0"), "alacak": Decimal("0")})
        adlar = {}
        for satir in satirlar:
            adlar[satir.hesap_id] = (satir.hesap.kod, satir.hesap.ad)
            ozet[satir.hesap_id]["borc"] += satir.borc
            ozet[satir.hesap_id]["alacak"] += satir.alacak
        return Response([
            {
                "hesap_kodu": adlar[hesap_id][0],
                "hesap_adi": adlar[hesap_id][1],
                "borc": str(degerler["borc"]),
                "alacak": str(degerler["alacak"]),
                "bakiye": str(degerler["borc"] - degerler["alacak"]),
            }
            for hesap_id, degerler in sorted(ozet.items(), key=lambda item: adlar[item[0]][0])
        ])


class AyarViewSet(TenantScopedViewSet):
    """Tenant kapsamındaki uygulama ayarları."""

    queryset = Ayar.objects.all()
    serializer_class = AyarSerializer
    permission_classes = [IsAuthenticated, IsFinansEditor]
    search_fields = ("anahtar", "deger", "aciklama")
    filterset_fields = ("anahtar",)
