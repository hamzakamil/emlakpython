from decimal import Decimal
import uuid

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from django.db import models

from tenants.models import TenantAwareModel

# Faz 1 — İnşaat Modülü (kaynak: .cline/tasks/roadmap.md Faz 1 + 02-VERI-MODELI.md)
# Kural: para/miktar her zaman Decimal, asla float; fiziksel DELETE yok.


def yeni_malzeme_qr_kodu() -> str:
    return f"EML-{uuid.uuid4().hex[:20].upper()}"


class PozGrubu(TenantAwareModel):
    """Poz grupları (hiyerarşik; örn. Beton, Demir, Kalıp, İşçilik)."""

    kod = models.CharField(max_length=20, verbose_name="Grup Kodu")
    ad = models.CharField(max_length=200, verbose_name="Grup Adı")
    ust_grup = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="alt_gruplar",
        verbose_name="Üst Grup",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Poz Grubu"
        verbose_name_plural = "Poz Grupları"
        ordering = ["kod"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "kod"], name="uniq_pozgrubu_tenant_kod"
            )
        ]

    def __str__(self) -> str:
        return f"{self.kod} — {self.ad}"


class Poz(TenantAwareModel):
    """Poz kartı — ÇŞİDB çalışma pozları ve firma özel pozları.

    Fiyatlar yıl bazlı `PozFiyat` üzerinde snapshot olarak tutulur
    (birim_fiyat_snapshot mantığı; pozun kendisinde fiyat tutulmaz).
    """

    class PozTipi(models.TextChoices):
        YAPIM = "yapim", "Yapım"
        ISCILIK = "iscilik", "İşçilik"
        NAKLIYE = "nakliye", "Nakliye"
        MAKINE = "makine", "Makine"
        DIGER = "diger", "Diğer"

    poz_no = models.CharField(max_length=30, verbose_name="Poz No")
    ad = models.CharField(max_length=255, verbose_name="Poz Adı")
    birim = models.CharField(max_length=20, verbose_name="Ölçü Birimi")  # m², m³, m, kg, adet, lt
    grup = models.ForeignKey(
        PozGrubu,
        on_delete=models.PROTECT,
        related_name="pozlar",
        verbose_name="Poz Grubu",
    )
    tip = models.CharField(
        max_length=20, choices=PozTipi.choices, default=PozTipi.YAPIM, verbose_name="Poz Tipi"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Poz"
        verbose_name_plural = "Pozlar"
        ordering = ["poz_no"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "poz_no"], name="uniq_poz_tenant_no")
        ]

    def __str__(self) -> str:
        return f"{self.poz_no} — {self.ad}"


class Malzeme(TenantAwareModel):
    """Malzeme kartı — TS/TS EN referanslı."""

    malzeme_kodu = models.CharField(max_length=30, verbose_name="Malzeme Kodu")
    ad = models.CharField(max_length=255, verbose_name="Malzeme Adı")
    birim = models.CharField(max_length=20, verbose_name="Ölçü Birimi")
    ts_no = models.CharField(max_length=100, blank=True, verbose_name="TS / TS EN Referansı")
    qr_kodu = models.CharField(
        max_length=40,
        default=yeni_malzeme_qr_kodu,
        verbose_name="QR Kodu",
        help_text="Malzeme etiketi için gizli bilgi içermeyen opak kod.",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Malzeme"
        verbose_name_plural = "Malzemeler"
        ordering = ["malzeme_kodu"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "malzeme_kodu"], name="uniq_malzeme_tenant_kod"
            ),
            models.UniqueConstraint(fields=["tenant", "qr_kodu"], name="uniq_malzeme_tenant_qr"),
        ]

    def __str__(self) -> str:
        return f"{self.malzeme_kodu} — {self.ad}"


class PozMalzemeIliskisi(TenantAwareModel):
    """Poz–Malzeme ilişkisi (through) — pozdaki malzeme miktarı.

    Metraj bütünlüğü: miktar her zaman pozitif; sıfır/negatif giriş reddedilir.
    """

    poz = models.ForeignKey(
        Poz, on_delete=models.PROTECT, related_name="malzeme_kalemleri", verbose_name="Poz"
    )
    malzeme = models.ForeignKey(
        Malzeme, on_delete=models.PROTECT, related_name="poz_kalemleri", verbose_name="Malzeme"
    )
    miktar = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
        verbose_name="Miktar (birim başına)",
        help_text="Pozun bir birimi için gereken malzeme miktarı. 0/negatif olamaz.",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")

    class Meta:
        verbose_name = "Poz - Malzeme İlişkisi"
        verbose_name_plural = "Poz - Malzeme İlişkileri"
        ordering = ["poz__poz_no", "malzeme__malzeme_kodu"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "poz", "malzeme"],
                name="uniq_poz_malzeme_tenant",
            ),
            models.CheckConstraint(
                condition=models.Q(miktar__gt=0),
                name="check_poz_malzeme_miktar_pozitif",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.poz.poz_no} x {self.miktar} {self.malzeme.birim} {self.malzeme.ad}"
class PozFiyat(TenantAwareModel):
    """Poz birim fiyatı – Yıl ve/veya dönem bazlı güncellenebilir."""

    poz = models.ForeignKey(
        Poz, on_delete=models.PROTECT, related_name="fiyatlar", verbose_name="Poz"
    )
    yil = models.PositiveSmallIntegerField(verbose_name="Yıl")
    donem = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Dönem (Ay)",
        help_text="Örn. Ocak, Şubat ... boş bırakılırsa yıl bazlı kabul edilir.",
    )
    kaynak = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Kaynak",
        help_text="Örn. ÇŞİDB 2026 tebliği",
    )
    birim_fiyat = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Birim Fiyat (₺)",
    )
    kaynak_url = models.URLField(
        max_length=250, blank=True, verbose_name="Kaynak URL", help_text="Fiyatın duyurulduğu bağlantı"
    )
    yayin_tarihi = models.DateField(
        null=True, blank=True, verbose_name="Yayın Tarihi", help_text="Fiyatın yayımlanadığı tarih"
    )
    gecerlilik_tarihi = models.DateField(
        null=True, blank=True, verbose_name="Geçerlilik Tarihi", help_text="Fiyatın geçerli olduğu tarih (örn. fatura tarihi)"
    )
    ice_aktarma_tarihi = models.DateTimeField(
        auto_now_add=True, verbose_name="İçe Aktarma Tarihi", help_text="Kayıt sisteme eklenme tarihi"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")

    class Meta:
        verbose_name = "Poz Birim Fiyatı"
        verbose_name_plural = "Poz Birim Fiyatları"
        ordering = ["-yil", "donem"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "poz", "yil", "donem"],
                name="uniq_poz_fiyat_yil_donem",
                violation_error_message="Aynı poz için aynı yıl ve dönemde yalnızca bir fiyat kaydı olabilir."
            )
        ]

    def clean(self):
        super().clean()
        # If donem is provided, ensure it's a valid month name in Turkish
        if self.donem:
            valid_months = [
                "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
            ]
            if self.donem not in valid_months:
                raise ValidationError({"donem": "Geçerli bir Türkçe ay adı olmalıdır."})

    def __str__(self) -> str:
        base = f"{self.poz.poz_no} / {self.yil}"
        if self.donem:
            base += f" {self.donem}"
        return f"{base}: {self.birim_fiyat} ₺"


class ProjePozFiyat(TenantAwareModel):
    """Projeye özel poz birim fiyatı – Genel PozFiyat'ın proje bazlı override'ı.

    Fallback zinciri:
    1. ProjePozFiyat (proje + poz + yıl)
    2. PozFiyat (tenant + poz + yıl)
    3. YfkFiyat (YFK referans)

    Snapshot mantığı: PozPlan, YaklasikMaliyetSatiri, HakedisSatiri kayıt anında
    etkin fiyatı (poz_etkin_fiyati servisiyle) kopyalar.
    """

    proje = models.ForeignKey(
        "Proje",
        on_delete=models.CASCADE,
        related_name="poz_fiyatlari",
        verbose_name="Proje",
    )
    poz = models.ForeignKey(
        Poz,
        on_delete=models.PROTECT,
        related_name="proje_fiyatlari",
        verbose_name="Poz",
    )
    yil = models.PositiveSmallIntegerField(verbose_name="Yıl")
    birim_fiyat = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Birim Fiyat (₺)",
    )
    kaynak = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Kaynak",
        help_text="Örn. Proje özel teklif, tedarikçi fiyatı",
    )
    kaynak_url = models.URLField(
        max_length=250, blank=True, verbose_name="Kaynak URL"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Proje Poz Fiyatı"
        verbose_name_plural = "Proje Poz Fiyatları"
        ordering = ["proje__proje_kodu", "poz__poz_no", "-yil"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "proje", "poz", "yil"],
                name="uniq_proje_poz_fiyat_tenant_proje_poz_yil",
                violation_error_message="Aynı proje ve poz için aynı yılda yalnızca bir fiyat kaydı olabilir."
            )
        ]

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.poz.poz_no} / {self.yil}: {self.birim_fiyat} ₺"


class YfkPozVersiyon(TenantAwareModel):
    """YFK poz tanımı — versiyonlu/tarihçeli."""

    poz_no = models.CharField(max_length=30, verbose_name="Poz No")
    ad = models.CharField(max_length=255, verbose_name="Poz Adı")
    birim = models.CharField(max_length=20, verbose_name="Ölçü Birimi")
    grup_kodu = models.CharField(max_length=20, blank=True, verbose_name="Grup Kodu")
    grup_adi = models.CharField(max_length=200, blank=True, verbose_name="Grup Adı")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    kaynak = models.CharField(max_length=100, blank=True, verbose_name="Kaynak (örn. YFK 2026)")
    kaynak_url = models.URLField(max_length=250, blank=True, verbose_name="Kaynak URL")
    yayin_tarihi = models.DateField(null=True, blank=True, verbose_name="Yayın Tarihi")
    gecerlilik_baslangic = models.DateField(null=True, blank=True, verbose_name="Geçerlilik Başlangıç")
    gecerlilik_bitis = models.DateField(null=True, blank=True, verbose_name="Geçerlilik Bitiş")
    versiyon = models.PositiveIntegerField(default=1, verbose_name="Versiyon No")
    onceki_versiyon = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sonraki_versiyonlar",
        verbose_name="Önceki Versiyon",
    )
    degisiklik_turu = models.CharField(
        max_length=20,
        choices=[
            ("yeni", "Yeni Poz"),
            ("guncelleme", "Güncelleme"),
            ("iptal", "İptal"),
            ("birlesme", "Birleşme"),
            ("bolunme", "Bölünme"),
        ],
        default="yeni",
        verbose_name="Değişiklik Türü",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "YFK Poz Versiyonu"
        verbose_name_plural = "YFK Poz Versiyonları"
        ordering = ["poz_no", "-versiyon"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "poz_no", "versiyon"], name="uniq_yfkpoz_tenant_no_versiyon"
            ),
            models.CheckConstraint(
                condition=models.Q(gecerlilik_bitis__isnull=True)
                | models.Q(gecerlilik_baslangic__isnull=True)
                | models.Q(gecerlilik_bitis__gte=models.F("gecerlilik_baslangic")),
                name="check_yfkpoz_gecerlilik_sirasi",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.poz_no} v{self.versiyon} — {self.ad}"


