from django.db import models

from tenants.models import TenantAwareModel


class CariTipi(models.TextChoices):
    """Cari taraf tipi (02-VERI-MODELI.md §2.3)."""

    KIRACI = "kiraci", "Kiracı"
    MALIK = "malik", "Malik"
    TEDARIKCI = "tedarikci", "Tedarikçi"
    TASERON = "taseron", "Taşeron"
    DIGER = "diger", "Diğer"

class VergiMukellefiyeti(models.TextChoices):
    KDV_MUKELLEFI = "kdv_mukellefi", "KDV Mükellefi"
    KDV_ISTISNA = "kdv_istisna", "KDV İstisna"
    BASIT_USUL = "basit_usul", "Basit Usul"
    VERGI_MUKELLEFI_DEGIL = "vergi_mukellefi_degil", "Vergi Mükellefi Değil"

class OdemeSekli(models.TextChoices):
    NAKIT = "nakit", "Nakit"
    HAVALE = "havale", "Havale"
    CEK = "cek", "Çek"
    SENET = "senet", "Senet"
    KREDI_KARTI = "kredi_karti", "Kredi Kartı"
    TAKAS = "takas", "Takas"

class CariParaBirimi(models.TextChoices):
    TRY = "TRY", "TRY"
    USD = "USD", "USD"
    EUR = "EUR", "EUR"
    GBP = "GBP", "GBP"

class EFaturaProfili(models.TextChoices):
    E_FATURA = "e_fatura", "e-Fatura"
    E_ARSIV = "e_arsiv", "e-Arşiv"
    KAGIT = "kagit", "Kağıt"


class Cari(TenantAwareModel):
    """Cari kartı — kiracı, malik, tedarikçi, taşeron vb. taraf."""

    class Tur(models.TextChoices):
        BIREYSEL = "bireysel", "Bireysel"
        KURUMSAL = "kurumsal", "Kurumsal"

    ad = models.CharField(max_length=255, verbose_name="Ad / Unvan")
    tip = models.CharField(
        max_length=20, choices=CariTipi.choices, default=CariTipi.DIGER, verbose_name="Cari Tipi"
    )
    tur = models.CharField(
        max_length=20, choices=Tur.choices, default=Tur.BIREYSEL, verbose_name="Bireysel / Kurumsal"
    )
    vergi_no = models.CharField(max_length=10, blank=True, verbose_name="Vergi Kimlik No")
    vergi_dairesi = models.CharField(max_length=150, blank=True, verbose_name="Vergi Dairesi")
    tc_kimlik_no = models.CharField(max_length=11, blank=True, verbose_name="T.C. Kimlik No")
    ticaret_sicil_no = models.CharField(max_length=50, blank=True, verbose_name="Ticaret Sicil No")
    mersis_no = models.CharField(max_length=16, blank=True, verbose_name="MERSİS No")
    vergi_mukellefiyeti = models.CharField(
        max_length=30, choices=VergiMukellefiyeti.choices,
        default=VergiMukellefiyeti.KDV_MUKELLEFI, verbose_name="Vergi Mükellefiyeti",
    )
    telefon = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    telefonlar = models.JSONField(default=list, blank=True, verbose_name="Telefonlar")
    fatura_adresi = models.TextField(blank=True, verbose_name="Fatura Adresi")
    sevk_adresi = models.TextField(blank=True, verbose_name="Sevk Adresi")
    il = models.CharField(max_length=100, blank=True, verbose_name="İl")
    ilce = models.CharField(max_length=100, blank=True, verbose_name="İlçe")
    posta_kodu = models.CharField(max_length=10, blank=True, verbose_name="Posta Kodu")
    yetkili_kisi = models.CharField(max_length=150, blank=True, verbose_name="Yetkili Kişi")
    yetkili_telefon = models.CharField(max_length=20, blank=True, verbose_name="Yetkili Telefon")
    yetkili_kisiler = models.JSONField(default=list, blank=True, verbose_name="Yetkili Kişiler")
    cep_telefonu = models.CharField(max_length=20, blank=True, verbose_name="Cep Telefonu")
    cep_telefonlari = models.JSONField(default=list, blank=True, verbose_name="Cep Telefonları")
    eposta = models.EmailField(blank=True, verbose_name="E-posta")
    epostalar = models.JSONField(default=list, blank=True, verbose_name="E-postalar")
    web_sitesi = models.URLField(blank=True, verbose_name="Web Sitesi")
    iban = models.CharField(max_length=34, blank=True, verbose_name="IBAN")
    banka_adi = models.CharField(max_length=150, blank=True, verbose_name="Banka Adı")
    sube_adi = models.CharField(max_length=150, blank=True, verbose_name="Şube Adı")
    odeme_sekli = models.CharField(
        max_length=20, choices=OdemeSekli.choices, default=OdemeSekli.HAVALE, verbose_name="Ödeme Şekli",
    )
    vade_gunu = models.PositiveIntegerField(default=0, verbose_name="Vade Günü")
    iskonto_orani = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="İskonto Oranı")
    risk_limiti = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Risk Limiti")
    para_birimi = models.CharField(
        max_length=3, choices=CariParaBirimi.choices, default=CariParaBirimi.TRY, verbose_name="Para Birimi",
    )
    muhasebe_hesap_kodu = models.CharField(max_length=30, blank=True, verbose_name="Muhasebe Hesap Kodu")
    e_fatura_profili = models.CharField(
        max_length=10, choices=EFaturaProfili.choices, default=EFaturaProfili.KAGIT, verbose_name="e-Fatura Profili",
    )
    adres = models.TextField(blank=True, verbose_name="Adres")
    eski_adres = models.TextField(blank=True, verbose_name="Eski Adres")
    ulke = models.CharField(max_length=100, default="Türkiye", blank=True, verbose_name="Ülke")
    grup = models.CharField(max_length=150, blank=True, verbose_name="Grup")
    proje = models.ForeignKey(
        "construction.Proje", on_delete=models.PROTECT, null=True, blank=True,
        related_name="cari_kartlari", verbose_name="Proje",
    )
    notlar = models.TextField(blank=True, verbose_name="Notlar")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Cari"
        verbose_name_plural = "Cariler"
        ordering = ["ad"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "ad"], name="uniq_cari_tenant_ad"),
        ]

    def __str__(self) -> str:
        return self.ad

    def clean(self) -> None:
        from django.core.exceptions import ValidationError

        if self.vergi_no and (not self.vergi_no.isdigit() or len(self.vergi_no) != 10):
            raise ValidationError({"vergi_no": "Vergi kimlik no 10 hane rakam olmalıdır."})


