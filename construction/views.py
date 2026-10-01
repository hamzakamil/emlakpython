"""İnşaat modülü ViewSet'leri — Faz 1 + Faz 2 (poz planı / S-eğrisi / hakediş, tenant izole)."""

from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from tenants.api import TenantScopedViewSet, tenant_kapsamli_queryset

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
    YapiSinifiBirimMaliyet,
    Tedarikci,
    MalzemeTedarikciIliskisi,
    TaseronSozlesi,
    KaliteKabulTeminati,
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
from .permissions import IsConstructionEditor
from .serializers import (
    HakedisSerializer,
    MalzemeSerializer,
    MalzemeFiyatSerializer,
    PozFiyatSerializer,
    ProjeMalzemeSerializer,
    ProjeMalzemeFiyatSerializer,
    ProjePozMalzemeSerializer,
    ProjePozFiyatSerializer,
    PozGrubuSerializer,
    PozMalzemeIliskisiSerializer,
    PozPlanSerializer,
    PozSerializer,
    ProjeSerializer,
    KaliteKontrolSerializer,
    SantiyeGunluguSerializer,
    YapiSinifiBirimMaliyetSerializer,
    TedarikciSerializer,
    MalzemeTedarikciIliskisiSerializer,
    TaseronSozlesiSerializer,
    KaliteKabulTeminatiSerializer,
    SantiyeCheckInSerializer,
    MalzemeHareketiSerializer,
    TedarikciTeklifiSerializer,
    EKBSerializer,
    IFCImportJobSerializer,
    IFCQuantityDraftSerializer,
    MahalSerializer,
    MahalElemaniSerializer,
    YaklasikMaliyetSerializer,
    YaklasikMaliyetSatiriSerializer,
    MetrajSerializer,
    PozAnalizSerializer,
    NakliyeMesafeSerializer,
    HatirlatmaSerializer,
    HatirlatmaKuraliSerializer,
    YfkPozVersiyonSerializer,
    YfkFiyatSerializer,
    YfkRayicSerializer,
    YfkAnalizSerializer,
    YfkGuncellemeGecmisiSerializer,
)
from .models import ContractTemplate, RiskStructure, LeaseAssistance
from .serializers import ContractTemplateSerializer, RiskStructureSerializer, LeaseAssistanceSerializer
from .services import fiyat_anomalilerini_bul, gantt_verisi, hakedis_onayla, hakedis_satirlari_olustur, metraj_kontrolu, portfoy_karsilastirmasi, proje_kar_zarar, proje_nakit_akisi, s_egrisi_raporu, teknik_sartname_taslagi
from .imports import (
    ImportHatasi,
    csv_satirlari_oku,
    import_poz_verisi,
    import_yapi_sinifi_verisi,
)
from .ifc import process_ifc_job
from .services.yaklasik_maliyet import hesapla as yaklasik_maliyet_hesapla, revize as yaklasik_maliyet_revize
from .services.mahal_metraj import mahal_metraj_uret, mahal_elemanlarindan_yaklasik_maliyet_uret
from .services.metraj import (
    demir_metraji, ifade_hesapla, profil_metraji, pursantaj_hesapla,
    MetrajHesapHatasi,
)
from .services.analiz import nakliye_hesapla, poz_analiz_toplam
from .services.hatirlatma import gunluk_getir, hatirlatmalari_uret

PERMISSIONS = [IsAuthenticated, IsConstructionEditor]


class MetrajViewSet(TenantScopedViewSet):
    queryset = Metraj.objects.select_related("tenant").all()
    serializer_class = MetrajSerializer
    permission_classes = PERMISSIONS
    search_fields = ("ad", "ifade", "metraj_tipi")
    filterset_fields = ("metraj_tipi", "birim", "is_active")

    @action(detail=False, methods=["post"], url_path="hesapla")
    def hesapla(self, request):
        """Kayıt oluşturmadan metraj önizlemesi."""
        data = request.data
        try:
            tip = data.get("metraj_tipi", data.get("tip", "genel"))
            if tip == "demir":
                sonuc = demir_metraji(data.get("cap", data.get("çap")),
                                      data.get("adet", 1), data.get("uzunluk", data.get("boy")))
            elif tip == "profil":
                sonuc = profil_metraji(data.get("uzunluk"), data.get("adet", 1),
                                       data.get("kg_m", data.get("kg_metre")),
                                       data.get("profil"))
            elif tip == "pursantaj":
                sonuc = pursantaj_hesapla(data.get("tutar"), data.get("oran"))
            else:
                sonuc = ifade_hesapla(data.get("ifade", data.get("expression", "")))
        except (MetrajHesapHatasi, KeyError, TypeError) as exc:
            raise ValidationError({"detail": str(exc)})
        return Response({"sonuc": str(sonuc), "birim": data.get("birim", "miktar"),
                         "metraj_tipi": tip, "ifade": data.get("ifade")})


class PozAnalizViewSet(TenantScopedViewSet):
    queryset = PozAnaliz.objects.select_related("tenant", "poz").all()
    serializer_class = PozAnalizSerializer
    permission_classes = PERMISSIONS
    search_fields = ("malzeme", "poz__poz_no")
    filterset_fields = ("poz", "analiz_tipi")

    @action(detail=False, methods=["get"], url_path="poz-toplam")
    def poz_toplam(self, request):
        poz_id = request.query_params.get("poz")
        if not poz_id:
            raise ValidationError({"poz": "Poz seçimi zorunludur."})
        return Response({"poz": int(poz_id), "toplam": str(poz_analiz_toplam(int(poz_id)))})


class NakliyeMesafeViewSet(TenantScopedViewSet):
    queryset = NakliyeMesafe.objects.select_related("tenant", "proje", "poz").all()
    serializer_class = NakliyeMesafeSerializer
    permission_classes = PERMISSIONS
    filterset_fields = ("proje", "poz")


class HatirlatmaViewSet(TenantScopedViewSet):
    queryset = Hatirlatma.objects.select_related("tenant", "sorumlu_kullanici").all()
    serializer_class = HatirlatmaSerializer
    permission_classes = PERMISSIONS
    filterset_fields = ("ilgili_modul", "seviye", "durum", "hatirlatma_tarihi")

    @action(detail=False, methods=["get"], url_path="gunluk")
    def gunluk(self, request):
        hatirlatmalar = gunluk_getir(request.user.tenant_id)
        return Response(self.get_serializer(hatirlatmalar, many=True).data)

    @action(detail=False, methods=["post"], url_path="uret")
    def uret(self, request):
        return Response({"uretilen": hatirlatmalari_uret(request.user.tenant_id)})


class HatirlatmaKuraliViewSet(TenantScopedViewSet):
    queryset = HatirlatmaKurali.objects.select_related("tenant").all()
    serializer_class = HatirlatmaKuraliSerializer
    permission_classes = PERMISSIONS
    filterset_fields = ("ilgili_modul", "tetikleyici", "aktif_mi", "seviye")


class PozGrubuViewSet(TenantScopedViewSet):
    queryset = PozGrubu.objects.select_related("tenant", "ust_grup").all()
    serializer_class = PozGrubuSerializer
    permission_classes = PERMISSIONS
    search_fields = ("kod", "ad")
    filterset_fields = ("is_active", "ust_grup")


