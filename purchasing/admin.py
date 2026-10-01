from django.contrib import admin

from .models import (
    Depo,
    MalKabul,
    MalKabulKalemi,
    SatinAlmaSiparisi,
    SatinAlmaSiparisiKalemi,
    SatinAlmaTalebi,
    SatinAlmaTalebiKalemi,
    StokHareketi,
)


@admin.register(SatinAlmaTalebi)
class SatinAlmaTalebiadmin(admin.ModelAdmin):
    list_display = ("talep_no", "proje", "talep_sahibi", "durum", "tarih", "is_active")
    list_filter = ("durum", "is_active")
    search_fields = ("talep_no",)


@admin.register(SatinAlmaTalebiKalemi)
class SatinAlmaTalebiKalemiadmin(admin.ModelAdmin):
    list_display = ("talep", "malzeme", "miktar", "birim", "is_active")
    search_fields = ("talep__talep_no", "malzeme__ad")


@admin.register(SatinAlmaSiparisi)
class SatinAlmaSiparisiadmin(admin.ModelAdmin):
    list_display = ("siparis_no", "tedarikci", "proje", "durum", "tarih", "is_active")
    list_filter = ("durum", "is_active")
    search_fields = ("siparis_no",)


@admin.register(SatinAlmaSiparisiKalemi)
class SatinAlmaSiparisiKalemiadmin(admin.ModelAdmin):
    list_display = ("siparis", "malzeme", "miktar", "birim_fiyat", "toplam_tutar", "is_active")
    search_fields = ("siparis__siparis_no", "malzeme__ad")


@admin.register(Depo)
class Depoadmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "is_active")
    list_filter = ("is_active",)
    search_fields = ("kod", "ad")


@admin.register(MalKabul)
class MalKabuladmin(admin.ModelAdmin):
    list_display = ("belge_no", "siparis", "depo", "durum", "kabul_tarihi", "is_active")
    list_filter = ("durum", "is_active")
    search_fields = ("belge_no",)


@admin.register(MalKabulKalemi)
class MalKabulKalemiadmin(admin.ModelAdmin):
    list_display = ("mal_kabul", "malzeme", "kabul_miktari", "red_miktari", "is_active")
    search_fields = ("mal_kabul__belge_no", "malzeme__ad")


@admin.register(StokHareketi)
class StokHareketiadmin(admin.ModelAdmin):
    list_display = ("depo", "malzeme", "hareket_tipi", "miktar", "tarih", "is_active")
    list_filter = ("hareket_tipi", "is_active")
    search_fields = ("malzeme__ad", "depo__kod")
