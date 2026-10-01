"""Faturaları gerçek fişe dokunmadan finansal olay olarak kaydetme."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError

from accounting.models import HesapPlani

from ..models import Fatura, FinansalOlay
from .finansal_olay import finansal_olay_olustur


def fatura_shadow_muhasebelestir(
    fatura: Fatura,
    *,
    tenant_id: int,
) -> FinansalOlay:
    if fatura.tenant_id != tenant_id:
        raise ValidationError("Fatura farklı tenant'a ait.")
    if fatura.durum == Fatura.DurumChoices.CANCELLED:
        raise ValidationError("İptal edilmiş fatura shadow muhasebeleştirilemez.")
    if fatura.fatura_turu == "proforma":
        raise ValidationError("Proforma fatura muhasebeleştirilemez.")

    toplam = Decimal(str(fatura_toplam(fatura)))
    if not fatura.kalemler.exists():
        toplam = Decimal(str(fatura.tutar))
    cari_kodu = "120" if fatura.alacakli else "320"
    karsilik_kodu = "600" if fatura.alacakli else "770"
    hesaplar = HesapPlani.objects.filter(
        tenant_id=tenant_id,
        kod__in=(cari_kodu, karsilik_kodu),
        is_active=True,
        detay_hesap_mi=True,
    )
    hesap_map = {hesap.kod: hesap for hesap in hesaplar}
    if len(hesap_map) != 2:
        raise ValidationError(
            f"Shadow muhasebeleştirme için {cari_kodu} ve {karsilik_kodu} hesapları gereklidir."
        )

    if fatura.alacakli:
        satirlar = [
            {"hesap_id": hesap_map[cari_kodu].id, "borc": toplam, "alacak": 0},
            {"hesap_id": hesap_map[karsilik_kodu].id, "borc": 0, "alacak": toplam},
        ]
    else:
        satirlar = [
            {"hesap_id": hesap_map[karsilik_kodu].id, "borc": toplam, "alacak": 0},
            {"hesap_id": hesap_map[cari_kodu].id, "borc": 0, "alacak": toplam},
        ]
    return finansal_olay_olustur(
        tenant_id=tenant_id,
        olay_turu="fatura_shadow_posting",
        kaynak_turu="finance.Fatura",
        kaynak_id=fatura.pk,
        olay_anahtari=f"fatura:{fatura.pk}:shadow-posting",
        tarih=fatura.tarih,
        satirlar=satirlar,
        aciklama=f"{fatura.No} shadow muhasebeleştirme",
    )


def fatura_toplam(fatura: Fatura) -> str:
    from .fatura_hesaplama import fatura_toplam_hesapla

    return fatura_toplam_hesapla(fatura)["genel_toplam"]
