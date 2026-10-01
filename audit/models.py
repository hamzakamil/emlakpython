"""Audit Log Modelleri - Kural 36: Audit Trail"""

import json

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth import get_user_model
from tenants.models import TenantAwareModel

User = get_user_model()


class AuditLog(TenantAwareModel):
    """
    Sistemde yapılan tüm değişikliklerin audit log'ını tutar (Kural 36).
    
    Kural 36 kapsamı:
    * Hesap açma/degistirme
    * Cari açma/degistirme
    * Fatura oluşturma/degistirme/iptal
    * Fiş oluşturma/Muhasebeleştirme/Ters kayıt
    * Dönem açma/kapatma
    * Hesap planı değişikliği
    * Manuel muhasebe fişi
    
    Tutulan bilgiler:
    * kullanıcı: Kim işlemi yapın
    * tarih: Ne zaman yapıldı
    * islem: Hangı işlem yapildi (CREATE, UPDATE, DELETE, REVERSE, CORRECTION)
    * eski_değer: Değişiklikten önceki değer (JSON)
    * yeni_değer: Değişiklikten sonraki değer (JSON)
    * kaynak: Hangı model/nesne değişti
    * ip: İşlemin yapıldığı IP
    * oturum: Oturum bilgisi
    * sebep: İşlemin sebebi/açıklaması
    """
    
    class IslemTürü(models.TextChoices):
        CREATE = "CREATE", "Yaratma"
        UPDATE = "UPDATE", "Güncelleme"
        DELETE = "DELETE", "Fiziksel Silme (iptal deseni)"
        REVERSE = "REVERSE", "Ters Kayıt"
        CORRECTION = "CORRECTION", "Düzeltme"
        LOGIN = "LOGIN", "Giriş"
        LOGOUT = "LOGOUT", "Çıkış"
        REJECTED = "REJECTED", "Reddedilen İşlem"
    
    kullanıcı = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Kullanıcı"
    )
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")
    
    islem_türü = models.CharField(
        max_length=20, choices=IslemTürü.choices, verbose_name="İşlem Türü"
    )
    
    # İlişkili nesne (content type + object_id ile genérico)
    içerik_türü = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True,
        verbose_name="İçerik Türü"
    )
    nesne_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="Nesne ID")
    nesne = GenericForeignKey('içerik_türü', 'nesne_id')
    
    # Eski ve yeni değerler (JSON formatında)
    eski_değer = models.TextField(blank=True, verbose_name="Eski Değer")
    yeni_değer = models.TextField(blank=True, verbose_name="Yeni Değer")
    
    # Ek bilgiler
    ip_adresi = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Adresi")
    oturum_kişi = models.CharField(max_length=100, blank=True, verbose_name="Oturum/Kişi Bilgisi")
    sebep = models.CharField(max_length=255, blank=True, verbose_name="Sebep/Açıklama")
    correlation_id = models.CharField(
        max_length=64, null=True, blank=True, verbose_name="Korelasyon ID",
        help_text="İstek zincirini loglarla ilişkilendirir (FAZ 6F-2).",
    )
    
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logları"
        ordering = ["-tarih"]
        indexes = [
            models.Index(fields=["islem_türü", "tarih"]),
            models.Index(fields=["içerik_türü", "nesne_id"]),
            models.Index(fields=["kullanıcı", "tarih"]),
        ]
    
    def __str__(self):
        return f"{self.islem_türü} - {self.kullanıcı} - {self.tarih} - {str(self.nesne)[:50] if self.nesne else 'bilinir'}"
    
    @classmethod
    def log_change(cls, kullanıcı, islem_türü, nesne, eski=None, yeni=None,
                   sebep="", ip_adresi=None, oturum_kişi="", correlation_id=None):
        """
        Audit log kaydı oluşturma kısayolu.
        """
        # IP adresi al (request'den gelebilir)
        ip = ip_adresi
        if not ip:
            ip = None
        
        # Oturum bilgisi
        session = oturum_kişi
        
        # Kullanıcının tenant_id'sini al
        tenant_id_val = None
        if kullanıcı and hasattr(kullanıcı, 'tenant_id'):
            tenant_id_val = kullanıcı.tenant_id
        
        return cls.objects.create(
            kullanıcı=kullanıcı,
            islem_türü=islem_türü,
            içerik_türü=ContentType.objects.get_for_model(nesne.__class__) if nesne else None,
            nesne_id=nesne.pk if nesne else None,
            eski_değer=json.dumps(eski or {}, ensure_ascii=False),
            yeni_değer=json.dumps(yeni or {}, ensure_ascii=False),
            ip_adresi=ip,
            oturum_kişi=session,
            sebep=sebep,
            tenant_id=tenant_id_val,
            correlation_id=correlation_id,
        )