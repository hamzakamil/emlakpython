from django.contrib import admin

from .models import FisSatiri, HesapPlani, MuhasebeFisi


@admin.register(HesapPlani)
class HesapPlaniAdmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "seviye", "ust_hesap", "tip", "normal_bakiye", "detay_hesap_mi", "is_active")
    list_filter = ("tip", "normal_bakiye", "seviye", "detay_hesap_mi", "is_active")
    search_fields = ("kod", "ad")


class FisSatiriInline(admin.TabularInline):
    model = FisSatiri
    extra = 0


@admin.register(MuhasebeFisi)
class MuhasebeFisiAdmin(admin.ModelAdmin):
    list_display = ("fis_no", "fis_tarihi", "durum")
    list_filter = ("durum",)
    search_fields = ("fis_no", "aciklama")
    inlines = (FisSatiriInline,)
