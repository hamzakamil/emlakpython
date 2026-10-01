"""Cari modülü API."""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("cariler", views.CariViewSet, basename="cari")
router.register("cari-hareketler", views.CariHareketViewSet, basename="cari-hareket")
router.register("hareketler", views.CariHareketViewSet, basename="hareket")

urlpatterns = router.urls