class YfkFiyat(TenantAwareModel):
    """YFK poz birim fiyatı — ay/yıl bazlı, versiyonlu."""

    poz_versiyon = models.ForeignKey(
        YfkPozVersiyon,
        on_delete=models.PROTECT,
        related_name="fiyatlar",
        verbose_name="YFK Poz Versiyonu",
    )
    yil = models.PositiveSmallIntegerField(verbose_name="Yıl")
    donem = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Dönem (Ay)",
        help_text="Örn. Ocak, Şubat ... boş bırakılırsa yıl bazlı kabul edilir.",
    )
    birim_fiyat = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Birim Fiyat (₺)",
    )
    kaynak = models.CharField(max_length=100, blank=True, verbose_name="Kaynak")
    kaynak_url = models.URLField(max_length=250, blank=True, verbose_name="Kaynak URL")
    yayin_tarihi = models.DateField(null=True, blank=True, verbose_name="Yayın Tarihi")
    gecerlilik_tarihi = models.DateField(
        null=True, blank=True, verbose_name="Geçerlilik Tarihi"
    )
    onceki_fiyat = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sonraki_fiyatlar",
        verbose_name="Önceki Fiyat",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "YFK Fiyat"
        verbose_name_plural = "YFK Fiyatlar"
        ordering = ["poz_versiyon__poz_no", "-yil", "donem", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "poz_versiyon", "yil", "donem"],
                name="uniq_yfkfiyat_tenant_poz_yil_donem",
            ),
        ]

    def __str__(self) -> str:
        base = f"{self.poz_versiyon.poz_no} / {self.yil}"
        if self.donem:
            base += f" {self.donem}"
        return f"{base}: {self.birim_fiyat} ₺"


class YfkRayic(TenantAwareModel):
    """YFK rayıç (katsayı) tanımı — versiyonlu."""

    class MalzemeTipi(models.TextChoices):
        MALZEME = "malzeme", "Malzeme"
        ISCILIK = "iscilik", "İşçilik"
        NAKLIYE = "nakliye", "Nakliye"
        MAKINE = "makine", "Makine"
        DIGER = "diger", "Diğer"

    poz_versiyon = models.ForeignKey(
        YfkPozVersiyon,
        on_delete=models.PROTECT,
        related_name="rayiclar",
        verbose_name="YFK Poz Versiyonu",
    )
    malzeme_tipi = models.CharField(
        max_length=20, choices=MalzemeTipi.choices, verbose_name="Malzeme Tipi"
    )
    malzeme_kodu = models.CharField(max_length=30, blank=True, verbose_name="Malzeme Kodu")
    malzeme_adi = models.CharField(max_length=255, blank=True, verbose_name="Malzeme Adı")
    birim = models.CharField(max_length=20, blank=True, verbose_name="Ölçü Birimi")
    katsayi = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Katsayı",
    )
    kaynak = models.CharField(max_length=100, blank=True, verbose_name="Kaynak")
    yayin_tarihi = models.DateField(null=True, blank=True, verbose_name="Yayın Tarihi")
    onceki_rayic = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sonraki_rayiclar",
        verbose_name="Önceki Rayıç",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "YFK Rayıç"
        verbose_name_plural = "YFK Rayıçlar"
        ordering = ["poz_versiyon__poz_no", "malzeme_tipi", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "poz_versiyon", "malzeme_tipi", "malzeme_kodu"],
                name="uniq_yfkrayic_tenant_poz_tipi_kod",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.poz_versiyon.poz_no} — {self.get_malzeme_tipi_display()}: {self.katsayi}"


class YfkAnaliz(TenantAwareModel):
    """YFK poz analizi — malzeme/işçilik/nakliye/makine detayları."""

    poz_versiyon = models.ForeignKey(
        YfkPozVersiyon,
        on_delete=models.PROTECT,
        related_name="analizler",
        verbose_name="YFK Poz Versiyonu",
    )
    malzeme_tipi = models.CharField(
        max_length=20, choices=YfkRayic.MalzemeTipi.choices, verbose_name="Malzeme Tipi"
    )
    sira_no = models.PositiveSmallIntegerField(default=0, verbose_name="Sıra No")
    malzeme_kodu = models.CharField(max_length=30, verbose_name="Malzeme Kodu")
    malzeme_adi = models.CharField(max_length=255, verbose_name="Malzeme Adı")
    birim = models.CharField(max_length=20, verbose_name="Ölçü Birimi")
    miktar = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Miktar",
    )
    birim_fiyat = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Birim Fiyat (₺)",
    )
    toplam_tutar = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        verbose_name="Toplam Tutar (₺)",
        editable=False,
    )
    kaynak = models.CharField(max_length=100, blank=True, verbose_name="Kaynak")
    yayin_tarihi = models.DateField(null=True, blank=True, verbose_name="Yayın Tarihi")
    onceki_analiz = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="sonraki_analizler",
        verbose_name="Önceki Analiz",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "YFK Analiz"
        verbose_name_plural = "YFK Analizler"
        ordering = ["poz_versiyon__poz_no", "malzeme_tipi", "sira_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "poz_versiyon", "malzeme_tipi", "sira_no", "malzeme_kodu"],
                name="uniq_yfkanaliz_tenant_poz_tipi_sira_kod",
            ),
        ]

    def clean(self) -> None:
        if self.miktar is not None and self.birim_fiyat is not None:
            self.toplam_tutar = (self.miktar * self.birim_fiyat).quantize(Decimal("0.01"))
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.poz_versiyon.poz_no} — {self.get_malzeme_tipi_display()} #{self.sira_no}: {self.malzeme_adi}"


class YfkGuncellemeGecmisi(TenantAwareModel):
    """YFK veri güncelleme geçmişi — audit log."""

    class IslemTuru(models.TextChoices):
        YILLIK_POZ = "yillik_poz", "Yıllık Poz Güncelleme"
        AYLIK_FIYAT = "aylik_fiyat", "Aylık Fiyat Güncelleme"
        RAYIC = "rayic", "Rayıç Güncelleme"
        ANALIZ = "analiz", "Analiz Güncelleme"
        TOPLU = "toplu", "Toplu Güncelleme"

    class Durum(models.TextChoices):
        BASARILI = "basarili", "Başarılı"
        BASARISIZ = "basarisiz", "Başarısız"
        KISMILI = "kismili", "Kısmi Başarılı"

    islem_turu = models.CharField(
        max_length=20, choices=IslemTuru.choices, verbose_name="İşlem Türü"
    )
    yil = models.PositiveSmallIntegerField(verbose_name="Yıl")
    donem = models.CharField(max_length=20, blank=True, verbose_name="Dönem (Ay)")
    kaynak = models.CharField(max_length=100, blank=True, verbose_name="Kaynak")
    kaynak_url = models.URLField(max_length=250, blank=True, verbose_name="Kaynak URL")
    dosya_adi = models.CharField(max_length=255, blank=True, verbose_name="Dosya Adı")
    islenen_satir = models.PositiveIntegerField(default=0, verbose_name="İşlenen Satır")
    olusturulan_poz = models.PositiveIntegerField(default=0, verbose_name="Oluşturulan Poz")
    guncellenen_poz = models.PositiveIntegerField(default=0, verbose_name="Güncellenen Poz")
    olusturulan_fiyat = models.PositiveIntegerField(default=0, verbose_name="Oluşturulan Fiyat")
    guncellenen_fiyat = models.PositiveIntegerField(default=0, verbose_name="Güncellenen Fiyat")
    olusturulan_rayic = models.PositiveIntegerField(default=0, verbose_name="Oluşturulan Rayıç")
    guncellenen_rayic = models.PositiveIntegerField(default=0, verbose_name="Güncellenen Rayıç")
    olusturulan_analiz = models.PositiveIntegerField(default=0, verbose_name="Oluşturulan Analiz")
    guncellenen_analiz = models.PositiveIntegerField(default=0, verbose_name="Güncellenen Analiz")
    arsivlenen_kayit = models.PositiveIntegerField(default=0, verbose_name="Arşivlenen Kayıt")
    durum = models.CharField(
        max_length=15, choices=Durum.choices, default=Durum.BASARILI, verbose_name="Durum"
    )
    hata_mesaji = models.TextField(blank=True, verbose_name="Hata Mesajı")
    baslayan_kullanici = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Baştayan Kullanıcı",
    )
    baslangic_zamani = models.DateTimeField(auto_now_add=True, verbose_name="Başlangıç Zamanı")
    bitis_zamani = models.DateTimeField(null=True, blank=True, verbose_name="Bitiş Zamanı")

    class Meta:
        verbose_name = "YFK Güncelleme Geçmişi"
        verbose_name_plural = "YFK Güncelleme Geçmişi"
        ordering = ["-baslangic_zamani"]

    def __str__(self) -> str:
        return f"{self.get_islem_turu_display()} — {self.yil}/{self.donem or 'Yıl'} — {self.durum}"


