from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from tenants.models import TenantAwareModel


class HesapTipi(models.TextChoices):
    AKTIF = "aktif", "Aktif"
    PASIF = "pasif", "Pasif"
    GELIR = "gelir", "Gelir"
    GIDER = "gider", "Gider"
    NAZIM = "nazim", "Nazım"


class NormalBakiye(models.TextChoices):
    BORC = "borc", "Borç"
    ALACAK = "alacak", "Alacak"


class HesapPlani(TenantAwareModel):
    """Hesap planı — 100 Kasa, 102 Bankalar, 120 Alıcılar vb. (03-IS-AKISLARI.md §2)."""

    kod = models.CharField(max_length=20, verbose_name="Hesap Kodu")
    ad = models.CharField(max_length=200, verbose_name="Hesap Adı")
    tip = models.CharField(
        max_length=10, choices=HesapTipi.choices, default=HesapTipi.AKTIF, verbose_name="Hesap Tipi"
    )
    ust_hesap = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="alt_hesaplar",
        verbose_name="Üst Hesap",
    )
    seviye = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="Hesap Seviyesi",
        help_text="1 ana sınıf, 2 hesap grubu, 3 ana hesap ve alt seviyeler.",
    )
    normal_bakiye = models.CharField(
        max_length=6,
        choices=NormalBakiye.choices,
        null=True,
        blank=True,
        verbose_name="Normal Bakiye",
    )
    detay_hesap_mi = models.BooleanField(
        default=True,
        verbose_name="Detay Hesap mı?",
        help_text="Muhasebe fişi satırında doğrudan kullanılabilir alt hesap.",
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")

    class Meta:
        verbose_name = "Hesap Planı"
        verbose_name_plural = "Hesap Planı"
        ordering = ["kod"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "kod"], name="uniq_hesap_tenant_kod"),
        ]

    def __str__(self) -> str:
        return f"{self.kod} — {self.ad}"


class MuhasebeFisi(TenantAwareModel):
    """Muhasebe fişi — çift kayıt; borç == alacak kayıt öncesi doğrulanır.

    Fiziksel DELETE yok: iptal için durum=iptal + ters kayıt açıklaması.
    """

    class Durum(models.TextChoices):
        TASLAK = "taslak", "Taslak"
        KAYITLI = "kayitli", "Kayıtlı"
        IPTAL = "iptal", "İptal"

    fis_no = models.CharField(max_length=30, verbose_name="Fiş No")
    fis_tarihi = models.DateField(verbose_name="Fiş Tarihi")
    aciklama = models.CharField(max_length=255, blank=True, verbose_name="Açıklama")
    durum = models.CharField(
        max_length=10, choices=Durum.choices, default=Durum.TASLAK, verbose_name="Durum"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")

    class Meta:
        verbose_name = "Muhasebe Fişi"
        verbose_name_plural = "Muhasebe Fişleri"
        ordering = ["-fis_tarihi", "fis_no"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "fis_no"], name="uniq_fis_tenant_no"),
        ]

    def __str__(self) -> str:
        return f"{self.fis_no} ({self.fis_tarihi})"

    def clean(self) -> None:
        satirlar = list(self.satirlar.all()) if self.pk else []
        if satirlar:
            toplam_borc = sum((s.borc for s in satirlar), Decimal("0"))
            toplam_alacak = sum((s.alacak for s in satirlar), Decimal("0"))
            if toplam_borc != toplam_alacak:
                raise ValidationError("Muhasebe fişinde borç ve alacak eşit olmalıdır.")
            if toplam_borc <= 0:
                raise ValidationError("Fiş tutarı 0'dan büyük olmalıdır.")


class FisSatiri(models.Model):
    """Fiş satırı — hesap + borç/alacak (fiş üzerinden tenant'a bağlı)."""

    fis = models.ForeignKey(
        MuhasebeFisi, on_delete=models.PROTECT, related_name="satirlar", verbose_name="Fiş",
    )
    hesap = models.ForeignKey(
        HesapPlani, on_delete=models.PROTECT, related_name="satirlar", verbose_name="Hesap",
    )
    borc = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))], verbose_name="Borç (₺)",
    )
    alacak = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))], verbose_name="Alacak (₺)",
    )
    aciklama = models.CharField(max_length=255, blank=True, verbose_name="Açıklama")

    class Meta:
        verbose_name = "Fiş Satırı"
        verbose_name_plural = "Fiş Satırları"

    def __str__(self) -> str:
        return f"{self.fis.fis_no} / {self.hesap.kod}: {self.borc} / {self.alacak}"

    def clean(self) -> None:
        if self.borc < 0 or self.alacak < 0:
            raise ValidationError("Borç/alacak negatif olamaz.")
        if self.borc > 0 and self.alacak > 0:
            raise ValidationError("Bir satırda hem borç hem alacak olamaz.")
        if self.borc == 0 and self.alacak == 0:
            raise ValidationError("Satır tutarı 0 olamaz.")
