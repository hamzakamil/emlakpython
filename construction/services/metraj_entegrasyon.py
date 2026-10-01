"""FAZ 5 — Metraj → maliyet/plan entegrasyonları (idempotent, deterministik).

METRAJ → POZ → ETKİN FİYAT → YAKLAŞIK MALİYET zinciri ile
METRAJ → gerçekleşen miktar → PozPlan → AV/S-eğrisi zinciri buradan kurulur.
Fiyat snapshot mantığı değişmez (kayıt anında snapshot, sonradan korunur).
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import (
    IFCQuantityDraft,
    Metraj,
    Poz,
    PozPlan,
    YaklasikMaliyet,
    YaklasikMaliyetSatiri,
)
from .yaklasik_maliyet import hesapla


def _ayni_kapsam(metraj: Metraj, tenant_id: int) -> None:
    if metraj.tenant_id != tenant_id:
        raise ValidationError({"metraj": "Metraj bu firma kapsamına ait değil."})


@transaction.atomic
def metrajdan_maliyet_satiri(
    yaklasik_maliyet: YaklasikMaliyet,
    metraj: Metraj,
    poz: Poz,
    mahal=None,
) -> tuple[YaklasikMaliyetSatiri, bool]:
    """Metrajdan maliyet satırı üretir; aynı metraj tekrar işlenemez.

    Mevcut (ym, metraj) satırı varsa miktarı metraj sonucuna eşitler ve
    toplamları yeniler; yoksa snapshot'lı yeni satır açar.
    """
    tenant_id = yaklasik_maliyet.tenant_id
    _ayni_kapsam(metraj, tenant_id)
    if poz.tenant_id != tenant_id:
        raise ValidationError({"poz": "Poz bu firma kapsamına ait değil."})
    if mahal is not None and (
        mahal.tenant_id != tenant_id or mahal.proje_id != yaklasik_maliyet.proje_id
    ):
        raise ValidationError({"mahal": "Mahal bu proje kapsamına ait değil."})
    if metraj.sonuc <= 0:
        raise ValidationError({"metraj": "Metraj sonucu pozitif olmalıdır."})
    satir = YaklasikMaliyetSatiri.objects.filter(
        tenant_id=tenant_id, yaklasik_maliyet=yaklasik_maliyet, metraj=metraj
    ).first()
    if satir is not None:
        satir.miktar = metraj.sonuc
        satir.poz = poz
        satir.mahal = mahal
        satir.save()
        hesapla(yaklasik_maliyet)
        return satir, False
    satir = YaklasikMaliyetSatiri.objects.create(
        tenant_id=tenant_id,
        yaklasik_maliyet=yaklasik_maliyet,
        poz=poz,
        mahal=mahal,
        miktar=metraj.sonuc,
        metraj=metraj,
        aciklama=f"Metraj: {metraj.ad}",
    )
    hesapla(yaklasik_maliyet)
    return satir, True


@transaction.atomic
def metraj_satirlarini_yenile(metraj: Metraj) -> int:
    """Metraja bağlı tüm maliyet satırlarının miktarını sonuca eşitler."""
    sayi = 0
    for satir in YaklasikMaliyetSatiri.objects.filter(
        tenant_id=metraj.tenant_id, metraj=metraj
    ).select_related("yaklasik_maliyet"):
        satir.miktar = metraj.sonuc
        satir.save()
        hesapla(satir.yaklasik_maliyet)
        sayi += 1
    return sayi


@transaction.atomic
def metrajdan_gercek_miktar_ata(poz_plan: PozPlan, metraj: Metraj) -> PozPlan:
    """PozPlan gerçekleşen miktarını bağlı metraj sonucuna eşitler.

    Bağlantı kullanıcı tarafından kurulur (otomatik tetik yok); aynı değerin
    tekrar yazılması no-op'tur. S-eğrisi/AV hesabı değişmez (gercek_miktar okur).
    """
    _ayni_kapsam(metraj, poz_plan.tenant_id)
    poz_plan.metraj = metraj
    poz_plan.gercek_miktar = metraj.sonuc
    poz_plan.save()
    return poz_plan


@transaction.atomic
def ifc_drafttan_metraj_uret(draft: IFCQuantityDraft) -> tuple[Metraj, bool]:
    """Eşleşmiş IFC taslağından deterministik adlı Metraj üretir.

    Aynı taslak tekrar işlenirse mevcut kayıt döner (duplicate yok).
    Eşleşmemiş/hatalı taslaklar reddedilir (sessiz kayıt yok).
    """
    if draft.mapping_status != IFCQuantityDraft.MappingStatus.MAPPED or draft.poz_id is None:
        raise ValidationError(
            {"draft": "Yalnızca eşleşmiş taslaklar metraja dönüştürülebilir."}
        )
    if draft.quantity <= 0:
        raise ValidationError({"draft": "Taslak miktarı pozitif olmalıdır."})
    ad = f"IFC-{draft.job_id}-{draft.source_name}"
    metraj, olustu = Metraj.objects.update_or_create(
        tenant_id=draft.tenant_id,
        ad=ad,
        defaults={
            "metraj_tipi": "ifc",
            "ifade": str(draft.quantity),
            "sonuc": draft.quantity,
            "birim": draft.unit,
            "aciklama": f"IFC içe aktarımı #{draft.job_id} ({draft.source_name})",
            "is_active": True,
        },
    )
    return metraj, olustu