class PozViewSet(TenantScopedViewSet):
    queryset = Poz.objects.select_related("tenant", "grup").all()
    serializer_class = PozSerializer
    permission_classes = PERMISSIONS
    search_fields = ("poz_no", "ad", "birim")
    filterset_fields = ("tip", "grup", "is_active")


class MalzemeViewSet(TenantScopedViewSet):
    queryset = Malzeme.objects.select_related("tenant").all()
    serializer_class = MalzemeSerializer
    permission_classes = PERMISSIONS
    search_fields = ("malzeme_kodu", "ad", "ts_no")
    filterset_fields = ("is_active",)


class PozMalzemeIliskisiViewSet(TenantScopedViewSet):
    queryset = (
        PozMalzemeIliskisi.objects.select_related("tenant", "poz", "malzeme").all()
    )
    serializer_class = PozMalzemeIliskisiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("poz__poz_no", "malzeme__ad")
    filterset_fields = ("poz", "malzeme")


class PozFiyatViewSet(TenantScopedViewSet):
    queryset = PozFiyat.objects.select_related("tenant", "poz").all()
    serializer_class = PozFiyatSerializer
    permission_classes = PERMISSIONS
    search_fields = ("poz__poz_no", "kaynak")
    filterset_fields = ("yil", "poz", "is_active")


class ProjePozFiyatViewSet(TenantScopedViewSet):
    queryset = ProjePozFiyat.objects.select_related("tenant", "proje", "poz").all()
    serializer_class = ProjePozFiyatSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "poz__poz_no", "kaynak")
    filterset_fields = ("proje", "poz", "yil", "is_active")


class YapiSinifiBirimMaliyetViewSet(TenantScopedViewSet):
    queryset = YapiSinifiBirimMaliyet.objects.select_related("tenant").all()
    serializer_class = YapiSinifiBirimMaliyetSerializer
    permission_classes = PERMISSIONS
    search_fields = ("sinif_kodu",)
    filterset_fields = ("yil", "sinif_kodu", "is_active")


