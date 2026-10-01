"""Core uygulama modeleri - Kural 36 & Kural 37 entegrasyonlu"""
from django.db import models


class SistemAyarları(models.Model):
    """Sistem ayarları - Kural 37: UI Status Display ve genel konfigürasyon"""
    
    class Tur(models.TextChoices):
        SISTEM = "sistem", "Sistem"
        KULLANICI = "kullanici", "Kullanıcı"
        KURUM = "kurum", "Kurum"
    
    tur = models.CharField(
        max_length=20, choices=Tur.choices, default=Tur.SISTEM, verbose_name="Ayar Türü"
    )
    anahtar = models.CharField(max_length=100, unique=True, verbose_name="Anahtar")
    deger = models.TextField(verbose_name="Değer")
    aciklama = models.CharField(max_length=255, blank=True, verbose_name="Açıklama")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncelleme")
    
    class Meta:
        verbose_name = "Sistem Ayarı"
        verbose_name_plural = "Sistem Ayarları"
        ordering = ["tur", "anahtar"]
    
    def __str__(self) -> str:
        return f"{self.anahtar}: {self.deger}"


class RaporTipi(models.Model):
    """Rapor tipleri - Kural 36: Audit Trail ve Kural 37: Dashboard raporları"""
    
    class RaporTur(models.TextChoices):
        BALANCE_SHEET = "balance_sheet", "Denge Hesabı"
        INCOME_STATEMENT = "income_statement", "Kar/Zarar Tablosu"
        CASH_FLOW = "cash_flow", "Nakit Akışı Raporu"
        TRIAL_BALANCE = "trial_balance", "Denen Deneme Denge Hesabı"
        AUDIT_LOG = "audit_log", "Audit Log Raporu"
        
    ad = models.CharField(max_length=100, verbose_name="Rapor Adı")
    tur = models.CharField(
        max_length=20, choices=RaporTur.choices, verbose_name="Rapor Türü"
    )
    description = models.TextField(blank=True, verbose_name="Açıklama")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncelleme")
    
    class Meta:
        verbose_name = "Rapor Tipi"
        verbose_name_plural = "Rapor Tipleri"
        ordering = ["ad"]
    
    def __str__(self) -> str:
        return f"{self.ad} ({self.get_tur_display()})"


class Rapor(models.Model):
    """Raporlar - Kural 36 & Kural 37 entegrasyonlu"""
    
    rapor_tipi = models.ForeignKey(
        RaporTipi, on_delete=models.PROTECT, verbose_name="Rapor Tipi"
    )
    baslik = models.CharField(max_length=200, verbose_name="Başlık")
    yil = models.IntegerField(verbose_name="Yıl")
    ay = models.IntegerField(null=True, blank=True, verbose_name="Ay")
    content = models.TextField(blank=True, verbose_name="İçerik/JSON")
    created_by = models.ForeignKey(
        "auth.User", on_delete=models.PROTECT, verbose_name="Oluşturan"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma")
    
    class Meta:
        verbose_name = "Rapor"
        verbose_name_plural = "Raporlar"
        ordering = ["-yil", "-ay", "baslik"]
    
    def __str__(self) -> str:
        ay_str = f"- {self.ay}" if self.ay else ""
        return f"{self.baslik} ({self.yil}{ay_str})"