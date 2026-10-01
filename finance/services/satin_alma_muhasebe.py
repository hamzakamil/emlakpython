"""FAZ 4 — Satın alma muhasebe orkestrasyonu.

MalKabul ONAYLANDI → alış faturası → CariHareket → MuhasebeFişi.
Mevcut servisleri çağırır (kopyalamaz): fatura_cari_hareketi_olustur,
fatura_durum_gecis. Fiş bacakları satın almaya özeldir (320 + stok + 191);
stok maliyeti KDV hariçtir. Değerleme yapılmaz.
"""

from __future__ import annotations

import logging
from decimal import Decimal

log = logging.getLogger("erp.finans")

from django.core.exceptions import ValidationError
from django.db import transaction

from accounting.models import FisSatiri, HesapPlani, MuhasebeFisi
from cari.models import CariHareket

from ..models import Fatura, FaturaKalemi
from .entegrasyon import fatura_cari_hareketi_olustur
from .state_machine import fatura_durum_gecis

STOK_HESAP_KODU = "150"
KDV_HESAP_KODU = "191"
SATICI_HESAP_KODU = "320"
KDV_VARSAYILAN_ORAN = Decimal("20")
KDV_VARSAYILAN_PROFIL_KODU = "VARSAYILAN"


def _kdv_orani_coz(tenant_id: int) -> Decimal:
    """KDV oranı çözüm sırası: tenant VARSAYILAN vergi profili → %20.

    Şema değişikliği gerektirmez; profil yoksa mevcut davranış korunur.
    """
    from ..models import VergiProfili

    profil = VergiProfili.objects.filter(
        tenant_id=tenant_id, kod=KDV_VARSAYILAN_PROFIL_KODU, is_active=True
    ).first()
    if profil is not None:
        return Decimal(profil.kdv_orani)
    return KDV_VARSAYILAN_ORAN


def _kalem_kdv_orani_coz(kabul_kalemi, tenant_id: int) -> Decimal:
    """FAZ 6C kalem-bazlı KDV çözüm sırası: kalem override → profil → %20."""
    oran = getattr(kabul_kalemi, "kdv_orani", None)
    if oran is not None:
        return Decimal(oran)
    return _kdv_orani_coz(tenant_id)


def _hesap_coz(tenant_id: int, malzeme_id: int | None, hesap_turu: str) -> HesapPlani:
    """Hesap çözüm sırası: malzemeye özel → tenant varsayılanı → sabit kod."""
    from purchasing.models import StokHesapEsleme

    if malzeme_id:
        esleme = StokHesapEsleme.objects.filter(
            tenant_id=tenant_id, malzeme_id=malzeme_id,
            hesap_turu=hesap_turu, is_active=True,
        ).select_related("hesap").first()
        if esleme:
            return esleme.hesap
    esleme = StokHesapEsleme.objects.filter(
        tenant_id=tenant_id, malzeme__isnull=True,
        hesap_turu=hesap_turu, is_active=True,
    ).select_related("hesap").first()
    if esleme:
        return esleme.hesap
    kod = STOK_HESAP_KODU if hesap_turu == "stok" else KDV_HESAP_KODU
    hesap, _ = HesapPlani.objects.get_or_create(
        tenant_id=tenant_id, kod=kod,
        defaults={"ad": "Stok" if hesap_turu == "stok" else "KDV", "tip": "aktif"},
    )
    return hesap


def _satici_hesap(tenant_id: int) -> HesapPlani:
    hesap, _ = HesapPlani.objects.get_or_create(
        tenant_id=tenant_id, kod=SATICI_HESAP_KODU,
        defaults={"ad": "Satıcılar", "tip": "pasif"},
    )
    return hesap


def _muhasebe_ozeti(mal_kabul_id: int, *, tenant_id: int) -> dict:
    """Mal kabulün fatura/cari/fiş bağlantı özeti (rozet + onay yanıtı)."""
    from purchasing.models import MalKabul

    ozet: dict = {"fatura_no": None, "cari_hareket_id": None, "fis_no": None}
    try:
        kabul = MalKabul.objects.get(pk=mal_kabul_id, tenant_id=tenant_id)
    except MalKabul.DoesNotExist:
        return ozet
    fatura = Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").first()
    if fatura is None:
        return ozet
    ozet["fatura_no"] = fatura.No
    hareket = CariHareket.objects.filter(fatura=fatura).first()
    if hareket is not None:
        ozet["cari_hareket_id"] = hareket.pk
    fis = MuhasebeFisi.objects.filter(
        tenant_id=tenant_id, fis_no=f"MK-{kabul.belge_no}"
    ).first()
    if fis is not None:
        ozet["fis_no"] = fis.fis_no
    return ozet


