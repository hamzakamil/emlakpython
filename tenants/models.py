from django.db import models


class Tenant(models.Model):
    """Kök kuruluş — tüm veriler bir Tenant'a bağlanır (02-VERI-MODELI.md)."""

    name = models.CharField(max_length=150, verbose_name="Firma Adı")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Kısa Ad")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")

    # Tenant başına limitler (02-VERI-MODELI.md §1)
    max_users = models.PositiveIntegerField(default=5, verbose_name="Maksimum Kullanıcı")
    max_projects = models.PositiveIntegerField(default=1, verbose_name="Maksimum Proje")
    max_storage_gb = models.PositiveIntegerField(default=5, verbose_name="Maksimum Depolama (GB)")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenantlar"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class TenantAwareModel(models.Model):
    """Multi-tenant izolasyon çekirdeği.

    Her tenant'a bağlı model bu sınıftan türer; tenant seçimi middleware /
    permission / queryset katmanında otomatik uygulanır (01-GELISTIRME-KURALLARI.md §1).
    """

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="Tenant",
    )

    class Meta:
        abstract = True
        indexes = [models.Index(fields=["tenant"])]
