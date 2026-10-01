"""Muhasebe modülü API."""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("hesap-plani", views.HesapPlaniViewSet, basename="hesap-plani")
router.register("accounts", views.HesapPlaniViewSet, basename="accounts")  # Frontend alias
router.register("chart-of-accounts", views.HesapPlaniViewSet, basename="chart-of-accounts")
router.register("muhasebe-fisi", views.MuhasebeFisiViewSet, basename="muhasebe-fisi")
router.register("fisler", views.MuhasebeFisiViewSet, basename="fisler")
router.register("vouchers", views.MuhasebeFisiViewSet, basename="vouchers")

urlpatterns = router.urls