class MahalViewSet(TenantScopedViewSet):
    queryset = Mahal.objects.select_related("tenant", "proje").prefetch_related("elemanlar").all()
    serializer_class = MahalSerializer
    permission_classes = PERMISSIONS
    search_fields = ("kod", "ad", "mahal_tipi", "proje__proje_kodu")
    filterset_fields = ("proje", "mahal_tipi", "kat", "is_active")

    @action(detail=True, methods=["post"], url_path="metraj-uret")
    def metraj_uret(self, request, pk=None):
        result = mahal_metraj_uret(self.get_object(), request.data)
        return Response({
            "mahal": result["mahal"].pk,
            "metrajlar": {key: str(value) for key, value in result["metrajlar"].items()},
        })

    @action(detail=True, methods=["get", "post", "put", "patch", "delete"], url_path="elemanlar")
    def elemanlar(self, request, pk=None):
        mahal = self.get_object()
        eleman_id = request.query_params.get("eleman_id")
        if request.method == "GET":
            return Response(MahalElemaniSerializer(
                mahal.elemanlar.filter(tenant_id=mahal.tenant_id), many=True,
                context={"request": request},
            ).data)
        if request.method == "POST":
            payload = request.data.copy()
            payload["mahal"] = mahal.pk
            serializer = MahalElemaniSerializer(data=payload, context={"request": request})
            serializer.is_valid(raise_exception=True)
            serializer.save(mahal=mahal, tenant_id=request.user.tenant_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not eleman_id:
            raise ValidationError({"eleman_id": "Güncelleme veya silme için eleman_id zorunludur."})
        eleman = get_object_or_404(mahal.elemanlar, pk=eleman_id, tenant_id=mahal.tenant_id)
        if request.method == "DELETE":
            eleman.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = MahalElemaniSerializer(
            eleman, data=request.data, partial=request.method == "PATCH",
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(mahal=mahal, tenant_id=mahal.tenant_id)
        return Response(serializer.data)


class MahalElemaniViewSet(TenantScopedViewSet):
    queryset = MahalElemani.objects.select_related("tenant", "mahal", "mahal__proje").all()
    serializer_class = MahalElemaniSerializer
    permission_classes = PERMISSIONS
    search_fields = ("eleman_tipi", "ad", "mahal__kod", "mahal__ad")
    filterset_fields = ("mahal", "eleman_tipi", "birim", "is_active")


class YaklasikMaliyetViewSet(TenantScopedViewSet):
    queryset = YaklasikMaliyet.objects.select_related("tenant", "proje", "onceki").prefetch_related("satirlar").all()
    serializer_class = YaklasikMaliyetSerializer
    permission_classes = PERMISSIONS
    search_fields = ("ad", "proje__proje_kodu")
    filterset_fields = ("proje", "yil", "versiyon", "is_active")

    @action(detail=True, methods=["post"])
    def hesapla(self, request, pk=None):
        maliyet = yaklasik_maliyet_hesapla(self.get_object())
        return Response(self.get_serializer(maliyet).data)

    @action(detail=True, methods=["post"])
    def revize(self, request, pk=None):
        maliyet = yaklasik_maliyet_revize(self.get_object(), **{
            key: request.data[key] for key in ("ad", "aciklama") if key in request.data
        })
        return Response(self.get_serializer(maliyet).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="mahal-listesinden-olustur")
    def mahal_listesinden_olustur(self, request, pk=None):
        maliyet = self.get_object()
        mapping = request.data.get("poz_eslestirme", request.data.get("pozler", {}))
        maliyet, lines = mahal_elemanlarindan_yaklasik_maliyet_uret(
            maliyet, poz_eslestirme=mapping,
            olculer=request.data.get("olculer", request.data),
        )
        return Response({
            **self.get_serializer(maliyet).data,
            "olusturulan_satir": len(lines),
        })


class YaklasikMaliyetSatiriViewSet(TenantScopedViewSet):
    queryset = YaklasikMaliyetSatiri.objects.select_related(
        "tenant", "yaklasik_maliyet", "poz", "mahal"
    ).all()
    serializer_class = YaklasikMaliyetSatiriSerializer
    permission_classes = PERMISSIONS
    filterset_fields = ("yaklasik_maliyet", "poz", "mahal")


class ProjeViewSet(TenantScopedViewSet):
    queryset = (
        Proje.objects.select_related("tenant", "yapisinif_maliyet").all()
    )
    serializer_class = ProjeSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje_kodu", "ad")
    filterset_fields = ("durum", "is_active")

    @action(detail=True, methods=["post"], url_path="tum-mahal-metrajlari")
    def tum_mahal_metrajlari(self, request, pk=None):
        proje = self.get_object()
        olculer = request.data.get("olculer", request.data)
        results = [
            mahal_metraj_uret(mahal, olculer)
            for mahal in proje.mahaller.filter(tenant_id=request.user.tenant_id, is_active=True)
        ]
        return Response({
            "proje": proje.pk,
            "mahaller": [
                {"mahal": item["mahal"].pk,
                 "metrajlar": {key: str(value) for key, value in item["metrajlar"].items()}}
                for item in results
            ],
        })

    @action(detail=True, methods=["post"], url_path="mahal-sablondan-olustur")
    def mahal_sablondan_olustur(self, request, pk=None):
        proje = self.get_object()
        data = request.data.copy()
        data.setdefault("kod", data.get("mahal_kodu", "MAHAL-001"))
        data.setdefault("ad", data.get("mahal_adi", "Standart Mahal"))
        data.setdefault("mahal_tipi", data.get("tip", "oda"))
        data.pop("mahal_kodu", None)
        data.pop("mahal_adi", None)
        data.pop("tip", None)
        with transaction.atomic():
            mahal = Mahal.objects.create(
                tenant_id=proje.tenant_id, proje=proje,
                kod=data.get("kod"), ad=data.get("ad"),
                mahal_tipi=data.get("mahal_tipi", ""),
                kat=data.get("kat", ""), alan=data.get("alan") or None,
                aciklama=data.get("aciklama", ""),
            )
            standart = [
                ("Duvar", "m²", "Duvar yüzeyleri"),
                ("Zemin", "m²", "Zemin kaplaması"),
                ("Tavan", "m²", "Tavan yüzeyi"),
                ("Kapı", "adet", "Kapı"),
                ("Pencere", "adet", "Pencere"),
            ]
            if isinstance(data.get("elemanlar"), list):
                standart = [
                    (
                        item.get("eleman_tipi", item.get("tip", "Eleman")),
                        item.get("birim", "adet"),
                        item.get("aciklama", ""),
                    )
                    for item in data["elemanlar"]
                    if isinstance(item, dict)
                ] or standart
            MahalElemani.objects.bulk_create([
                MahalElemani(
                    tenant_id=proje.tenant_id, mahal=mahal, eleman_tipi=tip,
                    ad=tip, miktar=1, birim=birim, aciklama=aciklama,
                ) for tip, birim, aciklama in standart
            ])
        return Response(MahalSerializer(mahal, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="portfoy-ozeti")
    def portfoy_ozeti(self, request):
        """Aktif projeleri bütçe ve gerçekleşen maliyet açısından karşılaştırır."""
        ham_yil = request.query_params.get("yil")
        try:
            yil = int(ham_yil) if ham_yil else timezone.now().year
        except (TypeError, ValueError):
            raise ValidationError({"yil": "Yıl sayısal bir değer olmalıdır."})
        projeler = self.get_queryset().filter(is_active=True)
        arama = request.query_params.get("arama", "").strip()
        if arama:
            projeler = projeler.filter(Q(proje_kodu__icontains=arama) | Q(ad__icontains=arama))
        durum = request.query_params.get("durum")
        if durum:
            projeler = projeler.filter(durum=durum)
        sinif = request.query_params.get("sinif")
        if sinif:
            projeler = projeler.filter(yapisinif_maliyet__sinif_kodu=sinif)
        return Response(portfoy_karsilastirmasi(projeler.order_by("proje_kodu"), yil))

    @action(detail=False, methods=["get"], url_path="teknik-sartname")
    def teknik_sartname(self, request):
        """Seçilen proje ve yıl için poz/malzeme tabanlı şartname taslağı üretir."""
        proje_id = request.query_params.get("proje")
        if not proje_id:
            raise ValidationError({"proje": "Şartname için proje seçmelisiniz."})
        proje = get_object_or_404(self.get_queryset(), pk=proje_id)
        ham_yil = request.query_params.get("yil")
        try:
            yil = int(ham_yil) if ham_yil else timezone.now().year
        except (TypeError, ValueError):
            raise ValidationError({"yil": "Yıl sayısal bir değer olmalıdır."})
        return Response(teknik_sartname_taslagi(proje, yil))


class IFCImportJobViewSet(TenantScopedViewSet):
    queryset = IFCImportJob.objects.select_related("project", "uploaded_by").all()
    serializer_class = IFCImportJobSerializer
    permission_classes = PERMISSIONS
    parser_classes = (MultiPartParser, FormParser)
    search_fields = ("file_name", "source_reference", "processing_message", "project__proje_kodu")
    filterset_fields = ("project", "year", "status", "parser_mode")

    def perform_create(self, serializer):
        import os
        import uuid

        from django.conf import settings

        uploaded = self.request.FILES.get("file")
        if not uploaded:
            raise ValidationError({"file": "IFC dosyası zorunludur."})
        # FAZ 6F-1: boyut sınırı storage'a yazılmadan önce (413 yerine 400
        # sözleşmesi korunur).
        azami = getattr(settings, "IFC_UPLOAD_MAX_BYTES", 50 * 1024 * 1024)
        boyut = getattr(uploaded, "size", 0) or 0
        if boyut <= 0:
            raise ValidationError({"file": "Boş dosya yüklenemez."})
        if boyut > azami:
            raise ValidationError(
                {"file": f"Dosya çok büyük (sınır {azami // (1024 * 1024)} MB)."}
            )
        ham_ad = uploaded.name or ""
        # FAZ 6F-1: yalnızca .ifc (IFCZIP parser tarafından desteklenmiyor).
        if not ham_ad.lower().endswith(".ifc"):
            raise ValidationError({"file": "Sadece .ifc dosyaları kabul edilir."})
        # FAZ 6F-1: istemci MIME tek başına güvenilmez; bariz dışı tipler reddedilir.
        # Esas yapısal doğrulama process adımındaki STEP header kontrolüdür.
        mime = (getattr(uploaded, "content_type", "") or "").split(";")[0].strip().lower()
        if mime not in (
            "application/octet-stream", "text/plain", "model/step",
            "model/ifc", "application/x-step",
        ):
            raise ValidationError({"file": "Desteklenmeyen dosya türü."})
        # FAZ 6F-1: dosya adı normalize edilir, storage anahtarı sunucuda üretilir.
        temiz_ad = os.path.basename(ham_ad).strip()
        if not temiz_ad:
            raise ValidationError({"file": "Geçersiz dosya adı."})
        uploaded.name = f"{uuid.uuid4().hex}.ifc"
        serializer.save(
            tenant_id=self.request.user.tenant_id,
            file=uploaded,
            file_name=temiz_ad[:255],
            file_size=boyut,
            content_type=getattr(uploaded, "content_type", ""),
            uploaded_by=self.request.user,
        )

    @action(detail=True, methods=["post"], url_path="process")
    def process(self, request, pk=None):
        from django.core.exceptions import ValidationError as DjangoValidationError

        job = self.get_object()
        if job.status == IFCImportJob.Status.PROCESSING:
            raise ValidationError({"status": "İş zaten işleniyor."})
        try:
            job = process_ifc_job(job)
        except DjangoValidationError as exc:
            raise ValidationError({"detail": str(exc)})
        return Response(IFCImportJobSerializer(job, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """Explicitly promote mapped rows; normal review never mutates PozPlan.

        FAZ 5: `create_metraj=true` ile eşleşmiş satırlardan idempotent Metraj
        üretilir; eşleşmemiş satırlar yanıtta raporlanır (sessiz geçilmez).
        """
        from .services.metraj_entegrasyon import ifc_drafttan_metraj_uret

        job = self.get_object()
        if job.status != IFCImportJob.Status.COMPLETED:
            raise ValidationError({"status": "Yalnızca tamamlanan içe aktarımlar onaylanabilir."})
        eslesmemis = list(
            job.draft_rows.filter(mapping_status="unmapped").values_list("id", "source_name")
        )
        if not request.data.get("create_plan"):
            return Response({
                "eligible": job.draft_rows.filter(mapping_status="mapped").count(),
                "created": 0,
                "unmapped": [{"id": i, "source_name": ad} for i, ad in eslesmemis],
            })
        created, skipped, metrajlar = 0, [], 0
        with transaction.atomic():
            for row in job.draft_rows.filter(mapping_status="mapped", poz__isnull=False):
                if PozPlan.objects.filter(
                    tenant_id=job.tenant_id, proje=job.project, poz=row.poz, yil=job.year,
                ).exists():
                    skipped.append({"id": row.id, "reason": "Poz Planı zaten mevcut."})
                    continue
                try:
                    PozPlan.objects.create(
                        tenant_id=job.tenant_id, proje=job.project, poz=row.poz,
                        yil=job.year, planlanan_miktar=row.quantity,
                        aciklama=f"IFC içe aktarımı #{job.pk}",
                    )
                    created += 1
                    if request.data.get("create_metraj"):
                        ifc_drafttan_metraj_uret(row)
                        metrajlar += 1
                except ValidationError as exc:
                    skipped.append({"id": row.id, "reason": str(exc)})
        return Response({
            "eligible": created + len(skipped),
            "created": created,
            "skipped": skipped,
            "metrajlar": metrajlar,
            "unmapped": [{"id": i, "source_name": ad} for i, ad in eslesmemis],
        })

class ContractTemplateViewSet(TenantScopedViewSet):
    queryset = ContractTemplate.objects.all()
    serializer_class = ContractTemplateSerializer
    permission_classes = [IsConstructionEditor]


class IFCQuantityDraftViewSet(TenantScopedViewSet):
    queryset = IFCQuantityDraft.objects.select_related("job", "project", "poz").all()
    serializer_class = IFCQuantityDraftSerializer
    permission_classes = PERMISSIONS
    search_fields = ("source_name", "validation_message", "poz__poz_no")
    filterset_fields = ("job", "project", "year", "mapping_status", "poz")

class RiskStructureViewSet(TenantScopedViewSet):
    queryset = RiskStructure.objects.all()
    serializer_class = RiskStructureSerializer
    permission_classes = [IsConstructionEditor]

    @transaction.atomic
    def perform_update(self, serializer):
        risk = serializer.save()
        terminal_durumlar = {"tahliye edildi", "yıkıldı", "yikildi"}
        yeni_durum = " ".join((risk.risk_durumu or "").strip().lower().split())
        if yeni_durum in terminal_durumlar:
            if not risk.proje_id:
                raise ValidationError(
                    {"proje": "Kira yardımı otomatik üretimi için riskli yapıya proje bağlanmalıdır."}
                )
            LeaseAssistance.objects.get_or_create(
                tenant_id=risk.tenant_id,
                proje_id=risk.proje_id,
                kira_yardim_id=f"RY-{risk.pk}",
                defaults={
                    "tahliye_sikligi": "otomatik",
                    "aciklama": f"Riskli Yapı Süreci #{risk.pk} terminal aşamaya geçti.",
                },
            )

class LeaseAssistanceViewSet(TenantScopedViewSet):
    queryset = LeaseAssistance.objects.select_related("tenant", "proje").all()
    serializer_class = LeaseAssistanceSerializer
    permission_classes = [IsConstructionEditor]
    search_fields = ("kira_yardim_id", "tahliye_sikligi", "proje__proje_kodu", "proje__ad")
    filterset_fields = ("proje",)

    def create(self, request, *args, **kwargs):
        raise ValidationError(
            {
                "detail": (
                    "Kira yardımı kullanıcı tarafından oluşturulamaz; "
                    "Riskli Yapı Süreci 'Tahliye Edildi / Yıkıldı' aşamasına geldiğinde otomatik oluşturulur."
                )
            }
        )


class EKBViewSet(TenantScopedViewSet):
    queryset = EKB.objects.select_related("tenant", "proje").all()
    serializer_class = EKBSerializer
    permission_classes = PERMISSIONS
    search_fields = ("belge_no", "duzenleyen", "notlar", "dokuman_referansi", "proje__proje_kodu", "proje__ad")
    filterset_fields = ("proje", "durum", "enerji_sinifi", "is_active")

    def get_queryset(self):
        queryset = super().get_queryset()
        # Arşiv açıkça istenmedikçe çalışma ekranı yalnızca aktif belgeleri
        # gösterir; tenant kapsamı TenantScopedViewSet'te korunur.
        if "is_active" not in self.request.query_params:
            queryset = queryset.filter(is_active=True)
        expiry_window = self.request.query_params.get("expiry_window")
        if expiry_window:
            try:
                days = int(expiry_window)
            except (TypeError, ValueError):
                raise ValidationError({"expiry_window": "Geçerli bir gün sayısı girin."})
            if days < 0 or days > 3650:
                raise ValidationError({"expiry_window": "Gün sayısı 0 ile 3650 arasında olmalıdır."})
            today = timezone.localdate()
            queryset = queryset.filter(
                gecerlilik_tarihi__isnull=False,
                gecerlilik_tarihi__gte=today,
                gecerlilik_tarihi__lte=today + timedelta(days=days),
            )
        return queryset

    def destroy(self, request, *args, **kwargs):
        """Belge geçmişi korunur; silme isteği arşivlemeye dönüşür."""
        belge = self.get_object()
        if not belge.is_active:
            raise ValidationError({"detail": "EKB zaten arşivlenmiş."})
        belge.is_active = False
        belge.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(belge).data)

    @action(detail=True, methods=["post"])
    def arsivden_cikar(self, request, pk=None):
        belge = self.get_object()
        belge.is_active = True
        belge.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(belge).data)

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        """İngilizce istemciler için arşivden çıkarma alias'ı."""
        return self.arsivden_cikar(request, pk)

    @action(detail=False, methods=["get"])
    def ozet(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        today = timezone.localdate()
        rows = list(queryset.values_list("durum", "gecerlilik_tarihi"))
        return Response({
            "toplam": len(rows),
            "onayli": sum(durum == EKB.Durum.ONAYLANDI for durum, _ in rows),
            "suresi_dolan": sum(tarih is not None and tarih < today for _, tarih in rows),
            "otuz_gun_icinde": sum(
                tarih is not None and today <= tarih <= today + timedelta(days=30)
                for _, tarih in rows
            ),
        })


class PozPlanViewSet(TenantScopedViewSet):
    """Poz maliyet planı — planlanan/gerçekleşen metraj (roadmap Faz 2).

    `birim_fiyat_snapshot` kayıt anında `PozFiyat`'tan otomatik alınır ve
    değişmez (snapshot); istemciden kabul edilmez.
    """

    queryset = (
        PozPlan.objects.select_related("tenant", "proje", "poz", "poz__grup").all()
    )
    serializer_class = PozPlanSerializer
    permission_classes = PERMISSIONS
    search_fields = ("poz__poz_no", "poz__ad", "proje__proje_kodu", "proje__ad")
    filterset_fields = ("proje", "poz", "yil", "is_active")

    def destroy(self, request, *args, **kwargs):
        """Metraj geçmişi korunur; silme isteği planı pasife çeker."""
        plan = self.get_object()
        if not plan.is_active:
            raise ValidationError({"detail": "Poz planı zaten pasif."})
        plan.is_active = False
        plan.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(plan).data)

    def get_queryset(self):
        """Poz planı listesi raporlar için sabit sırada döner."""
        return super().get_queryset().order_by("proje__proje_kodu", "poz__poz_no")

    # --- Rapor parametreleri (tenant izole) ---------------------------------

    def _kapsam_projesi(self, request) -> Proje:
        """`?proje=<id>` parametresini tenant kapsamına göre çözer."""
        proje_id = request.query_params.get("proje")
        if not proje_id:
            raise ValidationError({"detail": "Rapor için 'proje' parametresi zorunludur."})
        return get_object_or_404(
            tenant_kapsamli_queryset(request, Proje.objects.all()), pk=proje_id
        )

    @staticmethod
    def _yil_parametresi(request, zorunlu: bool = True) -> int | None:
        """`?yil=<yıl>` parametresini doğrular (zorunlu değilse None döner)."""
        ham = request.query_params.get("yil")
        if ham in (None, ""):
            if zorunlu:
                raise ValidationError({"detail": "Rapor için 'yil' parametresi zorunludur."})
            return None
        try:
            return int(ham)
        except (TypeError, ValueError):
            raise ValidationError({"yil": "Yıl sayısal bir değer olmalıdır."})

    # --- Raporlar ----------------------------------------------------------

    @action(detail=False, methods=["get"], url_path="s-egrisi")
    def s_egrisi(self, request):
        """Poz bazlı planlanan / gerçekleşen maliyet karşılaştırma raporu.

        Query: `?proje=<id>&yil=<yıl>` (ikisi de zorunlu).
        """
        proje = self._kapsam_projesi(request)
        yil = self._yil_parametresi(request, zorunlu=True)
        return Response(s_egrisi_raporu(proje, yil))

    @action(detail=False, methods=["get"], url_path="gantt")
    def gantt(self, request):
        """İş kalemi (poz) bazlı zaman çizelgesi verisi.

        Query: `?proje=<id>[&yil=<yıl>]` — yıl verilmezse tüm yıllar gelir.
        Tarih girilmemiş planlar `tarih_atandi=False` ile döner (frontend
        bunları "tarih bekliyor" olarak listeler).
        """
        proje = self._kapsam_projesi(request)
        yil = self._yil_parametresi(request, zorunlu=False)
        return Response(gantt_verisi(proje, yil))

    @action(detail=False, methods=["get"], url_path="nakit-akisi")
    def nakit_akisi(self, request):
        proje = self._kapsam_projesi(request)
        yil = self._yil_parametresi(request, zorunlu=True)
        return Response(proje_nakit_akisi(proje, yil))

    @action(detail=False, methods=["get"], url_path="kar-zarar")
    def kar_zarar(self, request):
        proje = self._kapsam_projesi(request)
        yil = self._yil_parametresi(request, zorunlu=True)
        return Response(proje_kar_zarar(proje, yil))

    @action(detail=False, methods=["get"], url_path="metraj-kontrolu")
    def metraj_kontrolu(self, request):
        proje = self._kapsam_projesi(request)
        yil = self._yil_parametresi(request, zorunlu=True)
        return Response(metraj_kontrolu(proje, yil))

    @action(detail=False, methods=["get"], url_path="fiyat-anomalileri")
    def fiyat_anomalileri(self, request):
        proje = self._kapsam_projesi(request)
        yil = self._yil_parametresi(request, zorunlu=True)
        return Response(fiyat_anomalilerini_bul(proje, yil))


class HakedisViewSet(TenantScopedViewSet):
    """Dönemsel hakediş — taslak → onaylandı / iptal (roadmap Faz 2).

    Fiziksel DELETE kapalı: destroy iptal durumuna çeker (yanıt 200).
    """

    queryset = Hakedis.objects.select_related("tenant", "proje", "cari").all()
    serializer_class = HakedisSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "donem")
    filterset_fields = ("proje", "donem", "durum")

    def get_queryset(self):
        return super().get_queryset().order_by("-donem", "proje__proje_kodu")

    def destroy(self, request, *args, **kwargs):
        """Fiziksel silme yok: taslak hakediş iptale çekilir, onaylı silinemez (400)."""
        hakedis = self.get_object()
        if hakedis.durum == Hakedis.Durum.ONAYLANDI:
            raise ValidationError({"detail": "Onaylanmış hakediş silinemez (iptal kaydı açınız)."})
        hakedis.durum = Hakedis.Durum.IPTAL
        hakedis.save(update_fields=["durum", "updated_at"])
        serializer = self.get_serializer(hakedis)
        # Renderer zaten zarflar — elle sarma yapılırsa çift zarf oluşur.
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="satirlari-olustur")
    def satirlari_olustur(self, request, pk=None):
        """Poz planlarından satır üretir (gerçekleşen metraj × snapshot)."""
        from django.core.exceptions import ValidationError as DjangoValidationError

        hakedis = self.get_object()
        if hakedis.durum != Hakedis.Durum.TASLAK:
            raise ValidationError({"detail": "Yalnızca taslak hakedişe satır üretilebilir."})
        try:
            eklenen = hakedis_satirlari_olustur(hakedis)
        except DjangoValidationError as exc:
            raise ValidationError({"detail": str(exc)})
        serializer = self.get_serializer(self.get_object())
        return Response({"eklenen_satir": eklenen, "hakedis": serializer.data})

    @action(detail=True, methods=["post"], url_path="onayla")
    def onayla(self, request, pk=None):
        """Taslak hakedişi onaylar: Cari Hareket + Muhasebe Fişi üretir.

        FAZ 6C: Idempotency-Key sarmalı (FAZ 4 FAILED semantiği aynen korunur).
        """
        from django.core.exceptions import ValidationError as DjangoValidationError

        from purchasing.views import _idempotent_post

        hakedis = self.get_object()

        def _onayla_ve_zarf():
            try:
                sonuc = hakedis_onayla(hakedis, onaylayan=request.user)
            except DjangoValidationError as exc:
                raise ValidationError({"detail": str(exc)})
            return Response(self.get_serializer(sonuc).data)

        return _idempotent_post(
            request,
            tenant_id=hakedis.tenant_id,
            operation="hakedis.onayla",
            payload={"hakedis_id": hakedis.pk},
            kaynak_turu="construction.Hakedis",
            kaynak_id=hakedis.pk,
            islem=_onayla_ve_zarf,
        )


class SantiyeGunluguViewSet(TenantScopedViewSet):
    queryset = SantiyeGunlugu.objects.select_related("proje", "created_by").all()
    serializer_class = SantiyeGunluguSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "yapilan_is", "sorunlar", "notlar")
    filterset_fields = ("proje", "tarih", "is_active")

    def get_queryset(self):
        queryset = super().get_queryset()
        # Arşiv açıkça istenmedikçe çalışma ekranı yalnızca aktif günlükleri gösterir
        if "is_active" not in self.request.query_params:
            queryset = queryset.filter(is_active=True)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Günlük geçmişi korunur; silme isteği arşivlemeye dönüşür."""
        gunluk = self.get_object()
        if not gunluk.is_active:
            raise ValidationError({"detail": "Şantiye günlüğü zaten arşivlenmiş."})
        gunluk.is_active = False
        gunluk.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(gunluk).data)

    @action(detail=True, methods=["post"])
    def arsivden_cikar(self, request, pk=None):
        gunluk = self.get_object()
        gunluk.is_active = True
        gunluk.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(gunluk).data)

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        """İngilizce istemciler için arşivden çıkarma alias'ı."""
        return self.arsivden_cikar(request, pk)