class YapiSinifiBirimMaliyet(TenantAwareModel):
    """Yıl bazlı yapı sınıfı taban maliyetleri (I-A … V-E, tebliğ yılı ile versiyonlu).

    Yıl+sinif kodu tenant içinde benzersizdir; değişen tebliğ eski sütun silinmez,
    `is_active=False` ile arşivlenir.
    """

    sinif_kodu = models.CharField(max_length=10, verbose_name="Yapı Sınıfı Kodu")  # I-A … V-E
    yil = models.PositiveSmallIntegerField(verbose_name="Tebliğ Yılı")
    birim_maliyet = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Birim Maliyet (₺/m²)",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")

    class Meta:
        verbose_name = "Yapı Sınıfı Birim Maliyeti"
        verbose_name_plural = "Yapı Sınıfı Birim Maliyetleri"
        ordering = ["-yil", "sinif_kodu"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "sinif_kodu", "yil"],
                name="uniq_yapi_sinifi_yil_tenant",
            )
        ]

    def __str__(self) -> str:
        return f"{self.sinif_kodu} / {self.yil}: {self.birim_maliyet} ₺"

class ContractTemplate(TenantAwareModel):
    """Sözleşme şablonları – yapı sözleşme, hasılat paylaşımlı, taşeron, tedarik."""

    name = models.CharField(max_length=200, verbose_name="Şablon Adı")
    type = models.CharField(max_length=50, verbose_name="Şablon Tipi")
    content = models.TextField(verbose_name="İçerik")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Sözleşme Şablonu"
        verbose_name_plural = "Sözleşme Şablonları"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"

class RiskStructure(TenantAwareModel):
    """Riskli yapı tespiti ve süreç takibi."""

    risk_durumu = models.CharField(max_length=50, verbose_name="Risk Durumu")
    proje = models.ForeignKey(
        "construction.Proje",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="riskli_yapi_surecleri",
        verbose_name="Proje",
    )
    aciklama = models.TextField(verbose_name="Açıklama", blank=True)
    son_durum_tarihi = models.DateField(null=True, blank=True, verbose_name="Son Durum Tarihi")
    baslangic_tarihi = models.DateField(null=True, blank=True, verbose_name="Başlangıç Tarihi")
    hedef_bitis_tarihi = models.DateField(null=True, blank=True, verbose_name="Hedef Bitiş Tarihi")
    asama = models.CharField(max_length=100, blank=True, verbose_name="Aşama")
    sonraki_adim_tarihi = models.DateField(null=True, blank=True, verbose_name="Sonraki Adım Tarihi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Risk Yapısı"
        verbose_name_plural = "Risk Yapıları"
        ordering = ["risk_durumu", "created_at"]

    def __str__(self) -> str:
        return f"{self.risk_durumu} – {self.created_at.date()}"

class LeaseAssistance(TenantAwareModel):
    """Kira yardımı / tahliye süreci takibi."""

    proje = models.ForeignKey(
        "construction.Proje",
        on_delete=models.PROTECT,
        related_name="lease_assistances",
        verbose_name="Proje",
    )
    kira_yardim_id = models.CharField(max_length=100, verbose_name="Kira Yardımı ID")
    tahliye_sikligi = models.CharField(max_length=50, verbose_name="Tahliye Sıklığı")
    baslangic_tarihi = models.DateField(null=True, blank=True, verbose_name="Başlangıç Tarihi")
    sure_ay = models.PositiveIntegerField(null=True, blank=True, verbose_name="Süre (Ay)")
    bitis_tarihi = models.DateField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    aylik_odeme_gunu = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Aylık Ödeme Günü")
    tahliye_son_tarihi = models.DateField(null=True, blank=True, verbose_name="Tahliye Son Tarihi")
    banka_iban = models.CharField(max_length=34, blank=True, verbose_name="Banka IBAN")
    banka_adi = models.CharField(max_length=150, blank=True, verbose_name="Banka Adı")
    odeme_notu = models.TextField(blank=True, verbose_name="Ödeme Notu")
    aciklama = models.TextField(verbose_name="Açıklama", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Tahliye Yardımı"
        verbose_name_plural = "Tahliye Yardımları"
        ordering = ["proje", "created_at"]

    def __str__(self) -> str:
        return f"{self.proje} – {self.tahliye_sikligi}"


class EKB(TenantAwareModel):
    """Enerji Kimlik Belgesi (EKB) başvuru ve geçerlilik süreci."""

    class Durum(models.TextChoices):
        TASLAK = "taslak", "Taslak"
        BASVURU = "basvuru", "Başvuru Yapıldı"
        INCELEME = "inceleme", "İncelemede"
        ONAYLANDI = "onaylandi", "Onaylandı"
        REDDEDILDI = "reddedildi", "Reddedildi"
        YENILEME = "yenileme", "Yenileme Gerekli"

    class EnerjiSinifi(models.TextChoices):
        A_PLUS = "A+", "A+"
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"
        E = "E", "E"
        F = "F", "F"
        G = "G", "G"

    proje = models.ForeignKey(
        "construction.Proje", on_delete=models.PROTECT, related_name="ekb_belgeleri",
        verbose_name="Proje",
    )
    belge_no = models.CharField(max_length=100, verbose_name="Belge Numarası")
    durum = models.CharField(max_length=20, choices=Durum.choices, default=Durum.TASLAK)
    enerji_sinifi = models.CharField(max_length=2, choices=EnerjiSinifi.choices, blank=True)
    duzenlenme_tarihi = models.DateField(null=True, blank=True, verbose_name="Düzenlenme Tarihi")
    gecerlilik_tarihi = models.DateField(null=True, blank=True, verbose_name="Geçerlilik Tarihi")
    duzenleyen = models.CharField(max_length=255, blank=True, verbose_name="Düzenleyen")
    notlar = models.TextField(blank=True, verbose_name="Notlar")
    dokuman_referansi = models.CharField(max_length=500, blank=True, verbose_name="Doküman Referansı")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Enerji Kimlik Belgesi"
        verbose_name_plural = "Enerji Kimlik Belgeleri"
        ordering = ["-gecerlilik_tarihi", "proje"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "belge_no"], name="uniq_ekb_tenant_belge_no"),
            models.CheckConstraint(
                condition=models.Q(gecerlilik_tarihi__isnull=True)
                | models.Q(duzenlenme_tarihi__isnull=True)
                | models.Q(gecerlilik_tarihi__gt=models.F("duzenlenme_tarihi")),
                name="check_ekb_gecerlilik_duzenlenme_sonrasi",
            ),
        ]

    def clean(self):
        super().clean()
        if self.duzenlenme_tarihi and self.gecerlilik_tarihi and self.gecerlilik_tarihi <= self.duzenlenme_tarihi:
            raise ValidationError({"gecerlilik_tarihi": "Geçerlilik tarihi düzenlenme tarihinden sonra olmalıdır."})

    def __str__(self) -> str:
        return f"{self.proje} – {self.belge_no}"


class Proje(TenantAwareModel):
    """İnşaat projesi — yapı sınıfı ve gayrimenkul ile ilişkilendirilebilir.

    Not: gayrimenkul FK'sı real_estate modülü modelleşince eklenecek (roadmap Faz 1
    "Proje ↔ Gayrimenkul ↔ Yapı Sınıfı"); şimdilik yapı sınıfı ilişkisi mevcuttur.
    """

    class Durum(models.TextChoices):
        TEKLIF = "teklif", "Teklif Aşaması"
        PLANLANAN = "planlanan", "Planlanan"
        DEVAM = "devam", "İnşaat Devam Ediyor"
        ASKIDA = "askida", "Askıda"
        TAMAMLANDI = "tamamlandi", "Tamamlandı"
        IPTAL = "iptal", "İptal"

    proje_kodu = models.CharField(max_length=30, verbose_name="Proje Kodu")
    ad = models.CharField(max_length=255, verbose_name="Proje Adı")
    yapisinif_maliyet = models.ForeignKey(
        YapiSinifiBirimMaliyet,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="projeler",
        verbose_name="Yapı Sınıfı Birim Maliyeti",
        help_text="Tebliğ yılı + yapı sınıfı seçimi (tüm değer snapshot olarak korunur).",
    )
    durum = models.CharField(
        max_length=20, choices=Durum.choices, default=Durum.TEKLIF, verbose_name="Durum"
    )
    baslangic = models.DateField(null=True, blank=True, verbose_name="Başlangıç")
    bitis = models.DateField(null=True, blank=True, verbose_name="Bitiş")
    sozlesme_bitis_tarihi = models.DateField(null=True, blank=True, verbose_name="Sözleşme Bitiş Tarihi")
    gecici_kabul_tarihi = models.DateField(null=True, blank=True, verbose_name="Geçici Kabul Tarihi")
    kesin_kabul_tarihi = models.DateField(null=True, blank=True, verbose_name="Kesin Kabul Tarihi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "İnşaat Projesi"
        verbose_name_plural = "İnşaat Projeleri"
        ordering = ["proje_kodu"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "proje_kodu"], name="uniq_proje_tenant_kod")
        ]

    def __str__(self) -> str:
        return f"{self.proje_kodu} — {self.ad}"


class Mahal(TenantAwareModel):
    """Proje içindeki mahal/oda kartı."""

    proje = models.ForeignKey(
        Proje, on_delete=models.CASCADE, related_name="mahaller", verbose_name="Proje"
    )
    kod = models.CharField(max_length=30, verbose_name="Mahal Kodu")
    ad = models.CharField(max_length=255, verbose_name="Mahal Adı")
    mahal_tipi = models.CharField(max_length=50, blank=True, verbose_name="Mahal Tipi")
    kat = models.CharField(max_length=30, blank=True, verbose_name="Kat")
    alan = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Alan (m²)"
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Mahal"
        verbose_name_plural = "Mahaller"
        ordering = ["proje", "kod"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "proje", "kod"], name="uniq_mahal_tenant_proje_kod"
            )
        ]
        indexes = [models.Index(fields=["tenant", "proje"], name="mahal_tenant_proje_idx")]

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} — {self.kod} {self.ad}"


