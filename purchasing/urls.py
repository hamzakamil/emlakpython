"""Satın alma API — FAZ 3A (talep/sipariş) + FAZ 3B (mal kabul/stok)."""

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("purchase-requests", views.SatinAlmaTalebiViewSet, basename="purchase-request")
router.register(
    "purchase-request-items", views.SatinAlmaTalebiKalemiViewSet, basename="purchase-request-item"
)
router.register("purchase-orders", views.SatinAlmaSiparisiViewSet, basename="purchase-order")
router.register(
    "purchase-order-items", views.SatinAlmaSiparisiKalemiViewSet, basename="purchase-order-item"
)
# FAZ 3B — Mal kabul + stok
router.register("purchase-depolar", views.DepoViewSet, basename="purchase-depo")
router.register("purchase-mal-kabul", views.MalKabulViewSet, basename="purchase-mal-kabul")
router.register(
    "purchase-mal-kabul-items", views.MalKabulKalemiViewSet, basename="purchase-mal-kabul-item"
)
router.register(
    "purchase-stok-hareketleri", views.StokHareketiViewSet, basename="purchase-stok-hareketi"
)
# FAZ 7R — Stok/KDV hesap eşlemesi
router.register(
    "purchase-stok-hesap-esleme", views.StokHesapEslemeViewSet, basename="purchase-stok-hesap-esleme"
)

urlpatterns = router.urls
