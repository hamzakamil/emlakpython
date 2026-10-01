"""FAZ 3A — Satın alma çekirdeği (talep + sipariş).

Kapsam dışı (FAZ 3B): MalKabul, StokHareketi, depo, malzeme tüketimi,
gerçek maliyet, stok değerleme. Bu fazda muhasebe fişi üretilmez.

Desen: construction TedarikciTeklifi (TenantAwareModel, is_active arşiv,
toplam_tutar save() hesabı, Check/UniqueConstraint).
"""

from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from tenants.models import TenantAwareModel


class BelgeTipi(models.TextChoices):
    """Merkezi numara üretiminde belge tipi (tenant + yıl + tip bazlı sayaç)."""

    TALEP = "talep", "Satın Alma Talebi"
    SIPARIS = "siparis", "Satın Alma Siparişi"
    MAL_KABUL = "mal_kabul", "Mal Kabul"


# Belge tipi → numara öneki (tek yer: services.belge_numarasi_uret kullanır).
BELGE_ONEKLERI = {
    BelgeTipi.TALEP: "ST",
    BelgeTipi.SIPARIS: "SS",
    BelgeTipi.MAL_KABUL: "MK",
}


class ParaBirimi(models.TextChoices):
    TRY = "TRY", "Türk Lirası (₺)"
    USD = "USD", "ABD Doları ($)"
    EUR = "EUR", "Euro (€)"


class BelgeNumaraSayaci(TenantAwareModel):
    """Merkezi belge numara sayacı — tenant + yıl + belge tipi bazında tekil satır.

    Numara üretimi services.belge_numarasi_uret içinden
    transaction.atomic + select_for_update ile yapılır; aynı numara iki kez
    üretilmez. UniqueConstraint ikinci güvencedir.
    """

    belge_tipi = models.CharField(
        max_length=20, choices=BelgeTipi.choices, verbose_name="Belge Tipi"
    )
    yil = models.PositiveSmallIntegerField(verbose_name="Yıl")
    son_no = models.PositiveIntegerField(default=0, verbose_name="Son Numara")

    class Meta:
        verbose_name = "Belge Numara Sayacı"
        verbose_name_plural = "Belge Numara Sayaçları"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "belge_tipi", "yil"],
                name="uniq_belge_sayac_tenant_tip_yil",
            )
        ]

    def __str__(self) -> str:
        return f"{self.tenant_id}/{self.belge_tipi}/{self.yil}: {self.son_no}"


class SatinAlmaTalebi(TenantAwareModel):
    """Satın alma talebi başlığı — onay akışı: taslak → onaya gönderildi →
    onaylandı/reddedildi → siparişe dönüştü / iptal.

    Fiziksel silme yok; destroy isteği iptal durumuna çeker (views).
    """

    class Durum(models.TextChoices):
        TASLAK = "taslak", "Taslak"
        ONAYA_GONDERILDI = "onaya_gonderildi", "Onaya Gönderildi"
        ONAYLANDI = "onaylandi", "Onaylandı"
        REDDEDILDI = "reddedildi", "Reddedildi"
        SIPARISE_DONUSTU = "siparise_donustu", "Siparişe Dönüştü"
        IPTAL = "iptal", "İptal"

    proje = models.ForeignKey(
        "construction.Proje",
        on_delete=models.PROTECT,
        related_name="satin_alma_talepleri",
        verbose_name="Proje",
    )
    talep_no = models.CharField(
        max_length=30,
        verbose_name="Talep No",
        help_text="Merkezi sayaçtan otomatik üretilir (ST-YYYY-NNNN).",
    )
    tarih = models.DateField(default=date.today, verbose_name="Talep Tarihi")
    talep_sahibi = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="satin_alma_talepleri",
        verbose_name="Talep Sahibi",
    )
    durum = models.CharField(
        max_length=20, choices=Durum.choices, default=Durum.TASLAK, verbose_name="Durum"
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Satın Alma Talebi"
        verbose_name_plural = "Satın Alma Talepleri"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "talep_no"], name="uniq_talep_tenant_no"
            )
        ]

    def __str__(self) -> str:
        return f"{self.talep_no} ({self.durum})"


