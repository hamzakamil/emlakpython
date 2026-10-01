from decimal import Decimal

from django.db import models

from tenants.models import TenantAwareModel


class HesapTipi(models.TextChoices):
    KASA = "kasa", "Kasa"
    BANKA = "banka", "Banka"
    KREDI_KARTI = "kredi_karti", "Kredi Kartı"
    CEK = "cek", "Çek"


class KasaBankaHesabi(TenantAwareModel):
    """Kasa / banka hesabı (03-IS-AKISLARI.md §2)."""

    kod = models.CharField(max_length=20, verbose_name="Hesap Kodu")
    ad = models.CharField(max_length=200, verbose_name="Hesap Adı")
    tip = models.CharField(
        max_length=15, choices=HesapTipi.choices, default=HesapTipi.KASA, verbose_name="Hesap Tipi"
    )
    iban = models.CharField(max_length=34, blank=True, verbose_name="IBAN")
    para_birimi = models.CharField(max_length=3, default="TRY", verbose_name="Para Birimi")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")

    class Meta:
        verbose_name = "Kasa / Banka Hesabı"
        verbose_name_plural = "Kasa / Banka Hesapları"
        ordering = ["kod"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "kod"], name="uniq_kasa_tenant_kod"),
        ]

    def __str__(self) -> str:
        return f"{self.kod} — {self.ad}"


class FinansalIslem(TenantAwareModel):
    """Finansal işlem — gelir/gider/transfer (iptal deseni, fiziksel DELETE yok)."""

    class Yon(models.TextChoices):
        GELIR = "gelir", "Gelir"
        GIDER = "gider", "Gider"
        TRANSFER = "transfer", "Transfer"

    hesap = models.ForeignKey(
        KasaBankaHesabi, on_delete=models.PROTECT, related_name="islemler", verbose_name="Hesap",
    )
    muhasebe_fisi = models.ForeignKey(
        "accounting.MuhasebeFisi",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="finansal_islemler",
        verbose_name="Muhasebe Fişi",
    )
    cari = models.ForeignKey(
        "cari.Cari", on_delete=models.PROTECT, null=True, blank=True,
        related_name="finans_islemleri", verbose_name="Cari",
    )
    yon = models.CharField(max_length=10, choices=Yon.choices, verbose_name="Yön")
    tutar = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Tutar (₺)")
    islem_tarihi = models.DateField(verbose_name="İşlem Tarihi")
    aciklama = models.CharField(max_length=255, blank=True, verbose_name="Açıklama")
    is_cancelled = models.BooleanField(default=False, verbose_name="İptal Edildi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")

    class Meta:
        verbose_name = "Finansal İşlem"
        verbose_name_plural = "Finansal İşlemler"
        ordering = ["-islem_tarihi", "-id"]

    def __str__(self) -> str:
        return f"{self.hesap.kod} — {self.get_yon_display()}: {self.tutar} ₺"


class CekSenet(TenantAwareModel):
    """Çek/senet vade ve tahsilat/ödeme planı."""

    class Tur(models.TextChoices):
        CEK = "cek", "Çek"
        SENET = "senet", "Senet"

    class Durum(models.TextChoices):
        BEKLIYOR = "bekliyor", "Bekliyor"
        TAHSIL_EDILDI = "tahsil_edildi", "Tahsil Edildi"
        ODENDI = "odendi", "Ödendi"
        KARSILIKSIZ = "karsiliksiz", "Karşılıksız"
        IPTAL = "iptal", "İptal"

    tur = models.CharField(max_length=10, choices=Tur.choices, verbose_name="Tür")
    numara = models.CharField(max_length=50, verbose_name="Belge No")
    cari = models.ForeignKey("cari.Cari", on_delete=models.PROTECT, null=True, blank=True, related_name="cek_senetler")
    hesap = models.ForeignKey(KasaBankaHesabi, on_delete=models.PROTECT, null=True, blank=True, related_name="cek_senetler")
    proje = models.ForeignKey("construction.Proje", on_delete=models.PROTECT, null=True, blank=True, related_name="cek_senetler")
    tutar = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Tutar (₺)")
    vade_tarihi = models.DateField(verbose_name="Vade Tarihi")
    durum = models.CharField(max_length=20, choices=Durum.choices, default=Durum.BEKLIYOR)
    aciklama = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["durum", "vade_tarihi", "id"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "tur", "numara"], name="uniq_cek_senet_tenant_numara"),
        ]

    def __str__(self) -> str:
        return f"{self.get_tur_display()} {self.numara} - {self.tutar} ₺"