class SantiyeCheckInViewSet(TenantScopedViewSet):
    queryset = SantiyeCheckIn.objects.select_related("proje", "kullanici").all()
    serializer_class = SantiyeCheckInSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "kullanici__username", "notlar")
    filterset_fields = ("proje", "kullanici", "giris_zamani", "is_active")

    def perform_create(self, serializer):
        serializer.save(kullanici=self.request.user, tenant_id=self.request.user.tenant_id)


class MalzemeHareketiViewSet(TenantScopedViewSet):
    queryset = MalzemeHareketi.objects.select_related("proje", "malzeme", "kaydeden").all()
    serializer_class = MalzemeHareketiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "malzeme__ad", "malzeme__malzeme_kodu", "qr_kodu")
    filterset_fields = ("proje", "malzeme", "yon", "gerceklesme_zamani", "is_active")

    def perform_create(self, serializer):
        serializer.save(kaydeden=self.request.user, tenant_id=self.request.user.tenant_id)


class KaliteKontrolViewSet(TenantScopedViewSet):
    queryset = KaliteKontrol.objects.select_related("proje", "poz", "kontrol_eden").all()
    serializer_class = KaliteKontrolSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "kontrol_tipi", "kriter", "aciklama", "duzeltici_faaliyet")
    filterset_fields = ("proje", "poz", "durum", "kontrol_tipi", "tarih")

    def perform_create(self, serializer):
        serializer.save(kontrol_eden=self.request.user)


