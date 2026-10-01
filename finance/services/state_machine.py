"""Finans durum geçişleri için merkezi ve açık kurallar."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import Fatura


FATURA_TRANSITIONS = {
    Fatura.DurumChoices.DRAFT: frozenset({Fatura.DurumChoices.ACTIVE, Fatura.DurumChoices.CANCELLED}),
    Fatura.DurumChoices.ACTIVE: frozenset({Fatura.DurumChoices.PAID, Fatura.DurumChoices.CANCELLED}),
    Fatura.DurumChoices.PAID: frozenset({Fatura.DurumChoices.CANCELLED}),
    Fatura.DurumChoices.CANCELLED: frozenset(),
}


@transaction.atomic
def fatura_durum_gecis(fatura_id: int, hedef_durum: str, *, tenant_id: int) -> Fatura:
    fatura = Fatura.objects.select_for_update().get(pk=fatura_id, tenant_id=tenant_id)
    izinli = FATURA_TRANSITIONS.get(fatura.durum, frozenset())
    if hedef_durum not in Fatura.DurumChoices.values:
        raise ValidationError({"durum": "Geçersiz fatura durumu."})
    if hedef_durum not in izinli:
        raise ValidationError(
            {"durum": f"{fatura.durum} durumundan {hedef_durum} durumuna geçilemez."}
        )
    fatura.durum = hedef_durum
    fatura.save(update_fields=["durum", "updated_at"])
    return fatura
