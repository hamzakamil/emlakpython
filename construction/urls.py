"""İnşaat modülü API — Faz 1 + PDF Import."""

from rest_framework.routers import DefaultRouter
from django.urls import path

from . import views
from .views import ImportViewSet

router = DefaultRouter()
router.register("poz-gruplari", views.PozGrubuViewSet, basename="pozgrubu")
router.register("pozlar", views.PozViewSet, basename="poz")
router.register("malzemeler", views.MalzemeViewSet, basename="malzeme")
router.register("poz-malzeme-iliskileri", views.PozMalzemeIliskisiViewSet, basename="pozmalzeme")
router.register("poz-fiyatlari", views.PozFiyatViewSet, basename="pozfiyat")
router.register("proje-poz-fiyatlari", views.ProjePozFiyatViewSet, basename="proje-poz-fiyat")
router.register("yapi-sinifi-birim-maliyetleri", views.YapiSinifiBirimMaliyetViewSet, basename="yapisinifi")
router.register("projeler", views.ProjeViewSet, basename="proje")
router.register("mahaller", views.MahalViewSet, basename="mahal")
router.register("mahal-elemanlari", views.MahalElemaniViewSet, basename="mahal-elemani")
router.register("yaklasik-maliyetler", views.YaklasikMaliyetViewSet, basename="yaklasik-maliyet")
router.register("yaklasik-maliyet-satirlari", views.YaklasikMaliyetSatiriViewSet, basename="yaklasik-maliyet-satiri")
router.register("poz-planlari", views.PozPlanViewSet, basename="pozplan")
router.register("hakedisler", views.HakedisViewSet, basename="hakedis")
router.register("contract-templates", views.ContractTemplateViewSet, basename="contracttemplate")
router.register("risk-structures", views.RiskStructureViewSet, basename="riskstructure")
router.register("lease-assistances", views.LeaseAssistanceViewSet, basename="leaseassistance")
router.register("ekb", views.EKBViewSet, basename="ekb")
router.register("santiye-gunlukleri", views.SantiyeGunluguViewSet, basename="santiye-gunlugu")
router.register("kalite-kontrolleri", views.KaliteKontrolViewSet, basename="kalite-kontrol")
router.register("tedarikciler", views.TedarikciViewSet, basename="tedarikci")
router.register("malzeme-tedarikci-iliskileri", views.MalzemeTedarikciIliskisiViewSet, basename="malzeme-tedarikci")
router.register("tedarikci-teklifleri", views.TedarikciTeklifiViewSet, basename="tedarikci-teklifi")
router.register("taseron-sozlesmeleri", views.TaseronSozlesiViewSet, basename="taseron-sozlesi")
router.register("kalite-kabul-teminatlari", views.KaliteKabulTeminatiViewSet, basename="kalite-kabul-teminati")
router.register("santiye-checkinleri", views.SantiyeCheckInViewSet, basename="santiye-checkin")
router.register("malzeme-hareketleri", views.MalzemeHareketiViewSet, basename="malzeme-hareketi")
router.register("ifc-importlari", views.IFCImportJobViewSet, basename="ifc-import")
router.register("ifc-miktar-taslaklari", views.IFCQuantityDraftViewSet, basename="ifc-quantity-draft")
router.register("metrajlar", views.MetrajViewSet, basename="metraj")
router.register("poz-analizleri", views.PozAnalizViewSet, basename="poz-analiz")
router.register("nakliye-mesafeleri", views.NakliyeMesafeViewSet, basename="nakliye-mesafe")
router.register("hatirlatmalar", views.HatirlatmaViewSet, basename="hatirlatma")
router.register("hatirlatma-kurallari", views.HatirlatmaKuraliViewSet, basename="hatirlatma-kurali")

# YFK (Yapı Fiyatları Kılavuzu) endpoints
router.register("yfk/poz-versiyonlari", views.YfkPozVersiyonViewSet, basename="yfkpozversiyon")
router.register("yfk/fiyatlar", views.YfkFiyatViewSet, basename="yfkfiyat")
router.register("yfk/rayiclar", views.YfkRayicViewSet, basename="yfkrayic")
router.register("yfk/analizler", views.YfkAnalizViewSet, basename="yfkanaliz")
router.register("yfk/guncelleme-gecmisi", views.YfkGuncellemeGecmisiViewSet, basename="yfkguncellemegecmisi")

# FAZ 2 — Projeye Özel Malzeme Sistemi endpoints
router.register("proje-malzemeler", views.ProjeMalzemeViewSet, basename="proje-malzeme")
router.register("proje-malzeme-fiyatlari", views.ProjeMalzemeFiyatViewSet, basename="proje-malzeme-fiyat")
router.register("proje-poz-malzemeler", views.ProjePozMalzemeViewSet, basename="proje-poz-malzeme")
router.register("malzeme-fiyatlari", views.MalzemeFiyatViewSet, basename="malzeme-fiyat")

# Taşeron Hakedişleri
router.register("subcontractor-billings", views.SubcontractorBillingViewSet, basename="subcontractor-billing")

urlpatterns = router.urls + [
    path("imports/upload/", ImportViewSet.as_view({"post": "upload"}), name="import-upload"),
]