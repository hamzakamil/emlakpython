"""Transactional outbox yazma ve kontrollü retry işlemleri."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from ..models import OutboxEvent


def enqueue_outbox_event(
    *,
    tenant_id: int,
    event_key: str,
    event_type: str,
    payload: dict,
) -> OutboxEvent:
    event, _ = OutboxEvent.objects.get_or_create(
        tenant_id=tenant_id,
        event_key=event_key,
        defaults={
            "event_type": event_type,
            "payload": payload,
        },
    )
    return event


@transaction.atomic
def process_outbox_events(
    *,
    limit: int = 100,
    handlers: dict[str, Callable[[dict], None]] | None = None,
) -> dict[str, int]:
    handlers = handlers or {}
    events = list(
        OutboxEvent.objects.select_for_update()
        .filter(
            status__in=(OutboxEvent.Durum.PENDING, OutboxEvent.Durum.RETRY),
            available_at__lte=timezone.now(),
        )
        .order_by("created_at")[:limit]
    )
    result = {"completed": 0, "retry": 0, "dead_letter": 0}
    for event in events:
        event.status = OutboxEvent.Durum.PROCESSING
        event.attempts += 1
        event.save(update_fields=["status", "attempts"])
        handler = handlers.get(event.event_type)
        try:
            if handler is None:
                raise RuntimeError(f"Outbox handler bulunamadı: {event.event_type}")
            handler(event.payload)
        except Exception as exc:
            event.last_error = str(exc)
            if event.attempts >= event.max_attempts:
                event.status = OutboxEvent.Durum.DEAD_LETTER
                result["dead_letter"] += 1
            else:
                event.status = OutboxEvent.Durum.RETRY
                event.available_at = timezone.now() + timedelta(minutes=event.attempts)
                result["retry"] += 1
            event.save(update_fields=["status", "available_at", "last_error"])
        else:
            event.status = OutboxEvent.Durum.COMPLETED
            event.processed_at = timezone.now()
            event.save(update_fields=["status", "processed_at"])
            result["completed"] += 1
    return result
