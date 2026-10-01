"""Dengeli finansal olay oluşturma servisi."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import FinansalOlay, FinansalOlayLog, FinansalOlaySatiri


@transaction.atomic
def finansal_olay_olustur(
    *,
    tenant_id: int,
    olay_turu: str,
    kaynak_turu: str,
    kaynak_id: int,
    olay_anahtari: str,
    tarih,
    satirlar: list[dict],
    aciklama: str = "",
) -> FinansalOlay:
    mevcut = FinansalOlay.objects.filter(
        tenant_id=tenant_id,
        olay_anahtari=olay_anahtari,
    ).first()
    if mevcut:
        return mevcut
    if not satirlar:
        raise ValidationError("Finansal olay en az iki satır içermelidir.")

    borc = sum((Decimal(str(s["borc"])) for s in satirlar), Decimal("0"))
    alacak = sum((Decimal(str(s["alacak"])) for s in satirlar), Decimal("0"))
    if borc <= 0 or borc != alacak:
        raise ValidationError("Finansal olayda borç ve alacak eşit ve pozitif olmalıdır.")

    olay, created = FinansalOlay.objects.get_or_create(
        tenant_id=tenant_id,
        olay_anahtari=olay_anahtari,
        defaults={
            "olay_turu": olay_turu,
            "kaynak_turu": kaynak_turu,
            "kaynak_id": kaynak_id,
            "tarih": tarih,
            "aciklama": aciklama,
            "durum": FinansalOlay.Durum.KAYITLI,
        },
    )
    if not created:
        return olay

    for satir in satirlar:
        if Decimal(str(satir["borc"])) > 0 and Decimal(str(satir["alacak"])) > 0:
            raise ValidationError("Bir finansal olay satırı hem borç hem alacak olamaz.")
        FinansalOlaySatiri.objects.create(
            olay=olay,
            hesap_id=satir["hesap_id"],
            borc=satir["borc"],
            alacak=satir["alacak"],
            aciklama=satir.get("aciklama", ""),
        )
    FinansalOlayLog.objects.create(
        tenant_id=tenant_id,
        olay=olay,
        islem="olustur",
        durum=olay.durum,
        veri={"kaynak_turu": kaynak_turu, "kaynak_id": kaynak_id},
    )
    return olay
