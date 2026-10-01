"""Muhasebe uygulama servisleri: hesap ve dengeli fiş üretimi."""

from decimal import Decimal

from django.db import transaction

from .models import FisSatiri, HesapPlani, MuhasebeFisi


class AccountingService:
    @staticmethod
    @transaction.atomic
    def auto_create_account(tenant_id, account_type, base_code, description):
        mevcut = HesapPlani.objects.filter(tenant_id=tenant_id, kod__startswith=f"{base_code}.").order_by("-kod").first()
        suffix = 1
        if mevcut:
            digits = "".join(character for character in mevcut.kod.rsplit(".", 1)[-1] if character.isdigit())
            suffix = int(digits or "0") + 1
        hesap = HesapPlani.objects.create(
            tenant_id=tenant_id, kod=f"{base_code}.{suffix:03d}", ad=description, tip="aktif"
        )
        return {"success": True, "account_id": hesap.id, "account_code": hesap.kod}

    @staticmethod
    @transaction.atomic
    def create_voucher_from_invoice(fatura):
        if fatura.durum == "iptal":
            raise ValueError("İptal edilmiş fatura muhasebeleştirilemez.")
        mevcut = MuhasebeFisi.objects.filter(
            tenant_id=fatura.tenant_id, fis_no=f"FAT-{fatura.No}"
        ).first()
        if mevcut is not None:
            return {"success": True, "fis": mevcut, "message": "Fiş zaten mevcut."}
        if not fatura.kasa_banka_hesabi_id:
            raise ValueError("Muhasebeleştirme için kasa/banka hesabı zorunludur.")
        tenant_id = fatura.tenant_id
        cari_kodu = "120" if fatura.alacakli else "320"
        cari_hesap = HesapPlani.objects.filter(tenant_id=tenant_id, kod=cari_kodu).first()
        if cari_hesap is None:
            cari_hesap = HesapPlani.objects.create(
                tenant_id=tenant_id, kod=cari_kodu,
                ad="Alıcılar" if fatura.alacakli else "Satıcılar", tip="aktif" if fatura.alacakli else "pasif",
            )
        fis = MuhasebeFisi.objects.create(
            tenant_id=tenant_id, fis_no=f"FAT-{fatura.No}", fis_tarihi=fatura.tarih,
            aciklama=fatura.aciklama or fatura.No, durum=MuhasebeFisi.Durum.KAYITLI,
        )
        tutar = Decimal(fatura.tutar)
        FisSatiri.objects.create(fis=fis, hesap=cari_hesap, borc=tutar if fatura.alacakli else Decimal("0"), alacak=Decimal("0") if fatura.alacakli else tutar)
        if fatura.kasa_banka_hesabi:
            karsilik, _ = HesapPlani.objects.get_or_create(
                tenant_id=tenant_id, kod="100", defaults={"ad": "Kasa", "tip": "aktif"}
            )
            FisSatiri.objects.create(fis=fis, hesap=karsilik, borc=Decimal("0") if fatura.alacakli else tutar, alacak=tutar if fatura.alacakli else Decimal("0"))
        return {"success": True, "fis": fis, "message": "Fatura muhasebe fişine aktarıldı."}