class ImportViewSet(TenantScopedViewSet):
    """
    ÇŞİDB PDF/CSV içe aktarma endpoint'leri.

    POST /api/v1/construction/imports/upload/
    multipart/form-data olarak PDF veya CSV dosyası kabul eder.
    PDF dosyası pdfplumber ile metne çevrilip CSV formatına çevrilir,
    ardından mevcut CSV parser (construction.imports) ile işlenir.
    """

    permission_classes = PERMISSIONS
    parser_classes = (MultiPartParser, FormParser)
    queryset = None

    def get_queryset(self):
        return None

    def _pdf_to_csv(self, dosya) -> str:
        try:
            import pdfplumber
        except ImportError:
            raise ImportError(
                "pdfplumber kütüphanesi yüklü değil. "
                "`pip install pdfplumber` ile yükleyin."
            )

        from io import StringIO
        from csv import writer

        csv_buffer = StringIO()
        csv_writer = writer(StringIO(), delimiter=";")
        csv_writer.writerow(["poz_no", "grup_kodu", "grup_adi", "ad", "birim", "yil", "birim_fiyat", "tip", "kaynak"])

        try:
            with pdfplumber.open(self.request.FILES["dosya"]) as pdf:
                for sayfa_no, sayfa in enumerate(pdf.pages, start=1):
                    tablo = sayfa.extract_table()
                    if not tablo:
                        continue
                    for satir in tablo:
                        if not satir or all(huc is None or str(huc).strip() == "" for huc in satir):
                            continue
                        temiz_satir = [
                            str(huc).strip().replace("\n", " ") if huc is not None else ""
                        ]
                        csv_writer.writerow(temiz_satir)
        except Exception as exc:
            raise ValidationError({"detail": f"PDF okuma hatası: {str(exc)}"})

        return csv_buffer.getvalue()

    def _csv_isle(self, csv_metni: str, yil: int, kaynak: str) -> dict:
        from tempfile import NamedTemporaryFile
        from django.db import transaction

        with NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8", newline="") as tmp:
            tmp.write(csv_metni)
            tmp_path = tmp.name

        try:
            from tenants.utils import tenant_baglam
            with tenant_baglam(self.request.user.tenant):
                with transaction.atomic():
                    satirlar = csv_satirlari_oku(tmp_path, ayrac=";")
                    ozet = import_poz_verisi(
                        tenant=self.request.user.tenant,
                        satirlar=satirlar,
                        yil=yil,
                        kaynak=kaynak,
                    )
            return {
                "satir_sayisi": ozet.satir_sayisi,
                "grup_olusturulan": ozet.grup_olusturulan,
                "poz_olusturulan": ozet.poz_olusturulan,
                "poz_guncellenen": ozet.poz_guncellenen,
                "fiyat_olusturulan": ozet.fiyat_olusturulan,
                "fiyat_guncellenen": ozet.fiyat_guncellenen,
            }
        except ImportHatasi as exc:
            raise ValidationError({"detail": str(exc)})
        except Exception as exc:
            raise ValidationError({"detail": f"İçe aktarma hatası: {str(exc)}"})
        finally:
            import os
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    @action(detail=False, methods=["post"], url_path="upload", parser_classes=(MultiPartParser, FormParser))
    def upload(self, request):
        dosya = request.FILES.get("dosya")
        if not dosya:
            raise ValidationError({"detail": "Dosya alanı zorunludur."})

        dosya_adi = dosya.name.lower()
        if not (dosya_adi.endswith(".pdf") or dosya_adi.endswith(".csv")):
            raise ValidationError(
                {"detail": "Sadece .pdf veya .csv dosyaları kabul edilir."}
            )

        if dosya_adi.endswith(".pdf") and dosya.content_type != "application/pdf":
            raise ValidationError({"detail": "Geçersiz PDF dosyası."})
        if dosya_adi.endswith(".csv") and dosya.content_type not in [
            "text/csv",
            "application/csv",
            "application/vnd.ms-excel",
        ]:
            raise ValidationError({"detail": "Geçersiz CSV dosyası."})

        yil_str = request.data.get("yil")
        if not yil_str:
            raise ValidationError({"detail": "Yıl alanı zorunludur."})
        try:
            yil = int(yil_str)
            if yil < 2000 or yil > 2100:
                raise ValueError()
        except ValueError:
            raise ValidationError({"detail": "Geçersiz yıl (örn. 2026)."})

        kaynak = request.data.get("kaynak", "PDF/CSV Yükleme")
        tip = request.data.get("tip", "poz")

        try:
            if dosya.name.lower().endswith(".pdf"):
                csv_metni = self._pdf_to_csv(dosya)
            else:
                csv_metni = dosya.read().decode("utf-8-sig")

            if tip == "yapi_sinifi":
                return self._yapi_sinifi_isle(request, csv_metni, yil, kaynak)
            else:
                return self._csv_isle(request, csv_metni, yil, kaynak)

        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError({"detail": f"Beklenmeyen hata: {str(exc)}"})

    def _yapi_sinifi_isle(self, request, csv_metni: str, yil: int, kaynak: str) -> dict:
        from tempfile import NamedTemporaryFile
        from django.db import transaction

        with NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8", newline="") as tmp:
            tmp.write(csv_metni)
            tmp_path = tmp.name

        try:
            from tenants.utils import tenant_baglam
            with tenant_baglam(request.user.tenant):
                with transaction.atomic():
                    satirlar = csv_satirlari_oku(tmp_path, ayrac=";")
                    ozet = import_yapi_sinifi_verisi(
                        tenant=request.user.tenant,
                        satirlar=satirlar,
                    )
            return {"ozet": str(ozet)}
        except ImportHatasi as exc:
            raise ValidationError({"detail": str(exc)})
        except Exception as exc:
            raise ValidationError({"detail": f"Yapı sınıfı içe aktarma hatası: {str(exc)}"})
        finally:
            import os
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

