"""Finans yardımcıları: maskeleme ve tenant içi kod üretimi."""

from django.db import transaction


def mask_sensitive_data(value: str | None, chars_to_show: int = 4) -> str | None:
    if not value:
        return None
    if len(value) <= chars_to_show * 2:
        return "*" * len(value)
    hidden = "*" * (len(value) - chars_to_show * 2)
    return f"{value[:chars_to_show]}{hidden}{value[-chars_to_show:]}"


def generate_friendly_code(model_type: str, tenant_id: int, prefix: str, max_digits: int = 6) -> str:
    from cari.models import Cari
    from finance.models import Fatura

    with transaction.atomic():
        model = Cari if model_type == "cari" else Fatura
        field = "ad" if model_type == "cari" else "No"
        last = model.objects.filter(tenant_id=tenant_id).order_by(f"-{field}").values_list(field, flat=True).first()
        next_number = 1
        if last:
            digits = "".join(character for character in str(last) if character.isdigit())
            if digits:
                next_number = int(digits[-max_digits:]) + 1
        return f"{prefix}-{next_number:0{max_digits}d}"