@transaction.atomic
def satin_alma_muhasebe_olustur(mal_kabul_id: int, *, tenant_id: int) -> dict:
    """Onaylı mal kabul için fatura + cari hareket + fiş üretir (idempotent).

    Deterministik anahtarlar (fatura No, fis_no) sayesinde ikinci çağrı
    yeni kayıt üretmez; mevcut kayıtları döner.
    """
    from purchasing.models import MalKabul

    try:
        kabul = (
            MalKabul.objects.select_for_update()
            .select_related("siparis__tedarikci", "proje")
            .prefetch_related("kalemler__malzeme")
            .get(pk=mal_kabul_id, tenant_id=tenant_id)
        )
    except MalKabul.DoesNotExist:
        raise ValidationError({"kabul": "Mal kabul bu firma kapsamına ait değil."})
    if kabul.durum != MalKabul.Durum.ONAYLANDI:
        raise ValidationError({"kabul": "Yalnızca onaylı kabul muhasebeleştirilir."})
    tedarikci = kabul.siparis.tedarikci
    cari = tedarikci.cari
    if cari is None:
        # Cari bağlanmamış tedarikçi: FAZ 3B davranışı korunur (onay çalışır),
        # muhasebe kaydı üretilmez. Rozet boş döner.
        return {"fatura": None, "cari_hareket": None, "fis": None}
    if cari.tenant_id != tenant_id:
        raise ValidationError({"tedarikci": "Cari kart bu firma kapsamına ait değil."})

    fatura_no = f"SAT-{kabul.belge_no}"
    fatura = Fatura.objects.filter(No=fatura_no).first()
    if fatura is not None and fatura.tenant_id != tenant_id:
        raise ValidationError({"fatura": "Fatura numarası başka firmada kullanılıyor."})
    if fatura is None:
        kalemler = [k for k in kabul.kalemler.filter(is_active=True) if k.kabul_miktari > 0]
        if not kalemler:
            raise ValidationError({"kabul": "Muhasebeleşecek kabul miktarı yok."})
        fatura = Fatura.objects.create(
            tenant_id=tenant_id,
            No=fatura_no,
            cari=cari,
            tarih=kabul.kabul_tarihi,
            tutar=Decimal("0"),
            fatura_turu="alis",
            alacakli=False,
            durum=Fatura.DurumChoices.DRAFT,
            aciklama=f"Mal Kabul {kabul.belge_no} satın alma faturası",
        )
        ara_toplam = Decimal("0")
        kdv_toplam = Decimal("0")
        for kalem in kalemler:
            oran = _kalem_kdv_orani_coz(kalem, tenant_id)
            ara = (kalem.kabul_miktari * kalem.birim_fiyat_snapshot).quantize(Decimal("0.01"))
            kdv = (ara * oran / Decimal("100")).quantize(Decimal("0.01"))
            FaturaKalemi.objects.create(
                fatura=fatura,
                aciklama=f"{kalem.malzeme.ad} (kabul)",
                miktar=kalem.kabul_miktari,
                birim=kalem.birim or kalem.malzeme.birim,
                birim_fiyat=kalem.birim_fiyat_snapshot,
                kdv_orani=oran,
                kaynak_kabul_kalemi=kalem,
            )
            ara_toplam += ara
            kdv_toplam += kdv
        fatura.tutar = ara_toplam + kdv_toplam
        fatura.save(update_fields=["tutar"])
        fatura = fatura_durum_gecis(fatura.pk, Fatura.DurumChoices.ACTIVE, tenant_id=tenant_id)

    hareket = fatura_cari_hareketi_olustur(fatura)
    fis = _satin_alma_fisi(fatura, kabul, tenant_id)
    log.info(
        "event=muhasebelestir fatura=%s fis=%s", fatura.No, fis.fis_no,
        extra={"tenant_id": tenant_id, "operation": "satin-alma.muhasebelestir",
               "resource_id": kabul.pk},
    )
    return {"fatura": fatura, "cari_hareket": hareket, "fis": fis}