class Fatura(TenantAwareModel):
    """Fatura kaydı — borç/alacak takibi."""
    
    class DurumChoices(models.TextChoices):
        DRAFT = "taslak", "Taslak"
        ACTIVE = "aktif", "Aktif"
        PAID = "odendi", "Ödendi"
        CANCELLED = "iptal", "İptal"
    
    No = models.CharField(max_length=30, unique=True, verbose_name="Fatura No")
    cari = models.ForeignKey(
        "cari.Cari", on_delete=models.PROTECT, null=True, blank=True,
        related_name="faturalar", verbose_name="Cari"
    )
    kasa_banka_hesabi = models.ForeignKey(
        KasaBankaHesabi, on_delete=models.PROTECT, null=True, blank=True,
        related_name="faturalar", verbose_name="Kasa/Banka Hesabı"
    )
    iade_faturasi = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="iadeler",
        verbose_name="İade Edilen Fatura",
    )
    durum = models.CharField(
        max_length=20, choices=DurumChoices.choices, default=DurumChoices.DRAFT,
        verbose_name="Durum"
    )
    tarih = models.DateField(verbose_name="Fatura Tarihi")
    vade_tarihi = models.DateField(null=True, blank=True, verbose_name="Vade Tarihi")
    tutar = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Toplam Tutar"
    )
    alacakli = models.BooleanField(default=False, verbose_name="Alacaklı mı?")
    aciklama = models.CharField(max_length=255, blank=True, verbose_name="Açıklama")
    fatura_turu = models.CharField(
        max_length=20,
        choices=[
            ("satis", "Satış"),
            ("kira", "Kira"),
            ("hakedis", "Hakediş"),
            ("iade", "İade"),
            ("aidat", "Aidat"),
            ("hizmet", "Hizmet"),
            ("proforma", "Proforma"),
            ("alis", "Alış"),
        ],
        default="satis",
        verbose_name="Fatura Türü",
    )
    senaryo = models.CharField(
        max_length=20,
        choices=[
            ("e_fatura", "e-Fatura"),
            ("e_arsiv", "e-Arşiv"),
            ("kagit", "Kağıt"),
        ],
        default="kagit",
        verbose_name="e-Belge Senaryosu",
    )
    para_birimi = models.CharField(
        max_length=3,
        choices=[
            ("TRY", "TRY"),
            ("USD", "USD"),
            ("EUR", "EUR"),
            ("GBP", "GBP"),
        ],
        default="TRY",
        verbose_name="Para Birimi",
    )
    kur = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=Decimal("1"),
        verbose_name="Kur",
    )
    kdv_dahil_mi = models.BooleanField(default=False, verbose_name="KDV Dahil mi?")
    iskonto_tutari = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Belge İskontosu",
    )
    odenen_tutar = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Ödenen Tutar",
    )
    e_fatura_uuid = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="e-Fatura UUID",
    )
    e_fatura_durum = models.CharField(
        max_length=20,
        choices=[
            ("gonderilmedi", "Gönderilmedi"),
            ("gonderildi", "Gönderildi"),
            ("kabul", "Kabul"),
            ("red", "Red"),
        ],
        default="gonderilmedi",
        verbose_name="e-Fatura Durumu",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Fatura"
        verbose_name_plural = "Faturalar"
        ordering = ["-tarih", "-id"]

    def __str__(self) -> str:
        return f"{self.No} - {self.cari.ad if self.cari else '—'}"


class IdempotencyKey(TenantAwareModel):
    """Tenant içi tekrar çalıştırmaları güvenle engelleyen işlem anahtarı."""

    class Durum(models.TextChoices):
        PROCESSING = "processing", "İşleniyor"
        COMPLETED = "completed", "Tamamlandı"
        FAILED = "failed", "Başarısız"

    key = models.CharField(max_length=255)
    operation = models.CharField(max_length=100)
    request_hash = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Durum.choices,
        default=Durum.PROCESSING,
    )
    response_data = models.JSONField(default=dict, blank=True)
    resource_type = models.CharField(max_length=100, blank=True)
    resource_id = models.PositiveBigIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "operation", "key"],
                name="uniq_idempotency_tenant_operation_key",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "operation", "status"],
                name="finance_ide_tenant__c6ba6b_idx",
            ),
        ]


