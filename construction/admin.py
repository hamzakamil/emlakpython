from django.contrib import admin
# test

from .models import (
    Hakedis,
    HakedisSatiri,
    KaliteKontrol,
    KaliteKabulTeminati,
    Malzeme,
    MalzemeTedarikciIliskisi,
    Poz,
    PozFiyat,
    PozGrubu,
    PozMalzemeIliskisi,
    PozPlan,
    Proje,
    SantiyeGunlugu,
    TaseronSozlesi,
    Tedarikci,
    TedarikciTeklifi,
    YapiSinifiBirimMaliyet,
    YfkAnaliz,
    YfkFiyat,
    YfkGuncellemeGecmisi,
    YfkPozVersiyon,
    YfkRayic,
    EKB,
)


@admin.register(PozGrubu)
class PozGrubuadmin(admin.ModelAdmin):
    list_display = ("kod", "ad", "ust_grup", "is_active")
    list_filter = ("is_active",)
    search_fields = ("kod", "ad")


@admin.register(Poz)
class Pozadmin(admin.ModelAdmin):
    list_display = ("poz_no", "ad", "grup", "birim", "tip", "is_active")
    list_filter = ("tip", "grup", "is_active")
    search_fields = ("poz_no", "ad")


@admin.register(Malzeme)
class Malzemeadmin(admin.ModelAdmin):
    list_display = ("malzeme_kodu", "ad", "birim", "ts_no", "is_active")
    list_filter = ("is_active",)
    search_fields = ("malzeme_kodu", "ad", "ts_no")


@admin.register(PozMalzemeIliskisi)
class PozMalzemeIliskisiadmin(admin.ModelAdmin):
    list_display = ("poz", "malzeme", "miktar")
    search_fields = ("poz__poz_no", "malzeme__ad")


@admin.register(PozFiyat)
class PozFiyatadmin(admin.ModelAdmin):
    list_display = ("poz", "yil", "donem", "birim_fiyat", "kaynak_url", "yayin_tarihi", "gecerlilik_tarihi", "ice_aktarma_tarihi", "is_active")
    list_filter = ("yil", "donem", "is_active")
    search_fields = ("poz__poz_no", "kaynak_url")
    readonly_fields = ("ice_aktarma_tarihi",)


@admin.register(YapiSinifiBirimMaliyet)
class YapiSinifiBirimMaliyetadmin(admin.ModelAdmin):
    list_display = ("sinif_kodu", "yil", "birim_maliyet", "is_active")
    list_filter = ("yil", "sinif_kodu", "is_active")


@admin.register(Proje)
class Projeadmin(admin.ModelAdmin):
    list_display = ("proje_kodu", "ad", "yapisinif_maliyet", "durum", "is_active")
    list_filter = ("durum", "is_active")
    search_fields = ("proje_kodu", "ad")


@admin.register(PozPlan)
class PozPlanadmin(admin.ModelAdmin):
    list_display = (
        "proje", "poz", "yil", "planlanan_miktar", "gercek_miktar",
        "planlanan_baslangic", "planlanan_bitis", "birim_fiyat_snapshot", "is_active",
    )
    list_filter = ("yil", "is_active", "proje")
    search_fields = ("proje__proje_kodu", "poz__poz_no", "poz__ad")
    readonly_fields = ("birim_fiyat_snapshot",)
    date_hierarchy = "planlanan_baslangic"


@admin.register(Hakedis)
class Hakedisadmin(admin.ModelAdmin):
    list_display = ("proje", "donem", "cari", "durum", "onay_tarihi")
    list_filter = ("durum", "proje")
    search_fields = ("proje__proje_kodu", "donem")
    readonly_fields = ("cari_hareket", "muhasebe_fisi", "onaylayan", "onay_tarihi")

    def get_readonly_fields(self, request, obj=None):
        # FAZ 6C: onaylı/iptal hakedişte çekirdek alanlar admin'de de kilitli.
        if obj is not None and obj.durum != Hakedis.Durum.TASLAK:
            return (
                "proje", "donem", "cari", "durum",
                "cari_hareket", "muhasebe_fisi", "onaylayan", "onay_tarihi",
            )
        return super().get_readonly_fields(request, obj)


@admin.register(HakedisSatiri)
class HakedisSatiriadmin(admin.ModelAdmin):
    list_display = ("hakedis", "poz", "miktar", "birim_fiyat")
    search_fields = ("hakedis__proje__proje_kodu", "poz__poz_no")

    def get_readonly_fields(self, request, obj=None):
        # FAZ 6C: onaylı/iptal hakedişin satırları admin'de salt okunur.
        if obj is not None and obj.hakedis.durum != Hakedis.Durum.TASLAK:
            return ("hakedis", "poz", "miktar", "birim_fiyat")
        return super().get_readonly_fields(request, obj)


@admin.register(SantiyeGunlugu)
class SantiyeGunluguadmin(admin.ModelAdmin):
    list_display = ("proje", "tarih", "hava_durumu", "created_by")
    list_filter = ("tarih", "proje")
    search_fields = ("proje__proje_kodu", "yapilan_is", "sorunlar")