class TedarikciViewSet(TenantScopedViewSet):
    """Tedarikçi / tedarik firması kartı."""
    queryset = Tedarikci.objects.all()
    serializer_class = TedarikciSerializer
    permission_classes = PERMISSIONS
    search_fields = ("firma_adi", "firma_kodu", "il", "ilce")
    filterset_fields = ("is_active", "il")


class MalzemeTedarikciIliskisiViewSet(TenantScopedViewSet):
    """Malzeme - tedarikçi ilişki ve sipariş takibi."""
    queryset = MalzemeTedarikciIliskisi.objects.select_related("tenant", "malzeme", "tedarikci").all()
    serializer_class = MalzemeTedarikciIliskisiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("malzeme__ad", "tedarikci__firma_adi")
    filterset_fields = ("malzeme", "tedarikci")


class TedarikciTeklifiViewSet(TenantScopedViewSet):
    """Proje/malzeme bazında teklifleri karşılaştırır; seçilen teklif korunur."""

    queryset = TedarikciTeklifi.objects.select_related(
        "tenant", "proje", "malzeme", "tedarikci"
    ).all()
    serializer_class = TedarikciTeklifiSerializer
    permission_classes = PERMISSIONS
    search_fields = (
        "proje__proje_kodu", "proje__ad", "malzeme__malzeme_kodu",
        "malzeme__ad", "tedarikci__firma_adi", "tedarikci__firma_kodu", "notlar",
    )
    filterset_fields = ("proje", "malzeme", "tedarikci", "durum", "secildi", "is_active")

    def destroy(self, request, *args, **kwargs):
        teklif = self.get_object()
        if not teklif.is_active:
            raise ValidationError({"detail": "Teklif zaten arşivlenmiş."})
        teklif.is_active = False
        teklif.secildi = False
        teklif.save(update_fields=["is_active", "secildi", "updated_at"])
        return Response(self.get_serializer(teklif).data)

    @action(detail=True, methods=["post"], url_path="kazanan-sec")
    def kazanan_sec(self, request, pk=None):
        """Aynı proje/malzeme grubundaki diğer aktif teklifleri seçilmemiş yapar.

        Grup satırları pk sırasında kilitlenir; eşzamanlı iki seçim serileşir,
        deadlock oluşmaz ve grupta her zaman tek kazanan kalır (500 yok).
        """
        with transaction.atomic():
            hedef = self.get_queryset().filter(pk=pk).values(
                "tenant_id", "proje_id", "malzeme_id", "is_active"
            ).first()
            if hedef is None:
                return get_object_or_404(self.get_queryset(), pk=pk)
            if not hedef["is_active"]:
                raise ValidationError({"detail": "Pasif teklif kazanan seçilemez."})
            grup = list(
                TedarikciTeklifi.objects.select_for_update()
                .filter(
                    tenant_id=hedef["tenant_id"],
                    proje_id=hedef["proje_id"],
                    malzeme_id=hedef["malzeme_id"],
                    is_active=True,
                )
                .order_by("pk")
            )
            teklif = next((t for t in grup if t.pk == int(pk)), None)
            if teklif is None:
                raise ValidationError({"detail": "Teklif grupta bulunamadı."})
            TedarikciTeklifi.objects.filter(
                tenant=teklif.tenant,
                proje=teklif.proje,
                malzeme=teklif.malzeme,
                is_active=True,
            ).exclude(pk=teklif.pk).update(secildi=False, updated_at=timezone.now())
            teklif.secildi = True
            teklif.durum = TedarikciTeklifi.Durum.KABUL
            teklif.save(update_fields=["secildi", "durum", "updated_at", "toplam_tutar"])
        return Response(self.get_serializer(teklif).data)


