"""Poz analiz ve nakliye hesapları."""

from decimal import Decimal

from ..models import Poz, PozAnaliz


def nakliye_hesapla(poz: Poz, mesafe_km, k) -> Decimal:
    """Poz birimi için OSKA/AMP tarzı nakliye tutarı."""
    birim = PozAnaliz.objects.filter(
        poz=poz, tenant_id=poz.tenant_id, analiz_tipi=PozAnaliz.AnalizTipi.NAKLIYE,
    ).order_by("satir_no").values_list("birim_fiyat", flat=True).first()
    if birim is None:
        raise ValueError("Poz için nakliye analiz birim fiyatı bulunamadı.")
    return (Decimal("0.00017") * Decimal(str(k)) * Decimal(str(mesafe_km)) * birim).quantize(Decimal("0.01"))


def poz_analiz_toplam(poz_id: int) -> Decimal:
    toplam = sum(
        (satir.tutar for satir in PozAnaliz.objects.filter(poz_id=poz_id)),
        Decimal("0"),
    )
    return toplam.quantize(Decimal("0.01"))


def poz_birim_fiyat_analizden_hesapla(poz_id: int) -> Decimal:
    return poz_analiz_toplam(poz_id)
