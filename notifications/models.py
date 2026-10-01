from django.conf import settings
from django.db import models
from django.utils import timezone

from tenants.models import Tenant


class Hatirlatma(models.Model):
    """Mevcut construction.hatirlatma tablosunun notifications API görünümü."""

    baslik = models.CharField(max_length=255)
    aciklama = models.TextField(blank=True)
    ilgili_app = models.CharField(max_length=80, db_column="ilgili_modul")
    ilgili_model = models.CharField(max_length=120, db_column="ilgili_kayit_tipi", blank=True)
    ilgili_kayit_id = models.PositiveBigIntegerField(null=True, blank=True)
    hatirlatma_tarihi = models.DateField()
    seviye = models.CharField(max_length=10)
    durum = models.CharField(max_length=12)
    sorumlu_kullanici = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_column="sorumlu_kullanici_id",
        related_name="+",
    )
    tekrarlama = models.CharField(max_length=10, db_column="tekrarlama_tipi", default="yok")
    tekrarlama_gun = models.PositiveSmallIntegerField(default=0)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, db_column="tenant_id", related_name="+")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "construction_hatirlatma"
        ordering = ["hatirlatma_tarihi", "-created_at"]


class HatirlatmaKurali(models.Model):
    """Mevcut construction.hatirlatmakurali tablosunun notifications görünümü."""

    ilgili_app = models.CharField(max_length=80, db_column="ilgili_modul")
    ilgili_model = models.CharField(max_length=120, blank=True, default="")
    tetikleyici_alan = models.CharField(max_length=80, db_column="tetikleyici")
    once_gun = models.PositiveSmallIntegerField(db_column="once_gun_sayisi")
    seviye = models.CharField(max_length=10)
    baslik_sablonu = models.CharField(max_length=255, blank=True, default="")
    aktif_mi = models.BooleanField(default=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, db_column="tenant_id", related_name="+")
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "construction_hatirlatmakurali"
        ordering = ["ilgili_app", "once_gun"]
