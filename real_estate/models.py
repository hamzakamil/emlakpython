from django.db import models

from tenants.models import TenantAwareModel


class Ada(TenantAwareModel):
    """Ada / parselin ait olduğu ada kartı (Faz 3: Kentsel Dönüşüm)."""

    ada_no = models.CharField(max_length=50, verbose_name="Ada No")
    mahalle = models.CharField(max_length=150, blank=True, verbose_name="Mahalle")
    ilce = models.CharField(max_length=150, blank=True, verbose_name="İlçe")
    il = models.CharField(max_length=150, blank=True, verbose_name="İl")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Ada"
        verbose_name_plural = "Adalar"
        ordering = ["il", "ilce", "mahalle", "ada_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "ada_no"],
                name="uniq_ada_no_tenant",
            )
        ]

    def __str__(self) -> str:
        return f"Ada {self.ada_no} ({self.ilce or self.il or self.mahalle or self.tenant.name})"


class Parsel(TenantAwareModel):
    """Arazi / parsel takibi için temel veri modeli (Faz 3)."""

    class ImarDurumu(models.TextChoices):
        IMARA_UYGUN = "imara_uygun", "İmara Uygun"
        IMARLI = "imarli", "İmarlı"
        IMAR_HAKKI_VERILMIS = "imar_hakki_verilmis", "İmar Hakkı Verilmiş"
        PLAN_DEGISIKLIGI = "plan_degisikligi", "Plan Değişikliği"
        BELIRSIZ = "belirsiz", "Belirsiz"

    ada = models.ForeignKey(
        Ada,
        on_delete=models.PROTECT,
        related_name="parseller",
        verbose_name="Ada",
    )
    parsel_no = models.CharField(max_length=50, verbose_name="Parsel No")
    pafta = models.CharField(max_length=50, blank=True, verbose_name="Pafta")
    alan_m2 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Alan (m²)",
    )
    imar_durumu = models.CharField(
        max_length=30,
        choices=ImarDurumu.choices,
        default=ImarDurumu.BELIRSIZ,
        verbose_name="İmar Durumu",
    )
    kat_karsiligi_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Kat Karşılığı Oranı (%)",
    )
    malik_sayisi = models.PositiveIntegerField(default=1, verbose_name="Malik Sayısı")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Parsel"
        verbose_name_plural = "Parseller"
        ordering = ["ada__ada_no", "parsel_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "ada", "parsel_no"],
                name="uniq_parsel_ada_tenant",
            )
        ]

    def __str__(self) -> str:
        return f"Ada {self.ada.ada_no} / Parsel {self.parsel_no}"


class KatKarsiligiSenaryo(TenantAwareModel):
    """Kat karşılığı senaryosu — arazi payı ve bağımsız bölüm dağılımı simülasyonu."""

    parsel = models.ForeignKey(
        Parsel,
        on_delete=models.PROTECT,
        related_name="kat_karsiligi_senaryolari",
        verbose_name="Parsel",
    )
    senaryo_adi = models.CharField(max_length=150, verbose_name="Senaryo Adı")
    arsa_pay_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Arsa Pay Oranı (%)",
    )
    kat_karsiligi_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Kat Karşılığı Oranı (%)",
    )
    bagimsiz_bolum_m2 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Bağımsız Bölüm Alanı (m²)",
    )
    toplam_birim_sayisi = models.PositiveIntegerField(default=0, verbose_name="Toplam Birim Sayısı")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Kat Karşılığı Senaryosu"
        verbose_name_plural = "Kat Karşılığı Senaryoları"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "parsel", "senaryo_adi"],
                name="uniq_senaryo_parsel_tenant",
            )
        ]

    def __str__(self) -> str:
        return f"{self.senaryo_adi} ({self.parsel})"


class MalikMutabakati(TenantAwareModel):
    """Malik mutabakatı takibi — oy durumu ve pay bilgisi."""

    class OyDurumu(models.TextChoices):
        BEKLIYOR = "bekliyor", "Bekliyor"
        KABUL = "kabul", "Kabul"
        RED = "red", "Red"
        BILINMIYOR = "bilinmiyor", "Bilinmiyor"

    senaryo = models.ForeignKey(
        KatKarsiligiSenaryo,
        on_delete=models.PROTECT,
        related_name="malik_mutabakatlari",
        verbose_name="Senaryo",
    )
    malik_adi = models.CharField(max_length=200, verbose_name="Malik Adı")
    pay_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Pay Oranı (%)",
    )
    oy_durumu = models.CharField(
        max_length=20,
        choices=OyDurumu.choices,
        default=OyDurumu.BEKLIYOR,
        verbose_name="Oy Durumu",
    )
    notlar = models.TextField(blank=True, verbose_name="Notlar")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncelleme")

    class Meta:
        verbose_name = "Malik Mutabakati"
        verbose_name_plural = "Malik Mutabakatları"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "senaryo", "malik_adi"],
                name="uniq_malik_senaryo_tenant",
            )
        ]

    def __str__(self) -> str:
        return f"{self.malik_adi} / {self.get_oy_durumu_display()}"


class RealEstate(TenantAwareModel):
    """Gayrimenkul kartı — Proje ↔ Gayrimenkul ↔ Yapı Sınıfı ilişkisi (roadmap Faz 1).

    Blok/kat/daire + brüt alan Decimal, tapu bilgileri ve durum bilgisi tutar.
    """

    class Durum(models.TextChoices):
        AVAILABLE = "available", "Müsait"
        RENTED = "rented", "Kirada"
        SOLD = "sold", "Satıldı"
        RESERVED = "reserved", "Rezerve"
        MAINTENANCE = "maintenance", "Bakımda"

    ad = models.CharField(max_length=200, verbose_name="Gayrimenkul Adı", blank=True)
    proje = models.ForeignKey(
        "construction.Proje",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="gayrimenkuller",
        verbose_name="İnşaat Projesi",
        help_text="Proje ↔ Gayrimenkul ilişkisi (roadmap Faz 1).",
    )
    blok = models.CharField(max_length=50, verbose_name="Blok", blank=True)
    kat = models.CharField(max_length=50, verbose_name="Kat", blank=True)
    daire_no = models.CharField(max_length=50, verbose_name="Daire No", blank=True)
    brut_m2 = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Brüt Alan (m²)",
        help_text="Decimal — float kullanılmaz (01-GELISTIRME-KURALLARI.md §4).",
    )
    durum = models.CharField(
        max_length=20,
        choices=Durum.choices,
        default=Durum.AVAILABLE,
        verbose_name="Durum",
    )
    ada = models.ForeignKey(
        "Ada",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="realestates",
        verbose_name="Ada",
        help_text="Ada ilişkili gayrimenkul (Faz 3: Kentsel Dönüşüm)",
    )
    tapu_adi = models.CharField(max_length=200, blank=True, verbose_name="Tapu Adı Bilgisi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Gayrimenkul"
        verbose_name_plural = "Gayrimenkuller"
        ordering = ["blok", "kat", "daire_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "blok", "kat", "daire_no"],
                name="uniq_gayrimenkul_konum_tenant",
            )
        ]

    def __str__(self) -> str:
        parcalar = [self.blok, self.kat, self.daire_no]
        konum = " ".join(p for p in parcalar if p)
        return f"{konum or self.ad or self.pk}"
