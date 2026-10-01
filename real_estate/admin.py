from django.contrib import admin

from .models import Ada, KatKarsiligiSenaryo, MalikMutabakati, Parsel, RealEstate


@admin.register(Ada)
class AdaAdmin(admin.ModelAdmin):
    list_display = ("tenant", "ada_no", "il", "ilce", "mahalle", "is_active")
    list_filter = ("is_active", "il", "ilce")
    search_fields = ("ada_no", "mahalle", "ilce", "il")


@admin.register(Parsel)
class ParselAdmin(admin.ModelAdmin):
    list_display = ("tenant", "ada", "parsel_no", "pafta", "alan_m2", "imar_durumu", "is_active")
    list_filter = ("imar_durumu", "is_active", "ada")
    search_fields = ("parsel_no", "pafta", "ada__ada_no")


@admin.register(KatKarsiligiSenaryo)
class KatKarsiligiSenaryoAdmin(admin.ModelAdmin):
    list_display = ("tenant", "parsel", "senaryo_adi", "arsa_pay_orani", "kat_karsiligi_orani", "is_active")
    list_filter = ("is_active", "parsel")
    search_fields = ("senaryo_adi", "parsel__parsel_no")


@admin.register(MalikMutabakati)
class MalikMutabakatiAdmin(admin.ModelAdmin):
    list_display = ("tenant", "senaryo", "malik_adi", "pay_orani", "oy_durumu")
    list_filter = ("oy_durumu", "senaryo")
    search_fields = ("malik_adi", "senaryo__senaryo_adi")


@admin.register(RealEstate)
class RealEstateAdmin(admin.ModelAdmin):
    list_display = ("ad", "proje", "blok", "kat", "daire_no", "brut_m2", "durum", "is_active")
    list_filter = ("durum", "is_active", "proje")
    search_fields = ("ad", "blok", "daire_no", "tapu_adi")