class SatinAlmaTalebiKalemi(TenantAwareModel):
    """Talep kalemi — proje başlıktan alınır, kalemde tekrar tutulmaz."""

    talep = models.ForeignKey(
        SatinAlmaTalebi,
        on_delete=models.CASCADE,
        related_name="kalemler",
        verbose_name="Talep",
    )
    malzeme = models.ForeignKey(
        "construction.Malzeme",
        on_delete=models.PROTECT,
        related_name="satin_alma_talep_kalemleri",
        verbose_name="Malzeme",
    )
    poz = models.ForeignKey(
        "construction.Poz",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="satin_alma_talep_kalemleri",
        verbose_name="Poz",
    )
    mahal = models.ForeignKey(
        "construction.Mahal",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="satin_alma_talep_kalemleri",
        verbose_name="Mahal",
    )
    miktar = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
        verbose_name="Miktar",
    )
    birim = models.CharField(max_length=20, blank=True, default="", verbose_name="Birim")
    ihtiyac_tarihi = models.DateField(null=True, blank=True, verbose_name="İhtiyaç Tarihi")
    tahmini_birim_fiyat = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Tahmini Birim Fiyat (₺)",
    )
    secili_teklif = models.ForeignKey(
        "construction.TedarikciTeklifi",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="secili_oldugu_talep_kalemleri",
        verbose_name="Seçili Teklif",
        help_text="Tenant/proje/malzeme uyumu zorunludur.",
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Satın Alma Talep Kalemi"
        verbose_name_plural = "Satın Alma Talep Kalemleri"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(miktar__gt=0), name="check_talep_kalem_miktar_pozitif"
            ),
        ]

    def clean(self):
        if self.talep_id and self.talep.proje_id:
            proje_id = self.talep.proje_id
            if self.mahal_id and self.mahal.proje_id != proje_id:
                raise ValidationError({"mahal": "Mahal, talebin projesine ait olmalıdır."})
        if self.secili_teklif_id:
            teklif = self.secili_teklif
            if teklif.tenant_id != self.tenant_id:
                raise ValidationError({"secili_teklif": "Teklif bu firma kapsamına ait değil."})
            if self.talep_id and teklif.proje_id != self.talep.proje_id:
                raise ValidationError({"secili_teklif": "Teklif, talebin projesine ait olmalıdır."})
            if self.malzeme_id and teklif.malzeme_id != self.malzeme_id:
                raise ValidationError({"secili_teklif": "Teklif, kalemin malzemesine ait olmalıdır."})

    def save(self, *args, **kwargs):
        if not self.birim and self.malzeme_id:
            self.birim = self.malzeme.birim
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.talep.talep_no} / {self.malzeme.ad} x {self.miktar}"


class SatinAlmaSiparisi(TenantAwareModel):
    """Satın alma siparişi başlığı — onay akışı: taslak → onay bekliyor →
    onaylandı → kısmi teslim / tamamlandı / iptal.

    Bu fazda muhasebe fişi üretilmez (FAZ 3B+).
    """

    class Durum(models.TextChoices):
        TASLAK = "taslak", "Taslak"
        ONAY_BEKLIYOR = "onay_bekliyor", "Onay Bekliyor"
        ONAYLANDI = "onaylandi", "Onaylandı"
        KISMI_TESLIM = "kismi_teslim", "Kısmi Teslim"
        TAMAMLANDI = "tamamlandi", "Tamamlandı"
        IPTAL = "iptal", "İptal"

    siparis_no = models.CharField(
        max_length=30,
        verbose_name="Sipariş No",
        help_text="Merkezi sayaçtan otomatik üretilir (SS-YYYY-NNNN).",
    )
    tedarikci = models.ForeignKey(
        "construction.Tedarikci",
        on_delete=models.PROTECT,
        related_name="satin_alma_siparisleri",
        verbose_name="Tedarikçi",
    )
    proje = models.ForeignKey(
        "construction.Proje",
        on_delete=models.PROTECT,
        related_name="satin_alma_siparisleri",
        verbose_name="Proje",
    )
    kaynak_talep = models.ForeignKey(
        SatinAlmaTalebi,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="siparisler",
        verbose_name="Kaynak Talep",
    )
    tarih = models.DateField(default=date.today, verbose_name="Sipariş Tarihi")
    teslim_tarihi = models.DateField(null=True, blank=True, verbose_name="Teslim Tarihi")
    para_birimi = models.CharField(
        max_length=3, choices=ParaBirimi.choices, default=ParaBirimi.TRY, verbose_name="Para Birimi"
    )
    kur = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.0001"))],
        verbose_name="Kur",
    )
    durum = models.CharField(
        max_length=20, choices=Durum.choices, default=Durum.TASLAK, verbose_name="Durum"
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Satın Alma Siparişi"
        verbose_name_plural = "Satın Alma Siparişleri"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "siparis_no"], name="uniq_siparis_tenant_no"
            )
        ]

    def __str__(self) -> str:
        return f"{self.siparis_no} ({self.durum})"