def _satin_alma_fisi(fatura: Fatura, kabul, tenant_id: int) -> MuhasebeFisi:
    """Satın alma fişi (MK-belge_no): stok BORC + KDV BORC + satıcı ALACAK.

    FAZ 6C: oranlar profilden yeniden çözülmez; faturaya yazılmış kalem
    snapshot'ları (matrah/KDV) birebir kullanılır.
    """
    fis_no = f"MK-{kabul.belge_no}"
    mevcut = MuhasebeFisi.objects.filter(tenant_id=tenant_id, fis_no=fis_no).first()
    if mevcut is not None:
        return mevcut
    stok_bacaklari: dict[int, Decimal] = {}
    kdv_toplam = Decimal("0")
    for satir in fatura.kalemler.select_related("kaynak_kabul_kalemi").all():
        ara = satir.ara_toplam
        kdv = satir.kdv_tutari
        kaynak = satir.kaynak_kabul_kalemi
        malzeme_id = kaynak.malzeme_id if kaynak is not None else None
        hesap = _hesap_coz(tenant_id, malzeme_id, "stok")
        stok_bacaklari[hesap.pk] = stok_bacaklari.get(hesap.pk, Decimal("0")) + ara
        kdv_toplam += kdv
    ara_toplam = sum(stok_bacaklari.values(), Decimal("0"))
    fis = MuhasebeFisi.objects.create(
        tenant_id=tenant_id,
        fis_no=fis_no,
        fis_tarihi=kabul.kabul_tarihi,
        aciklama=f"Mal Kabul {kabul.belge_no} satın alma fişi",
        durum=MuhasebeFisi.Durum.KAYITLI,
    )
    for hesap_pk, tutar in sorted(stok_bacaklari.items()):
        FisSatiri.objects.create(fis=fis, hesap_id=hesap_pk, borc=tutar, alacak=Decimal("0"))
    if kdv_toplam > 0:
        kdv_hesap = _hesap_coz(tenant_id, None, "kdv")
        FisSatiri.objects.create(fis=fis, hesap=kdv_hesap, borc=kdv_toplam, alacak=Decimal("0"))
    FisSatiri.objects.create(
        fis=fis, hesap=_satici_hesap(tenant_id),
        borc=Decimal("0"), alacak=ara_toplam + kdv_toplam,
    )
    return fis


@transaction.atomic
def satin_alma_muhasebe_iptal(mal_kabul_id: int, *, tenant_id: int, neden: str = "") -> dict:
    """Kabul iptalinin muhasebe ters kayıtları (idempotent).

    Cari hareket iptale çekilir; orijinal fiş IPTAL + ters fiş açılır.
    """
    from purchasing.models import MalKabul

    sonuc: dict = {"cari_hareket": None, "fis": None, "ters_fis": None}
    try:
        kabul = MalKabul.objects.get(pk=mal_kabul_id, tenant_id=tenant_id)
    except MalKabul.DoesNotExist:
        raise ValidationError({"kabul": "Mal kabul bulunamadı."})
    fatura = Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").first()
    if fatura is None:
        return sonuc
    hareket = CariHareket.objects.filter(fatura=fatura).first()
    if hareket is not None and not hareket.is_cancelled:
        hareket.is_cancelled = True
        hareket.iptal_nedeni = neden or "Mal kabul iptali"
        hareket.save(update_fields=["is_cancelled", "iptal_nedeni"])
    sonuc["cari_hareket"] = hareket
    fis = MuhasebeFisi.objects.filter(
        tenant_id=tenant_id, fis_no=f"MK-{kabul.belge_no}"
    ).first()
    if fis is not None and fis.durum != MuhasebeFisi.Durum.IPTAL:
        ters = MuhasebeFisi.objects.filter(
            tenant_id=tenant_id, fis_no=f"MKTR-{kabul.belge_no}"
        ).first()
        if ters is None:
            ters = MuhasebeFisi.objects.create(
                tenant_id=tenant_id,
                fis_no=f"MKTR-{kabul.belge_no}",
                fis_tarihi=fis.fis_tarihi,
                aciklama=f"TERS KAYIT: {fis.aciklama}",
                durum=MuhasebeFisi.Durum.KAYITLI,
            )
            for satir in fis.satirlar.all():
                FisSatiri.objects.create(
                    fis=ters, hesap=satir.hesap,
                    borc=satir.alacak, alacak=satir.borc,
                )
        fis.durum = MuhasebeFisi.Durum.IPTAL
        fis.save(update_fields=["durum"])
        sonuc["ters_fis"] = ters
    sonuc["fis"] = fis
    log.info(
        "event=muhasebe_iptal kabul=%s", kabul.belge_no,
        extra={"tenant_id": tenant_id, "operation": "satin-alma.muhasebe_iptal",
               "resource_id": kabul.pk},
    )
    return sonuc