class MahalElemani(TenantAwareModel):
    """Mahaldeki kapı, pencere, duvar ve benzeri yapı elemanı."""

    mahal = models.ForeignKey(
        Mahal, on_delete=models.CASCADE, related_name="elemanlar", verbose_name="Mahal"
    )
    eleman_tipi = models.CharField(max_length=50, verbose_name="Eleman Tipi")
    ad = models.CharField(max_length=255, blank=True, verbose_name="Eleman Adı")
    miktar = models.DecimalField(
        max_digits=12, decimal_places=2, default=1, verbose_name="Miktar"
    )
    birim = models.CharField(max_length=20, default="adet", verbose_name="Birim")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Mahal Elemanı"
        verbose_name_plural = "Mahal Elemanları"
        ordering = ["mahal", "eleman_tipi", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "mahal", "eleman_tipi", "ad"],
                name="uniq_mahal_elemani_tenant_tip_ad",
            )
        ]
        indexes = [models.Index(fields=["tenant", "mahal"], name="mahalel_tenant_mahal_idx")]

    def __str__(self) -> str:
        return f"{self.mahal} — {self.eleman_tipi}"


class YaklasikMaliyet(TenantAwareModel):
    """Proje için poz bazlı yaklaşık maliyet ve revizyon başlığı."""

    proje = models.ForeignKey(
        Proje, on_delete=models.PROTECT, related_name="yaklasik_maliyetler",
        verbose_name="Proje",
    )
    yil = models.PositiveSmallIntegerField(verbose_name="Fiyat Yılı")
    ad = models.CharField(max_length=255, default="Yaklaşık Maliyet", verbose_name="Ad")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    versiyon = models.PositiveIntegerField(default=1, verbose_name="Versiyon")
    onceki = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        related_name="revizyonlar", verbose_name="Önceki Versiyon",
    )
    toplam_tutar = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0"),
        verbose_name="Toplam Tutar (₺)",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Yaklaşık Maliyet"
        verbose_name_plural = "Yaklaşık Maliyetler"
        ordering = ["-yil", "proje", "-versiyon"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "proje", "yil", "versiyon"],
                name="uniq_yaklasik_maliyet_tenant_proje_yil_ver",
            ),
            models.CheckConstraint(
                condition=models.Q(versiyon__gt=0),
                name="check_yaklasik_maliyet_versiyon_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(toplam_tutar__gte=0),
                name="check_yaklasik_maliyet_toplam_pozitif",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} — {self.yil} / v{self.versiyon}"


class YaklasikMaliyetSatiri(TenantAwareModel):
    """Yaklaşık maliyet poz satırı; fiyat kayıt anında snapshot alınır."""

    yaklasik_maliyet = models.ForeignKey(
        YaklasikMaliyet, on_delete=models.CASCADE, related_name="satirlar",
        verbose_name="Yaklaşık Maliyet",
    )
    poz = models.ForeignKey(
        Poz, on_delete=models.PROTECT, related_name="yaklasik_maliyet_satirlari",
        verbose_name="Poz",
    )
    mahal = models.ForeignKey(
        Mahal, null=True, blank=True, on_delete=models.PROTECT,
        related_name="yaklasik_maliyet_satirlari", verbose_name="Mahal",
    )
    miktar = models.DecimalField(
        max_digits=14, decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))], verbose_name="Miktar",
    )
    metraj = models.ForeignKey(
        "Metraj", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="maliyet_satirlari", verbose_name="Kaynak Metraj",
        help_text="Satır bir metrajdan üretildiyse bağlantı (FAZ 5).",
    )
    birim_fiyat_snapshot = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0"),
        verbose_name="Birim Fiyat Snapshot (₺)",
    )
    toplam_tutar = models.DecimalField(
        max_digits=18, decimal_places=2, default=Decimal("0"),
        verbose_name="Toplam Tutar (₺)",
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    sira = models.PositiveIntegerField(default=0, verbose_name="Sıra")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Yaklaşık Maliyet Satırı"
        verbose_name_plural = "Yaklaşık Maliyet Satırları"
        ordering = ["sira", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(miktar__gt=0),
                name="check_yaklasik_maliyet_satiri_miktar_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(birim_fiyat_snapshot__gte=0),
                name="check_yaklasik_maliyet_satiri_fiyat_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(toplam_tutar__gte=0),
                name="check_yaklasik_maliyet_satiri_toplam_pozitif",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            eski_snapshot = type(self).objects.filter(pk=self.pk).values_list(
                "birim_fiyat_snapshot", flat=True
            ).first()
            if eski_snapshot is not None:
                self.birim_fiyat_snapshot = eski_snapshot
        if self._state.adding and not self.birim_fiyat_snapshot:
            # FAZ 2: Yeni kayıtlar için proje_poz_etkin_fiyati kullan (ProjePozFiyat → Proje bazlı analiz → PozFiyat → YfkFiyat)
            from .services import proje_poz_etkin_fiyati

            fiyat = proje_poz_etkin_fiyati(self.yaklasik_maliyet.proje, self.poz, self.yaklasik_maliyet.yil)
            if fiyat is not None:
                self.birim_fiyat_snapshot = fiyat
        self.toplam_tutar = (
            Decimal(str(self.miktar)) * Decimal(str(self.birim_fiyat_snapshot))
        ).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

class Metraj(TenantAwareModel):
    """Hesaplanmış metraj kaydı (ifade ve sonuç snapshot'ı)."""

    ad = models.CharField(max_length=200, verbose_name="Metraj Adı")
    metraj_tipi = models.CharField(max_length=30, default="genel", verbose_name="Metraj Tipi")
    ifade = models.CharField(max_length=500, verbose_name="Hesap İfadesi")
    sonuc = models.DecimalField(max_digits=18, decimal_places=6, verbose_name="Sonuç")
    birim = models.CharField(max_length=20, default="miktar", verbose_name="Birim")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Metraj"
        verbose_name_plural = "Metrajlar"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "ad"], name="uniq_metraj_tenant_ad"),
            models.CheckConstraint(condition=models.Q(sonuc__gte=0), name="check_metraj_sonuc_pozitif"),
        ]

    def __str__(self) -> str:
        return f"{self.ad} — {self.sonuc} {self.birim}"


class PozAnaliz(TenantAwareModel):
    """Pozun malzeme, işçilik, makine ve nakliye analiz satırı."""

    class AnalizTipi(models.TextChoices):
        MALZEME = "malzeme", "Malzeme"
        ISCLIK = "iscilik", "İşçilik"
        MAKINE = "makine", "Makine"
        NAKLIYE = "nakliye", "Nakliye"
        DIGER = "diger", "Diğer"

    poz = models.ForeignKey(Poz, on_delete=models.PROTECT, related_name="analizler", verbose_name="Poz")
    satir_no = models.PositiveIntegerField(default=1, verbose_name="Satır No")
    malzeme = models.CharField(max_length=255, verbose_name="Analiz Kalemi")
    birim = models.CharField(max_length=20, verbose_name="Birim")
    miktar = models.DecimalField(max_digits=14, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))])
    birim_fiyat = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    tutar = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0"))
    analiz_tipi = models.CharField(max_length=20, choices=AnalizTipi.choices, default=AnalizTipi.MALZEME)

    class Meta:
        ordering = ["poz", "satir_no", "id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "poz", "satir_no"], name="uniq_poz_analiz_tenant_satir"),
            models.CheckConstraint(condition=models.Q(tutar__gte=0), name="check_poz_analiz_tutar_pozitif"),
        ]

    def save(self, *args, **kwargs):
        self.tutar = (self.miktar * self.birim_fiyat).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)


class NakliyeMesafe(TenantAwareModel):
    """Poz için proje bazlı nakliye mesafesi ve K katsayısı."""

    proje = models.ForeignKey(Proje, on_delete=models.CASCADE, related_name="nakliye_mesafeleri", verbose_name="Proje")
    poz = models.ForeignKey(Poz, on_delete=models.PROTECT, related_name="nakliye_mesafeleri", verbose_name="Poz")
    mesafe_km = models.DecimalField(max_digits=10, decimal_places=3, validators=[MinValueValidator(Decimal("0"))])
    k_katsayisi = models.DecimalField(max_digits=8, decimal_places=4, default=Decimal("1"), validators=[MinValueValidator(Decimal("0"))])

    class Meta:
        ordering = ["proje", "poz"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "proje", "poz"], name="uniq_nakliye_mesafe_tenant_proje_poz"),
        ]


