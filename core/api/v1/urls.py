"""Core modülü API - Kural 36 & Kural 37 entegrasyonlu"""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("sistem-ayarları", views.SistemAyarlarViewSet, basename="sistem-ayarları")
router.register("rapor-tipleri", views.RaporTipiViewSet, basename="rapor-tipleri")
router.register("raporlar", views.RaporViewSet, basename="raporlar")

urlpatterns = router.urls