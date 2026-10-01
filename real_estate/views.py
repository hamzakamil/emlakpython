from django.shortcuts import render

"""Gayrimenkul API view'ları (tenant izole)."""

from rest_framework.permissions import IsAuthenticated

from construction.permissions import IsConstructionEditor
from tenants.api import TenantScopedViewSet

from .models import Ada, KatKarsiligiSenaryo, MalikMutabakati, Parsel, RealEstate
from .serializers import AdaSerializer, KatKarsiligiSenaryoSerializer, MalikMutabakatiSerializer, ParselSerializer, RealEstateSerializer


class AdaViewSet(TenantScopedViewSet):
    queryset = Ada.objects.select_related("tenant").all()
    serializer_class = AdaSerializer
    permission_classes = [IsAuthenticated, IsConstructionEditor]
    search_fields = ("ada_no", "mahalle", "ilce", "il")
    filterset_fields = ("is_active", "il", "ilce")


class ParselViewSet(TenantScopedViewSet):
    queryset = Parsel.objects.select_related("tenant", "ada").all()
    serializer_class = ParselSerializer
    permission_classes = [IsAuthenticated, IsConstructionEditor]
    search_fields = ("parsel_no", "pafta", "ada__ada_no")
    filterset_fields = ("imar_durumu", "is_active", "ada")


class KatKarsiligiSenaryoViewSet(TenantScopedViewSet):
    queryset = KatKarsiligiSenaryo.objects.select_related("tenant", "parsel").all()
    serializer_class = KatKarsiligiSenaryoSerializer
    permission_classes = [IsAuthenticated, IsConstructionEditor]
    search_fields = ("senaryo_adi", "parsel__parsel_no")
    filterset_fields = ("is_active", "parsel")


class MalikMutabakatiViewSet(TenantScopedViewSet):
    queryset = MalikMutabakati.objects.select_related("tenant", "senaryo", "senaryo__parsel").all()
    serializer_class = MalikMutabakatiSerializer
    permission_classes = [IsAuthenticated, IsConstructionEditor]
    search_fields = ("malik_adi", "senaryo__senaryo_adi")
    filterset_fields = ("oy_durumu", "senaryo")


class RealEstateViewSet(TenantScopedViewSet):
    queryset = RealEstate.objects.select_related("tenant", "proje").all()
    serializer_class = RealEstateSerializer
    permission_classes = [IsAuthenticated, IsConstructionEditor]
    search_fields = ("ad", "blok", "daire_no", "tapu_adi")
    filterset_fields = ("durum", "is_active", "proje")