class TaseronSozlesiViewSet(TenantScopedViewSet):
    """Taşeron sözleşmesi - projeler arası taşeron ilişkisi."""
    queryset = TaseronSozlesi.objects.select_related("tenant", "proje").all()
    serializer_class = TaseronSozlesiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "taseron_firma", "sosyal_unvan", "sicil_no")
    filterset_fields = ("proje", "durum")

    def destroy(self, request, *args, **kwargs):
        """Sözleşme geçmişi korunur; silme isteği iptal durumuna çeker."""
        sozlesme = self.get_object()
        if sozlesme.durum == TaseronSozlesi.Durum.IPTAL:
            raise ValidationError({"detail": "Sözleşme zaten iptal edilmiş."})
        sozlesme.durum = TaseronSozlesi.Durum.IPTAL
        sozlesme.save(update_fields=["durum", "updated_at"])
        return Response(self.get_serializer(sozlesme).data)


class KaliteKabulTeminatiViewSet(TenantScopedViewSet):
    """Kalite kabul teminatı - poz kabul/kontrol kayıtları."""
    queryset = KaliteKabulTeminati.objects.select_related("tenant", "proje", "poz", "created_by").all()
    serializer_class = KaliteKabulTeminatiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "poz__poz_no", "kriter")
    filterset_fields = ("proje", "poz", "sonuc", "tarih")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class YfkPozVersiyonViewSet(TenantScopedViewSet):
    """YFK poz versiyonları — versiyonlu poz tanımları."""
    queryset = YfkPozVersiyon.objects.select_related("tenant").prefetch_related("fiyatlar", "rayiclar", "analizler").all()
    serializer_class = YfkPozVersiyonSerializer
    permission_classes = PERMISSIONS
    search_fields = ("poz_no", "ad", "grup_kodu", "grup_adi")
    filterset_fields = ("degisiklik_turu", "is_active", "versiyon", "yayin_tarihi")


class YfkFiyatViewSet(TenantScopedViewSet):
    """YFK poz fiyatları — ay/yıl bazlı."""
    queryset = YfkFiyat.objects.select_related("tenant", "poz_versiyon").all()
    serializer_class = YfkFiyatSerializer
    permission_classes = PERMISSIONS
    search_fields = ("poz_versiyon__poz_no", "kaynak")
    filterset_fields = ("yil", "donem", "is_active")


class YfkRayicViewSet(TenantScopedViewSet):
    """YFK rayıç (katsayı) tanımları."""
    queryset = YfkRayic.objects.select_related("tenant", "poz_versiyon").all()
    serializer_class = YfkRayicSerializer
    permission_classes = PERMISSIONS
    search_fields = ("poz_versiyon__poz_no", "malzeme_kodu", "malzeme_adi")
    filterset_fields = ("malzeme_tipi", "is_active", "yayin_tarihi")


