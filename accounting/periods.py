"""Period Closure & Locking - Kural 33: Dönem Kılavuzu"""

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class MuhasebeDonemi(models.Model):
    """Muhasebe Dönemi Yapısı. Lifecycle: OPEN -> CLOSED -> LOCKED"""

    class Durum(models.TextChoices):
        ACIK = "aci", "Açık"
        KAPALI = "kpt", "Kapalı"
        KILITLI = "kll", "Kilitli"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        verbose_name="Kiracı",
        related_name="muhasebe_donemleri",
    )
    baslangic_tarihi = models.DateField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateField(verbose_name="Bitiş Tarihi")
    durum = models.CharField(
        max_length=10,
        choices=Durum.choices,
        default=Durum.ACI,
        verbose_name="Durum",
    )
    kapanma_tarihi = models.DateField(
        null=True, blank=True, verbose_name="Kapanma Tarihi"
    )
    kilit_tarihi = models.DateTimeField(
        null=True, blank=True, verbose_name="Kilit Zamanı"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Muhasebe Dönemi"
        verbose_name_plural = "Muhasebe Dönemleri"
        unique_together = [["tenant", "baslangic_tarihi"]]
        ordering = ["-baslangic_tarihi"]

    def __str__(self):
        return f"{self.baslangic_tarihi} - {self.bitis_tarihi} ({self.get_durum_display()})"

    @property
    def is_open(self):
        """Açık mı kontrolü."""
        return (
            self.durum == self.Durum.ACI
            and self.baslangic_tarihi
            <= timezone.now().date()
            <= self.bitis_tarihi
        )

    @property
    def is_closed(self):
        """Kapalı mı kontrolü."""
        return self.durum == self.Durum.KAPALI

    @property
    def is_locked(self):
        """Kilitli mı kontrolü."""
        return self.durum == self.Durum.KILITLI

    def close_period(self, closed_by=None):
        """Dönemi kapat - Sadece ACI durumunda."""
        if not self.is_open:
            raise ValidationError("Açık olmayan dönem kapatılamaz.")
        self.durum = self.Durum.KAPALI
        self.kapanma_tarihi = timezone.now().date()
        self.save()
        return self

    def lock_period(self, locked_by=None):
        """Dönemi kilitle - Sadece KAPALI durumunda."""
        if not self.is_closed:
            raise ValidationError("Sadece kapatılabilen dönemler kilitlenebilir.")
        self.durum = self.Durum.KILITLI
        self.kilit_tarihi = timezone.now()
        self.save()
        return self

    def can_post(self):
        """POST işlemi yapılabilir mi?"""
        return self.is_open

    def can_modify(self):
        """Düzenleme yapılabilir mi?"""
        return self.is_open or self._has_modification_permission()

    def _has_modification_permission(self):
        """Düzenleme izni var mı? (admin, audit trace vb.)."""
        return False


def get_active_period(tenant):
    """Aktif (açık) dönemi getir. Yoksa oluştur."""
    try:
        return MuhasebeDonemi.objects.get(
            tenant=tenant, durum=MuhasebeDonemi.Durum.ACI
        )
    except MuhasebeDonemi.DoesNotExist:
        from datetime import date
        baslangic = date(timezone.now().year, 1, 1)
        bitis = date(timezone.now().year, 12, 31)
        return MuhasebeDonemi.objects.create(
            tenant=tenant,
            baslangic_tarihi=baslangic,
            bitis_tarihi=bitis,
            durum=MuhasebeDonemi.Durum.ACI,
        )


def validate_period_for_post(tenant, islem_tarihi):
    """
    POST işlemi için dönem kontrolü.
    
    Returns: (is_allowed, period, error_message)
    """
    try:
        period = MuhasebeDonemi.objects.get(
            tenant=tenant,
            baslangic_tarihi__lte=islem_tarihi,
            bitis_tarihi__gte=islem_tarihi,
            durum=MuhasebeDonemi.Durum.ACI,
        )
        return True, period, None
    except MuhasebeDonemi.DoesNotExist:
        active = MuhasebeDonemi.objects.filter(
            tenant=tenant, durum=MuhasebeDonemi.Durum.ACI
        ).first()

        if not active:
            return False, None, "Açık bir muhasebe dönemi bulunamadı."

        if islem_tarihi < active.baslangic_tarihi or islem_tarihi > active.bitis_tarihi:
            return (
                False,
                None,
                f"İşlem tarihi ({islem_tarihi}) aktif dönem ({active.baslangic_tarihi} - {active.bitis_tarihi}) içinde değil.",
            )

        if active.is_locked:
            return (
                False,
                None,
                f"Dönem kilitli ({active.kilit_tarih}). Yönetici onayı gerektiriyor.",
            )

        if active.is_closed:
            return (
                False,
                None,
                f"Dönem kapalı ({active.kapanma_tarihi}). Yönetici onayı gerektiriyor.",
            )

        return False, None, "Bilinmeyen hata."
