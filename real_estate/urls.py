"""Gayrimenkul modülü API."""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("adalar", views.AdaViewSet, basename="ada")
router.register("parseller", views.ParselViewSet, basename="parsel")
router.register("kat-karsiligi-senaryolari", views.KatKarsiligiSenaryoViewSet, basename="kat-karsiligi-senaryo")
router.register("malik-mutabakatlari", views.MalikMutabakatiViewSet, basename="malik-mutabakati")
router.register("gayrimenkuller", views.RealEstateViewSet, basename="gayrimenkul")

urlpatterns = router.urls