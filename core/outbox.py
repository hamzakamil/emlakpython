"""Outbox Event System - Kural 20: Idempotency"""

import uuid
from django.db import models
from django.utils import timezone


class OutboxEvent(models.Model):
    """Kritik olayları güvenilir bir şekilde yayınlayan outbox tablosu."""

    class EventType(models.TextChoices):
        INVOICE_POSTED = "INVOICE_POSTED", "Fatura Muhasebeleştirildi"
        PAYMENT_POSTED = "PAYMENT_POSTED", "Ödeme Muhasebeleştirildi"
        BANK_TRANSACTION_POSTED = "BANK_TRANSACTION_POSTED", "Banka Hareketi Muhasebeleştirildi"
        ACCOUNTING_VOUCHER_POSTED = "ACCOUNTING_VOUCHER_POSTED", "Muhasebe Fişi POSTED"
        ACCOUNTING_VOUCHER_REVERSED = "ACCOUNTING_VOUCHER_REVERSED", "Muhasebe Fişi Ters Kayıt"
        CARTI_CREATE = "CARTI_CREATE", "Cari Kartı Oluşturuldu"
        CARI_UPDATE = "CARI_UPDATE", "Cari Kartı Güncellendi"

    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    aggregate_type = models.CharField(max_length=50, verbose_name="Aggregate Type")
    aggregate_id = models.CharField(max_length=100, verbose_name="Aggregate ID")
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    payload = models.JSONField(default=dict, verbose_name="Payload")
    status = models.CharField(
        max_length=20,
        default="PENDING",
        choices=[
            ("PENDING", "Bekliyor"),
            ("PROCESSING", "İşleniyor"),
            ("PROCESSED", "İşlendi"),
            ("FAILED", "Başarısız"),
        ],
    )
    retry_count = models.IntegerField(default=0, verbose_name="Retry Sayısı")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="İşlenme Zamanı")
    error_message = models.TextField(blank=True, verbose_name="Hata Mesajı")

    class Meta:
        verbose_name = "Outbox Olayı"
        verbose_name_plural = "Outbox Olayları"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "processed_at"]),
            models.Index(fields=["aggregate_type", "aggregate_id"]),
        ]

    def mark_processed(self):
        """Olayı işlenmiş olarak işaretle."""
        self.status = "PROCESSED"
        self.processed_at = timezone.now()
        self.save(update_fields=["status", "processed_at", "updated_at"])

    def mark_failed(self, error_message):
        """Olayı başarısız olarak işaretle."""
        self.status = "FAILED"
        self.retry_count += 1
        self.error_message = error_message
        self.save(
            update_fields=["status", "retry_count", "error_message", "updated_at"]
        )

    @classmethod
    def create_event_if_not_exists(cls, aggregate_type, aggregate_id, event_type, payload=None):
        """
        Aynı aggregate_id + event_type kombinasyonu için duplicate event oluşturmaz.
        
        Returns: (event, created) tuple
        """
        event, created = cls.objects.get_or_create(
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            event_type=event_type,
            defaults={"payload": payload or {}, "status": "PENDING"},
        )
        return event, created