class SatinAlmaSiparisiKalemi(TenantAwareModel):
    """Sipariş kalemi — birim_fiyat sipariş anındaki kesin fiyattır; teklif
    sonradan değişse bile geriye dönük değişmez (snapshot, ek alan yok)."""

    siparis = models.ForeignKey(
        SatinAlmaSiparisi,
        on_delete=models.CASCADE,
        related_name="kalemler",
        verbose_name="Sipariş",
    )
    malzeme = models.ForeignKey(
        "construction.Malzeme",
        on_delete=models.PROTECT,
        related_name="satin_alma_siparis_kalemleri",
        verbose_name="Malzeme",
    )
    poz = models.ForeignKey(
        "construction.Poz",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="satin_alma_siparis_kalemleri",
        verbose_name="Poz",
    )
    mahal = models.ForeignKey(
        "construction.Mahal",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="satin_alma_siparis_kalemleri",
        verbose_name="Mahal",
    )
    miktar = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
        verbose_name="Miktar",
    )
    birim = models.CharField(max_length=20, blank=True, default="", verbose_name="Birim")
    birim_fiyat = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Birim Fiyat",
        help_text="Sipariş anındaki kesin fiyat; sonradan değişmez.",
    )
    toplam_tutar = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Toplam Tutar",
        help_text="Miktar x birim fiyat; kayıtta otomatik hesaplanır.",
    )
    kaynak_teklif = models.ForeignKey(
        "construction.TedarikciTeklifi",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kaynak_oldugu_siparis_kalemleri",
        verbose_name="Kaynak Teklif",
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Satın Alma Sipariş Kalemi"
        verbose_name_plural = "Satın Alma Sipariş Kalemleri"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(miktar__gt=0), name="check_siparis_kalem_miktar_pozitif"
            ),
            models.CheckConstraint(
                condition=models.Q(birim_fiyat__gt=0), name="check_siparis_kalem_fiyat_pozitif"
            ),
        ]

    def save(self, *args, **kwargs):
        miktar = Decimal(str(self.miktar))
        birim_fiyat = Decimal(str(self.birim_fiyat))
        self.toplam_tutar = (miktar * birim_fiyat).quantize(Decimal("0.01"))
        if not self.birim and self.malzeme_id:
            self.birim = self.malzeme.birim
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.siparis.siparis_no} / {self.malzeme.ad} x {self.miktar}"


# =============================================================================
# FAZ 3B — Mal Kabul + Stok Hareketi
# =============================================================================


class Depo(TenantAwareModel):
    """Depo — malzemenin stoklandığı fiziksel veya mantıksal alan."""

    kod = models.CharField(max_length=30, verbose_name="Depo Kodu")
    ad = models.CharField(max_length=150, verbose_name="Depo Adı")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Depo"
        verbose_name_plural = "Depolar"
        ordering = ["kod"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "kod"], name="uniq_depo_tenant_kod"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.kod} — {self.ad}"


class MalKabul(TenantAwareModel):
    """Mal kabul belgesi — onaylanan sipariş kalemlerinin kısmi/tam kabulü.

    Onaylanan kabul, depo ekseninde GİRİŞ stok hareketi üretir (services).
    """

    class Durum(models.TextChoices):
        TASLAK = "taslak", "Taslak"
        ONAYLANDI = "onaylandi", "Onaylandı"
        KISMI_TESLIM = "kismi_teslim", "Kısmi Teslim"
        TAMAMLANDI = "tamamlandi", "Tamamlandı"
        IPTAL = "iptal", "İptal"

    siparis = models.ForeignKey(
        SatinAlmaSiparisi,
        on_delete=models.PROTECT,
        related_name="mal_kabulleri",
        verbose_name="Satın Alma Siparişi",
    )
    proje = models.ForeignKey(
        "construction.Proje",
        on_delete=models.PROTECT,
        related_name="mal_kabulleri",
        verbose_name="Proje",
    )
    depo = models.ForeignKey(
        Depo,
        on_delete=models.PROTECT,
        related_name="mal_kabulleri",
        verbose_name="Depo",
    )
    belge_no = models.CharField(
        max_length=30,
        verbose_name="Belge No",
        help_text="Merkezi sayaçtan otomatik üretilir (MK-YYYY-NNNN).",
    )
    kabul_tarihi = models.DateField(default=date.today, verbose_name="Kabul Tarihi")
    durum = models.CharField(
        max_length=20,
        choices=Durum.choices,
        default=Durum.TASLAK,
        verbose_name="Durum",
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mal_kabulleri_created",
        verbose_name="Oluşturan",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mal_kabulleri_updated",
        null=True,
        blank=True,
        verbose_name="Güncelleyen",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Mal Kabul"
        verbose_name_plural = "Mal Kabulleri"
        ordering = ["-kabul_tarihi", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "belge_no"], name="uniq_mal_kabul_tenant_belge_no"
            ),
            models.CheckConstraint(
                # Meta gövdesi sınıf niteliği göremediği için liste açık yazılır.
                condition=models.Q(
                    durum__in=["taslak", "onaylandi", "kismi_teslim", "tamamlandi", "iptal"]
                ),
                name="check_mal_kabul_durum_gecerli",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.belge_no} ({self.get_durum_display()})"


