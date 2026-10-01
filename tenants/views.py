from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from tenants.models import Tenant
from users.permissions import IsSuperUser
from users.serializers import TenantSecimSerializer, TenantSerializer


class TenantSecimViewSet(ReadOnlyModelViewSet):
    """GET /api/v1/tenants/ — tenant seçici listesi (yalnızca süper admin).

    Normal kullanıcılar kendi tenant'ını /auth/me üzerinden öğrenir; bu liste
    yalnızca kapsam daraltma yetkisi olan süper admin'e açıktır
    (04-API-VE-ROLLER.md §2: tenant yönetimi yalnızca süper admin).
    """

    queryset = Tenant.objects.all().order_by("name")
    serializer_class = TenantSecimSerializer
    permission_classes = [IsSuperUser]


class TenantViewSet(ModelViewSet):
    """Süper admin firma (tenant) yönetimi — tam CRUD.

    Firma ekleme, düzenleme, silme ve limitler (kullanıcı/proje/depolama)
    yalnızca süper admin yetkisindedir (04-API-VE-ROLLER.md §2).
    """

    queryset = Tenant.objects.all().order_by("name")
    serializer_class = TenantSerializer
    permission_classes = [IsSuperUser]