class FinansalOlay(TenantAwareModel):
    """Bir ekonomik işlemin değişmez, dengeli finansal olay kaydı."""

    class Durum(models.TextChoices):
        TASLAK = "taslak", "Taslak"
        KAYITLI = "kayitli", "Kayıtlı"
        IPTAL = "iptal", "İptal"

    olay_turu = models.CharField(max_length=50)
    kaynak_turu = models.CharField(max_length=100)
    kaynak_id = models.PositiveBigIntegerField()
    olay_anahtari = models.CharField(max_length=255)
    tarih = models.DateField()
    aciklama = models.CharField(max_length=255, blank=True)
    durum = models.CharField(
        max_length=20,
        choices=Durum.choices,
        default=Durum.TASLAK,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "olay_anahtari"],
                name="uniq_finansal_olay_tenant_key",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "kaynak_turu", "kaynak_id"],
                name="finance_fin_tenant__7e4ca2_idx",
            ),
            models.Index(
                fields=["tenant", "olay_turu", "tarih"],
                name="finance_fin_tenant__be0f04_idx",
            ),
        ]


class FinansalOlaySatiri(models.Model):
    """Finansal olayın borç/alacak satırı."""

    olay = models.ForeignKey(
        FinansalOlay,
        on_delete=models.PROTECT,
        related_name="satirlar",
    )
    hesap = models.ForeignKey(
        "accounting.HesapPlani",
        on_delete=models.PROTECT,
        related_name="finansal_olay_satirlari",
    )
    borc = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    alacak = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0"))
    aciklama = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(borc__gte=0) & models.Q(alacak__gte=0),
                name="fin_olay_satiri_nonnegative",
            ),
        ]


class FinansalOlayLog(TenantAwareModel):
    """Finansal olay geçişlerinin ve yan etkilerinin operasyon günlüğü."""

    olay = models.ForeignKey(
        FinansalOlay,
        on_delete=models.PROTECT,
        related_name="loglar",
    )
    islem = models.CharField(max_length=50)
    durum = models.CharField(max_length=20)
    veri = models.JSONField(default=dict, blank=True)
    hata = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class OutboxEvent(TenantAwareModel):
    """Transaction içinde yazılan, sonradan güvenle işlenecek olay kuyruğu."""

    class Durum(models.TextChoices):
        PENDING = "pending", "Bekliyor"
        PROCESSING = "processing", "İşleniyor"
        COMPLETED = "completed", "Tamamlandı"
        RETRY = "retry", "Tekrar Denenecek"
        DEAD_LETTER = "dead_letter", "Dead Letter"

    event_key = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20,
        choices=Durum.choices,
        default=Durum.PENDING,
    )
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)
    available_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "event_key"],
                name="uniq_outbox_tenant_event_key",
            ),
        ]
        indexes = [
            models.Index(
                fields=["tenant", "status", "available_at"],
                name="finance_out_tenant__e1e596_idx",
            ),
        ]


