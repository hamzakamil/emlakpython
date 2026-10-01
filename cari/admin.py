from django.contrib import admin

from .models import Cari, CariHareket


@admin.register(Cari)
class CariAdmin(admin.ModelAdmin):
    list_display = ("ad", "tip", "tur", "vergi_dairesi", "is_active")
    list_filter = ("tip", "tur", "is_active")
    search_fields = ("ad", "vergi_dairesi")


@admin.register(CariHareket)
class CariHareketAdmin(admin.ModelAdmin):
    list_display = ("cari", "yon", "tutar", "islem_tarihi", "is_cancelled")
    list_filter = ("yon", "is_cancelled", "cari")
    search_fields = ("cari__ad", "aciklama")