class MalKabulKalemi(TenantAwareModel):
    """Mal kabul kalemi — sipariş kalemine bağlanır, kabul/red miktarını taşır."""

    mal_kabul = models.ForeignKey(
        MalKabul,
        on_delete=models.CASCADE,
        related_name="kalemler",
        verbose_name="Mal Kabul",
    )
    siparis_kalemi = models.ForeignKey(
        SatinAlmaSiparisiKalemi,
        on_delete=models.PROTECT,
        related_name="mal_kabul_kalemleri",
        verbose_name="Sipariş Kalemi",
    )
    malzeme = models.ForeignKey(
        "construction.Malzeme",
        on_delete=models.PROTECT,
        related_name="mal_kabul_kalemleri",
        verbose_name="Malzeme",
    )
    siparis_miktari = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
        verbose_name="Sipariş Miktarı",
        help_text="Sipariş kaleminden kopyalanan miktar (snapshot).",
    )
    kabul_miktari = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0"))],
        default=Decimal("0"),
        verbose_name="Kabul Miktarı",
    )
    red_miktari = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0"))],
        default=Decimal("0"),
        verbose_name="Red Miktarı",
    )
    birim = models.CharField(max_length=20, blank=True, default="", verbose_name="Birim")
    birim_fiyat_snapshot = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Birim Fiyat Snapshot",
        help_text="Sipariş kalemindeki birim fiyatın kopyası (mal kabul anında).",
    )
    kdv_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="KDV (%)",
        help_text="Kaleme özel KDV oranı (FAZ 6C); boşsa tenant VARSAYILAN profili → %20 uygulanır.",
    )
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Mal Kabul Kalemi"
        verbose_name_plural = "Mal Kabul Kalemleri"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kabul_miktari__gte=0),
                name="check_mal_kabul_kalem_kabul_miktar_negatif_olmaz",
            ),
            models.CheckConstraint(
                condition=models.Q(red_miktari__gte=0),
                name="check_mal_kabul_kalem_red_miktar_negatif_olmaz",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(kabul_miktari__gt=0) | models.Q(red_miktari__gt=0)
                ),
                name="check_mal_kabul_kalem_en_az_bir_miktar",
            ),
        ]

    def clean(self):
        if self.malzeme_id and self.siparis_kalemi_id:
            if self.malzeme_id != self.siparis_kalemi.malzeme_id:
                raise ValidationError(
                    {"malzeme": "Malzeme sipariş kalemindeki malzeme ile uyuşmuyor."}
                )
        if not self.birim and self.malzeme_id:
            self.birim = self.malzeme.birim
        if not self.birim_fiyat_snapshot and self.siparis_kalemi_id:
            self.birim_fiyat_snapshot = self.siparis_kalemi.birim_fiyat
        if not self.siparis_miktari and self.siparis_kalemi_id:
            self.siparis_miktari = self.siparis_kalemi.miktar
        if self.kdv_orani is not None and not Decimal("0") <= self.kdv_orani <= Decimal("100"):
            raise ValidationError({"kdv_orani": "KDV oranı 0-100 arasında olmalıdır."})
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.mal_kabul.belge_no} / {self.malzeme.ad} kabul={self.kabul_miktari} red={self.red_miktari}"


