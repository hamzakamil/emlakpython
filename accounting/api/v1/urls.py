"""Accounting API v1 URLs - Kural 37: UI Status Display"""

from django.urls import path
from accounting.api.v1.status import SystemStatusView

urlpatterns = [
    path('status/', SystemStatusView.as_view(), name='system_status'),
]