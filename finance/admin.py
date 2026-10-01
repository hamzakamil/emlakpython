from django.contrib import admin

from .models import Ayar, Fatura, FinansalIslem, KasaBankaHesabi, Rapor


@admin.register(KasaBankaHesabi)
class KasaBankaHesabiAdmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "tip", "para_birimi", "is_active")
    list_filter = ("tip", "is_active")
    search_fields = ("kod", "ad")


@admin.register(FinansalIslem)
class FinansalIslemAdmin(admin.ModelAdmin):
    list_display = ("hesap", "cari", "yon", "tutar", "islem_tarihi", "is_cancelled")
    list_filter = ("yon", "is_cancelled", "hesap")
    search_fields = ("hesap__kod", "aciklama", "cari__ad")


@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = ("No", "cari", "tarih", "vade_tarihi", "fatura_turu", "para_birimi", "tutar", "durum", "alacakli")
    list_filter = ("durum", "fatura_turu", "para_birimi", "e_fatura_durum", "alacakli")
    search_fields = ("No", "cari__ad")
    search_fields = ("No", "cari__ad", "aciklama")


@admin.register(Rapor)
class RaporAdmin(admin.ModelAdmin):
    list_display = ("baslik", "tip", "created_at")
    list_filter = ("tip",)
    search_fields = ("baslik",)


@admin.register(Ayar)
class AyarAdmin(admin.ModelAdmin):
    list_display = ("anahtar", "deger", "updated_at")
    list_filter = ("anahtar",)