@transaction.atomic
def stok_iade_muhasebelestir(iade_hareket_id: int, *, tenant_id: int) -> dict:
    """Stok iade hareketinin iade faturası + cari + fiş kayıtları (idempotent)."""
    from purchasing.models import MalKabul, StokHareketi

    try:
        hareket = StokHareketi.objects.select_related(
            "malzeme", "depo"
        ).get(pk=iade_hareket_id, tenant_id=tenant_id)
    except StokHareketi.DoesNotExist:
        raise ValidationError({"hareket": "Stok hareketi bu firma kapsamına ait değil."})
    if hareket.kaynak_belge_tipi != "Iade":
        raise ValidationError({"hareket": "Yalnızca iade hareketleri muhasebeleştirilir."})
    try:
        kabul = MalKabul.objects.select_related("siparis__tedarikci").get(
            pk=hareket.kaynak_belge_id, tenant_id=tenant_id
        )
    except MalKabul.DoesNotExist:
        raise ValidationError({"kabul": "Mal kabul bu firma kapsamına ait değil."})
    cari = kabul.siparis.tedarikci.cari
    if cari is None or cari.tenant_id != tenant_id:
        raise ValidationError({"tedarikci": "Tedarikçiye cari kart bağlanmalıdır."})
    from purchasing.models import MalKabulKalemi

    iade_no = f"IAD-{kabul.belge_no}-{hareket.kaynak_belge_kalem_id}-{hareket.pk}"
    fatura = Fatura.objects.filter(No=iade_no).first()
    if fatura is None:
        try:
            kabul_kalemi = MalKabulKalemi.objects.select_related("malzeme").get(
                pk=hareket.kaynak_belge_kalem_id, tenant_id=tenant_id
            )
        except MalKabulKalemi.DoesNotExist:
            raise ValidationError({"hareket": "İade hareketinin kabul kalemi bulunamadı."})
        kaynak_satir = FaturaKalemi.objects.filter(
            kaynak_kabul_kalemi=kabul_kalemi
        ).order_by("id").first()
        kdv_orani = (
            kaynak_satir.kdv_orani
            if kaynak_satir is not None
            else _kdv_orani_coz(tenant_id)
        )
        tutar = (hareket.miktar * hareket.maliyet).quantize(Decimal("0.01"))
        kdv = (tutar * kdv_orani / Decimal("100")).quantize(Decimal("0.01"))
        original = Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").first()
        fatura = Fatura.objects.create(
            tenant_id=tenant_id,
            No=iade_no,
            cari=cari,
            tarih=hareket.tarih,
            tutar=tutar + kdv,
            fatura_turu="iade",
            alacakli=True,
            durum=Fatura.DurumChoices.DRAFT,
            aciklama=f"Mal Kabul {kabul.belge_no} iade faturası",
            iade_faturasi=original,
        )
        FaturaKalemi.objects.create(
            fatura=fatura,
            aciklama=f"{hareket.malzeme.ad} (iade)",
            miktar=hareket.miktar,
            birim=hareket.birim,
            birim_fiyat=hareket.maliyet,
            kdv_orani=kdv_orani,
            kaynak_kabul_kalemi=kabul_kalemi,
        )
        fatura = fatura_durum_gecis(fatura.pk, Fatura.DurumChoices.ACTIVE, tenant_id=tenant_id)
    hareket_ = fatura_cari_hareketi_olustur(fatura)
    fis = _iade_fisi(fatura, hareket, tenant_id)
    log.info(
        "event=iade_muhasebe fatura=%s fis=%s", fatura.No, fis.fis_no,
        extra={"tenant_id": tenant_id, "operation": "stok.iade_muhasebe",
               "resource_id": hareket.pk},
    )
    return {"fatura": fatura, "cari_hareket": hareket_, "fis": fis}


def _iade_fisi(fatura: Fatura, hareket, tenant_id: int) -> MuhasebeFisi:
    """İade ters fişi (IAD-belge-kalem-hareket): satıcı BORC + stok/KDV ALACAK."""
    from purchasing.models import MalKabulKalemi as _KK

    fis_no = f"MI-{hareket.pk}"
    mevcut = MuhasebeFisi.objects.filter(tenant_id=tenant_id, fis_no=fis_no).first()
    if mevcut is not None:
        return mevcut
    kalem = fatura.kalemler.order_by("id").first()
    ara = kalem.ara_toplam if kalem else fatura.tutar
    kdv = kalem.kdv_tutari if kalem else Decimal("0")
    stok_hesap = _hesap_coz(tenant_id, hareket.malzeme_id, "stok")
    fis = MuhasebeFisi.objects.create(
        tenant_id=tenant_id,
        fis_no=fis_no,
        fis_tarihi=fatura.tarih,
        aciklama=f"İade ters fişi ({fatura.No})",
        durum=MuhasebeFisi.Durum.KAYITLI,
    )
    FisSatiri.objects.create(
        fis=fis, hesap=_satici_hesap(tenant_id),
        borc=ara + kdv, alacak=Decimal("0"),
    )
    FisSatiri.objects.create(
        fis=fis, hesap=stok_hesap, borc=Decimal("0"), alacak=ara,
    )
    if kdv > 0:
        FisSatiri.objects.create(
            fis=fis, hesap=_hesap_coz(tenant_id, None, "kdv"),
            borc=Decimal("0"), alacak=kdv,
        )
    return fis