@admin.register(KaliteKontrol)
class KaliteKontroladmin(admin.ModelAdmin):
    list_display = ("proje", "poz", "tarih", "kontrol_tipi", "durum")
    list_filter = ("durum", "kontrol_tipi", "tarih", "proje")
    search_fields = ("proje__proje_kodu", "kontrol_tipi", "kriter")


@admin.register(Tedarikci)
class Tedarikciadmin(admin.ModelAdmin):
    list_display = ("firma_adi", "firma_kodu", "il", "ilce", "is_active")
    list_filter = ("is_active",)
    search_fields = ("firma_adi", "firma_kodu", "il")


@admin.register(MalzemeTedarikciIliskisi)
class MalzemeTedarikciIliskisiadmin(admin.ModelAdmin):
    list_display = ("malzeme", "tedarikci", "miktar", "durum")
    list_filter = ("durum",)
    search_fields = ("malzeme__ad", "tedarikci__firma_adi")


@admin.register(TedarikciTeklifi)
class TedarikciTeklifiAdmin(admin.ModelAdmin):
    list_display = ("proje", "malzeme", "tedarikci", "birim_fiyat", "toplam_tutar", "durum", "secildi", "is_active")
    list_filter = ("durum", "secildi", "is_active", "proje")
    search_fields = ("proje__proje_kodu", "malzeme__ad", "tedarikci__firma_adi")
    readonly_fields = ("toplam_tutar",)


@admin.register(TaseronSozlesi)
class TaseronSozlesiadmin(admin.ModelAdmin):
    list_display = ("proje", "taseron_firma", "tarih_baslangic", "durum")
    list_filter = ("durum", "tarih_baslangic")
    search_fields = ("proje__proje_kodu", "taseron_firma")


@admin.register(KaliteKabulTeminati)
class KaliteKabulTeminatiadmin(admin.ModelAdmin):
    list_display = ("proje", "poz", "tarih", "sonuc")
    list_filter = ("sonuc", "tarih", "proje")
    search_fields = ("proje__proje_kodu", "kriter")


@admin.register(EKB)
class EKBAdmin(admin.ModelAdmin):
    list_display = ("belge_no", "proje", "durum", "enerji_sinifi", "duzenlenme_tarihi", "gecerlilik_tarihi", "is_active")
    list_filter = ("durum", "enerji_sinifi", "is_active", "proje")
    search_fields = ("belge_no", "proje__proje_kodu", "proje__ad", "duzenleyen")


@admin.register(YfkPozVersiyon)
class YfkPozVersiyonAdmin(admin.ModelAdmin):
    list_display = ("poz_no", "ad", "birim", "grup_kodu", "versiyon", "degisiklik_turu", "yayin_tarihi", "gecerlilik_baslangic", "gecerlilik_bitis", "is_active")
    list_filter = ("degisiklik_turu", "is_active", "yayin_tarihi")
    search_fields = ("poz_no", "ad", "grup_kodu", "grup_adi")
    readonly_fields = ("created_at", "updated_at")


@admin.register(YfkFiyat)
class YfkFiyatAdmin(admin.ModelAdmin):
    list_display = ("poz_versiyon", "yil", "donem", "birim_fiyat", "kaynak", "yayin_tarihi", "gecerlilik_tarihi", "is_active")
    list_filter = ("yil", "donem", "is_active")
    search_fields = ("poz_versiyon__poz_no", "kaynak")
    readonly_fields = ("created_at", "updated_at")


@admin.register(YfkRayic)
class YfkRayicAdmin(admin.ModelAdmin):
    list_display = ("poz_versiyon", "malzeme_tipi", "malzeme_kodu", "malzeme_adi", "birim", "katsayi", "yayin_tarihi", "is_active")
    list_filter = ("malzeme_tipi", "is_active", "yayin_tarihi")
    search_fields = ("poz_versiyon__poz_no", "malzeme_kodu", "malzeme_adi")
    readonly_fields = ("created_at", "updated_at")


@admin.register(YfkAnaliz)
class YfkAnalizAdmin(admin.ModelAdmin):
    list_display = ("poz_versiyon", "malzeme_tipi", "sira_no", "malzeme_kodu", "malzeme_adi", "birim", "miktar", "birim_fiyat", "toplam_tutar", "yayin_tarihi", "is_active")
    list_filter = ("malzeme_tipi", "is_active", "yayin_tarihi")
    search_fields = ("poz_versiyon__poz_no", "malzeme_kodu", "malzeme_adi")
    readonly_fields = ("toplam_tutar", "created_at", "updated_at")


@admin.register(YfkGuncellemeGecmisi)
class YfkGuncellemeGecmisiAdmin(admin.ModelAdmin):
    list_display = ("islem_turu", "yil", "donem", "kaynak", "durum", "islenen_satir", "olusturulan_poz", "guncellenen_poz", "olusturulan_fiyat", "guncellenen_fiyat", "olusturulan_rayic", "guncellenen_rayic", "olusturulan_analiz", "guncellenen_analiz", "baslangic_zamani", "bitis_zamani")
    list_filter = ("islem_turu", "durum", "yil", "donem")
    search_fields = ("kaynak", "dosya_adi", "hata_mesaji")
    readonly_fields = ("baslangic_zamani", "bitis_zamani")




