"""
FAZ 2 — Malzeme Fiyat Servisleri

Bu modül proje bazlı malzeme fiyatlarını çözmek için kullanılır.
Fallback sırası KESİN:
1. ProjeMalzemeFiyat
2. ProjeMalzeme.selected_teklif
3. MalzemeFiyat
4. None

YFK MALZEME FİYATI BU FAZDA KULLANILMAYACAK.
PozFiyat veya ProjePozFiyat kullanılarak malzeme fiyatı türetmek YASAK.
Her kaynak TRY olmalı. TRY dışındaki fiyat maliyet hesabına girerse hata/None üret.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from ..models import Malzeme, Poz, Proje, ProjeMalzeme, ProjeMalzemeFiyat, ProjePozMalzeme, MalzemeFiyat, TedarikciTeklifi


@dataclass
class FiyatSonucu:
    """Fiyat hesaplama sonucu."""
    fiyat: Optional[Decimal]
    kaynak: str
    kaynak_id: Optional[int]
    para_birimi: str


def _sadece_try(fiyat: Optional[Decimal], para_birimi: str) -> Optional[Decimal]:
    """Sadece TRY para birimi kabul edilir, diğerleri None döner."""
    if fiyat is not None and para_birimi != "TRY":
        return None
    return fiyat


def etkin_poz_malzeme(proje: Proje, poz: Poz, kaynak_malzeme: Malzeme) -> tuple[Malzeme, Optional[Decimal]]:
    """
    Proje-poz seviyesinde etkin malzemeyi ve miktar override'ını döner.

    Mantık:
    - Aktif ProjePozMalzeme varsa etkin_malzeme ve miktar_override.
    - Yoksa kaynak_malzeme ve None (override yok).

    Returns:
        (etkin_malzeme, miktar_override)
    """
    ppm = ProjePozMalzeme.objects.filter(
        tenant_id=proje.tenant_id,
        proje=proje,
        poz=poz,
        kaynak_malzeme=kaynak_malzeme,
        is_active=True,
    ).first()

    if ppm:
        return ppm.etkin_malzeme, ppm.miktar_override

    return kaynak_malzeme, None


def malzeme_etkin_fiyati(proje: Proje, malzeme: Malzeme, yil: int) -> FiyatSonucu:
    """
    Malzemenin etkin birim fiyatını fallback zinciriyle çözer.

    Fallback sırası:
    1. ProjeMalzemeFiyat (proje + malzeme + yıl, is_active=True, TRY)
    2. ProjeMalzeme.selected_teklif (tenant/proje/malzeme uyumlu, is_active=True, TRY)
    3. MalzemeFiyat (tenant + malzeme + yıl, is_active=True, TRY)
    4. None

    Returns:
        FiyatSonucu (fiyat, kaynak, kaynak_id, para_birimi)
    """
    # 1. ProjeMalzemeFiyat
    pmf = ProjeMalzemeFiyat.objects.filter(
        tenant_id=proje.tenant_id,
        proje=proje,
        malzeme=malzeme,
        yil=yil,
        is_active=True,
    ).order_by("-created_at").first()

    if pmf:
        fiyat = _sadece_try(pmf.birim_fiyat, pmf.para_birimi)
        if fiyat is not None:
            return FiyatSonucu(
                fiyat=fiyat,
                kaynak="ProjeMalzemeFiyat",
                kaynak_id=pmf.id,
                para_birimi=pmf.para_birimi,
            )

    # 2. ProjeMalzeme.selected_teklif
    pm = ProjeMalzeme.objects.filter(
        tenant_id=proje.tenant_id,
        proje=proje,
        malzeme=malzeme,
        is_active=True,
    ).first()

    if pm and pm.selected_teklif:
        teklif = pm.selected_teklif
        # Tenant/proje/malzeme/is_active validasyonu model clean()'de yapılıyor
        if teklif.is_active and teklif.tenant_id == proje.tenant_id and teklif.proje_id == proje.id and teklif.malzeme_id == malzeme.id:
            fiyat = _sadece_try(teklif.birim_fiyat, "TRY")  # Teklif her zaman TRY
            if fiyat is not None:
                return FiyatSonucu(
                    fiyat=fiyat,
                    kaynak="ProjeMalzeme.selected_teklif",
                    kaynak_id=teklif.id,
                    para_birimi="TRY",
                )

    # 3. MalzemeFiyat (genel tenant bazlı)
    mf = MalzemeFiyat.objects.filter(
        tenant_id=proje.tenant_id,
        malzeme=malzeme,
        yil=yil,
        is_active=True,
    ).order_by("-created_at").first()

    if mf:
        fiyat = _sadece_try(mf.birim_fiyat, mf.para_birimi)
        if fiyat is not None:
            return FiyatSonucu(
                fiyat=fiyat,
                kaynak="MalzemeFiyat",
                kaynak_id=mf.id,
                para_birimi=mf.para_birimi,
            )

    # 4. Bulunamadı
    return FiyatSonucu(
        fiyat=None,
        kaynak="Bulunamadı",
        kaynak_id=None,
        para_birimi="TRY",
    )


def proje_poz_etkin_fiyati(proje: Proje, poz: Poz, yil: int) -> Optional[Decimal]:
    """
    Pozun proje bazlı etkin birim fiyatını döner.

    Öncelik:
    1. ProjePozFiyat varsa doğrudan döndür (poz birim fiyat override'ıdır).
    2. Yoksa proje bazlı poz analizi hesapla.
    3. Hesaplanamıyorsa PozFiyat.
    4. PozFiyat yoksa YfkFiyat.
    5. Yoksa None.

    ÇOK ÖNEMLİ: ProjePozFiyat bulunduğunda ProjePozMalzeme dikkate alınmaz.
    Çünkü ProjePozFiyat nihai poz birim fiyat override'ıdır.
    """
    from ..models import ProjePozFiyat, PozFiyat, YfkFiyat, YfkPozVersiyon

    # 1. ProjePozFiyat - poz birim fiyat override'ı
    ppf = ProjePozFiyat.objects.filter(
        tenant_id=proje.tenant_id,
        proje=proje,
        poz=poz,
        yil=yil,
        is_active=True,
    ).order_by("-created_at").first()

    if ppf:
        return ppf.birim_fiyat

    # 2. Proje bazlı poz analizi hesapla
    # PozAnaliz'deki malzeme kalemleri için etkin malzeme ve fiyatı bul
    from ..models import PozAnaliz, PozMalzemeIliskisi

    analiz_kalemleri = PozAnaliz.objects.filter(
        tenant_id=proje.tenant_id,
        poz=poz,
        analiz_tipi=PozAnaliz.AnalizTipi.MALZEME,
    ).select_related("malzeme")

    if not analiz_kalemleri.exists():
        # Malzeme analizi yoksa genel fiyata düş
        pass
    else:
        toplam_malzeme_tutari = Decimal("0")
        hesaplanabilir = True

        for analiz in analiz_kalemleri:
            # PozMalzemeIliskisi üzerinden kaynak malzemeyi bul
            pmi = PozMalzemeIliskisi.objects.filter(
                tenant_id=proje.tenant_id,
                poz=poz,
                malzeme__malzeme_kodu=analiz.malzeme,
            ).first()

            if not pmi:
                hesaplanabilir = False
                break

            kaynak_malzeme = pmi.malzeme
            # Etkin malzeme ve miktar override
            etkin_malzeme, miktar_override = etkin_poz_malzeme(proje, poz, kaynak_malzeme)
            miktar = miktar_override if miktar_override is not None else pmi.miktar

            # Etkin malzemenin fiyatı
            sonuc = malzeme_etkin_fiyati(proje, etkin_malzeme, yil)
            if sonuc.fiyat is None:
                hesaplanabilir = False
                break

            toplam_malzeme_tutari += (miktar * sonuc.fiyat).quantize(Decimal("0.01"))

        if hesaplanabilir:
            # İşçilik, makine, nakliye, diğer kalemleri ekle
            diger_toplam = PozAnaliz.objects.filter(
                tenant_id=proje.tenant_id,
                poz=poz,
            ).exclude(analiz_tipi=PozAnaliz.AnalizTipi.MALZEME).aggregate(
                toplam=models.Sum("tutar")
            )["toplam"] or Decimal("0")

            return (toplam_malzeme_tutari + diger_toplam).quantize(Decimal("0.01"))

    # 3. PozFiyat (genel)
    genel_fiyat = PozFiyat.objects.filter(
        tenant_id=proje.tenant_id,
        poz=poz,
        yil=yil,
        is_active=True,
    ).order_by("-created_at").first()

    if genel_fiyat:
        return genel_fiyat.birim_fiyat

    # 4. YfkFiyat
    yfk_fiyat = YfkFiyat.objects.filter(
        tenant_id=proje.tenant_id,
        poz_versiyon__poz_no=poz.poz_no,
        yil=yil,
        is_active=True,
    ).select_related("poz_versiyon").order_by("-created_at").first()

    if yfk_fiyat:
        return yfk_fiyat.birim_fiyat

    # 5. Bulunamadı
    return None