class PozPlan(TenantAwareModel):
    """Poz maliyet plani - proje bazli planlanan / gerceklesen metraj (Faz 2).

    S-egrisi raporu icin:
      PV (Planned Value)     = planlanan_miktar x birim_fiyat_snapshot
      AV (Actual Value)      = gercek_miktar x birim_fiyat_snapshot

    `yil`, `proje` ve `poz` tripleti tenant icinde benzersizdir; ayni
    pozun ayni yilda iki kez planlanmasina izin verilmez. Fiyat snapshot'i
    olusturulurken `PozFiyat.is_active=True` kaydidindan alinir.
    """

    proje = models.ForeignKey(
        Proje,
        on_delete=models.CASCADE,
        related_name="poz_planlari",
        verbose_name="Proje",
    )
    poz = models.ForeignKey(
        Poz,
        on_delete=models.PROTECT,
        related_name="poz_planlari",
        verbose_name="Poz",
    )
    yil = models.PositiveSmallIntegerField(verbose_name="Fiyat Yılı")
    planlanan_miktar = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
        verbose_name="Planlanan Metraj",
        help_text="Bu poz için planlanan toplam miktar. 0/negatif olamaz.",
    )
    gercek_miktar = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=Decimal("0"),
        verbose_name="Gerçekleşen Metraj",
        help_text="Bu poz için gerçekleşen (harcanan) miktar. Negatif olamaz.",
    )
    metraj = models.ForeignKey(
        "Metraj", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="poz_planlari", verbose_name="Kaynak Metraj",
        help_text="Gerçekleşen miktar bir metrajdan alındıysa bağlantı (FAZ 5).",
    )
    planlanan_baslangic = models.DateField(
        null=True,
        blank=True,
        verbose_name="Planlanan Başlangıç",
        help_text="Gantt şeması için planlanan iş kalemi başlangıcı (opsiyonel).",
    )
    planlanan_bitis = models.DateField(
        null=True,
        blank=True,
        verbose_name="Planlanan Bitiş",
        help_text="Gantt şeması için planlanan iş kalemi bitişi (başlangıçtan önce olamaz).",
    )
    birim_fiyat_snapshot = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Birim Fiyat Snapshot (₺)",
        help_text="Planlama anındaki birim fiyat (değişmez).",
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Poz Maliyet Planı"
        verbose_name_plural = "Poz Maliyet Planları"
        ordering = ["proje__proje_kodu", "poz__poz_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "proje", "poz", "yil"],
                name="uniq_poz_plan_tenant_proje_poz_yil",
            ),
            models.CheckConstraint(
                condition=models.Q(gercek_miktar__gte=0),
                name="check_poz_plan_gercek_pozitif",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(planlanan_baslangic__isnull=True)
                    | models.Q(planlanan_bitis__isnull=True)
                    | models.Q(planlanan_bitis__gte=models.F("planlanan_baslangic"))
                ),
                name="check_poz_plan_tarih_sirasi",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.poz.poz_no} / {self.yil}"

    def clean(self) -> None:
        """Metraj bütünlüğü: planlanan > 0; gerçekleşen ≥ 0; birim fiyat > 0;
        planlanan bitiş, başlangıçtan önce olamaz."""

        if self.planlanan_miktar <= 0:
            raise ValidationError({"planlanan_miktar": "Planlanan metraj 0'dan büyük olmalıdır."})
        if self.gercek_miktar < 0:
            raise ValidationError({"gercek_miktar": "Gerçekleşen metraj negatif olamaz."})
        if (
            self.planlanan_baslangic
            and self.planlanan_bitis
            and self.planlanan_bitis < self.planlanan_baslangic
        ):
            raise ValidationError(
                {"planlanan_bitis": "Planlanan bitiş tarihi başlangıçtan önce olamaz."}
            )
        if self.birim_fiyat_snapshot <= 0:
            raise ValidationError(
                {
                    "birim_fiyat_snapshot": (
                        "Birim fiyat 0'dan büyük olmalıdır. Seçilen poz için girilen yılda "
                        "aktif PozFiyat kaydı bulunamadı."
                    )
                }
            )

    def save(self, *args, **kwargs) -> None:
        """Oluşturulurken `proje_poz_etkin_fiyati` snapshot'tan otomatik fiyat alınır (eğer boşsa).

        FAZ 2: ProjePozFiyat → Proje bazlı poz analizi → PozFiyat → YfkFiyat hiyerarşisi kullanılır.
        Mevcut snapshot varsa ASLA yeniden hesaplama.
        FAZ 6C: güncellemede snapshot DB değerine geri alınır (ORM bypass koruması).
        """
        if self.pk and not self._state.adding:
            eski_snapshot = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("birim_fiyat_snapshot", flat=True)
                .first()
            )
            if eski_snapshot is not None:
                self.birim_fiyat_snapshot = eski_snapshot
        if not self.birim_fiyat_snapshot or self.birim_fiyat_snapshot <= 0:
            from .services import proje_poz_etkin_fiyati

            fiyat = proje_poz_etkin_fiyati(self.proje, self.poz, self.yil)
            if fiyat is not None:
                self.birim_fiyat_snapshot = fiyat
        self.clean()
        super().save(*args, **kwargs)


