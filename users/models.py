from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    """Rol listesi (02-VERI-MODELI.md §3 ilişki diyagramı)."""

    SUPER_ADMIN = "super_admin", "Süper Admin"
    TENANT_ADMIN = "tenant_admin", "Tenant Admin"
    FIRMA_ADMIN = "firma_admin", "Firma Admin"
    MUHASEBE = "muhasebe", "Muhasebe"
    FINANS = "finans", "Finans"
    PROJE_YONETICISI = "proje_yoneticisi", "Proje Yöneticisi"
    SATIS = "satis", "Satış"
    SANTIYE_SEFI = "santiye_sefi", "Şantiye Şefi"      # roadmap Faz 1 — inşaat
    MALIYET_MUHENDISI = "maliyet_muhendisi", "Maliyet Mühendisi"  # roadmap Faz 1
    KULLANICI = "kullanici", "Kullanıcı"


class User(AbstractUser):
    """Özel kullanıcı modeli — tenant bazlı, rol destekli."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Tenant",
        help_text="Süper admin dışındaki kullanıcılar için zorunludur.",
    )
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.KULLANICI,
        verbose_name="Rol",
    )
    email = models.EmailField(unique=True, verbose_name="E-posta")

    class Meta:
        verbose_name = "Kullanıcı"
        verbose_name_plural = "Kullanıcılar"
        ordering = ["username"]

    def __str__(self) -> str:
        return self.get_full_name() or self.username


class LoginDenemesi(models.Model):
    """FAZ 6F-1 — kullanıcı adı bazlı kalıcı başarısız-login sayacı.

    IP değişse de aynı kullanıcı adı kilitli kalır (hesap kilidi).
    Başarılı login'de kayıt silinir; sayaç yalnızca bu tabloda tutulur.
    """

    kullanici_adi = models.CharField(
        max_length=150, unique=True, verbose_name="Kullanıcı Adı (küçük harf)",
    )
    basarisiz_sayisi = models.PositiveIntegerField(
        default=0, verbose_name="Başarısız Sayısı",
    )
    kilit_bitis = models.DateTimeField(
        null=True, blank=True, verbose_name="Kilit Bitişi",
    )
    guncellendi = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Login Denemesi"
        verbose_name_plural = "Login Denemeleri"

    def __str__(self) -> str:
        return f"{self.kullanici_adi} ({self.basarisiz_sayisi})"
