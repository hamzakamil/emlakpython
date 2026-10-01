"""Idempotent finansal işlem yardımcıları."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from django.db import IntegrityError, transaction
from django.utils import timezone

from ..models import IdempotencyKey

log = logging.getLogger("erp.idempotency")


class IdempotencyConflict(Exception):
    """Aynı anahtar farklı istek veya devam eden işlem için kullanıldı."""


def request_hash(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


@contextmanager
def idempotent_operation(
    *,
    tenant_id: int,
    operation: str,
    key: str,
    payload: object,
) -> Iterator[IdempotencyKey]:
    """İşlem kaydını kilitleyerek aynı anahtarın tek kez işlenmesini sağlar."""
    digest = request_hash(payload)
    try:
        with transaction.atomic():
            record, created = IdempotencyKey.objects.select_for_update().get_or_create(
                tenant_id=tenant_id,
                operation=operation,
                key=key,
                defaults={"request_hash": digest},
            )
            if not created:
                if record.request_hash != digest:
                    log.warning(
                        "event=idempotency_conflict operation=%s key=%s sebep=hash",
                        operation, key,
                        extra={"tenant_id": tenant_id, "operation": operation,
                               "resource_id": "-"},
                    )
                    raise IdempotencyConflict("Idempotency anahtarı farklı istekle kullanıldı.")
                if record.status == IdempotencyKey.Durum.COMPLETED:
                    yield record
                    return
                if record.status == IdempotencyKey.Durum.PROCESSING:
                    log.warning(
                        "event=idempotency_conflict operation=%s key=%s sebep=sürüyor",
                        operation, key,
                        extra={"tenant_id": tenant_id, "operation": operation,
                               "resource_id": "-"},
                    )
                    raise IdempotencyConflict("Aynı işlem halen yürütülüyor.")
                record.status = IdempotencyKey.Durum.PROCESSING
                record.error_message = ""
                record.save(update_fields=["status", "error_message"])
            yield record
    except IntegrityError as exc:
        log.warning(
            "event=idempotency_conflict operation=%s key=%s sebep=yarış",
            operation, key,
            extra={"tenant_id": tenant_id, "operation": operation,
                   "resource_id": "-"},
        )
        raise IdempotencyConflict("Idempotency anahtarı eşzamanlı kullanıldı.") from exc


def complete_operation(
    record: IdempotencyKey,
    *,
    response_data: dict,
    resource_type: str = "",
    resource_id: int | None = None,
) -> IdempotencyKey:
    record.status = IdempotencyKey.Durum.COMPLETED
    record.response_data = response_data
    record.resource_type = resource_type
    record.resource_id = resource_id
    record.completed_at = timezone.now()
    record.save(
        update_fields=[
            "status",
            "response_data",
            "resource_type",
            "resource_id",
            "completed_at",
        ]
    )
    return record
