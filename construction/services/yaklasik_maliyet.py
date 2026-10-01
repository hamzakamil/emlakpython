"""Yaklaşık maliyet hesaplama ve revizyon servisleri."""

from decimal import Decimal

from django.db import transaction

from ..models import PozFiyat, YaklasikMaliyet, YaklasikMaliyetSatiri

PARA = Decimal("0.01")


def aktif_poz_fiyati(*, tenant_id, poz_id, yil):
    return (
        PozFiyat.objects.filter(
            tenant_id=tenant_id, poz_id=poz_id, yil=yil, is_active=True
        ).order_by("-created_at").first()
    )


def satir_tutar(miktar, birim_fiyat):
    return (Decimal(str(miktar)) * Decimal(str(birim_fiyat))).quantize(PARA)


@transaction.atomic
def hesapla(yaklasik_maliyet: YaklasikMaliyet) -> YaklasikMaliyet:
    """Satır toplamlarını ve başlık toplamını Decimal ile yeniden hesaplar."""
    toplam = Decimal("0")
    for satir in yaklasik_maliyet.satirlar.all():
        satir.toplam_tutar = satir_tutar(satir.miktar, satir.birim_fiyat_snapshot)
        satir.save(update_fields=["toplam_tutar", "updated_at"])
        toplam += satir.toplam_tutar
    yaklasik_maliyet.toplam_tutar = toplam.quantize(PARA)
    yaklasik_maliyet.save(update_fields=["toplam_tutar", "updated_at"])
    return yaklasik_maliyet


@transaction.atomic
def revize(yaklasik_maliyet: YaklasikMaliyet, **overrides) -> YaklasikMaliyet:
    """Mevcut maliyeti değiştirmeden satırları yeni versiyona kopyalar."""
    son = (
        YaklasikMaliyet.objects.filter(
            tenant_id=yaklasik_maliyet.tenant_id,
            proje_id=yaklasik_maliyet.proje_id,
            yil=yaklasik_maliyet.yil,
        ).order_by("-versiyon").first()
    )
    if yaklasik_maliyet.is_active:
        yaklasik_maliyet.is_active = False
        yaklasik_maliyet.save(update_fields=["is_active", "updated_at"])
    yeni = YaklasikMaliyet.objects.create(
        tenant_id=yaklasik_maliyet.tenant_id,
        proje_id=yaklasik_maliyet.proje_id,
        yil=yaklasik_maliyet.yil,
        ad=overrides.get("ad", yaklasik_maliyet.ad),
        aciklama=overrides.get("aciklama", yaklasik_maliyet.aciklama),
        versiyon=(son.versiyon + 1 if son else yaklasik_maliyet.versiyon + 1),
        onceki=yaklasik_maliyet,
    )
    for satir in yaklasik_maliyet.satirlar.all():
        YaklasikMaliyetSatiri.objects.create(
            tenant_id=yeni.tenant_id, yaklasik_maliyet=yeni, poz_id=satir.poz_id,
            mahal_id=satir.mahal_id, miktar=satir.miktar,
            birim_fiyat_snapshot=satir.birim_fiyat_snapshot,
            aciklama=satir.aciklama, sira=satir.sira,
        )
    return hesapla(yeni)


def mahal_listesinden_olustur(*args, **kwargs):
    """Projedeki mahallerin üretilmiş metrajlarını maliyet satırlarına aktarır."""
    from .mahal_metraj import mahal_elemanlarindan_yaklasik_maliyet_uret

    return mahal_elemanlarindan_yaklasik_maliyet_uret(*args, **kwargs)


# Türkçe alan adıyla açık servis isimleri; kısa isimler de alt modül içindir.
yaklasik_maliyet_hesapla = hesapla
yaklasik_maliyet_revize = revize
