"""Finans modülü API."""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("kasa-banka-hesaplari", views.KasaBankaHesabiViewSet, basename="kasa-banka")
router.register("finansal-islemler", views.FinansalIslemViewSet, basename="finansal-islem")
router.register("cek-senetler", views.CekSenetViewSet, basename="cek-senet")
router.register("faturalar", views.FaturaViewSet, basename="fatura")
router.register("vergi-profilleri", views.VergiProfiliViewSet, basename="vergi-profili")
router.register("raporlar", views.RaporViewSet, basename="rapor")
router.register("ayarlar", views.AyarViewSet, basename="ayar")

urlpatterns = router.urls
