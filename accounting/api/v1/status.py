"""System status API - Kural 37: UI Status Display"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from accounting.periods import get_active_period
from tenants.middleware import get_current_tenant


class SystemStatusView(APIView):
    """Sistem durumunu gösteren API endpointi (Kural 37)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Aktif dönem
        active_period = get_active_period()

        # Mevcut tenant
        tenant = get_current_tenant(request)

        return Response({
            'active_period': {
                'id': active_period.id if active_period else None,
                'baslangic': str(active_period.baslangic_tarihi) if active_period else None,
                'bitis': str(active_period.bitis_tarihi) if active_period else None,
                'durum': active_period.durum if active_period else 'YOK',
                'kapatilmis': not active_period.is_active if active_period else True,
            },
            'tenant': {
                'id': tenant.id if tenant else None,
                'ad': tenant.ad if tenant else None,
            } if tenant else None,
            'server_time': timezone.now().isoformat(),
            'authenticated': request.user.is_authenticated,
        })