class FaturaKalemi(models.Model):
    """Fatura satırı; KDV ve tevkifat hesaplamasının tek kaynağı."""

    fatura = models.ForeignKey(Fatura, on_delete=models.CASCADE, related_name="kalemler")
    aciklama = models.CharField(max_length=255, verbose_name="Kalem Açıklaması")
    miktar = models.DecimalField(max_digits=14, decimal_places=4, verbose_name="Miktar")
    birim = models.CharField(max_length=20, default="ADET", verbose_name="Birim")
    birim_fiyat = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Birim Fiyat")
    kdv_orani = models.DecimalField(max_digits=5, decimal_places=2, default=20, verbose_name="KDV (%)")
    tevkifat_orani = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Tevkifat (%)")
    stopaj_orani = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Stopaj (%)")
    poz_no = models.CharField(max_length=50, blank=True, default="", verbose_name="Poz No")
    iskonto_orani = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="İskonto (%)",
    )
    kaynak_kabul_kalemi = models.ForeignKey(
        "purchasing.MalKabulKalemi",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fatura_kalemleri",
        verbose_name="Kaynak Kabul Kalemi",
        help_text="Satın alma/iade faturasında KDV ve fiyat snapshot kaynağı (FAZ 6B).",
    )

    class Meta:
        ordering = ["id"]

    @property
    def ara_toplam(self):
        brut = self.miktar * self.birim_fiyat
        iskonto = brut * self.iskonto_orani / Decimal("100")
        return (brut - iskonto).quantize(Decimal("0.01"))

    @property
    def kdv_tutari(self):
        return (self.ara_toplam * self.kdv_orani / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def tevkifat_tutari(self):
        return (self.kdv_tutari * self.tevkifat_orani / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def stopaj_tutari(self):
        return (self.ara_toplam * self.stopaj_orani / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def satir_toplami(self):
        return self.ara_toplam + self.kdv_tutari - self.tevkifat_tutari - self.stopaj_tutari


class VergiProfili(TenantAwareModel):
    """Tenant'a ait tekrar kullanılabilir KDV/tevkifat/stopaj kuralı."""

    kod = models.CharField(max_length=40, verbose_name="Profil Kodu")
    ad = models.CharField(max_length=120, verbose_name="Profil Adı")
    kdv_orani = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    tevkifat_orani = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    stopaj_orani = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ad"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "kod"], name="uniq_vergi_profili_tenant_kod"),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if any(not 0 <= oran <= 100 for oran in (self.kdv_orani, self.tevkifat_orani, self.stopaj_orani)):
            raise ValidationError("Vergi profili oranları 0-100 arasında olmalıdır.")


class Rapor(TenantAwareModel):
    """Rapor kaydı - various business reports."""

    class RaporTipiChoices(models.TextChoices):
        MIZAN = "mizan", "Mizan"
        CARI_OZET = "cari_ozet", "Cari Özet"
        FINANSAL_SUMMARY = "finansal_toplam", "Finansal Toplam"
        POZ_PLANI = "poz_planı", "Poz Planı (S-eğrisi)"

    tip = models.CharField(
        max_length=30, choices=RaporTipiChoices.choices, default=RaporTipiChoices.MIZAN,
        verbose_name="Rapor Tipi"
    )
    baslik = models.CharField(max_length=200, verbose_name="Başlık")
    filtreleme_verisi = models.JSONField(default=dict, blank=True, verbose_name="Filtreleme Verisi")
    sonuc_verisi = models.JSONField(default=dict, blank=True, verbose_name="Sonuç Verisi")
    cari = models.ForeignKey(
        "cari.Cari", on_delete=models.PROTECT, null=True, blank=True,
        related_name="raporlar", verbose_name="Cari"
    )
    kasa_banka_hesabi = models.ForeignKey(
        KasaBankaHesabi, on_delete=models.PROTECT, null=True, blank=True,
        related_name="raporlar", verbose_name="Kasa/Banka Hesabı"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Rapor"
        verbose_name_plural = "Raporlar"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_tip_display()}: {self.baslik}"


class Ayar(TenantAwareModel):
    """Uygulama ayarları - sistem reconfigurasyonu."""
    
    class AnahtarChoices(models.TextChoices):
        SITE_ADI = "site_adi", "Site Adı"
        VERGI_NO = "vergi_no", "Vergi Numarası"
        TELEFON = "telefon", "Telefon"
        EPOSTA = "eposta", "E-posta"
        CURRENCY_DEFAULT = "para_birimi_default", "Varsayılan Para Birimi"
    
    anahtar = models.CharField(max_length=50, choices=AnahtarChoices.choices, verbose_name="Anahtar")
    deger = models.CharField(max_length=255, verbose_name="Değer")
    aciklama = models.CharField(max_length=255, blank=True, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme")

    class Meta:
        verbose_name = "Ayar"
        verbose_name_plural = "Ayarlar"
        ordering = ["anahtar"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "anahtar"], name="uniq_ayar_tenant_anahtar"),
        ]

    def __str__(self) -> str:
        return f"{self.get_anahtar_display()}: {self.deger}"