class IFCImportJob(TenantAwareModel):
    """Tenant-scoped IFC import and review envelope.

    Parsing is deliberately isolated from ``PozPlan``: an import can only
    produce draft rows until an operator explicitly promotes them.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", "Kuyrukta"
        PROCESSING = "processing", "İşleniyor"
        COMPLETED = "completed", "Tamamlandı"
        FAILED = "failed", "Başarısız"

    project = models.ForeignKey(
        Proje, on_delete=models.PROTECT, related_name="ifc_import_jobs", verbose_name="Proje"
    )
    year = models.PositiveSmallIntegerField(verbose_name="Plan Yılı")
    file = models.FileField(upload_to="construction/ifc/%Y/%m/", null=True, blank=True)
    file_name = models.CharField(max_length=255, verbose_name="Dosya Adı")
    file_size = models.PositiveBigIntegerField(default=0, verbose_name="Dosya Boyutu")
    content_type = models.CharField(max_length=100, blank=True)
    source_reference = models.CharField(max_length=500, blank=True)
    checksum = models.CharField(max_length=64, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    parser_mode = models.CharField(max_length=40, blank=True)
    validation_errors = models.JSONField(default=list, blank=True)
    processing_message = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="ifc_import_jobs",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant", "project", "year", "status"])]


class IFCQuantityDraft(TenantAwareModel):
    """A reviewable quantity extracted from an IFC import."""

    class MappingStatus(models.TextChoices):
        MAPPED = "mapped", "Eşleşti"
        UNMAPPED = "unmapped", "Eşleşmedi"
        INVALID = "invalid", "Geçersiz"

    job = models.ForeignKey(IFCImportJob, on_delete=models.CASCADE, related_name="draft_rows")
    project = models.ForeignKey(Proje, on_delete=models.PROTECT, related_name="+")
    year = models.PositiveSmallIntegerField()
    poz = models.ForeignKey(Poz, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    source_name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit = models.CharField(max_length=30)
    ifc_entity_type = models.CharField(max_length=80, blank=True)
    mapping_status = models.CharField(max_length=20, choices=MappingStatus.choices)
    validation_message = models.CharField(max_length=500, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["mapping_status", "source_name", "id"]
        indexes = [models.Index(fields=["tenant", "job", "mapping_status"])]


class Hakedis(TenantAwareModel):
    """Dönemsel hakediş — proje bazlı, onay akışlı (roadmap Faz 2).

    - Satırlar (`HakedisSatiri`) poz planlarından (gerçekleşen metraj × snapshot)
      otomatik hesaplanır; tutarlar `services.hakedis_hesapla` ile bulunur.
    - Onay (`services.hakedis_onayla`) Cari Hareket + Muhasebe Fişi üretir
      (readme §52.6 madde 4 — ayrı gölge muhasebe yok).
    - Fiziksel DELETE yok: iptal için durum=iptal.
    """

    class Durum(models.TextChoices):
        TASLAK = "taslak", "Taslak"
        ONAYLANDI = "onaylandi", "Onaylandı"
        IPTAL = "iptal", "İptal"

    proje = models.ForeignKey(
        Proje, on_delete=models.PROTECT, related_name="hakedisler", verbose_name="Proje",
    )
    donem = models.CharField(
        max_length=7, verbose_name="Dönem (YYYY-MM)",
        help_text="Hakediş dönemi, örn. 2026-03.",
    )
    cari = models.ForeignKey(
        "cari.Cari", on_delete=models.PROTECT, null=True, blank=True,
        related_name="hakedisler", verbose_name="Yüklenici / Cari",
        help_text="Taşeron/yüklenici cari kartı (onayda Cari Hareket buraya işlenir).",
    )
    durum = models.CharField(
        max_length=10, choices=Durum.choices, default=Durum.TASLAK, verbose_name="Durum"
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    odeme_vadesi = models.DateField(null=True, blank=True, verbose_name="Ödeme Vadesi")
    # Onayda üretilen kayıtların referansları (tekrar onayı engeller)
    cari_hareket = models.ForeignKey(
        "cari.CariHareket", on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", verbose_name="Cari Hareket",
    )
    muhasebe_fisi = models.ForeignKey(
        "accounting.MuhasebeFisi", on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", verbose_name="Muhasebe Fişi",
    )
    onaylayan = models.ForeignKey(
        "users.User", on_delete=models.PROTECT, null=True, blank=True,
        related_name="+", verbose_name="Onaylayan",
    )
    onay_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Onay Tarihi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Hakediş"
        verbose_name_plural = "Hakedişler"
        ordering = ["-donem", "proje__proje_kodu"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "proje", "donem"], name="uniq_hakedis_tenant_proje_donem"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.donem} ({self.get_durum_display()})"

    def clean(self) -> None:
        import re

        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", self.donem or ""):
            raise ValidationError({"donem": "Dönem YYYY-MM biçiminde olmalıdır (örn. 2026-03)."})
        # Onaylı/iptal hakedişte çekirdek alanlar değişmez (iptal deseni, model katmanı).
        if self.pk and not self._state.adding:
            eski = type(self).objects.filter(pk=self.pk).first()
            if eski and eski.durum != self.Durum.TASLAK:
                if (
                    eski.proje_id != self.proje_id
                    or eski.donem != self.donem
                    or eski.cari_id != self.cari_id
                ):
                    raise ValidationError(
                        "Onaylanmış/iptal hakedişte proje, dönem ve cari değiştirilemez."
                    )
                if eski.durum == self.Durum.ONAYLANDI and self.durum == self.Durum.TASLAK:
                    raise ValidationError("Onaylanmış hakediş taslağa döndürülemez.")

    @property
    def toplam_tutar(self) -> Decimal:
        """Satır toplamı (onaysız taslaklarda da hesaplanabilir)."""
        return sum((s.satir_tutar for s in self.satirlar.all()), Decimal("0"))


class HakedisSatiri(models.Model):
    """Hakediş satırı — poz planı karşılığı (poz + miktar + snapshot fiyat)."""

    hakedis = models.ForeignKey(
        Hakedis, on_delete=models.CASCADE, related_name="satirlar", verbose_name="Hakediş",
    )
    poz = models.ForeignKey(
        Poz, on_delete=models.PROTECT, related_name="hakedis_satirlari", verbose_name="Poz",
    )
    miktar = models.DecimalField(
        max_digits=14, decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))], verbose_name="Miktar",
    )
    birim_fiyat = models.DecimalField(
        max_digits=14, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))], verbose_name="Birim Fiyat (₺)",
    )

    class Meta:
        verbose_name = "Hakediş Satırı"
        verbose_name_plural = "Hakediş Satırları"
        constraints = [
            models.UniqueConstraint(
                fields=["hakedis", "poz"], name="uniq_hakedis_satir_hakedis_poz"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.hakedis} / {self.poz.poz_no}: {self.miktar}"

    @property
    def satir_tutar(self) -> Decimal:
        return (self.miktar * self.birim_fiyat).quantize(Decimal("0.01"))

    def clean(self) -> None:
        if self.miktar <= 0:
            raise ValidationError({"miktar": "Miktar 0'dan büyük olmalıdır."})
        if self.birim_fiyat <= 0:
            raise ValidationError({"birim_fiyat": "Birim fiyat 0'dan büyük olmalıdır."})
        # FAZ 6C: onaylı/iptal hakedişin satırları değişmez (fiyat/miktar/poz).
        if self.pk and not self._state.adding:
            eski = (
                type(self)
                .objects.select_related("hakedis")
                .filter(pk=self.pk)
                .first()
            )
            if eski is not None and eski.hakedis.durum != Hakedis.Durum.TASLAK:
                if (
                    eski.miktar != self.miktar
                    or eski.birim_fiyat != self.birim_fiyat
                    or eski.poz_id != self.poz_id
                ):
                    raise ValidationError(
                        "Onaylanmış/iptal hakedişin satırları değiştirilemez."
                    )

    def save(self, *args, **kwargs) -> None:
        # FAZ 6C: ORM/admin bypass koruması (DRF clean() çağırmaz).
        self.full_clean()
        super().save(*args, **kwargs)


class Tedarikci(TenantAwareModel):
    """Tedarikçi / tedarik firması kartı."""

    firma_adi = models.CharField(max_length=255, verbose_name="Firma Adı")
    firma_kodu = models.CharField(max_length=30, unique=True, verbose_name="Firma Kodu")
    il = models.CharField(max_length=100, blank=True, verbose_name="İl")
    ilce = models.CharField(max_length=100, blank=True, verbose_name="İlçe")
    telefon = models.CharField(max_length=30, blank=True, verbose_name="Telefon")
    email = models.CharField(max_length=255, blank=True, verbose_name="E-posta")
    adres = models.TextField(blank=True, verbose_name="Adres")
    cari = models.ForeignKey(
        "cari.Cari",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="tedarikciler",
        verbose_name="Cari Kart",
        help_text="Satın alma faturası bu cari karta işlenir (FAZ 4).",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Tedarikçi"
        verbose_name_plural = "Tedarikçiler"
        ordering = ["firma_adi"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "firma_kodu"], name="uniq_tenant_firma_kodu")
        ]

    def __str__(self) -> str:
        return f"{self.firma_adi} ({self.firma_kodu})"


class MalzemeTedarikciIliskisi(TenantAwareModel):
    """Malzeme - tedarikçi ilişki ve sipariş takibi."""

    class Durum(models.TextChoices):
        BASLIYOR = "basliyor", "Başlıyor"
        AKTIF = "aktif", "Aktif"
        GECIKIYOR = "gecikiyor", "Gecikiyor"
        TAMAMLANDI = "tamamlandi", "Tamamlandı"
        iptal = "iptal", "İptal"

    malzeme = models.ForeignKey(Malzeme, on_delete=models.PROTECT, related_name="tedarikci_kalemleri", verbose_name="Malzeme")
    tedarikci = models.ForeignKey("construction.Tedarikci", on_delete=models.PROTECT, related_name="malzeme_kalemleri", verbose_name="Tedarikçi")
    miktar = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
        verbose_name="Sipariş Miktarı",
        help_text="Malzeme birimi (örn. m², m³, adet)",
    )
    birim = models.CharField(max_length=20, verbose_name="Birim", default="adet")
    durum = models.CharField(max_length=20, choices=Durum.choices, default=Durum.BASLIYOR, verbose_name="Durum")
    teslim_tarihi = models.DateField(null=True, blank=True, verbose_name="Tahmini Teslim Tarihi")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Malzeme - Tedarikçi İlişki"
        verbose_name_plural = "Malzeme - Tedarikçi İlişkileri"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "malzeme", "tedarikci"], name="uniq_malzeme_tedarikci_tenant"),
        ]

    def __str__(self) -> str:
        return f"{self.malzeme.ad} - {self.tedarikci.firma_adi} ({self.durum})"


class TedarikciTeklifi(TenantAwareModel):
    """Proje/malzeme için tedarikçilerden alınan karşılaştırmalı teklifler.

    Teklifler fiziksel olarak silinmez; ``is_active`` ile arşivlenir. Bir
    proje-malzeme grubu içinde aynı anda yalnızca bir teklif seçilebilir.
    """

    class Durum(models.TextChoices):
        TASLAK = "taslak", "Taslak"
        ISTENDI = "istendi", "İstendi"
        GELDI = "geldi", "Teklif Alındı"
        DEGERLENDIRILIYOR = "degerlendiriliyor", "Değerlendiriliyor"
        KABUL = "kabul", "Kabul Edildi"
        RED = "red", "Reddedildi"
        IPTAL = "iptal", "İptal"

    proje = models.ForeignKey(
        Proje, on_delete=models.PROTECT, related_name="tedarikci_teklifleri", verbose_name="Proje"
    )
    malzeme = models.ForeignKey(
        Malzeme, on_delete=models.PROTECT, related_name="tedarikci_teklifleri", verbose_name="Malzeme"
    )
    tedarikci = models.ForeignKey(
        Tedarikci, on_delete=models.PROTECT, related_name="teklifler", verbose_name="Tedarikçi"
    )
    miktar = models.DecimalField(
        max_digits=14, decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))], verbose_name="Miktar",
    )
    birim_fiyat = models.DecimalField(
        max_digits=14, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))], verbose_name="Birim Fiyat (₺)",
    )
    toplam_tutar = models.DecimalField(
        max_digits=16, decimal_places=2, blank=True, null=True,
        verbose_name="Toplam Tutar (₺)", help_text="Miktar x birim fiyat; kayıtta otomatik hesaplanır.",
    )
    durum = models.CharField(
        max_length=24, choices=Durum.choices, default=Durum.TASLAK, verbose_name="Durum"
    )
    gecerlilik_tarihi = models.DateField(null=True, blank=True, verbose_name="Geçerlilik Tarihi")
    notlar = models.TextField(blank=True, verbose_name="Notlar")
    secildi = models.BooleanField(default=False, verbose_name="Kazanan teklif")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Tedarikçi Teklifi"
        verbose_name_plural = "Tedarikçi Teklifleri"
        ordering = ["-secildi", "birim_fiyat", "-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(miktar__gt=0), name="check_tedarikci_teklifi_miktar_pozitif"),
            models.CheckConstraint(condition=models.Q(birim_fiyat__gt=0), name="check_tedarikci_teklifi_fiyat_pozitif"),
            models.UniqueConstraint(
                fields=["tenant", "proje", "malzeme", "tedarikci"],
                condition=models.Q(is_active=True),
                name="uniq_aktif_tedarikci_teklifi",
            ),
        ]

    def save(self, *args, **kwargs):
        miktar = Decimal(str(self.miktar))
        birim_fiyat = Decimal(str(self.birim_fiyat))
        self.toplam_tutar = (miktar * birim_fiyat).quantize(Decimal("0.01"))
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.malzeme.ad} / {self.tedarikci.firma_adi}"


class TaseronSozlesi(TenantAwareModel):
    """Taşeron sözleşmesi - projeler arası taşeron ilişkisi."""

    class Durum(models.TextChoices):
        TASLAK = "taslak", "Taslak"
        ONAYLANDI = "onaylandi", "Onaylandı"
        AKTIF = "aktif", "Aktif"
        TAMAMLANDI = "tamamlandi", "Tamamlandı"
        iptal = "iptal", "İptal"

    proje = models.ForeignKey(Proje, on_delete=models.PROTECT, related_name="taseron_sozlesi", verbose_name="Proje")
    taseron_firma = models.CharField(max_length=255, verbose_name="Taşeron Firma")
    sosyal_unvan = models.CharField(max_length=255, blank=True, verbose_name="Sosyal Ünvan")
    sicil_no = models.CharField(max_length=50, blank=True, verbose_name="Şirket Sicil No")
    tarih_baslangic = models.DateField(verbose_name="Başlangıç Tarihi")
    tarih_bitis = models.DateField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    teminat_bitis_tarihi = models.DateField(null=True, blank=True, verbose_name="Teminat Bitiş Tarihi")
    tutar = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Sözleşme Tutarı (₺)",
    )
    durum = models.CharField(max_length=20, choices=Durum.choices, default=Durum.TASLAK, verbose_name="Durum")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Taşeron Sözleşmesi"
        verbose_name_plural = "Taşeron Sözleşmeleri"
        ordering = ["-tarih_baslangic"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "proje"], name="uniq_tenant_proje_sozlesi"),
        ]

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} - {self.taseron_firma} ({self.durum})"


class KaliteKabulTeminati(TenantAwareModel):
    """Kalite kabul teminatı - poz kabul/kontrol kayıtları."""

    class Sonuc(models.TextChoices):
        BEKLEMEDE = "beklemede", "Beklemede"
        UYGULANDI = "uygulandi", "Uygulandı"
        REDDEDILDI = "reddedildi", "Reddedildi"

    proje = models.ForeignKey(Proje, on_delete=models.PROTECT, related_name="kabul_teminati", verbose_name="Proje")
    poz = models.ForeignKey(Poz, null=True, blank=True, on_delete=models.PROTECT, related_name="kabul_teminati", verbose_name="Poz")
    tarih = models.DateField(verbose_name="Kontrol Tarihi")
    kriter = models.CharField(max_length=255, verbose_name="Kriter")
    sonuc = models.CharField(max_length=20, choices=Sonuc.choices, default=Sonuc.BEKLEMEDE, verbose_name="Sonuç")
    belge = models.FileField(upload_to="kabul_teminati/", null=True, blank=True, verbose_name="Belge")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    created_by = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="kabul_teminati_kayitlari", verbose_name="Oluşturan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Kalite Kabul Teminatı"
        verbose_name_plural = "Kalite Kaufmanninatı"
        ordering = ["-tarih", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "proje", "tarih"], name="uniq_tenant_proje_tarih_kabul"),
        ]

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.tarih} - {self.get_sonuc_display()}"


class Hatirlatma(TenantAwareModel):
    """Tenant kapsamındaki merkezi iş ve tarih hatırlatması."""

    class Seviye(models.TextChoices):
        KRITIK = "kritik", "Kritik"
        UYARI = "uyari", "Uyarı"
        BILGI = "bilgi", "Bilgi"

    class Durum(models.TextChoices):
        BEKLIYOR = "bekliyor", "Bekliyor"
        OKUNDU = "okundu", "Okundu"
        TAMAMLANDI = "tamamlandi", "Tamamlandı"
        IPTAL = "iptal", "İptal"

    class TekrarlamaTipi(models.TextChoices):
        YOK = "yok", "Tekrarsız"
        GUNLUK = "gunluk", "Günlük"
        HAFTALIK = "haftalik", "Haftalık"
        AYLIK = "aylik", "Aylık"

    baslik = models.CharField(max_length=255, verbose_name="Başlık")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    ilgili_modul = models.CharField(max_length=80, verbose_name="İlgili Modül")
    ilgili_kayit_id = models.PositiveBigIntegerField(null=True, blank=True, verbose_name="İlgili Kayıt ID")
    ilgili_kayit_tipi = models.CharField(max_length=120, blank=True, verbose_name="İlgili Kayıt Tipi")
    hatirlatma_tarihi = models.DateField(verbose_name="Hatırlatma Tarihi")
    seviye = models.CharField(max_length=10, choices=Seviye.choices, default=Seviye.BILGI)
    durum = models.CharField(max_length=12, choices=Durum.choices, default=Durum.BEKLIYOR)
    sorumlu_kullanici = models.ForeignKey(
        "users.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="hatirlatmalar", verbose_name="Sorumlu Kullanıcı",
    )
    tekrarlama_tipi = models.CharField(max_length=10, choices=TekrarlamaTipi.choices, default=TekrarlamaTipi.YOK)
    tekrarlama_gun = models.PositiveSmallIntegerField(default=0, verbose_name="Tekrarlama Günü")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["hatirlatma_tarihi", "-created_at"]
        indexes = [
            models.Index(fields=["tenant", "hatirlatma_tarihi", "durum"]),
            models.Index(fields=["tenant", "ilgili_modul", "ilgili_kayit_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "ilgili_modul", "ilgili_kayit_id", "hatirlatma_tarihi"],
                name="uniq_hatirlatma_tenant_kayit_tarih",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.hatirlatma_tarihi} — {self.baslik}"


class HatirlatmaKurali(TenantAwareModel):
    """Bir modül tarihinden hatırlatma üretmek için tenant kuralı."""

    ilgili_modul = models.CharField(max_length=80, verbose_name="İlgili Modül")
    ilgili_model = models.CharField(max_length=120, blank=True, default="", verbose_name="İlgili Model")
    tetikleyici = models.CharField(max_length=80, verbose_name="Tetikleyici")
    once_gun_sayisi = models.PositiveSmallIntegerField(default=0, verbose_name="Önce Gün Sayısı")
    seviye = models.CharField(max_length=10, choices=Hatirlatma.Seviye.choices, default=Hatirlatma.Seviye.UYARI)
    baslik_sablonu = models.CharField(max_length=255, blank=True, default="", verbose_name="Başlık Şablonu")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ilgili_modul", "once_gun_sayisi"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "ilgili_modul", "ilgili_model", "tetikleyici", "once_gun_sayisi"],
                name="uniq_hatirlatma_kurali_tenant_tetik",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.ilgili_modul} / {self.tetikleyici} - {self.once_gun_sayisi} gün"

class KaliteKontrol(TenantAwareModel):
    """Poz veya proje bazlı kalite/iş güvenliği kontrol kaydı."""

    class KontrolTipi(models.TextChoices):
        MALZEME = "malzeme", "Malzeme Kontrolü"
        ISCILIK = "iscilik", "İşçilik Kontrolü"
        BOYUT = "boyut", "Boyut Ölçümü"
        TEST = "test", "Test/Analiz"
        GORUNTULEME = "goruntuleme", "Görsel İnceleme"
        DIGER = "diger", "Diğer"

    class Durum(models.TextChoices):
        BEKLEMEDE = "beklemede", "Beklemede"
        GECTI = "gecti", "Geçti"
        KALDI = "kaldi", "Kaldı"
        ONAYLANDI = "onaylandi", "Onaylandı"
        REDDEDILDI = "reddedildi", "Reddedildi"

    proje = models.ForeignKey(Proje, on_delete=models.PROTECT, related_name="kalite_kontrolleri", verbose_name="Proje")
    poz = models.ForeignKey(Poz, null=True, blank=True, on_delete=models.PROTECT, related_name="kalite_kontrolleri", verbose_name="Poz")
    tarih = models.DateField(verbose_name="Tarih")
    kontrol_tipi = models.CharField(max_length=20, choices=KontrolTipi.choices, default=KontrolTipi.MALZEME, verbose_name="Kontrol Tipi")
    durum = models.CharField(max_length=20, choices=Durum.choices, default=Durum.BEKLEMEDE, verbose_name="Durum")
    olculen_deger = models.CharField(max_length=255, blank=True, verbose_name="Ölçülen Değer")
    beklenen_deger = models.CharField(max_length=255, blank=True, verbose_name="Beklenen Değer")
    tolerek_aralik = models.CharField(max_length=255, blank=True, verbose_name="Tolerans Aralığı")
    kriter = models.CharField(max_length=255, verbose_name="Kriter")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    kontrol_eden = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="kalite_kontrol_eden", verbose_name="Kontrol Eden")
    onaylayan = models.ForeignKey("users.User", on_delete=models.PROTECT, null=True, blank=True, related_name="kalite_kontrol_onaylayan", verbose_name="Onaylayan")
    onay_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Onay Tarihi")
    ek_gorseller = models.JSONField(default=list, blank=True, verbose_name="Ek Görseller")
    duzeltici_faaliyet = models.TextField(blank=True, verbose_name="Düzeltici Faaliyet")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        ordering = ["-tarih", "-id"]
        verbose_name = "Kalite Kontrol"
        verbose_name_plural = "Kalite Kontrolleri"

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.get_kontrol_tipi_display()} / {self.tarih}"


class SantiyeGunlugu(TenantAwareModel):
    """Proje bazlı günlük saha kaydı."""

    class HavaDurumu(models.TextChoices):
        GUNESLI = "gunesli", "Güneşli"
        PARCALI_BULUTLU = "parcali_bulutlu", "Parçalı Bulutlu"
        BULUTLU = "bulutlu", "Bulutlu"
        YAGMURLU = "yagmurlu", "Yağmurlu"
        SAGANAK = "saganak", "Sağanak"
        KARLI = "karli", "Karlı"
        SISLI = "sisli", "Sisli"

    class IsciTipi(models.TextChoices):
        USTA = "usta", "Usta"
        CIRAK = "cirak", "Çırak"
        GENEL = "genel", "Genel İşçi"
        MAKINE_OPERATORU = "makine_operatoru", "Makine Operatörü"
        MUHENDIS = "muhendis", "Mühendis"
        TEKNIKER = "tekniker", "Teknisyen"
        GUVENLIK = "guvenlik", "Güvenlik"

    proje = models.ForeignKey(Proje, on_delete=models.PROTECT, related_name="gunlukler", verbose_name="Proje")
    tarih = models.DateField(verbose_name="Tarih")
    hava_durumu = models.CharField(max_length=20, choices=HavaDurumu.choices, default=HavaDurumu.GUNESLI, verbose_name="Hava Durumu")
    sicaklik_min = models.IntegerField(null=True, blank=True, verbose_name="Sıcaklık Min (°C)")
    sicaklik_max = models.IntegerField(null=True, blank=True, verbose_name="Sıcaklık Max (°C)")
    isci_sayisi = models.PositiveIntegerField(default=0, verbose_name="İşçi Sayısı")
    isci_tipi = models.CharField(max_length=20, choices=IsciTipi.choices, default=IsciTipi.GENEL, verbose_name="İşçi Tipi")
    calisma_saati = models.PositiveIntegerField(default=8, verbose_name="Çalışma Saati")
    yapilan_isler = models.TextField(verbose_name="Yapılan İşler")
    malzeme_giris = models.TextField(blank=True, verbose_name="Malzeme Giriş")
    malzeme_cikis = models.TextField(blank=True, verbose_name="Malzeme Çıkış")
    ekipmanlar = models.TextField(blank=True, verbose_name="Ekipmanlar")
    sorunlar = models.TextField(blank=True, verbose_name="Sorunlar")
    notlar = models.TextField(blank=True, verbose_name="Notlar")
    created_by = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="santiye_gunlukleri", verbose_name="Oluşturan")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")

    class Meta:
        ordering = ["-tarih", "-id"]
        verbose_name = "Şantiye Günlüğü"
        verbose_name_plural = "Şantiye Günlükleri"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "proje", "tarih"], name="uniq_gunluk_tenant_proje_tarih")
        ]

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.tarih}"


class SantiyeCheckIn(TenantAwareModel):
    """Mobil saha giriş/çıkış kaydı; geçmiş kayıtlar korunur."""

    proje = models.ForeignKey(Proje, on_delete=models.PROTECT, related_name="checkinler", verbose_name="Proje")
    kullanici = models.ForeignKey(
        "users.User", on_delete=models.PROTECT, related_name="santiye_checkinleri", verbose_name="Kullanıcı"
    )
    giris_zamani = models.DateTimeField(verbose_name="Giriş Zamanı")
    cikis_zamani = models.DateTimeField(null=True, blank=True, verbose_name="Çıkış Zamanı")
    notlar = models.TextField(blank=True, verbose_name="Notlar")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        ordering = ["-giris_zamani", "-id"]
        verbose_name = "Şantiye Giriş Çıkış"
        verbose_name_plural = "Şantiye Giriş Çıkışları"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cikis_zamani__isnull=True) | models.Q(cikis_zamani__gte=models.F("giris_zamani")),
                name="check_santiye_cikis_giris_sonrasi",
            )
        ]

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.kullanici} / {self.giris_zamani:%Y-%m-%d %H:%M}"


class MalzemeHareketi(TenantAwareModel):
    """QR veya manuel kod ile malzeme giriş/çıkış hareketi."""

    class Yonu(models.TextChoices):
        GIRIS = "giris", "Giriş"
        CIKIS = "cikis", "Çıkış"

    proje = models.ForeignKey(Proje, on_delete=models.PROTECT, related_name="malzeme_hareketleri", verbose_name="Proje")
    malzeme = models.ForeignKey(Malzeme, on_delete=models.PROTECT, related_name="hareketler", verbose_name="Malzeme")
    yon = models.CharField(max_length=10, choices=Yonu.choices, verbose_name="Hareket")
    miktar = models.DecimalField(
        max_digits=14, decimal_places=4, validators=[MinValueValidator(Decimal("0.0001"))], verbose_name="Miktar"
    )
    birim = models.CharField(max_length=20, verbose_name="Birim")
    qr_kodu = models.CharField(max_length=40, verbose_name="QR / Manuel Kod")
    gerceklesme_zamani = models.DateTimeField(verbose_name="Gerçekleşme Zamanı")
    kaydeden = models.ForeignKey("users.User", on_delete=models.PROTECT, related_name="malzeme_hareketleri", verbose_name="Kaydeden")
    notlar = models.TextField(blank=True, verbose_name="Notlar")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        ordering = ["-gerceklesme_zamani", "-id"]
        verbose_name = "Malzeme Hareketi"
        verbose_name_plural = "Malzeme Hareketleri"

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.malzeme.ad} / {self.get_yon_display()} / {self.miktar} {self.birim}"


# =============================================================================
# FAZ 2 — Projeye Özel Malzeme Sistemi
# =============================================================================

class ProjeMalzeme(TenantAwareModel):
    """Proje seviyesinde kullanılan malzemenin tedarik, teklif ve aktiflik bilgileri.

    Global Malzeme kartının (ad, birim, ts_no) alanları override edilmez.
    Bu model projeye özel tedarikçi, cari, seçili teklif ve kaynak bilgilerini tutar.
    """

    proje = models.ForeignKey(
        Proje,
        on_delete=models.CASCADE,
        related_name="proje_malzemeleri",
        verbose_name="Proje",
    )
    malzeme = models.ForeignKey(
        Malzeme,
        on_delete=models.PROTECT,
        related_name="proje_malzemeleri",
        verbose_name="Malzeme",
    )
    tedarikci = models.ForeignKey(
        "Tedarikci",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="proje_malzemeleri",
        verbose_name="Tedarikçi",
    )
    cari = models.ForeignKey(
        "cari.Cari",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="proje_malzemeleri",
        verbose_name="Cari",
    )
    selected_teklif = models.ForeignKey(
        "TedarikciTeklifi",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="secili_olan_proje_malzemeleri",
        verbose_name="Seçili Teklif",
        help_text="Bu proje-malzeme için onaylı tek teklif. Tenant/proje/malzeme uyumu zorunludur.",
    )
    kaynak = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Kaynak",
        help_text="Örn. Tedarikçi listesi, piyasa araştırması, ihale sonucu",
    )
    kaynak_url = models.URLField(
        max_length=250,
        blank=True,
        verbose_name="Kaynak URL",
        help_text="Fiyat/tedarik kaynağının bağlantısı",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Proje Malzemesi"
        verbose_name_plural = "Proje Malzemeleri"
        ordering = ["proje__proje_kodu", "malzeme__malzeme_kodu"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "proje", "malzeme"],
                name="uniq_proje_malzeme_tenant_proje_malzeme",
            ),
        ]

    def clean(self):
        super().clean()
        # selected_teklif tenant/proje/malzeme/is_active validasyonu
        if self.selected_teklif:
            if self.selected_teklif.tenant_id != self.tenant_id:
                raise ValidationError({"selected_teklif": "Seçili teklif bu tenant'a ait değil."})
            if self.selected_teklif.proje_id != self.proje_id:
                raise ValidationError({"selected_teklif": "Seçili teklif bu projeye ait değil."})
            if self.selected_teklif.malzeme_id != self.malzeme_id:
                raise ValidationError({"selected_teklif": "Seçili teklif bu malzemeye ait değil."})
            if not self.selected_teklif.is_active:
                raise ValidationError({"selected_teklif": "Seçili teklif aktif değil."})

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.malzeme.malzeme_kodu} — {self.malzeme.ad}"


class ProjeMalzemeFiyat(TenantAwareModel):
    """Proje bazlı malzeme yıl bazlı fiyatı.

    FAZ 2'de maliyet hesabına girecek para birimi yalnızca TRY'dir.
    TRY dışındaki fiyat doğrudan maliyet hesabına sokulmayacaktır.
    """

    class ParaBirimi(models.TextChoices):
        TRY = "TRY", "Türk Lirası (₺)"
        USD = "USD", "ABD Doları ($)"
        EUR = "EUR", "Euro (€)"

    proje = models.ForeignKey(
        Proje,
        on_delete=models.CASCADE,
        related_name="malzeme_fiyatlari",
        verbose_name="Proje",
    )
    malzeme = models.ForeignKey(
        Malzeme,
        on_delete=models.PROTECT,
        related_name="proje_fiyatlari",
        verbose_name="Malzeme",
    )
    yil = models.PositiveSmallIntegerField(verbose_name="Yıl")
    birim_fiyat = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Birim Fiyat",
    )
    para_birimi = models.CharField(
        max_length=3,
        choices=ParaBirimi.choices,
        default=ParaBirimi.TRY,
        verbose_name="Para Birimi",
    )
    kaynak = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Kaynak",
        help_text="Örn. Tedarikçi teklifi, piyasa fiyatı, ihale sonucu",
    )
    kaynak_url = models.URLField(
        max_length=250,
        blank=True,
        verbose_name="Kaynak URL",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Proje Malzeme Fiyatı"
        verbose_name_plural = "Proje Malzeme Fiyatları"
        ordering = ["proje__proje_kodu", "malzeme__malzeme_kodu", "-yil"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "proje", "malzeme", "yil"],
                name="uniq_proje_malzeme_fiyat_tenant_proje_malzeme_yil",
            ),
        ]

    def clean(self):
        super().clean()
        # FAZ 2: Maliyet hesabına sadece TRY girecek
        if self.para_birimi != self.ParaBirimi.TRY:
            raise ValidationError({"para_birimi": "FAZ 2'de maliyet hesabı yalnızca TRY para birimini destekler."})

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.malzeme.malzeme_kodu} / {self.yil}: {self.birim_fiyat} {self.para_birimi}"


class ProjePozMalzeme(TenantAwareModel):
    """Proje-poz seviyesinde malzeme alternatifi ve miktar override.

    Aynı malzeme farklı pozlarda farklı alternatiflere bağlanabilir:
    Poz 15 → Malzeme B, Poz 20 → Malzeme C şeklinde.
    """

    proje = models.ForeignKey(
        Proje,
        on_delete=models.CASCADE,
        related_name="poz_malzemeleri",
        verbose_name="Proje",
    )
    poz = models.ForeignKey(
        Poz,
        on_delete=models.PROTECT,
        related_name="proje_malzeme_alternatifleri",
        verbose_name="Poz",
    )
    kaynak_malzeme = models.ForeignKey(
        Malzeme,
        on_delete=models.PROTECT,
        related_name="kaynak_olan_proje_poz_malzemeleri",
        verbose_name="Kaynak Malzeme",
        help_text="PozMalzemeIliskisi üzerindeki orijinal malzeme",
    )
    etkin_malzeme = models.ForeignKey(
        Malzeme,
        on_delete=models.PROTECT,
        related_name="etkin_olan_proje_poz_malzemeleri",
        verbose_name="Etkin Malzeme",
        help_text="Bu projede bu poz için kullanılacak alternatif malzeme",
    )
    miktar_override = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0001"))],
        verbose_name="Miktar Override",
        help_text="PozMalzemeIliskisi.miktar yerine kullanılacak miktar (birim uyumu kontrol edilmez, FAZ 2'de dönüşüm yok)",
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Proje Poz Malzemesi"
        verbose_name_plural = "Proje Poz Malzemeleri"
        ordering = ["proje__proje_kodu", "poz__poz_no", "kaynak_malzeme__malzeme_kodu"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "proje", "poz", "kaynak_malzeme"],
                name="uniq_proje_poz_malzeme_tenant_proje_poz_kaynak",
            ),
            models.CheckConstraint(
                condition=~models.Q(kaynak_malzeme=models.F("etkin_malzeme")),
                name="check_proje_poz_malzeme_kaynak_etkin_farkli",
            ),
        ]

    def clean(self):
        super().clean()
        # Kaynak ve etkin malzeme aynı olamaz (constraint ile de sağlanıyor)
        if self.kaynak_malzeme_id == self.etkin_malzeme_id:
            raise ValidationError({"etkin_malzeme": "Kaynak malzeme ve etkin malzeme aynı olamaz."})

    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.poz.poz_no}: {self.kaynak_malzeme.malzeme_kodu} → {self.etkin_malzeme.malzeme_kodu}"


class MalzemeFiyat(TenantAwareModel):
    """Genel tenant bazlı malzeme fiyat modeli.

    ProjeMalzemeFiyat ve selected_teklif bulunamadığında fallback olarak kullanılır.
    Maliyet hesaplarında yalnızca TRY kabul edilecek.
    """

    class ParaBirimi(models.TextChoices):
        TRY = "TRY", "Türk Lirası (₺)"
        USD = "USD", "ABD Doları ($)"
        EUR = "EUR", "Euro (€)"

    malzeme = models.ForeignKey(
        Malzeme,
        on_delete=models.PROTECT,
        related_name="genel_fiyatlari",
        verbose_name="Malzeme",
    )
    yil = models.PositiveSmallIntegerField(verbose_name="Yıl")
    birim_fiyat = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Birim Fiyat",
    )
    para_birimi = models.CharField(
        max_length=3,
        choices=ParaBirimi.choices,
        default=ParaBirimi.TRY,
        verbose_name="Para Birimi",
    )
    kaynak = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Kaynak",
        help_text="Örn. Piyasa ortalaması, YFK, tedarikçi listesi",
    )
    kaynak_url = models.URLField(
        max_length=250,
        blank=True,
        verbose_name="Kaynak URL",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Malzeme Fiyatı (Genel)"
        verbose_name_plural = "Malzeme Fiyatları (Genel)"
        ordering = ["malzeme__malzeme_kodu", "-yil"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "malzeme", "yil"],
                name="uniq_malzeme_fiyat_tenant_malzeme_yil",
            ),
        ]

    def clean(self):
        super().clean()
        # Maliyet hesaplarında yalnızca TRY
        if self.para_birimi != self.ParaBirimi.TRY:
            raise ValidationError({"para_birimi": "Maliyet hesapları yalnızca TRY para birimini destekler."})

    def __str__(self) -> str:
        return f"{self.malzeme.malzeme_kodu} / {self.yil}: {self.birim_fiyat} {self.para_birimi}"
