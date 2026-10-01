"""Fatura/cari ve finansal işlem/muhasebe entegrasyon servisleri."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from accounting.models import FisSatiri, HesapPlani, MuhasebeFisi
from cari.models import CariHareket

from ..models import Fatura, FinansalIslem


@transaction.atomic
def fatura_cari_hareketi_olustur(fatura: Fatura) -> CariHareket:
    if not fatura.cari_id:
        raise ValidationError("Cari hareketi için fatura cari hesabına bağlı olmalıdır.")
    if fatura.durum == Fatura.DurumChoices.CANCELLED:
        raise ValidationError("İptal faturadan cari hareket oluşturulamaz.")
    hareket, _ = CariHareket.objects.get_or_create(
        tenant_id=fatura.tenant_id,
        fatura=fatura,
        defaults={
            "cari_id": fatura.cari_id,
            "yon": CariHareket.Yon.BORC if fatura.alacakli else CariHareket.Yon.ALACAK,
            "tutar": fatura.tutar,
            "aciklama": f"{fatura.No} kaynaklı cari hareket",
            "islem_tarihi": fatura.tarih,
        },
    )
    return hareket


@transaction.atomic
def finansal_islem_muhasebelestir(
    islem: FinansalIslem,
    *,
    karsilik_hesap_id: int,
) -> MuhasebeFisi:
    if islem.muhasebe_fisi_id:
        return islem.muhasebe_fisi
    if islem.is_cancelled:
        raise ValidationError("İptal edilmiş finansal işlem muhasebeleştirilemez.")
    if islem.tutar <= 0:
        raise ValidationError("Finansal işlem tutarı pozitif olmalıdır.")
    karsilik = HesapPlani.objects.get(
        pk=karsilik_hesap_id,
        tenant_id=islem.tenant_id,
        is_active=True,
    )
    kasa_hesap, _ = HesapPlani.objects.get_or_create(
        tenant_id=islem.tenant_id,
        kod=islem.hesap.kod,
        defaults={"ad": islem.hesap.ad, "tip": "aktif"},
    )
    fis = MuhasebeFisi.objects.create(
        tenant_id=islem.tenant_id,
        fis_no=f"FIN-{islem.pk}",
        fis_tarihi=islem.islem_tarihi,
        aciklama=islem.aciklama,
        durum=MuhasebeFisi.Durum.KAYITLI,
    )
    kasa_borc = islem.yon == FinansalIslem.Yon.GELIR
    FisSatiri.objects.create(
        fis=fis,
        hesap=kasa_hesap,
        borc=islem.tutar if kasa_borc else Decimal("0"),
        alacak=Decimal("0") if kasa_borc else islem.tutar,
    )
    FisSatiri.objects.create(
        fis=fis,
        hesap=karsilik,
        borc=Decimal("0") if kasa_borc else islem.tutar,
        alacak=islem.tutar if kasa_borc else Decimal("0"),
    )
    islem.muhasebe_fisi = fis
    islem.save(update_fields=["muhasebe_fisi"])
    return fis


@transaction.atomic
def finansal_islem_iptal(islem_id: int, *, tenant_id: int, neden: str = "") -> dict:
    """Ödeme iptali: ters cari hareket + ters fiş (idempotent).

    Zaten iptal edilmiş işlemde mevcut ters kayıtlar dönülür (yenisi açıldez).
    Fiziksel DELETE yok; orijinal fiş IPTAL durumuna çekilir.
    """
    islem = FinansalIslem.objects.select_for_update().get(
        pk=islem_id, tenant_id=tenant_id
    )
    sonuc: dict = {"islem": islem, "ters_cari": None, "ters_fis": None}
    if islem.is_cancelled:
        sonuc["ters_cari"] = CariHareket.objects.filter(finansal_islem=islem).first()
        if islem.muhasebe_fisi_id:
            sonuc["ters_fis"] = MuhasebeFisi.objects.filter(
                tenant_id=tenant_id, fis_no=f"FINTR-{islem.pk}"
            ).first()
        sonuc["zaten_iptal"] = True
        return sonuc
    if islem.cari_id:
        ters_yon = (
            CariHareket.Yon.BORC
            if islem.yon == FinansalIslem.Yon.GIDER
            else CariHareket.Yon.ALACAK
        )
        ters_cari, _ = CariHareket.objects.get_or_create(
            tenant_id=tenant_id,
            finansal_islem=islem,
            defaults={
                "cari_id": islem.cari_id,
                "yon": ters_yon,
                "tutar": islem.tutar,
                "aciklama": f"İptal: {islem.aciklama or islem.hesap.kod}",
                "islem_tarihi": islem.islem_tarihi,
            },
        )
        sonuc["ters_cari"] = ters_cari
    if islem.muhasebe_fisi_id:
        ters_fis = MuhasebeFisi.objects.filter(
            tenant_id=tenant_id, fis_no=f"FINTR-{islem.pk}"
        ).first()
        if ters_fis is None:
            original = islem.muhasebe_fisi
            ters_fis = MuhasebeFisi.objects.create(
                tenant_id=tenant_id,
                fis_no=f"FINTR-{islem.pk}",
                fis_tarihi=original.fis_tarihi,
                aciklama=f"TERS KAYIT: {original.aciklama}",
                durum=MuhasebeFisi.Durum.KAYITLI,
            )
            for satir in original.satirlar.all():
                FisSatiri.objects.create(
                    fis=ters_fis, hesap=satir.hesap,
                    borc=satir.alacak, alacak=satir.borc,
                )
        original = islem.muhasebe_fisi
        if original.durum != MuhasebeFisi.Durum.IPTAL:
            original.durum = MuhasebeFisi.Durum.IPTAL
            original.save(update_fields=["durum"])
        sonuc["ters_fis"] = ters_fis
    islem.is_cancelled = True
    islem.save(update_fields=["is_cancelled"])
    import logging

    logging.getLogger("erp.finans").info(
        "event=odeme_iptal islem=%s", islem.pk,
        extra={"tenant_id": tenant_id, "operation": "finansal-islem.iptal",
               "resource_id": islem.pk},
    )
    return sonuc
