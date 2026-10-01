"""FAZ 3A servisleri — merkezi belge no, durum geçişleri, talep→sipariş dönüşümü.

Desen: finance/services/state_machine.py (geçiş haritası + atomic +
select_for_update) ve construction/services.py hakedis_onayla.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from .models import (
    BELGE_ONEKLERI,
    BelgeNumaraSayaci,
    BelgeTipi,
    Depo,
    MalKabul,
    MalKabulKalemi,
    SatinAlmaSiparisi,
    SatinAlmaSiparisiKalemi,
    SatinAlmaTalebi,
    SatinAlmaTalebiKalemi,
    StokHareketi,
)


TALEP_GECISLERI = {
    SatinAlmaTalebi.Durum.TASLAK: frozenset(
        {SatinAlmaTalebi.Durum.ONAYA_GONDERILDI, SatinAlmaTalebi.Durum.IPTAL}
    ),
    SatinAlmaTalebi.Durum.ONAYA_GONDERILDI: frozenset(
        {
            SatinAlmaTalebi.Durum.ONAYLANDI,
            SatinAlmaTalebi.Durum.REDDEDILDI,
            SatinAlmaTalebi.Durum.IPTAL,
        }
    ),
    SatinAlmaTalebi.Durum.ONAYLANDI: frozenset(
        {SatinAlmaTalebi.Durum.SIPARISE_DONUSTU, SatinAlmaTalebi.Durum.IPTAL}
    ),
    SatinAlmaTalebi.Durum.REDDEDILDI: frozenset({SatinAlmaTalebi.Durum.IPTAL}),
    SatinAlmaTalebi.Durum.SIPARISE_DONUSTU: frozenset(),
    SatinAlmaTalebi.Durum.IPTAL: frozenset(),
}

SIPARIS_GECISLERI = {
    SatinAlmaSiparisi.Durum.TASLAK: frozenset(
        {SatinAlmaSiparisi.Durum.ONAY_BEKLIYOR, SatinAlmaSiparisi.Durum.IPTAL}
    ),
    SatinAlmaSiparisi.Durum.ONAY_BEKLIYOR: frozenset(
        {SatinAlmaSiparisi.Durum.ONAYLANDI, SatinAlmaSiparisi.Durum.IPTAL}
    ),
    SatinAlmaSiparisi.Durum.ONAYLANDI: frozenset(
        {
            SatinAlmaSiparisi.Durum.KISMI_TESLIM,
            SatinAlmaSiparisi.Durum.TAMAMLANDI,
            SatinAlmaSiparisi.Durum.IPTAL,
        }
    ),
    SatinAlmaSiparisi.Durum.KISMI_TESLIM: frozenset({SatinAlmaSiparisi.Durum.TAMAMLANDI}),
    SatinAlmaSiparisi.Durum.TAMAMLANDI: frozenset(),
    SatinAlmaSiparisi.Durum.IPTAL: frozenset(),
}


@transaction.atomic
def belge_numarasi_uret(tenant_id: int, belge_tipi: str, yil: int | None = None) -> str:
    """Merkezi belge numarası üretir: tenant + yıl + belge tipi bazlı sayaç.

    Tek uygulama noktası — her model kendi numara mantığını yazmaz.
    Aynı numaranın iki kez üretilmesi select_for_update + unique constraint
    ile engellenir. Format: ``ST-2026-0001`` / ``SS-2026-0001``.
    """
    if belge_tipi not in BelgeTipi.values:
        raise ValidationError({"belge_tipi": "Geçersiz belge tipi."})
    yil = yil or timezone.now().year
    sayac, _ = BelgeNumaraSayaci.objects.select_for_update().get_or_create(
        tenant_id=tenant_id, belge_tipi=belge_tipi, yil=yil, defaults={"son_no": 0}
    )
    sayac.son_no += 1
    sayac.save(update_fields=["son_no"])
    onek = BELGE_ONEKLERI[belge_tipi]
    return f"{onek}-{yil}-{sayac.son_no:04d}"


@transaction.atomic
def talep_durum_gecis(talep_id: int, hedef_durum: str, *, tenant_id: int) -> SatinAlmaTalebi:
    """Talep durum geçişi (geçiş haritası + satır kilidi)."""
    log = logging.getLogger("erp.purchasing")
    talep = SatinAlmaTalebi.objects.select_for_update().get(pk=talep_id, tenant_id=tenant_id)
    if hedef_durum not in SatinAlmaTalebi.Durum.values:
        raise ValidationError({"durum": "Geçersiz talep durumu."})
    if hedef_durum not in TALEP_GECISLERI.get(talep.durum, frozenset()):
        raise ValidationError(
            {"durum": f"{talep.durum} durumundan {hedef_durum} durumuna geçilemez."}
        )
    kaynak = talep.durum
    talep.durum = hedef_durum
    talep.save(update_fields=["durum", "updated_at"])
    if hedef_durum in (
        SatinAlmaTalebi.Durum.ONAYLANDI,
        SatinAlmaTalebi.Durum.REDDEDILDI,
        SatinAlmaTalebi.Durum.IPTAL,
    ):
        log.info(
            "event=talep_durum %s -> %s (%s)", kaynak, hedef_durum, talep.talep_no,
            extra={"tenant_id": tenant_id, "operation": "satin-alma.durum",
                   "resource_id": talep.pk},
        )
    return talep


@transaction.atomic
def siparis_durum_gecis(
    siparis_id: int, hedef_durum: str, *, tenant_id: int
) -> SatinAlmaSiparisi:
    """Sipariş durum geçişi (geçiş haritası + satır kilidi)."""
    log = logging.getLogger("erp.purchasing")
    siparis = SatinAlmaSiparisi.objects.select_for_update().get(
        pk=siparis_id, tenant_id=tenant_id
    )
    if hedef_durum not in SatinAlmaSiparisi.Durum.values:
        raise ValidationError({"durum": "Geçersiz sipariş durumu."})
    if hedef_durum not in SIPARIS_GECISLERI.get(siparis.durum, frozenset()):
        raise ValidationError(
            {"durum": f"{siparis.durum} durumundan {hedef_durum} durumuna geçilemez."}
        )
    kaynak = siparis.durum
    siparis.durum = hedef_durum
    siparis.save(update_fields=["durum", "updated_at"])
    if hedef_durum in (
        SatinAlmaSiparisi.Durum.ONAYLANDI, SatinAlmaSiparisi.Durum.IPTAL,
    ):
        log.info(
            "event=siparis_durum %s -> %s (%s)", kaynak, hedef_durum, siparis.siparis_no,
            extra={"tenant_id": tenant_id, "operation": "satin-alma.durum",
                   "resource_id": siparis.pk},
        )
    return siparis


@transaction.atomic
def talepten_siparis_olustur(
    talep_id: int,
    *,
    tenant_id: int,
    tedarikci_id: int,
    para_birimi: str = "TRY",
    kur: Decimal | str = Decimal("1"),
    teslim_tarihi: date | None = None,
    aciklama: str = "",
) -> SatinAlmaSiparisi:
    """Onaylı talebi siparişe dönüştürür.

    Kurallar:
    - Yalnızca ONAYLANDI durumundaki talep dönüşebilir.
    - Aynı talep ikinci kez dönüşemez (aktif kaynak kontrolü).
    - Dönüşen her kalemin seçili teklifi olmalı; tüm teklifler verilen
      tedarikçiye ait olmalı; tenant/proje/malzeme uyumu doğrulanır.
    - birim_fiyat, dönüşüm anındaki teklif fiyatıdır (snapshot); teklif
      sonradan değişse bile sipariş kalemi değişmez.
    """
    from construction.models import Tedarikci

    talep = SatinAlmaTalebi.objects.select_for_update().get(pk=talep_id, tenant_id=tenant_id)
    if talep.durum != SatinAlmaTalebi.Durum.ONAYLANDI:
        raise ValidationError(
            {"talep": "Yalnızca onaylanmış talep siparişe dönüştürülebilir."}
        )
    if SatinAlmaSiparisi.objects.filter(kaynak_talep=talep, is_active=True).exists():
        raise ValidationError({"talep": "Bu talep zaten siparişe dönüştürülmüş."})
    try:
        tedarikci = Tedarikci.objects.get(pk=tedarikci_id, tenant_id=tenant_id)
    except Tedarikci.DoesNotExist:
        raise ValidationError({"tedarikci": "Seçilen tedarikçi bu firma kapsamına ait değil."})

    kalemler = list(
        SatinAlmaTalebiKalemi.objects.select_related("malzeme", "poz", "mahal", "secili_teklif")
        .filter(talep=talep, is_active=True)
        .order_by("id")
    )
    if not kalemler:
        raise ValidationError({"talep": "Talepte aktarılacak aktif kalem yok."})
    for kalem in kalemler:
        if kalem.secili_teklif_id is None:
            raise ValidationError(
                {"talep": f"Kalemde seçili teklif yok (kalem id={kalem.pk})."}
            )
        teklif = kalem.secili_teklif
        if teklif.tedarikci_id != tedarikci.pk:
            raise ValidationError(
                {"tedarikci": "Tüm kalem teklifleri aynı tedarikçiye ait olmalıdır."}
            )
        if teklif.tenant_id != tenant_id or teklif.proje_id != talep.proje_id:
            raise ValidationError({"talep": "Teklif tenant/proje uyumu sağlanamadı."})
        if teklif.malzeme_id != kalem.malzeme_id:
            raise ValidationError({"talep": "Teklif malzeme uyumu sağlanamadı."})

    siparis = SatinAlmaSiparisi.objects.create(
        tenant_id=tenant_id,
        siparis_no=belge_numarasi_uret(tenant_id, BelgeTipi.SIPARIS),
        tedarikci=tedarikci,
        proje_id=talep.proje_id,
        kaynak_talep=talep,
        para_birimi=para_birimi,
        kur=Decimal(str(kur)),
        teslim_tarihi=teslim_tarihi,
        aciklama=aciklama,
    )
    for kalem in kalemler:
        SatinAlmaSiparisiKalemi.objects.create(
            tenant_id=tenant_id,
            siparis=siparis,
            malzeme_id=kalem.malzeme_id,
            poz_id=kalem.poz_id,
            mahal_id=kalem.mahal_id,
            miktar=kalem.miktar,
            birim=kalem.birim or kalem.malzeme.birim,
            birim_fiyat=kalem.secili_teklif.birim_fiyat,
            kaynak_teklif=kalem.secili_teklif,
            aciklama=kalem.aciklama,
        )
    talep.durum = SatinAlmaTalebi.Durum.SIPARISE_DONUSTU
    talep.save(update_fields=["durum", "updated_at"])
    return siparis


# =============================================================================
# FAZ 3B — Mal Kabul + Stok Hareketi
# =============================================================================

MAL_KABUL_GECISLERI = {
    MalKabul.Durum.TASLAK: frozenset(
        {MalKabul.Durum.ONAYLANDI, MalKabul.Durum.IPTAL}
    ),
    MalKabul.Durum.ONAYLANDI: frozenset(
        {MalKabul.Durum.KISMI_TESLIM, MalKabul.Durum.TAMAMLANDI, MalKabul.Durum.IPTAL}
    ),
    MalKabul.Durum.KISMI_TESLIM: frozenset({MalKabul.Durum.TAMAMLANDI, MalKabul.Durum.IPTAL}),
    MalKabul.Durum.TAMAMLANDI: frozenset({MalKabul.Durum.IPTAL}),
    MalKabul.Durum.IPTAL: frozenset(),
}


@transaction.atomic
def mal_kabul_durum_gecis(
    mal_kabul_id: int, hedef_durum: str, *, tenant_id: int
) -> MalKabul:
    """Mal kabul durum geçişi (geçiş haritası + satır kilidi).

    ONAYLANDI geçişinde kabul kalemleri için GİRİŞ stok hareketleri üretilir
    ve sipariş durumu güncellenir; IPTAL geçişinde ters (ÇIKIŞ) hareket açılır.
    """
    mal_kabul = (
        MalKabul.objects.select_for_update()
        .select_related("siparis", "proje", "depo")
        .prefetch_related("kalemler__siparis_kalemi__malzeme")
        .get(pk=mal_kabul_id, tenant_id=tenant_id)
    )
    if hedef_durum not in MalKabul.Durum.values:
        raise ValidationError({"durum": "Geçersiz mal kabul durumu."})
    if hedef_durum not in MAL_KABUL_GECISLERI.get(mal_kabul.durum, frozenset()):
        raise ValidationError(
            {"durum": f"{mal_kabul.durum} durumundan {hedef_durum} durumuna geçilemez."}
        )
    kaynak = mal_kabul.durum
    mal_kabul.durum = hedef_durum
    mal_kabul.save(update_fields=["durum", "updated_at"])
    if hedef_durum == MalKabul.Durum.ONAYLANDI:
        _mal_kabul_onayla(mal_kabul, tenant_id)
    elif hedef_durum == MalKabul.Durum.IPTAL:
        _mal_kabul_iptal(mal_kabul, tenant_id)
    if hedef_durum in (MalKabul.Durum.ONAYLANDI, MalKabul.Durum.IPTAL):
        logging.getLogger("erp.purchasing").info(
            "event=malkabul_durum %s -> %s (%s)", kaynak, hedef_durum,
            mal_kabul.belge_no,
            extra={"tenant_id": tenant_id, "operation": "mal-kabul.durum",
                   "resource_id": mal_kabul.pk},
        )
    return mal_kabul


def _mal_kabul_onayla(mal_kabul: MalKabul, tenant_id: int) -> None:
    """Onayda her kabul kalemi için tek GİRİŞ stok hareketi üretir."""
    for kalem in mal_kabul.kalemler.filter(is_active=True):
        if StokHareketi.objects.filter(
            kaynak_belge_tipi="MalKabul",
            kaynak_belge_id=mal_kabul.pk,
            kaynak_belge_kalem_id=kalem.pk,
            is_active=True,
        ).exists():
            continue  # Zaten üretilmiş, atla (unique constraint ikinci güvence).
        StokHareketi.objects.create(
            tenant_id=tenant_id,
            depo=mal_kabul.depo,
            malzeme=kalem.malzeme,
            hareket_tipi=StokHareketi.HareketTipi.GIRIS,
            miktar=kalem.kabul_miktari,
            birim=kalem.birim,
            maliyet=kalem.birim_fiyat_snapshot,
            tarih=mal_kabul.kabul_tarihi,
            aciklama=f"Mal Kabul: {mal_kabul.belge_no} - {kalem.aciklama}",
            kaynak_belge_tipi="MalKabul",
            kaynak_belge_id=mal_kabul.pk,
            kaynak_belge_kalem_id=kalem.pk,
            proje=mal_kabul.proje,
            created_by=mal_kabul.created_by,
        )
    _siparis_durumu_guncelle(mal_kabul.siparis_id, tenant_id)
    # FAZ 4 — aynı transaction içinde alış faturası + cari + fiş.
    from finance.services.satin_alma_muhasebe import satin_alma_muhasebe_olustur

    satin_alma_muhasebe_olustur(mal_kabul.pk, tenant_id=tenant_id)


def _mal_kabul_iptal(mal_kabul: MalKabul, tenant_id: int) -> None:
    """İptalde üretilmiş GİRİŞ hareketlerine karşılık ÇIKIŞ hareketi açar."""
    giris_hareketleri = list(
        StokHareketi.objects.select_for_update().filter(
            kaynak_belge_tipi="MalKabul",
            kaynak_belge_id=mal_kabul.pk,
            hareket_tipi=StokHareketi.HareketTipi.GIRIS,
            is_active=True,
        )
    )
    for hareket in giris_hareketleri:
        if StokHareketi.objects.filter(
            kaynak_belge_tipi="MalKabul_Iptal",
            kaynak_belge_id=mal_kabul.pk,
            kaynak_belge_kalem_id=hareket.kaynak_belge_kalem_id,
            is_active=True,
        ).exists():
            continue
        StokHareketi.objects.create(
            tenant_id=tenant_id,
            depo=hareket.depo,
            malzeme=hareket.malzeme,
            hareket_tipi=StokHareketi.HareketTipi.CIKIS,
            miktar=hareket.miktar,
            birim=hareket.birim,
            maliyet=hareket.maliyet,
            tarih=date.today(),
            aciklama=f"Mal Kabul İptal: {mal_kabul.belge_no} (Orijinal: {hareket.pk})",
            kaynak_belge_tipi="MalKabul_Iptal",
            kaynak_belge_id=mal_kabul.pk,
            kaynak_belge_kalem_id=hareket.kaynak_belge_kalem_id,
            proje=hareket.proje,
            created_by=mal_kabul.updated_by or mal_kabul.created_by,
        )
    _siparis_durumu_guncelle(mal_kabul.siparis_id, tenant_id)
    # FAZ 4 — cari iptal + fiş reversal (aynı transaction).
    from finance.services.satin_alma_muhasebe import satin_alma_muhasebe_iptal

    satin_alma_muhasebe_iptal(mal_kabul.pk, tenant_id=tenant_id)


def _siparis_durumu_guncelle(siparis_id: int, tenant_id: int) -> None:
    """Sipariş durumunu kabul toplamlarına göre ilerletir (geri gitmez)."""
    siparis = (
        SatinAlmaSiparisi.objects.select_for_update()
        .filter(pk=siparis_id, tenant_id=tenant_id)
        .first()
    )
    if not siparis or siparis.durum in (
        SatinAlmaSiparisi.Durum.TAMAMLANDI,
        SatinAlmaSiparisi.Durum.IPTAL,
    ):
        return
    kalemler = list(
        SatinAlmaSiparisiKalemi.objects.filter(
            siparis=siparis, is_active=True
        ).select_related("malzeme")
    )
    if not kalemler:
        return
    tum_tamamlandi = True
    herhangi_bir_kismi = False
    for kalem in kalemler:
        toplam_kabul = (
            MalKabulKalemi.objects.filter(
                siparis_kalemi=kalem, is_active=True
            ).aggregate(toplam=models.Sum("kabul_miktari"))["toplam"]
            or Decimal("0")
        )
        if toplam_kabul >= kalem.miktar:
            continue
        elif toplam_kabul > 0:
            herhangi_bir_kismi = True
            tum_tamamlandi = False
        else:
            tum_tamamlandi = False
    if tum_tamamlandi and not herhangi_bir_kismi:
        yeni_durum = SatinAlmaSiparisi.Durum.TAMAMLANDI
    elif herhangi_bir_kismi:
        yeni_durum = SatinAlmaSiparisi.Durum.KISMI_TESLIM
    else:
        yeni_durum = SatinAlmaSiparisi.Durum.ONAYLANDI
    mevcut_sira = list(SatinAlmaSiparisi.Durum.values).index(siparis.durum)
    hedef_sira = list(SatinAlmaSiparisi.Durum.values).index(yeni_durum)
    if hedef_sira > mevcut_sira and yeni_durum in SIPARIS_GECISLERI.get(
        siparis.durum, frozenset()
    ):
        siparis.durum = yeni_durum
        siparis.save(update_fields=["durum", "updated_at"])


@transaction.atomic
def mal_kabul_olustur(
    *,
    tenant_id: int,
    siparis_id: int,
    depo_id: int,
    kabul_tarihi: date | None = None,
    aciklama: str = "",
    created_by_id: int,
    kalemler: list[dict],
) -> MalKabul:
    """Onaylı/kısmi teslim siparişten TASLAK mal kabul belgesi üretir.

    Kabul miktarı kalanı aşamaz; kalem başına kabul+red toplamı sipariş
    miktarını aşamaz. Muhasebe/cari/fatura üretilmez.
    """
    siparis = SatinAlmaSiparisi.objects.select_for_update().get(
        pk=siparis_id, tenant_id=tenant_id, is_active=True
    )
    if siparis.durum not in (
        SatinAlmaSiparisi.Durum.ONAYLANDI,
        SatinAlmaSiparisi.Durum.KISMI_TESLIM,
    ):
        raise ValidationError(
            {"siparis": "Sadece onaylanmış/kısmi teslim siparişlere mal kabul girilebilir."}
        )
    depo = Depo.objects.get(pk=depo_id, tenant_id=tenant_id, is_active=True)
    for k in kalemler:
        siparis_kalemi = SatinAlmaSiparisiKalemi.objects.select_for_update().get(
            pk=k["siparis_kalemi_id"], siparis=siparis, is_active=True
        )
        # Kalan hesabı kilitli satırlardan türetilir (paralel kabuller serileşir).
        kilitli_kabuller = list(
            MalKabulKalemi.objects.select_for_update().filter(
                siparis_kalemi=siparis_kalemi, is_active=True
            )
        )
        onceki_kabul = sum((s.kabul_miktari for s in kilitli_kabuller), Decimal("0"))
        kalan = siparis_kalemi.miktar - onceki_kabul
        yeni_kabul = Decimal(str(k["kabul_miktari"]))
        yeni_red = Decimal(str(k.get("red_miktari", 0)))
        if yeni_kabul < 0:
            raise ValidationError({"kabul_miktari": "Kabul miktarı negatif olamaz."})
        if yeni_red < 0:
            raise ValidationError({"red_miktari": "Red miktarı negatif olamaz."})
        if yeni_kabul == 0 and yeni_red == 0:
            raise ValidationError(
                {"kabul_miktari": "Kabul veya red miktarından en az biri pozitif olmalıdır."}
            )
        if yeni_kabul > kalan:
            raise ValidationError(
                {"kabul_miktari": f"Kabul miktarı ({yeni_kabul}) kalan miktarı ({kalan}) aşamaz."}
            )
        if yeni_kabul + yeni_red > siparis_kalemi.miktar:
            raise ValidationError(
                {"kabul_miktari": "Kabul + red miktarı sipariş miktarını aşamaz."}
            )
    mal_kabul = MalKabul.objects.create(
        tenant_id=tenant_id,
        siparis=siparis,
        proje=siparis.proje,
        depo=depo,
        belge_no=belge_numarasi_uret(tenant_id, BelgeTipi.MAL_KABUL),
        kabul_tarihi=kabul_tarihi or date.today(),
        durum=MalKabul.Durum.TASLAK,
        aciklama=aciklama,
        created_by_id=created_by_id,
    )
    for k in kalemler:
        siparis_kalemi = SatinAlmaSiparisiKalemi.objects.get(
            pk=k["siparis_kalemi_id"], siparis=siparis, is_active=True
        )
        MalKabulKalemi.objects.create(
            tenant_id=tenant_id,
            mal_kabul=mal_kabul,
            siparis_kalemi=siparis_kalemi,
            malzeme=siparis_kalemi.malzeme,
            siparis_miktari=siparis_kalemi.miktar,
            kabul_miktari=Decimal(str(k["kabul_miktari"])),
            red_miktari=Decimal(str(k.get("red_miktari", 0))),
            birim=siparis_kalemi.birim,
            birim_fiyat_snapshot=siparis_kalemi.birim_fiyat,
            aciklama=k.get("aciklama", ""),
        )
    return mal_kabul


# =============================================================================
# FAZ 3C — Stok Yönetimi / Tüketim (bakiye + transfer + tüketim + iade)
#
# Kurallar: yeni tablo yok (StokHareketi üzerinden); değerleme yok (maliyet
# snapshot); negatif stok yok; ters-hareket deseni; MalzemeHareketi ayrı kalır.
# =============================================================================


def _hareketleri_kilitle(tenant_id: int, depo_id: int, malzeme_id: int):
    """Bakiye-oku-then-yaz yarışını kapatmak için ilgili satırları kilitler.

    Hareket satırları (varsa) + depo ve malzeme kartları her zaman kilitlenir;
    böylece geçmişi boş (depo, malzeme) çiftinde de serileşme sağlanır.
    Kilit sırası sabittir (depo → malzeme → hareketler): deadlock önlenir.
    """
    from construction.models import Malzeme

    Depo.objects.select_for_update().get(pk=depo_id, tenant_id=tenant_id)
    Malzeme.objects.select_for_update().get(pk=malzeme_id, tenant_id=tenant_id)
    return list(
        StokHareketi.objects.select_for_update()
        .filter(tenant_id=tenant_id, depo_id=depo_id, malzeme_id=malzeme_id, is_active=True)
        .order_by("id")
    )


def stok_bakiye(*, tenant_id: int, depo_id: int, malzeme_id: int) -> Decimal:
    """Depo + malzeme bakiyesi: Σ GİRİŞ − Σ ÇIKIŞ (yalnızca aktif hareketler).

    Tüm yazımlar servislerden GİRİŞ/ÇIKIŞ tipiyle yapıldığından formül tamdır;
    değerleme yapılmaz, yalnızca miktar döner.
    """
    from django.db.models import Sum

    giris = (
        StokHareketi.objects.filter(
            tenant_id=tenant_id,
            depo_id=depo_id,
            malzeme_id=malzeme_id,
            hareket_tipi=StokHareketi.HareketTipi.GIRIS,
            is_active=True,
        ).aggregate(toplam=Sum("miktar"))["toplam"]
        or Decimal("0")
    )
    cikis = (
        StokHareketi.objects.filter(
            tenant_id=tenant_id,
            depo_id=depo_id,
            malzeme_id=malzeme_id,
            hareket_tipi=StokHareketi.HareketTipi.CIKIS,
            is_active=True,
        ).aggregate(toplam=Sum("miktar"))["toplam"]
        or Decimal("0")
    )
    return Decimal(giris) - Decimal(cikis)


def depo_bakiyeleri(*, tenant_id: int, depo_id: int) -> list[dict]:
    """Depodaki tüm malzemelerin bakiye özeti (stok durum ekranı için)."""
    from django.db.models import Sum

    satirlar = (
        StokHareketi.objects.filter(
            tenant_id=tenant_id, depo_id=depo_id, is_active=True
        )
        .values("malzeme_id")
        .annotate(
            giris=Sum("miktar", filter=models.Q(hareket_tipi=StokHareketi.HareketTipi.GIRIS)),
            cikis=Sum("miktar", filter=models.Q(hareket_tipi=StokHareketi.HareketTipi.CIKIS)),
        )
        .order_by("malzeme_id")
    )
    return [
        {
            "malzeme_id": s["malzeme_id"],
            "bakiye": str(Decimal(s["giris"] or 0) - Decimal(s["cikis"] or 0)),
        }
        for s in satirlar
    ]


@transaction.atomic
def stok_transfer(
    *,
    tenant_id: int,
    kaynak_depo_id: int,
    hedef_depo_id: int,
    malzeme_id: int,
    miktar: Decimal | str,
    aciklama: str = "",
    created_by_id: int,
) -> tuple[StokHareketi, StokHareketi]:
    """Depolar arası transfer: tek transaction'da ÇIKIŞ (kaynak) + GİRİŞ (hedef).

    Kaynak bakiye yetersizse reddedilir; biri başarısızsa ikisi de oluşmaz.
    """
    from construction.models import Malzeme

    miktar = Decimal(str(miktar))
    if miktar <= 0:
        raise ValidationError({"miktar": "Miktar 0'dan büyük olmalıdır."})
    if kaynak_depo_id == hedef_depo_id:
        raise ValidationError({"depo": "Kaynak ve hedef depo aynı olamaz."})
    try:
        kaynak = Depo.objects.get(pk=kaynak_depo_id, tenant_id=tenant_id, is_active=True)
        hedef = Depo.objects.get(pk=hedef_depo_id, tenant_id=tenant_id, is_active=True)
        malzeme = Malzeme.objects.get(pk=malzeme_id, tenant_id=tenant_id)
    except (Depo.DoesNotExist, Malzeme.DoesNotExist):
        raise ValidationError({"depo": "Seçilen kayıt bu firma kapsamına ait değil."})
    # Çapraz transfer deadlock'unu önlemek için depolar artan id sırasında kilitlenir.
    for _depo_id in sorted([kaynak.pk, hedef.pk]):
        Depo.objects.select_for_update().get(pk=_depo_id)
    _hareketleri_kilitle(tenant_id, kaynak.pk, malzeme.pk)
    bakiye = stok_bakiye(tenant_id=tenant_id, depo_id=kaynak.pk, malzeme_id=malzeme.pk)
    if bakiye < miktar:
        raise ValidationError(
            {"miktar": f"Yetersiz stok (bakiye: {bakiye}, istenen: {miktar})."}
        )
    cikis = StokHareketi.objects.create(
        tenant_id=tenant_id,
        depo=kaynak,
        malzeme=malzeme,
        hareket_tipi=StokHareketi.HareketTipi.CIKIS,
        miktar=miktar,
        birim=malzeme.birim,
        tarih=date.today(),
        aciklama=aciklama or f"Transfer → {hedef.kod}",
        kaynak_belge_tipi="Transfer",
        proje=None,
        created_by_id=created_by_id,
    )
    giris = StokHareketi.objects.create(
        tenant_id=tenant_id,
        depo=hedef,
        malzeme=malzeme,
        hareket_tipi=StokHareketi.HareketTipi.GIRIS,
        miktar=miktar,
        birim=malzeme.birim,
        tarih=date.today(),
        aciklama=aciklama or f"Transfer ← {kaynak.kod}",
        kaynak_belge_tipi="Transfer",
        proje=None,
        created_by_id=created_by_id,
    )
    return cikis, giris


@transaction.atomic
def stok_tuketim(
    *,
    tenant_id: int,
    depo_id: int,
    malzeme_id: int,
    miktar: Decimal | str,
    proje_id: int,
    mahal_id: int,
    aciklama: str = "",
    created_by_id: int,
) -> StokHareketi:
    """Projeye/mahale tüketim: proje+mahal zorunlu ÇIKIŞ hareketi."""
    from construction.models import Mahal, Malzeme, Proje

    miktar = Decimal(str(miktar))
    if miktar <= 0:
        raise ValidationError({"miktar": "Miktar 0'dan büyük olmalıdır."})
    try:
        depo = Depo.objects.get(pk=depo_id, tenant_id=tenant_id, is_active=True)
        malzeme = Malzeme.objects.get(pk=malzeme_id, tenant_id=tenant_id)
        proje = Proje.objects.get(pk=proje_id, tenant_id=tenant_id)
        mahal = Mahal.objects.get(pk=mahal_id, tenant_id=tenant_id, proje=proje)
    except (Depo.DoesNotExist, Malzeme.DoesNotExist, Proje.DoesNotExist, Mahal.DoesNotExist):
        raise ValidationError({"depo": "Seçilen kayıt bu firma kapsamına ait değil."})
    _hareketleri_kilitle(tenant_id, depo.pk, malzeme.pk)
    bakiye = stok_bakiye(tenant_id=tenant_id, depo_id=depo.pk, malzeme_id=malzeme.pk)
    if bakiye < miktar:
        raise ValidationError(
            {"miktar": f"Yetersiz stok (bakiye: {bakiye}, istenen: {miktar})."}
        )
    return StokHareketi.objects.create(
        tenant_id=tenant_id,
        depo=depo,
        malzeme=malzeme,
        hareket_tipi=StokHareketi.HareketTipi.CIKIS,
        miktar=miktar,
        birim=malzeme.birim,
        tarih=date.today(),
        aciklama=aciklama or f"Tüketim: {proje.proje_kodu}/{mahal.kod}",
        kaynak_belge_tipi="Tuketim",
        proje=proje,
        mahal=mahal,
        created_by_id=created_by_id,
    )


@transaction.atomic
def stok_iade(
    *,
    tenant_id: int,
    mal_kabul_kalemi_id: int,
    miktar: Decimal | str,
    aciklama: str = "",
    created_by_id: int,
) -> StokHareketi:
    """Tedarikçiye iade: kabul kalemine bağlı ÇIKIŞ hareketi.

    Kümülatif iade kabul miktarını aşamaz; stok yetersizse reddedilir.
    """
    miktar = Decimal(str(miktar))
    if miktar <= 0:
        raise ValidationError({"miktar": "Miktar 0'dan büyük olmalıdır."})
    try:
        kalem = MalKabulKalemi.objects.select_for_update().select_related(
            "mal_kabul__depo", "malzeme", "siparis_kalemi"
        ).get(pk=mal_kabul_kalemi_id, tenant_id=tenant_id, is_active=True)
    except MalKabulKalemi.DoesNotExist:
        raise ValidationError({"kalem": "Kabul kalemi bu firma kapsamına ait değil."})
    kabul = kalem.mal_kabul
    # Kümülatif toplam kilitli satırlardan türetilir (paralel iadeler serileşir).
    kilitli_iadeler = list(
        StokHareketi.objects.select_for_update().filter(
            kaynak_belge_tipi="Iade",
            kaynak_belge_id=kabul.pk,
            kaynak_belge_kalem_id=kalem.pk,
            is_active=True,
        )
    )
    onceki_iade = sum((s.miktar for s in kilitli_iadeler), Decimal("0"))
    if onceki_iade + miktar > kalem.kabul_miktari:
        raise ValidationError(
            {"miktar": "Kümülatif iade, kabul miktarını aşamaz."}
        )
    _hareketleri_kilitle(tenant_id, kabul.depo_id, kalem.malzeme_id)
    bakiye = stok_bakiye(
        tenant_id=tenant_id, depo_id=kabul.depo_id, malzeme_id=kalem.malzeme_id
    )
    if bakiye < miktar:
        raise ValidationError(
            {"miktar": f"Yetersiz stok (bakiye: {bakiye}, istenen: {miktar})."}
        )
    hareket = StokHareketi.objects.create(
        tenant_id=tenant_id,
        depo_id=kabul.depo_id,
        malzeme=kalem.malzeme,
        hareket_tipi=StokHareketi.HareketTipi.CIKIS,
        miktar=miktar,
        birim=kalem.birim,
        maliyet=kalem.birim_fiyat_snapshot,
        tarih=date.today(),
        aciklama=aciklama or f"İade: {kabul.belge_no}",
        kaynak_belge_tipi="Iade",
        kaynak_belge_id=kabul.pk,
        kaynak_belge_kalem_id=kalem.pk,
        proje=kabul.proje,
        created_by_id=created_by_id,
    )
    logging.getLogger("erp.purchasing").info(
        "event=iade miktar=%s (%s)", miktar, kabul.belge_no,
        extra={"tenant_id": tenant_id, "operation": "stok.iade",
               "resource_id": hareket.pk},
    )
    return hareket