class CariHareket(TenantAwareModel):
    """Cari hesap hareketi — borç/alacak kalemi (iptal deseni, fiziksel DELETE yok)."""

    class Yon(models.TextChoices):
        BORC = "borc", "Borç"
        ALACAK = "alacak", "Alacak"

    cari = models.ForeignKey(
        Cari, on_delete=models.PROTECT, related_name="hareketler", verbose_name="Cari",
    )
    fatura = models.ForeignKey(
        "finance.Fatura",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cari_hareketleri",
        verbose_name="Kaynak Fatura",
    )
    muhasebe_fisi = models.ForeignKey(
        "accounting.MuhasebeFisi",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cari_hareketleri",
        verbose_name="Muhasebe Fişi",
    )
    yon = models.CharField(max_length=10, choices=Yon.choices, verbose_name="Yön")
    tutar = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Tutar (₺)")
    aciklama = models.CharField(max_length=255, blank=True, verbose_name="Açıklama")
    islem_tarihi = models.DateField(verbose_name="İşlem Tarihi")
    is_cancelled = models.BooleanField(default=False, verbose_name="İptal Edildi")
    iptal_nedeni = models.CharField(max_length=255, blank=True, verbose_name="İptal Nedeni")
    finansal_islem = models.ForeignKey(
        "finance.FinansalIslem",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cari_hareketleri",
        verbose_name="Kaynak Finansal İşlem",
        help_text="Ödeme iptali ters hareket bağlantısı (FAZ 6B).",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")

    class Meta:
        verbose_name = "Cari Hareket"
        verbose_name_plural = "Cari Hareketler"
        ordering = ["-islem_tarihi", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["fatura"],
                condition=models.Q(fatura__isnull=False),
                name="uniq_cari_hareket_fatura",
            ),
            models.UniqueConstraint(
                fields=["finansal_islem"],
                condition=models.Q(finansal_islem__isnull=False),
                name="uniq_cari_hareket_finansal_islem",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cari.ad} — {self.get_yon_display()}: {self.tutar} ₺"
