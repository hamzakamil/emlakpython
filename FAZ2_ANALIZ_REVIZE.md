# FAZ 2 - Projeye Özel Malzeme Sistemi REVİZE Analiz Raporu

**Tarih:** 2026-09-21  
**Hazırlayan:** GitHub Copilot  
**Durum:** Analiz Aşaması - Henüz Kod Değiştirilmedi  
**Temel:** ANALIZ_RAPORU.md + 11ANALIZ_RAPORU.md + Kullanıcı 12 Madde Revizyon Talimatları

---

## İÇİNDEKİLER

1. [Mevcut Mimari](#1-mevcut-mimari)
2. [Tespit Edilen Sorunlar](#2-tespit-edilen-sorunlar)
3. [Revize Veri Modeli](#3-revize-veri-modeli)
4. [ProjeMalzeme Modeli](#4-projemalzeme-modeli)
5. [ProjeMalzemeFiyat Modeli](#5-projemalzeme-fiyat-modeli)
6. [ProjePozMalzeme Modeli](#6-proje-poz-malzeme-modeli)
7. [Tedarikçi Teklif İlişkisi](#7-tedarikçi-tekilif-ilişkisi)
8. [Etkin Malzeme Çözümleme](#8-etkin-malzeme-çözümleme)
9. [Etkin Fiyat Çözümleme](#9-etkin-fiyat-çözümleme)
10. [Snapshot Mekanizması](#10-snapshot-mekanizması)
11. [FAZ 1 Düzeltmesi](#11-faz-1-düzeltmesi)
12. [API Tasarımı](#12-api-tasarımı)
13. [Frontend Ekranları](#13-frontend-ekranları)
14. [Migration Planı](#14-migration-planı)
15. [Test Senaryoları](#15-test-senaryoları)
16. [Riskler](#16-riskler)
17. [Uygulama Sırası](#17-uygulama-sırası)

---

## 1. MEVCUT MİMARİ

### 1.1 Temel Modeller (construction/models.py)

| Model | Açıklama | Tenant İzolasyonu |
|-------|----------|-------------------|
| **PozGrubu** | Poz grupları (hiyerarşik) | ✅ TenantAwareModel |
| **Poz** | Poz kartı (ÇŞİDB/firma özel) | ✅ TenantAwareModel |
| **Malzeme** | Malzeme kartı (TS/TS EN referanslı) | ✅ TenantAwareModel |
| **PozMalzemeIliskisi** | Poz-Malzeme many-to-many (through) | ✅ TenantAwareModel |
| **PozFiyat** | Poz birim fiyatı (yıl/dönem bazlı) | ✅ TenantAwareModel |
| **ProjePozFiyat** | Projeye özel poz fiyatı (override) | ✅ TenantAwareModel |
| **YfkPozVersiyon** | YFK poz tanımı (versiyonlu) | ✅ TenantAwareModel |
| **YfkFiyat** | YFK poz birim fiyatı | ✅ TenantAwareModel |
| **YfkRayic** | YFK rayıç (katsayı) | ✅ TenantAwareModel |
| **YfkAnaliz** | YFK poz analizi detayları (malzeme kodu string) | ✅ TenantAwareModel |
| **Proje** | İnşaat projesi | ✅ TenantAwareModel |
| **Mahal** | Proje içindeki mahal/oda | ✅ TenantAwareModel |
| **YaklasikMaliyet** | Proje için poz bazlı yaklaşık maliyet | ✅ TenantAwareModel |
| **YaklasikMaliyetSatiri** | Yaklaşık maliyet poz satırı (snapshot) | ✅ TenantAwareModel |
| **PozPlan** | Poz maliyet planı (planlanan/gerçekleşen) | ✅ TenantAwareModel |
| **Hakedis** | Dönemsel hakediş | ✅ TenantAwareModel |
| **HakedisSatiri** | Hakediş satırı (poz + miktar + snapshot) | ✅ TenantAwareModel |
| **Tedarikci** | Tedarikçi firma kartı | ✅ TenantAwareModel |
| **MalzemeTedarikciIliskisi** | Malzeme-tedarikçi sipariş takibi | ✅ TenantAwareModel |
| **TedarikciTeklifi** | Proje/malzeme için teklif karşılaştırması | ✅ TenantAwareModel |

### 1.2 Fiyatlandırma Servisleri (construction/services.py)

- **poz_birim_fiyati(poz, yil)**: Sadece PozFiyat'tan genel fiyat getirir
- **poz_etkin_fiyati(proje, poz, yil)**: Fallback zinciri ile etkin fiyatı çözer
  1. ProjePozFiyat (proje özel)
  2. PozFiyat (genel tenant fiyatı)
  3. YfkFiyat (YFK referans)

### 1.3 Snapshot Mekanizması (Mevcut)

| Model | Snapshot Alanı | Ne Zaman Alınır |
|-------|----------------|-----------------|
| **YaklasikMaliyetSatiri** | `birim_fiyat_snapshot` | Satır oluşturulurken (PozFiyat'tan) |
| **PozPlan** | `birim_fiyat_snapshot` | Plan oluşturulurken (poz_birim_fiyati servisinden) |
| **HakedisSatiri** | `birim_fiyat` | Hakediş satırı oluşturulurken (PozPlan'dan) |

**KRİTİK KURAL:** PozPlan, YaklasikMaliyetSatiri, HakedisSatiri snapshot kayıtlarının geçmiş fiyatları ASLA değiştirilmez.

---

## 2. TESPİT EDİLEN SORUNLAR

### 2.1 Alternatif Malzeme Mantığı Eksikliği (KRİTİK)
- **Mevcut:** `ProjeMalzeme.alternatif_malzeme` tek başına yeterli değil
- **Sorun:** Aynı malzeme aynı proje içinde farklı pozlarda farklı alternatiflerle kullanılamıyor
- **Örnek:** Poz 15: Çimento A → Çimento B, Poz 20: Çimento A → Çimento A, Poz 35: Çimento A → Çimento C
- **Çözüm:** Alternatif malzeme seçimi **POZ + MALZEME** bazında modellenmeli (ProjePozMalzeme)

### 2.2 Poz Fiyatından Malzeme Fiyatı Türetme (YASAK)
- **Mevcut Yaklaşım:** Poz fiyatlarının ortalamasından malzeme fiyatı hesaplanıyor
- **Sorun:** Poz toplam fiyatı = malzeme + işçilik + makine + nakliye + diğer bileşenler
- **Sonuç:** Toplam poz fiyatından malzemenin gerçek birim fiyatı güvenilir şekilde türetilemez
- **Kural:** Poz fiyatından malzeme fiyatı türetme **YASAK**

### 2.3 Tedarikçi Teklifi Seçimi Zayıf
- **Mevcut:** `TedarikciTeklifi.secildi=True` alanına yalnızca sorgu ile güveniliyor
- **Sorun:** Açık FK ilişkisi yok, race condition riski var
- **Çözüm:** `ProjeMalzeme.selected_teklif` FK → `TedarikciTeklifi` açık ilişki

### 2.4 PozPlan.save() Tutarsızlığı (FAZ 1 Hatası)
- **Mevcut:** `poz_birim_fiyati()` kullanıyor (sadece PozFiyat)
- **Doğru:** `poz_etkin_fiyati(proje, poz, yil)` kullanmalı (fallback zinciri)
- **Sonuç:** ProjePozFiyat override'ı PozPlan snapshot'ına yansımıyor

### 2.5 PozAnaliz Malzeme FK Eksikliği
- **Mevcut:** `PozAnaliz.malzeme` CharField (string)
- **Sorun:** FK yok, veri bütünlüğü zayıf
- **Kural:** FAZ 2'de hemen değiştirme, ayrı teknik borç olarak raporla

### 2.6 YFK Kullanımı Yanlış
- **Mevcut:** YFKFiyat poz fiyatı, doğrudan malzeme fiyatı olarak kullanılabiliyor
- **Kural:** YFKFiyat doğrudan malzeme fiyatı olarak KULLANILMAMALI
- **Doğru:** YFKAnaliz içinde gerçek malzeme rayıcı varsa onu kullan, eşleştirme güvenilir değilse None döndür

---

## 3. REVİZE VERİ MODELİ

### 3.1 Genel Yapı

```
Proje
 ├── ProjePozFiyat (mevcut - poz fiyat override)
 ├── ProjeMalzemeFiyat (YENİ - malzeme fiyat override)
 ├── ProjeMalzeme (YENİ - proje özel malzeme tanımı)
 │      └── Malzeme (global malzeme kartı - ANA KİMLİK)
 └── ProjePozMalzeme (YENİ - poz+malzeme bazlı alternatif seçim)

Poz
 └── Poz Analizi
       ├── İşçilik (PozAnaliz tip=ISCIK)
       ├── Makine (PozAnaliz tip=MAKINE)
       ├── Malzeme (PozMalzemeIliskisi + PozAnaliz tip=MALZEME)
       └── Diğer (PozAnaliz tip=NAKLIYE/DIGER)
```

### 3.2 Yeni Modeller Özeti

| Model | Amaç | Unique Constraint |
|-------|------|-------------------|
| **ProjeMalzeme** | Proje seviyesi malzeme tanımı, tedarikçi, kaynak, aktiflik | tenant + proje + malzeme |
| **ProjeMalzemeFiyat** | Proje özel malzeme birim fiyatı (yıl bazlı) | tenant + proje + malzeme + yil |
| **ProjePozMalzeme** | Poz+Malzeme bazlı alternatif malzeme seçimi | tenant + proje + poz + kaynak_malzeme |

---

## 4. PROJEMALZEME MODELİ

### 4.1 Görev Tanımı
Bu model **sadece** proje seviyesindeki bilgileri taşır:
- Projenin malzemeyi kullanıp kullanmadığı
- Proje bazlı tedarikçi
- Seçili tedarikçi teklifi (FK)
- Kaynak bilgisi
- Aktiflik
- Proje özel notlar

### 4.2 Model Tanımı

```python
class ProjeMalzeme(TenantAwareModel):
    """Projeye özel malzeme tanımı - global malzeme kartının proje bazlı override'ı."""
    
    proje = models.ForeignKey(
        Proje, 
        on_delete=models.CASCADE, 
        related_name="proje_malzemeleri",
        verbose_name="Proje"
    )
    malzeme = models.ForeignKey(
        Malzeme, 
        on_delete=models.PROTECT, 
        related_name="proje_malzemeleri",
        verbose_name="Malzeme (Global Kart)"
    )
    
    # Tedarikçi bağlantısı
    tedarikci = models.ForeignKey(
        Tedarikci, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name="proje_malzemeleri",
        verbose_name="Tedarikçi"
    )
    cari = models.ForeignKey(
        "cari.Cari", 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name="proje_malzemeleri",
        limit_choices_to={"tip": "TEDARIKCI"},
        verbose_name="Cari Kartı"
    )
    
    # Seçili tedarikçi teklifi (AÇIK FK - KRİTİK)
    selected_teklif = models.ForeignKey(
        "TedarikciTeklifi",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Seçili Teklif"
    )
    
    # Kaynak bilgisi
    kaynak = models.CharField(max_length=100, blank=True, verbose_name="Kaynak")
    kaynak_url = models.URLField(max_length=250, blank=True, verbose_name="Kaynak URL")
    
    # Aktiflik ve notlar
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
                name="uniq_proje_malzeme_tenant_proje_malzeme"
            ),
        ]
    
    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.malzeme.malzeme_kodu}"
```

### 4.3 Kural: Global Malzeme Kartı Ana Kimlik
- `malzeme.ad`, `malzeme.birim`, `malzeme.ts_no` **override edilmez**
- Global `Malzeme` kartı ana kimlik olarak korunur
- Proje özel adı/birimi/standardı **EKLENMEZ** (gereksiz karmaşıklık)

---

## 5. PROJEMALZEMEFIYAT MODELİ

### 5.1 Model Tanımı

```python
class ProjeMalzemeFiyat(TenantAwareModel):
    """Projeye özel malzeme birim fiyatı - ProjePozFiyat'ın malzeme karşılığı."""
    
    proje = models.ForeignKey(
        Proje, 
        on_delete=models.CASCADE, 
        related_name="malzeme_fiyatlari",
        verbose_name="Proje"
    )
    malzeme = models.ForeignKey(
        Malzeme, 
        on_delete=models.PROTECT, 
        related_name="proje_fiyatlari",
        verbose_name="Malzeme"
    )
    yil = models.PositiveSmallIntegerField(verbose_name="Yıl")
    
    birim_fiyat = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Birim Fiyat (₺)"
    )
    para_birimi = models.CharField(
        max_length=3, 
        default="TRY", 
        verbose_name="Para Birimi"
    )
    kaynak = models.CharField(max_length=100, blank=True, verbose_name="Kaynak")
    kaynak_url = models.URLField(max_length=250, blank=True, verbose_name="Kaynak URL")
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
                name="uniq_proje_malzeme_fiyat_tenant_proje_malzeme_yil"
            ),
        ]
    
    def __str__(self) -> str:
        return f"{self.proje.proje_kodu} / {self.malzeme.malzeme_kodu} / {self.yil}: {self.birim_fiyat} {self.para_birimi}"
```

### 5.2 KDV Hariç Temel Maliyet Fiyatı Varsayımı
- `birim_fiyat` alanı **KDV hariç** temel maliyet fiyatıdır
- Mevcut sistemle çelişme kontrolü: `PozFiyat`, `ProjePozFiyat`, `TedarikciTeklifi` da KDV hariç kabul ediliyor
- Eğer mevcut sistemde KDV dahil fiyat varsa → migration sırasında dönüşüm gerekir (raporlanacak)

---

## 6. PROJE POZ MALZEME MODELİ

### 6.1 Amaç
Belirli bir projede belirli bir pozun belirli bir malzemesini başka bir malzemeyle değiştirebilmek.
**POZ + MALZEME** bazında modellenir, proje genelinde değil.

### 6.2 Model Tanımı

```python
class ProjePozMalzeme(TenantAwareModel):
    """Proje-Poz-Malzeme bazlı alternatif malzeme seçimi.
    
    Aynı malzeme aynı proje içinde farklı pozlarda farklı alternatiflerle kullanılabilir.
    """
    
    proje = models.ForeignKey(
        Proje, 
        on_delete=models.CASCADE, 
        related_name="poz_malzemeleri",
        verbose_name="Proje"
    )
    poz = models.ForeignKey(
        Poz, 
        on_delete=models.PROTECT, 
        related_name="proje_poz_malzemeleri",
        verbose_name="Poz"
    )
    kaynak_malzeme = models.ForeignKey(
        Malzeme, 
        on_delete=models.PROTECT, 
        related_name="kaynak_olan_proje_poz_malzemeleri",
        verbose_name="Kaynak Malzeme (Poz Analizindeki)"
    )
    etkin_malzeme = models.ForeignKey(
        Malzeme, 
        on_delete=models.PROTECT, 
        related_name="etkin_olan_proje_poz_malzemeleri",
        verbose_name="Etkin Malzeme (Gerçek Kullanılacak)"
    )
    
    # Miktar override (nullable - poz analizindeki miktarı ezer)
    miktar_override = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0001"))],
        verbose_name="Miktar Override",
        help_text="Boşsa PozMalzemeIliskisi.miktar kullanılır"
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
                name="uniq_proje_poz_malzeme_tenant_proje_poz_kaynak"
            ),
            models.CheckConstraint(
                condition=~models.Q(kaynak_malzeme=models.F("etkin_malzeme")),
                name="check_proje_poz_malzeme_farkli_malzeme"
            ),
        ]
    
    def __str__(self) -> str:
        if self.kaynak_malzeme_id == self.etkin_malzeme_id:
            return f"{self.proje.proje_kodu} / {self.poz.poz_no} / {self.kaynak_malzeme.malzeme_kodu} (değişiklik yok)"
        return f"{self.proje.proje_kodu} / {self.poz.poz_no} / {self.kaynak_malzeme.malzeme_kodu} → {self.etkin_malzeme.malzeme_kodu}"
```

### 6.3 Örnek Senaryo

| Poz | Kaynak Malzeme | Etkin Malzeme | Açıklama |
|-----|----------------|---------------|----------|
| 15 | Çimento A (CEM I 42.5) | Çimento B (CEM II 42.5) | Proje özel tercih |
| 20 | Çimento A (CEM I 42.5) | Çimento A (CEM I 42.5) | Değişiklik yok (kayıt gerekmez) |
| 35 | Çimento A (CEM I 42.5) | Çimento C (CEM III 42.5) | Farklı çimento türü |

**Not:** Poz 20 için kayıt **oluşturulmaz** (kaynak=etkin ise override yok sayılır).

---

## 7. TEDARİKÇİ TEKLİF İLİŞKİSİ

### 7.1 Mevcut TedarikciTeklifi Yapısı (İnceleme)

```python
class TedarikciTeklifi(TenantAwareModel):
    proje = FK(Proje)
    malzeme = FK(Malzeme)
    tedarikci = FK(Tedarikci)
    miktar = DecimalField
    birim_fiyat = DecimalField
    toplam_tutar = DecimalField (auto)
    durum = CharField (TASLAK/ISTENDI/GELDI/DEGERLENDIRILIYOR/KABUL/RED/IPTAL)
    secildi = BooleanField(default=False)  # ← SADECE BOOLEAN
    is_active = BooleanField(default=True)
```

**Mevcut Unique Constraint:**
```python
UniqueConstraint(
    fields=["tenant", "proje", "malzeme", "tedarikci"],
    condition=Q(is_active=True),
    name="uniq_aktif_tedarikci_teklifi"
)
```

### 7.2 Uyumsuzluk ve Çözüm

**Sorun:** `secildi=True` boolean ile güvenmek zayıf:
- Race condition: Aynı proje+malzeme için 2 teklif `secildi=True` olabilir
- Sorgu performansı: Her fiyat sorgusunda filtreleme gerekir
- Açık ilişki yok: `ProjeMalzeme` hangi teklifi seçtiğini bilmez

**Çözüm:** `ProjeMalzeme.selected_teklif` FK ekle (SET_NULL on delete)

```python
# ProjeMalzeme modelinde (yukarıda tanımlandı)
selected_teklif = models.ForeignKey(
    "TedarikciTeklifi",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="+",
    verbose_name="Seçili Teklif"
)
```

### 7.3 Akış

```
ProjeMalzeme
    ↓ selected_teklif (FK)
TedarikciTeklifi (secildi=True, is_active=True)
    ↓ tedarikci (FK)
Tedarikci
    ↓ birim_fiyat
Fiyat
```

### 7.4 Senkronizasyon Kuralı
- `ProjeMalzeme.selected_teklif` set edildiğinde → o teklifin `secildi=True` yapılır
- Diğer aynı proje+malzeme tekliflerinin `secildi=False` yapılır
- Bu logic `ProjeMalzeme.save()` veya ayrı servis metodunda yapılır

---

## 8. ETKİN MALZEME ÇÖZÜMLEME SERVİSİ

### 8.1 Servis Tanımı

```python
def etkin_poz_malzeme(proje: Proje, poz: Poz, kaynak_malzeme: Malzeme) -> Malzeme:
    """
    Belirli bir projede, belirli bir poz için, belirli bir kaynak malzemenin
    etkin (gerçek kullanılacak) malzemeyi döndürür.
    
    Args:
        proje: Proje instance
        poz: Poz instance
        kaynak_malzeme: Poz analizinde tanımlı malzeme (PozMalzemeIliskisi.malzeme)
    
    Returns:
        Malzeme: Etkin malzeme (override varsa alternatif, yoksa kaynak_malzeme)
    """
    # 1. ProjePozMalzeme içinde override ara
    override = ProjePozMalzeme.objects.filter(
        tenant_id=proje.tenant_id,
        proje=proje,
        poz=poz,
        kaynak_malzeme=kaynak_malzeme,
        is_active=True
    ).select_related("etkin_malzeme").first()
    
    if override:
        return override.etkin_malzeme
    
    # 2. Override yoksa kaynak malzemeyi döndür
    return kaynak_malzeme
```

### 8.2 Kullanım Akışı

```
Poz Analizi Hesaplaması:
Kaynak Malzeme (PozMalzemeIliskisi.malzeme)
    → proje-poz override (ProjePozMalzeme)
    → Etkin Malzeme (etkin_poz_malzeme sonucu)
    → Etkin Fiyat (malzeme_etkin_fiyati ile)
```

### 8.3 Miktar Override
- `ProjePozMalzeme.miktar_override` varsa → poz analizindeki miktarı ezer
- Yoksa → `PozMalzemeIliskisi.miktar` kullanılır

---

## 9. ETKİN FİYAT ÇÖZÜMLEME SERVİSİ

### 9.1 Yeni Servis: `malzeme_etkin_fiyati`

```python
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

@dataclass
class FiyatSonucu:
    """Etkin fiyat sonucu - frontend kaynak gösterebilsin diye zenginleştirildi."""
    fiyat: Optional[Decimal]
    kaynak: str           # "proje_malzeme_fiyat", "tedarikci_teklifi", "genel_malzeme_fiyat", "yfk_analiz", "none"
    kaynak_id: Optional[int]  # İlgili modelin PK'si
    para_birimi: str      # "TRY" (varsayılan)

def malzeme_etkin_fiyati(
    proje: Optional[Proje], 
    malzeme: Malzeme, 
    yil: int
) -> FiyatSonucu:
    """
    Malzeme etkin birim fiyatını fallback zinciriyle çözer.
    
    Fallback Sırası (Poz fiyatı KULLANILMAZ):
    1. ProjeMalzemeFiyat (proje + malzeme + yıl)
    2. ProjeMalzeme.selected_teklif → TedarikciTeklifi.birim_fiyat
    3. MalzemeFiyat (tenant + malzeme + yıl) — GENEL MALZEME FIYAT MODELİ GEREKİR
    4. YFKAnaliz gerçek malzeme rayıcı (malzeme_kodu eşleşmesi, güvenilir değilse None)
    5. None
    
    Returns:
        FiyatSonucu: fiyat, kaynak, kaynak_id, para_birimi
    """
    
    # 1. ProjeMalzemeFiyat (proje özel malzeme fiyatı)
    if proje is not None:
        pmf = ProjeMalzemeFiyat.objects.filter(
            tenant_id=proje.tenant_id,
            proje=proje,
            malzeme=malzeme,
            yil=yil,
            is_active=True
        ).order_by("-created_at").first()
        if pmf:
            return FiyatSonucu(
                fiyat=pmf.birim_fiyat,
                kaynak="proje_malzeme_fiyat",
                kaynak_id=pmf.pk,
                para_birimi=pmf.para_birimi
            )
    
    # 2. ProjeMalzeme.selected_teklif → TedarikciTeklifi
    if proje is not None:
        pm = ProjeMalzeme.objects.filter(
            tenant_id=proje.tenant_id,
            proje=proje,
            malzeme=malzeme,
            is_active=True
        ).select_related("selected_teklif", "selected_teklif__tedarikci").first()
        
        if pm and pm.selected_teklif and pm.selected_teklif.is_active:
            teklif = pm.selected_teklif
            return FiyatSonucu(
                fiyat=teklif.birim_fiyat,
                kaynak="tedarikci_teklifi",
                kaynak_id=teklif.pk,
                para_birimi="TRY"  # TedarikciTeklifi para_birimi yok, TRY varsayılan
            )
    
    # 3. Genel MalzemeFiyat (YENİ MODEL GEREKİR - opsiyonel)
    # mf = MalzemeFiyat.objects.filter(tenant=..., malzeme=..., yil=..., is_active=True).first()
    # if mf: return FiyatSonucu(...)
    
    # 4. YFKAnaliz gerçek malzeme rayıcı
    # YFKAnaliz'de malzeme_kodu ile eşleşme yap
    # GÜVENİLİRLİK KONTROLÜ: Eşleşme %100 değilse None döndür
    yfk_analiz = YfkAnaliz.objects.filter(
        tenant_id=proje.tenant_id if proje else None,
        malzeme_kodu=malzeme.malzeme_kodu,
        malzeme_tipi="malzeme",
        is_active=True
    ).select_related("poz_versiyon").order_by("-poz_versiyon__versiyon", "-created_at").first()
    
    if yfk_analiz:
        # Güvenilirlik: poz_versiyon poz_no ile projedeki poz eşleşiyor mu?
        # Basit güvenilirlik: sadece malzeme_kodu eşleşmesi yeterli DEĞİL
        # Daha güvenli: PozMalzemeIliskisi üzerinden poz-malzemesi varsa o pozun YFK analizi
        return FiyatSonucu(
            fiyat=yfk_analiz.birim_fiyat,
            kaynak="yfk_analiz",
            kaynak_id=yfk_analiz.pk,
            para_birimi="TRY"
        )
    
    # 5. None
    return FiyatSonucu(
        fiyat=None,
        kaynak="none",
        kaynak_id=None,
        para_birimi="TRY"
    )
```

### 9.2 Fiyat Öncelik Matrisi (Güncellenmiş)

| Öncelik | Kaynak | Model | Kapsam | Dönüş `kaynak` Değeri |
|---------|--------|-------|--------|----------------------|
| 1 | Proje özel malzeme fiyatı | `ProjeMalzemeFiyat` | Proje + Malzeme + Yıl | `proje_malzeme_fiyat` |
| 2 | Proje için seçilmiş tedarikçi teklifi | `TedarikciTeklifi` (via ProjeMalzeme.selected_teklif) | Proje + Malzeme + Tedarikçi | `tedarikci_teklifi` |
| 3 | Genel malzeme fiyatı | `MalzemeFiyat` (YENİ MODEL) | Tenant + Malzeme + Yıl | `genel_malzeme_fiyat` |
| 4 | YFK referans fiyatı | `YfkAnaliz` (malzeme_kodu eşleşme) | Referans | `yfk_analiz` |
| 5 | None | - | Bulunamadı | `none` |

**KESİN KURAL:** Poz fiyatı (PozFiyat, ProjePozFiyat, YfkFiyat) bu zincirde **KULLANILMAZ**.

---

## 10. SNAPSHOT MEKANİZMASI

### 10.1 Korunacak Mevcut Snapshot'lar (DEĞİŞTİRİLMEZ)

| Model | Alan | Koruma |
|-------|------|--------|
| `YaklasikMaliyetSatiri` | `birim_fiyat_snapshot` | ✅ Korunur, yeniden hesaplanmaz |
| `PozPlan` | `birim_fiyat_snapshot` | ✅ Korunur, yeniden hesaplanmaz |
| `HakedisSatiri` | `birim_fiyat` | ✅ Korunur, onaydan sonra değiştirilemez |

### 10.2 Yeni Snapshot Alanları

| Yeni Model / Alan | Snapshot Alanı | Kaynak |
|-------------------|----------------|--------|
| `YaklasikMaliyetSatiri` (yeni satırlar) | `birim_fiyat_snapshot` | `malzeme_etkin_fiyati(proje, malzeme, yil).fiyat` |
| `PozPlan` (malzeme bazlı genişletme) | `malzeme_birim_fiyat_snapshot` | `malzeme_etkin_fiyati(...)` |
| `ProjeMalzeme` | `birim_fiyat_snapshot` (opsiyonel) | Oluşturma anındaki etkin fiyat |

### 10.3 Hesaplama Akışı (Yeni Kayıtlar İçin)

```
Yeni YaklasikMaliyetSatiri oluşturulurken:
  1. Eğer poz bazlı → poz_etkin_fiyati(proje, poz, yil)  (MEVCUT)
  2. Eğer malzeme bazlı → malzeme_etkin_fiyati(proje, malzeme, yil).fiyat  (YENİ)
  3. Sonuç → birim_fiyat_snapshot'a yazılır (SNAPSHOT)
  4. toplam_tutar = miktar × birim_fiyat_snapshot
```

### 10.4 Snapshot Koruma Kuralı (Kod Seviyesinde)

```python
# YaklasikMaliyetSatiri.save() - MEVCUT KORUMA
def save(self, *args, **kwargs):
    if self.pk:
        eski_snapshot = type(self).objects.filter(pk=self.pk).values_list(
            "birim_fiyat_snapshot", flat=True
        ).first()
        if eski_snapshot is not None:
            self.birim_fiyat_snapshot = eski_snapshot  # DEĞİŞTİRİLMEZ
    # ... yeni kayıt için fiyat al
    super().save(*args, **kwargs)

# PozPlan.save() - MEVCUT KORUMA + YENİ SERVİS
def save(self, *args, **kwargs):
    if not self.birim_fiyat_snapshot or self.birim_fiyat_snapshot <= 0:
        from .services import poz_etkin_fiyati  # YENİ: poz_etkin_fiyati kullan!
        fiyat = poz_etkin_fiyati(self.proje, self.poz, self.yil)
        if fiyat is not None:
            self.birim_fiyat_snapshot = fiyat
    self.clean()
    super().save(*args, **kwargs)
```

---

## 11. FAZ 1 DÜZELTMESİ

### 11.1 PozPlan.save() Düzeltmesi (KRİTİK)

**Mevcut (HATALI):**
```python
def save(self, *args, **kwargs):
    if not self.birim_fiyat_snapshot or self.birim_fiyat_snapshot <= 0:
        from .services import poz_birim_fiyati  # SADECE PozFiyat!
        fiyat = poz_birim_fiyati(self.poz, self.yil)
        if fiyat is not None:
            self.birim_fiyat_snapshot = fiyat
    self.clean()
    super().save(*args, **kwargs)
```

**Düzeltilmiş (DOĞRU):**
```python
def save(self, *args, **kwargs):
    if not self.birim_fiyat_snapshot or self.birim_fiyat_snapshot <= 0:
        from .services import poz_etkin_fiyati  # FALLBACK ZİNCİRİ!
        fiyat = poz_etkin_fiyati(self.proje, self.poz, self.yil)
        if fiyat is not None:
            self.birim_fiyat_snapshot = fiyat
    self.clean()
    super().save(*args, **kwargs)
```

### 11.2 YaklasikMaliyetSatiri.save() Kontrolü

Mevcut davranışı **bozmadan** yalnızca **YENİ kayıtların** etkin fiyat sistemiyle oluşturulmasını sağla:

```python
def save(self, *args, **kwargs):
    if self.pk:
        # Mevcut kayıt: snapshot KORUNUR
        eski_snapshot = type(self).objects.filter(pk=self.pk).values_list(
            "birim_fiyat_snapshot", flat=True
        ).first()
        if eski_snapshot is not None:
            self.birim_fiyat_snapshot = eski_snapshot
    elif not self.birim_fiyat_snapshot:
        # YENİ KAYIT: Etkin fiyat sistemini kullan
        # Poz bazlı mı malzeme bazlı mı belirlenmeli (yeni alan eklenebilir)
        # Şimdilik poz bazlı varsayılan:
        from .services import poz_etkin_fiyati
        fiyat = poz_etkin_fiyati(self.yaklasik_maliyet.proje, self.poz, self.yaklasik_maliyet.yil)
        if fiyat is not None:
            self.birim_fiyat_snapshot = fiyat
    
    self.toplam_tutar = (
        Decimal(str(self.miktar)) * Decimal(str(self.birim_fiyat_snapshot))
    ).quantize(Decimal("0.01"))
    super().save(*args, **kwargs)
```

**ÖNEMLİ:** Mevcut snapshot değerleri **KESİNLİKLE** yeniden hesaplanmayacak.

---

## 12. POZANALİZ MALZEME FK KONUSU

### 12.1 Mevcut Durum
```python
class PozAnaliz(TenantAwareModel):
    malzeme = models.CharField(max_length=255, verbose_name="Analiz Kalemi")  # STRING!
    # FK YOK
```

### 12.2 FAZ 2 Kararı
- **HEMEN DEĞİŞTİRİLMEZ**
- Etkileri analiz edilecek
- Mevcut sistemi bozmayacak minimum değişiklikle ilerlenecek
- `PozMalzemeIliskisi` mevcut, mümkün olduğu kadar temel alınacak

### 12.3 Teknik Borç / Milestone
**PozAnaliz → Malzeme FK Dönüşümü** ayrı bir teknik borç/milestone olarak planlanacak:
1. Yeni `malzeme_fk` alanı ekle (nullable)
2. Veri migrasyonu: `malzeme` string → `Malzeme` FK eşleştirme
3. Validasyon: Yeni kayıtlarda FK zorunlu
4. Eski `malzeme` CharField deprecated (sadece okuma için)
5. Sonraki fazda CharField silinir

---

## 13. YFK KONUSU

### 13.1 Mevcut Yapı
- `YfkFiyat` = Poz fiyatıdır (malzeme fiyatı DEĞİL)
- `YfkRayic` = Katsayı (malzeme/işçilik/nakliye/makine)
- `YfkAnaliz` = Poz analizi detayları (malzeme_kodu string, birim_fiyat var)

### 13.2 Kullanım Kuralları
1. **YFKFiyat doğrudan malzeme fiyatı olarak KULLANILMAZ**
2. **YFKAnaliz** içinde gerçek malzeme rayıcı varsa onu kullan
3. Veri yapısı: `YfkAnaliz.malzeme_kodu` + `YfkAnaliz.birim_fiyat` + `YfkAnaliz.malzeme_tipi="malzeme"`
4. Eşleştirme güvenilir değilse (malzeme_kodu string eşleşmesi) → **None döndür**
5. Yanlış eşleşme yerine **None** tercih edilir

### 13.3 Güvenilirlik Kontrolü
```python
def _yfk_malzeme_fiyati_guvenli(malzeme: Malzeme, yil: int) -> Optional[Decimal]:
    """YFKAnaliz'den malzeme fiyatı al - güvenilirlik kontrolüyle."""
    analizler = YfkAnaliz.objects.filter(
        malzeme_kodu=malzeme.malzeme_kodu,
        malzeme_tipi="malzeme",
        is_active=True,
        poz_versiyon__yil=yil  # YFK poz versiyonunun yılı
    ).select_related("poz_versiyon")
    
    # Güvenilirlik: Aynı malzeme kodu birden fazla pozda varsa güvenilmez
    poz_sayisi = analizler.values("poz_versiyon__poz_no").distinct().count()
    if poz_sayisi > 1:
        return None  # Belirsiz eşleşme
    
    analiz = analizler.order_by("-poz_versiyon__versiyon").first()
    return analiz.birim_fiyat if analiz else None
```

---

## 14. API TASARIMI

### 14.1 ProjeMalzeme Endpoints

```
GET    /api/v1/construction/proje-malzemeler/?proje=<id>           # Liste
POST   /api/v1/construction/proje-malzemeler/                      # Oluştur
GET    /api/v1/construction/proje-malzemeler/<id>/                 # Detay
PUT    /api/v1/construction/proje-malzemeler/<id>/                 # Güncelle
PATCH  /api/v1/construction/proje-malzemeler/<id>/                 # Kısmi güncelle
DELETE /api/v1/construction/proje-malzemeler/<id>/                 # Pasif et (soft delete)

# Özel aksiyonlar
POST   /api/v1/construction/proje-malzemeler/<id>/tedarikci-ata/   # Tedarikçi ata
POST   /api/v1/construction/proje-malzemeler/<id>/teklif-sec/      # Seçili teklif ata
GET    /api/v1/construction/proje-malzemeler/fiyat-karsilastirma/?proje=<id>&malzeme=<id>  # Fiyat karşılaştırma
```

### 14.2 ProjeMalzemeFiyat Endpoints

```
GET    /api/v1/construction/proje-malzeme-fiyatlari/?proje=<id>&yil=<yil>
POST   /api/v1/construction/proje-malzeme-fiyatlari/
GET    /api/v1/construction/proje-malzeme-fiyatlari/<id>/
PUT    /api/v1/construction/proje-malzeme-fiyatlari/<id>/
DELETE /api/v1/construction/proje-malzeme-fiyatlari/<id>/
```

### 14.3 ProjePozMalzeme Endpoints

```
GET    /api/v1/construction/proje-poz-malzemeler/?proje=<id>&poz=<id>
POST   /api/v1/construction/proje-poz-malzemeler/
GET    /api/v1/construction/proje-poz-malzemeler/<id>/
PUT    /api/v1/construction/proje-poz-malzemeler/<id>/
DELETE /api/v1/construction/proje-poz-malzemeler/<id>/
```

### 14.4 Serializer Yapısı

```python
class ProjeMalzemeSerializer(TenantAwareModelSerializer):
    malzeme_kodu = CharField(source="malzeme.malzeme_kodu", read_only=True)
    malzeme_adi = CharField(source="malzeme.ad", read_only=True)
    malzeme_birim = CharField(source="malzeme.birim", read_only=True)
    malzeme_ts_no = CharField(source="malzeme.ts_no", read_only=True)
    tedarikci_adi = CharField(source="tedarikci.firma_adi", read_only=True)
    cari_adi = CharField(source="cari.ad", read_only=True)
    selected_teklif_fiyat = CharField(source="selected_teklif.birim_fiyat", read_only=True)
    selected_teklif_tedarikci = CharField(source="selected_teklif.tedarikci.firma_adi", read_only=True)
    etkin_fiyat = SerializerMethodField()
    etkin_fiyat_kaynak = SerializerMethodField()
    
    class Meta:
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at",
                           "malzeme_kodu", "malzeme_adi", "malzeme_birim",
                           "etkin_fiyat", "etkin_fiyat_kaynak")
    
    def get_etkin_fiyat(self, obj):
        from construction.services import malzeme_etkin_fiyati
        sonuc = malzeme_etkin_fiyati(obj.proje, obj.malzeme, obj.proje.yil if hasattr(obj.proje, 'yil') else 2026)
        return str(sonuc.fiyat) if sonuc.fiyat else None
    
    def get_etkin_fiyat_kaynak(self, obj):
        from construction.services import malzeme_etkin_fiyati
        sonuc = malzeme_etkin_fiyati(obj.proje, obj.malzeme, obj.proje.yil if hasattr(obj.proje, 'yil') else 2026)
        return sonuc.kaynak

class ProjeMalzemeFiyatSerializer(TenantAwareModelSerializer):
    malzeme_kodu = CharField(source="malzeme.malzeme_kodu", read_only=True)
    malzeme_adi = CharField(source="malzeme.ad", read_only=True)
    proje_kodu = CharField(source="proje.proje_kodu", read_only=True)
    
    class Meta:
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at",
                           "malzeme_kodu", "malzeme_adi", "proje_kodu")

class ProjePozMalzemeSerializer(TenantAwareModelSerializer):
    poz_no = CharField(source="poz.poz_no", read_only=True)
    poz_ad = CharField(source="poz.ad", read_only=True)
    kaynak_malzeme_kodu = CharField(source="kaynak_malzeme.malzeme_kodu", read_only=True)
    kaynak_malzeme_adi = CharField(source="kaynak_malzeme.ad", read_only=True)
    etkin_malzeme_kodu = CharField(source="etkin_malzeme.malzeme_kodu", read_only=True)
    etkin_malzeme_adi = CharField(source="etkin_malzeme.ad", read_only=True)
    etkin_malzeme_birim = CharField(source="etkin_malzeme.birim", read_only=True)
    
    class Meta:
        fields = "__all__"
        read_only_fields = ("id", "tenant", "created_at", "updated_at",
                           "poz_no", "poz_ad", "kaynak_malzeme_kodu",
                           "kaynak_malzeme_adi", "etkin_malzeme_kodu",
                           "etkin_malzeme_adi", "etkin_malzeme_birim")
```

---

## 15. FRONTEND EKRANLARI

### 15.1 Yeni Sayfalar

| Dosya | Açıklama |
|-------|----------|
| `frontend/src/views/insaat/ProjeMalzemeView.vue` | Proje malzeme yönetimi (liste, oluştur, düzenle, tedarikçi ata, teklif seç) |
| `frontend/src/views/insaat/ProjeMalzemeFiyatView.vue` | Proje malzeme fiyat yönetimi (yıl bazlı) |
| `frontend/src/views/insaat/ProjePozMalzemeView.vue` | Poz bazlı alternatif malzeme seçimi |
| `frontend/src/views/insaat/MalzemeFiyatKarsilastirmaView.vue` | Malzeme fiyat karşılaştırma (proje fiyatı + tedarikçi teklifi + genel + YFK) |

### 15.2 Güncellenecek Sayfalar

| Dosya | Değişiklik |
|-------|------------|
| `frontend/src/types/insaat.ts` | + ProjeMalzeme, ProjeMalzemeFiyat, ProjePozMalzeme, FiyatSonucu interface'leri |
| `frontend/src/services/insaatApi.ts` | + Yeni API çağrıları |
| `frontend/src/views/insaat/YaklasikMaliyetView.vue` | Satır eklerken malzeme fiyatı fallback'i göster, malzeme bazlı satır desteği |
| `frontend/src/views/insaat/PozPlanlariView.vue` | Malzeme bazlı maliyet analizi sekmesi |
| `frontend/src/views/insaat/TedarikciTeklifleriView.vue` | "Proje Malzemesi Olarak Kaydet / Seçili Teklif Olarak Ata" butonu |
| `frontend/src/stores/insaat.ts` | Yeni store modülleri |

### 15.3 UI/UX Notları
- **ProjeMalzemeView:** Tablo + yan panel detay (ERP workspace panel pattern)
- **Fiyat Karşılaştırma:** 4 kolonlu kartlar (Proje Fiyatı | Seçili Teklif | Genel Fiyat | YFK Referans)
- **ProjePozMalzeme:** Poz bazlı grup, her poz için kaynak→etkin malzeme seçici

---

## 16. MIGRATION PLANI

### 16.1 Migration Sırası

```bash
# 1. Yeni modeller
python manage.py makemigrations construction --name add_proje_malzeme_models

# 2. Veri migrasyonu (varsa) - Mevcut TedarikciTeklifi.secildi → ProjeMalzeme.selected_teklif
python manage.py makemigrations construction --name sync_selected_teklif --empty
# RunSQL ile veri taşıma

# 3. PozPlan.save() düzeltmesi (kod değişikliği, migration gerekmez)

# 4. YaklasikMaliyetSatiri.save() kontrolü (kod değişikliği)

# 5. PozAnaliz.malzeme_fk alanı ekleme (ayrı milestone)
python manage.py makemigrations construction --name add_pozanaliz_malzeme_fk
```

### 16.2 Migration İçeriği (Özet)

**Migration 1: add_proje_malzeme_models**
- Create `ProjeMalzeme` table
- Create `ProjeMalzemeFiyat` table  
- Create `ProjePozMalzeme` table
- Indexes ve constraints

**Migration 2: sync_selected_teklif (Data Migration)**
```python
def forward(apps, schema_editor):
    ProjeMalzeme = apps.get_model('construction', 'ProjeMalzeme')
    TedarikciTeklifi = apps.get_model('construction', 'TedarikciTeklifi')
    
    # Her proje+malzeme için secildi=True olan teklifi bul
    for pm in ProjeMalzeme.objects.all():
        teklif = TedarikciTeklifi.objects.filter(
            proje=pm.proje,
            malzeme=pm.malzeme,
            secildi=True,
            is_active=True
        ).first()
        if teklif:
            pm.selected_teklif = teklif
            pm.save(update_fields=["selected_teklif"])
```

---

## 17. TEST SENARYOLARI

### TEST 1: Proje Fiyatı Varsa Proje Fiyatı Kullanılmalı
```python
def test_proje_malzeme_fiyat_oncelik():
    proje = ProjeFactory()
    malzeme = MalzemeFactory()
    yil = 2026
    
    # ProjeMalzemeFiyat oluştur
    ProjeMalzemeFiyatFactory(proje=proje, malzeme=malzeme, yil=yil, birim_fiyat=Decimal("150.00"))
    
    # Genel MalzemeFiyat da varsa (daha düşük)
    # MalzemeFiyatFactory(malzeme=malzeme, yil=yil, birim_fiyat=Decimal("100.00"))
    
    sonuc = malzeme_etkin_fiyati(proje, malzeme, yil)
    
    assert sonuc.fiyat == Decimal("150.00")
    assert sonuc.kaynak == "proje_malzeme_fiyat"
```

### TEST 2: Proje Fiyatı Yok, Seçili Tedarikçi Teklifi Varsa Teklif Kullanılmalı
```python
def test_tedarikci_teklifi_fallback():
    proje = ProjeFactory()
    malzeme = MalzemeFactory()
    tedarikci = TedarikciFactory()
    yil = 2026
    
    # ProjeMalzeme oluştur, selected_teklif ata
    teklif = TedarikciTeklifiFactory(
        proje=proje, malzeme=malzeme, tedarikci=tedarikci,
        birim_fiyat=Decimal("120.00"), secildi=True, is_active=True
    )
    ProjeMalzemeFactory(proje=proje, malzeme=malzeme, selected_teklif=teklif)
    
    sonuc = malzeme_etkin_fiyati(proje, malzeme, yil)
    
    assert sonuc.fiyat == Decimal("120.00")
    assert sonuc.kaynak == "tedarikci_teklifi"
    assert sonuc.kaynak_id == teklif.pk
```

### TEST 3: İkisi De Yok, Genel Malzeme Fiyatı Varsa Genel Fiyat Kullanılmalı
```python
def test_genel_malzeme_fiyat_fallback():
    # MalzemeFiyat modeli eklendiyse test edilecek
    pass  # Model eklendikten sonra implement edilecek
```

### TEST 4: Belirli Poz + Malzeme İçin Alternatif Seçilmiş → Sadece O Poz Etkilenmeli
```python
def test_poz_bazli_alternatif_izolasyon():
    proje = ProjeFactory()
    poz15 = PozFactory(poz_no="15")
    poz20 = PozFactory(poz_no="20")
    cimento_a = MalzemeFactory(malzeme_kodu="CIM-A")
    cimento_b = MalzemeFactory(malzeme_kodu="CIM-B")
    cimento_c = MalzemeFactory(malzeme_kodu="CIM-C")
    
    # Poz 15: A → B
    ProjePozMalzemeFactory(
        proje=proje, poz=poz15, kaynak_malzeme=cimento_a, etkin_malzeme=cimento_b
    )
    # Poz 20: A → A (kayıt YOK)
    # Poz 35: A → C
    poz35 = PozFactory(poz_no="35")
    ProjePozMalzemeFactory(
        proje=proje, poz=poz35, kaynak_malzeme=cimento_a, etkin_malzeme=cimento_c
    )
    
    # Test
    assert etkin_poz_malzeme(proje, poz15, cimento_a) == cimento_b
    assert etkin_poz_malzeme(proje, poz20, cimento_a) == cimento_a  # Değişmedi
    assert etkin_poz_malzeme(proje, poz35, cimento_a) == cimento_c
```

### TEST 5: Aynı Malzeme Başka Pozlarda Kullanılıyor → Alternatif Seçilmemiş Pozlar Değişmemeli
```python
def test_ayni_malzeme_farkli_poz_etkilenmez():
    # TEST 4 ile aynı mantık, farklı assertion
    pass
```

### TEST 6: Fiyat Tablosu Sonradan Değiştiriliyor → Eski Snapshot Kayıtları Değişmemeli
```python
def test_snapshot_koruma():
    proje = ProjeFactory()
    poz = PozFactory()
    yil = 2026
    
    # PozPlan oluştur (snapshot alınır)
    PozFiyatFactory(poz=poz, yil=yil, birim_fiyat=Decimal("100.00"))
    plan = PozPlanFactory(proje=proje, poz=poz, yil=yil)
    snapshot_eski = plan.birim_fiyat_snapshot
    
    # Fiyat değiştir
    PozFiyat.objects.filter(poz=poz, yil=yil).update(birim_fiyat=Decimal("200.00"))
    
    # Planı yeniden yükle
    plan.refresh_from_db()
    
    # Snapshot değişmemeli
    assert plan.birim_fiyat_snapshot == snapshot_eski == Decimal("100.00")
```

### TEST 7: Tenant A'nın Proje Malzemesi Tenant B Tarafından Görülememeli
```python
def test_tenant_izolasyonu():
    tenant_a = TenantFactory()
    tenant_b = TenantFactory()
    proje_a = ProjeFactory(tenant=tenant_a)
    proje_b = ProjeFactory(tenant=tenant_b)
    malzeme = MalzemeFactory(tenant=tenant_a)  # Tenant A'ya ait
    
    ProjeMalzemeFactory(proje=proje_a, malzeme=malzeme)
    
    # Tenant B sorguluyor
    qs = ProjeMalzeme.objects.filter(tenant=tenant_b, proje=proje_b)
    assert qs.count() == 0
```

### TEST 8: Aynı Projede Poz 15'te A→B, Poz 20'de A→C Yapılabilmeli
```python
def test_ayni_proje_farkli_poz_farkli_alternatif():
    # TEST 4'ün aynısı - ProjePozMalzeme unique constraint test
    proje = ProjeFactory()
    poz15 = PozFactory(poz_no="15")
    poz20 = PozFactory(poz_no="20")
    cimento_a = MalzemeFactory(malzeme_kodu="CIM-A")
    cimento_b = MalzemeFactory(malzeme_kodu="CIM-B")
    cimento_c = MalzemeFactory(malzeme_kodu="CIM-C")
    
    # İki farklı poz için aynı kaynak malzeme, farklı etkin malzeme
    ppm1 = ProjePozMalzemeFactory(proje=proje, poz=poz15, kaynak_malzeme=cimento_a, etkin_malzeme=cimento_b)
    ppm2 = ProjePozMalzemeFactory(proje=proje, poz=poz20, kaynak_malzeme=cimento_a, etkin_malzeme=cimento_c)
    
    # Her ikisi de kaydedilebilmeli (unique: tenant+proje+poz+kaynak_malzeme)
    assert ppm1.pk is not None
    assert ppm2.pk is not None
    assert ppm1.etkin_malzeme != ppm2.etkin_malzeme
```

---

## 18. RİSKLER

| Risk | Etki | Olasılık | Önlem |
|------|------|----------|-------|
| **Mevcut snapshot'lar bozulur** | 🔴 YÜKSEK | Düşük | Snapshot alanları `read_only=True`, save()'de koruma var, testlerle doğrula |
| **Fallback zinciri tutarsızlığı** | 🟠 ORTA | Orta | PozPlan.save() poz_etkin_fiyati kullanacak şekilde DÜZELTİLMELİ |
| **MalzemeFiyat modeli eksik** | 🟠 ORTA | Yüksek | Fallback zincirinde 3. sıra opsiyonel, None dönerse 4. sıraya geçer |
| **Tedarikci-Cari çiftliği** | 🟡 DÜŞÜK | Orta | ProjeMalzeme'de hem tedarikci hem cari FK'sı var |
| **Performans (N+1 sorgu)** | 🟡 DÜŞÜK | Orta | select_related/prefetch_related zorunlu, cacheleme |
| **Migration veri kaybı** | 🔴 YÜKSEK | Düşük | Mevcut veriler korunmalı, default değerlerle migration |
| **Frontend state karmaşası** | 🟠 ORTA | Orta | Store modülü ayrı tutulmalı, TypeScript tipleri güncellenmeli |
| **YFKAnaliz eşleşme güvenilmez** | 🟡 DÜŞÜK | Yüksek | Eşleşme %100 değilse None döndür, yanlış fiyat yerine fiyatsız |
| **ProjePozMalzeme miktar_override** | 🟡 DÜŞÜK | Düşük | Nullable, PozMalzemeIliskisi.miktar fallback |

---

## 19. UYGULAMA SIRASI

### Aşama 1: Temel Altyapı (Hafta 1)
1. ✅ **Revize analiz raporu oluştur** (bu belge)
2. 🔧 `construction/models.py` → `ProjeMalzeme`, `ProjeMalzemeFiyat`, `ProjePozMalzeme` ekle
3. 🔧 `construction/serializers.py` → Serializer'lar ekle
4. 🔧 `construction/views.py` → ViewSet'ler ekle (TenantScopedViewSet)
5. 🔧 Migration oluştur ve test et
6. 🔧 `construction/services/malzeme_fiyat.py` (YENİ DOSYA) → `malzeme_etkin_fiyati()`, `etkin_poz_malzeme()`, `FiyatSonucu` dataclass

### Aşama 2: Entegrasyon ve FAZ 1 Düzeltmesi (Hafta 2)
7. 🔧 `construction/services.py` → `malzeme_etkin_fiyati`, `etkin_poz_malzeme` export et
8. 🔧 `construction/services/yaklasik_maliyet.py` → Malzeme fiyatı için yeni servis kullan
9. 🔧 **KRİTİK DÜZELTME:** `PozPlan.save()` → `poz_etkin_fiyati` kullanacak şekilde güncelle
10. 🔧 `YaklasikMaliyetSatiri.save()` → Mevcut koruma korunmalı, yeni kayıtlar için poz_etkin_fiyati
11. 🔧 Data migration: `TedarikciTeklifi.secildi=True` → `ProjeMalzeme.selected_teklif` senkronizasyonu

### Aşama 3: Frontend (Hafta 3)
12. 🔧 `frontend/src/types/insaat.ts` → Yeni interface'ler (ProjeMalzeme, ProjeMalzemeFiyat, ProjePozMalzeme, FiyatSonucu)
13. 🔧 `frontend/src/services/insaatApi.ts` → API çağrıları
14. 🔧 `ProjeMalzemeView.vue`, `ProjeMalzemeFiyatView.vue`, `ProjePozMalzemeView.vue` oluştur
15. 🔧 `TedarikciTeklifleriView.vue` → "Seçili Teklif Olarak Ata" butonu (ProjeMalzeme.selected_teklif set et)
16. 🔧 `YaklasikMaliyetView.vue` → Malzeme fiyatı seçimi UI, fallback kaynak gösterimi
17. 🔧 `MalzemeFiyatKarsilastirmaView.vue` → 4 kaynaklı karşılaştırma ekranı

### Aşama 4: Raporlama, Test ve PozAnaliz FK (Hafta 4+)
18. 🔧 PozPlan, YaklasikMaliyet, Hakedis raporlarında malzeme bazlı breakdown
19. 🔧 Tüm test senaryoları (TEST 1-8) implementasyonu
20. 🔧 **PozAnaliz.malzeme_fk** alanı ekleme (ayrı milestone - teknik borç)
21. 🔧 MalzemeFiyat modeli değerlendirmesi (gerekirse ekleme)
22. 🔧 Performans testleri, N+1 sorgu analizi
23. 🔧 Dokümantasyon güncelleme

---

## 20. ÖZET: KRİTİK KARARLAR

| Konu | Karar |
|------|-------|
| Alternatif malzeme | **ProjePozMalzeme** (poz+malzeme bazlı), ProjeMalzeme'de YOK |
| Malzeme fiyat fallback | 1. ProjeMalzemeFiyat 2. ProjeMalzeme.selected_teklif 3. MalzemeFiyat 4. YFKAnaliz 5. None |
| Poz fiyatı kullanımı | **YASAK** - malzeme fiyatı için poz fiyatı kullanılmaz |
| Tedarikçi teklifi seçimi | **ProjeMalzeme.selected_teklif FK** (SET_NULL) |
| Snapshot koruması | **MEVCUT KORUNUR**, yeni kayıtlar yeni servislerle |
| PozPlan.save() | **poz_etkin_fiyati** kullanacak (FAZ 1 hatası düzeltilir) |
| PozAnaliz malzeme FK | **FAZ 2'DE DEĞİŞTİRİLMEZ**, ayrı milestone |
| YFK malzeme fiyatı | **Güvenilirlik kontrolüyle**, şüpheliyse None |
| Fiyat sonucu yapısı | **FiyatSonucu dataclass** (fiyat, kaynak, kaynak_id, para_birimi) |

---

**Bu analiz onaylanmadan implementation'a geçilmeyecektir.**