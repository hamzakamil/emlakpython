"""Cari kartı için tenant güvenli uygulama servisleri."""

from django.db import transaction
from decimal import Decimal
from django.core.exceptions import ValidationError

from accounting.models import FisSatiri, HesapPlani, MuhasebeFisi

from .models import Cari, CariHareket


class CariService:
    @staticmethod
    @transaction.atomic
    def cari_olustur(form_data, user):
        cari = Cari.objects.create(
            tenant=user.tenant,
            ad=form_data["ad"].strip(),
            tip=form_data.get("tip", "diger"),
            tur=form_data.get("tur", "bireysel"),
            vergi_no=form_data.get("vergi_no", "").strip(),
            vergi_dairesi=form_data.get("vergi_dairesi", "").strip(),
            telefon=form_data.get("telefon", "").strip(),
            iban=form_data.get("iban", "").strip(),
            adres=form_data.get("adres", "").strip(),
            is_active=form_data.get("is_active", True),
        )
        return {"success": True, "cari": cari, "message": "Cari başarıyla oluşturuldu."}

    @staticmethod
    @transaction.atomic
    def cari_guncelle(cari_id, form_data, user):
        cari = Cari.objects.get(id=cari_id, tenant_id=user.tenant_id)
        for alan in ("ad", "tip", "tur", "vergi_no", "vergi_dairesi", "telefon", "iban", "adres", "is_active"):
            if alan in form_data:
                setattr(cari, alan, form_data[alan])
        cari.save()
        return {"success": True, "cari": cari, "message": "Cari güncellendi."}


@transaction.atomic
def cari_hareketi_muhasebelestir(hareket_id: int, *, tenant_id: int) -> CariHareket:
    hareket = (
        CariHareket.objects.select_for_update()
        .select_related("cari")
        .get(pk=hareket_id, tenant_id=tenant_id)
    )
    if hareket.muhasebe_fisi_id:
        return hareket
    if hareket.is_cancelled:
        raise ValidationError("İptal edilmiş cari hareket muhasebeleştirilemez.")
    if hareket.tutar <= 0:
        raise ValidationError("Cari hareket tutarı pozitif olmalıdır.")

    cari_kodu = hareket.cari.muhasebe_hesap_kodu.strip() or (
        "120" if hareket.yon == CariHareket.Yon.BORC else "320"
    )
    cari_hesap, _ = HesapPlani.objects.get_or_create(
        tenant_id=tenant_id,
        kod=cari_kodu,
        defaults={"ad": hareket.cari.ad[:200], "tip": "aktif", "detay_hesap_mi": True},
    )
    karsilik_hesap, _ = HesapPlani.objects.get_or_create(
        tenant_id=tenant_id,
        kod="770",
        defaults={"ad": "Cari Hareket Karşılık Hesabı", "tip": "gider", "detay_hesap_mi": True},
    )
    fis = MuhasebeFisi.objects.create(
        tenant_id=tenant_id,
        fis_no=f"CH-{hareket.pk}",
        fis_tarihi=hareket.islem_tarihi,
        aciklama=hareket.aciklama or f"Cari hareket #{hareket.pk}",
        durum=MuhasebeFisi.Durum.KAYITLI,
    )
    tutar = Decimal(hareket.tutar)
    cari_borc = hareket.yon == CariHareket.Yon.BORC
    FisSatiri.objects.create(
        fis=fis, hesap=cari_hesap,
        borc=tutar if cari_borc else Decimal("0"),
        alacak=Decimal("0") if cari_borc else tutar,
    )
    FisSatiri.objects.create(
        fis=fis, hesap=karsilik_hesap,
        borc=Decimal("0") if cari_borc else tutar,
        alacak=tutar if cari_borc else Decimal("0"),
    )
    hareket.muhasebe_fisi = fis
    hareket.save(update_fields=["muhasebe_fisi"])
    return hareket