class YfkAnalizViewSet(TenantScopedViewSet):
    """YFK poz analiz detayları."""
    queryset = YfkAnaliz.objects.select_related("tenant", "poz_versiyon").all()
    serializer_class = YfkAnalizSerializer
    permission_classes = PERMISSIONS
    search_fields = ("poz_versiyon__poz_no", "malzeme_kodu", "malzeme_adi")
    filterset_fields = ("malzeme_tipi", "is_active", "yayin_tarihi")


class YfkGuncellemeGecmisiViewSet(TenantScopedViewSet):
    """YFK güncelleme geçmişi — audit log."""
    queryset = YfkGuncellemeGecmisi.objects.select_related("tenant", "baslayan_kullanici").all()
    serializer_class = YfkGuncellemeGecmisiSerializer
    permission_classes = PERMISSIONS
    search_fields = ("kaynak", "dosya_adi", "hata_mesaji")
    filterset_fields = ("islem_turu", "durum", "yil", "donem")


# =============================================================================
# FAZ 2 — Projeye Özel Malzeme Sistemi ViewSet'leri
# =============================================================================

class ProjeMalzemeViewSet(TenantScopedViewSet):
    """Proje bazlı malzeme tedarik ve teklif yönetimi."""
    queryset = ProjeMalzeme.objects.select_related("tenant", "proje", "malzeme", "tedarikci", "cari", "selected_teklif").all()
    serializer_class = ProjeMalzemeSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "malzeme__malzeme_kodu", "malzeme__ad", "tedarikci__firma_adi")
    filterset_fields = ("proje", "malzeme", "tedarikci", "is_active")

    def destroy(self, request, *args, **kwargs):
        """Soft delete: is_active=False"""
        obj = self.get_object()
        if not obj.is_active:
            raise ValidationError({"detail": "Kayıt zaten pasif."})
        obj.is_active = False
        obj.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=["post"], url_path="teklif-sec")
    def teklif_sec(self, request, pk=None):
        """ProjeMalzeme için selected_teklif seç."""
        proje_malzeme = self.get_object()
        teklif_id = request.data.get("teklif_id")
        if not teklif_id:
            raise ValidationError({"teklif_id": "Teklif ID zorunludur."})
        
        from .models import TedarikciTeklifi
        try:
            teklif = TedarikciTeklifi.objects.get(
                pk=teklif_id,
                tenant_id=proje_malzeme.tenant_id,
                proje=proje_malzeme.proje,
                malzeme=proje_malzeme.malzeme,
                is_active=True,
            )
        except TedarikciTeklifi.DoesNotExist:
            raise ValidationError({"teklif_id": "Geçerli bir teklif bulunamadı (tenant/proje/malzeme/is_active uyuşmazlığı)."})
        
        proje_malzeme.selected_teklif = teklif
        proje_malzeme.save(update_fields=["selected_teklif", "updated_at"])
        return Response(self.get_serializer(proje_malzeme).data)

    @action(detail=True, methods=["post"], url_path="tedarikci-ata")
    def tedarikci_ata(self, request, pk=None):
        """ProjeMalzeme için tedarikci ata."""
        proje_malzeme = self.get_object()
        tedarikci_id = request.data.get("tedarikci_id")
        if not tedarikci_id:
            raise ValidationError({"tedarikci_id": "Tedarikçi ID zorunludur."})
        
        from .models import Tedarikci
        try:
            tedarikci = Tedarikci.objects.get(pk=tedarikci_id, tenant_id=proje_malzeme.tenant_id, is_active=True)
        except Tedarikci.DoesNotExist:
            raise ValidationError({"tedarikci_id": "Geçerli bir tedarikçi bulunamadı."})
        
        proje_malzeme.tedarikci = tedarikci
        proje_malzeme.save(update_fields=["tedarikci", "updated_at"])
        return Response(self.get_serializer(proje_malzeme).data)


class ProjeMalzemeFiyatViewSet(TenantScopedViewSet):
    """Proje bazlı malzeme yıl bazlı fiyatları."""
    queryset = ProjeMalzemeFiyat.objects.select_related("tenant", "proje", "malzeme").all()
    serializer_class = ProjeMalzemeFiyatSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "malzeme__malzeme_kodu", "malzeme__ad", "kaynak")
    filterset_fields = ("proje", "malzeme", "yil", "is_active")

    def destroy(self, request, *args, **kwargs):
        """Soft delete: is_active=False"""
        obj = self.get_object()
        if not obj.is_active:
            raise ValidationError({"detail": "Kayıt zaten pasif."})
        obj.is_active = False
        obj.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(obj).data)


class ProjePozMalzemeViewSet(TenantScopedViewSet):
    """Proje-poz seviyesinde malzeme alternatifi ve miktar override."""
    queryset = ProjePozMalzeme.objects.select_related("tenant", "proje", "poz", "kaynak_malzeme", "etkin_malzeme").all()
    serializer_class = ProjePozMalzemeSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "poz__poz_no", "kaynak_malzeme__malzeme_kodu", "etkin_malzeme__malzeme_kodu")
    filterset_fields = ("proje", "poz", "kaynak_malzeme", "etkin_malzeme", "is_active")

    def destroy(self, request, *args, **kwargs):
        """Soft delete: is_active=False"""
        obj = self.get_object()
        if not obj.is_active:
            raise ValidationError({"detail": "Kayıt zaten pasif."})
        obj.is_active = False
        obj.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(obj).data)


class MalzemeFiyatViewSet(TenantScopedViewSet):
    """Genel tenant bazlı malzeme fiyatları."""
    queryset = MalzemeFiyat.objects.select_related("tenant", "malzeme").all()
    serializer_class = MalzemeFiyatSerializer
    permission_classes = PERMISSIONS
    search_fields = ("malzeme__malzeme_kodu", "malzeme__ad", "kaynak")
    filterset_fields = ("malzeme", "yil", "is_active")

    def destroy(self, request, *args, **kwargs):
        """Soft delete: is_active=False"""
        obj = self.get_object()
        if not obj.is_active:
            raise ValidationError({"detail": "Kayıt zaten pasif."})
        obj.is_active = False
        obj.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(obj).data)


# =============================================================================
# Taşeron Hakedişleri (Subcontractor Billings) — Hakedis alt kümesi, cari.tip == TASERON
# =============================================================================

class SubcontractorBillingViewSet(TenantScopedViewSet):
    """Taşeron hakedişleri — cari tipi TASERON olan hakedişler.

    GET /api/v1/construction/subcontractor-billings/
    """

    queryset = Hakedis.objects.select_related("tenant", "proje", "cari").filter(cari__tip="taseron")
    serializer_class = HakedisSerializer
    permission_classes = PERMISSIONS
    search_fields = ("proje__proje_kodu", "donem", "cari__ad")
    filterset_fields = ("proje", "donem", "durum", "cari")

    def get_queryset(self):
        return super().get_queryset().order_by("-donem", "proje__proje_kodu")