class StokHareketi(TenantAwareModel):
    """Stok hareketi — depo eksenli giriş/çıkış kaydı.

    Mal kabul ONAYLANDIĞINDA GİRİŞ hareketi oluşur (services); iptalde ters
    (ÇIKIŞ) hareket açılır. Bakiye tabloda tutulmaz, hareketlerden türetilir.
    """

    class HareketTipi(models.TextChoices):
        GIRIS = "giris", "Giriş"
        CIKIS = "cikis", "Çıkış"
        TRANSFER = "transfer", "Transfer"
        IADE = "iade", "İade"
        FIRE = "fire", "Fire"
        SAYIM = "sayim", "Sayım"
        DUZELTME = "duzeltme", "Düzeltme"

    depo = models.ForeignKey(
        Depo,
        on_delete=models.PROTECT,
        related_name="stok_hareketleri",
        verbose_name="Depo",
    )
    malzeme = models.ForeignKey(
        "construction.Malzeme",
        on_delete=models.PROTECT,
        related_name="stok_hareketleri",
        verbose_name="Malzeme",
    )
    hareket_tipi = models.CharField(
        max_length=20,
        choices=HareketTipi.choices,
        verbose_name="Hareket Tipi",
    )
    miktar = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
        verbose_name="Miktar",
    )
    birim = models.CharField(max_length=20, blank=True, default="", verbose_name="Birim")
    maliyet = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Birim Maliyet",
        help_text="Hareket anındaki birim maliyet (sipariş fiyatı snapshotu; değerleme yok).",
    )
    tarih = models.DateField(default=date.today, verbose_name="Hareket Tarihi")
    aciklama = models.TextField(blank=True, verbose_name="Açıklama")
    kaynak_belge_tipi = models.CharField(
        max_length=50, blank=True, default="", verbose_name="Kaynak Belge Tipi"
    )
    kaynak_belge_id = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name="Kaynak Belge ID"
    )
    kaynak_belge_kalem_id = models.PositiveBigIntegerField(
        null=True, blank=True, verbose_name="Kaynak Belge Kalem ID"
    )
    proje = models.ForeignKey(
        "construction.Proje",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stok_hareketleri",
        verbose_name="Proje",
    )
    poz = models.ForeignKey(
        "construction.Poz",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stok_hareketleri",
        verbose_name="Poz",
    )
    mahal = models.ForeignKey(
        "construction.Mahal",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stok_hareketleri",
        verbose_name="Mahal",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stok_hareketleri_created",
        verbose_name="Oluşturan",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Stok Hareketi"
        verbose_name_plural = "Stok Hareketleri"
        ordering = ["-tarih", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(miktar__gt=0),
                name="check_stok_hareketi_miktar_pozitif",
            ),
            models.CheckConstraint(
                condition=models.Q(maliyet__gte=0),
                name="check_stok_hareketi_maliyet_negatif_olmaz",
            ),
            # Aynı mal kabul kalemi için tek aktif GİRİŞ hareketi (duplicate engeli).
            models.UniqueConstraint(
                fields=["kaynak_belge_tipi", "kaynak_belge_id", "kaynak_belge_kalem_id"],
                condition=models.Q(kaynak_belge_tipi="MalKabul") & models.Q(is_active=True),
                name="uniq_stok_hareketi_mal_kabul_kalem",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_hareket_tipi_display()} {self.malzeme.ad} {self.miktar} {self.birim}"


class StokHesapEsleme(TenantAwareModel):
    """FAZ 4 — Malzeme bazında stok/KDV hesap eşlemesi.

    Malzeme boşsa tenant varsayılanıdır. Çözüm sırası: malzemeye özel →
    tenant varsayılanı → sabit kod (stok: 150, KDV: 191). Yeni hesap planı
    oluşturmaz; mevcut HesapPlani kayıtlarına bağlanır.
    """

    class HesapTuru(models.TextChoices):
        STOK = "stok", "Stok Hesabı"
        KDV = "kdv", "KDV Hesabı"

    malzeme = models.ForeignKey(
        "construction.Malzeme",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="hesap_eslemeleri",
        verbose_name="Malzeme",
        help_text="Boş bırakılırsa tenant varsayılanı olur.",
    )
    hesap_turu = models.CharField(
        max_length=10, choices=HesapTuru.choices, verbose_name="Hesap Türü"
    )
    hesap = models.ForeignKey(
        "accounting.HesapPlani",
        on_delete=models.PROTECT,
        related_name="stok_eslemeleri",
        verbose_name="Hesap",
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Stok Hesap Eşlemesi"
        verbose_name_plural = "Stok Hesap Eşlemeleri"
        ordering = ["hesap_turu", "malzeme__malzeme_kodu"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "hesap_turu"],
                condition=models.Q(malzeme__isnull=True),
                name="uniq_stok_hesap_varsayilan",
            ),
            models.UniqueConstraint(
                fields=["tenant", "malzeme", "hesap_turu"],
                condition=models.Q(malzeme__isnull=False),
                name="uniq_stok_hesap_malzeme",
            ),
        ]

    def __str__(self) -> str:
        hedef = self.malzeme.malzeme_kodu if self.malzeme_id else "VARSAYILAN"
        return f"{hedef} / {self.hesap_turu} → {self.hesap.kod}"



