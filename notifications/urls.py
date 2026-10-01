from rest_framework.routers import DefaultRouter

from .views import HatirlatmaKuraliViewSet, HatirlatmaViewSet

router = DefaultRouter()
router.register("hatirlatmalar", HatirlatmaViewSet, basename="notification-hatirlatma")
router.register("hatirlatma-kurallari", HatirlatmaKuraliViewSet, basename="notification-hatirlatma-kurali")

urlpatterns = router.urls
