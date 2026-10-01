"""Merkezi hatırlatma üretimi ve günlük sorguları."""

from __future__ import annotations

from datetime import date, timedelta

from django.utils import timezone

from ..models import (
    EKB,
    Hakedis,
    Hatirlatma,
    HatirlatmaKurali,
    LeaseAssistance,
    Proje,
    RiskStructure,
    TaseronSozlesi,
    TedarikciTeklifi,
)

VARSAYILAN_KURALLAR = {
    "kira_yardimi": [("tahliye_son_tarihi", 60), ("tahliye_son_tarihi", 30), ("tahliye_son_tarihi", 7)],
    "ekb": [("gecerlilik_tarihi", 90), ("gecerlilik_tarihi", 60), ("gecerlilik_tarihi", 30), ("gecerlilik_tarihi", 15), ("gecerlilik_tarihi", 7)],
    "proje": [("sozlesme_bitis_tarihi", 30)],
    "taseron": [("teminat_bitis_tarihi", 30)],
}


def varsayilan_kurallari_olustur(tenant_id: int) -> None:
    for modul, kurallar in VARSAYILAN_KURALLAR.items():
        for tetikleyici, gun in kurallar:
            HatirlatmaKurali.objects.get_or_create(
                tenant_id=tenant_id,
                ilgili_modul=modul,
                tetikleyici=tetikleyici,
                once_gun_sayisi=gun,
                defaults={"seviye": Hatirlatma.Seviye.UYARI, "aktif_mi": True},
            )


def _kayitlar(tenant_id: int):
    return (
        ("kira_yardimi", LeaseAssistance.objects.filter(tenant_id=tenant_id), "tahliye_son_tarihi", "Tahliye son tarihi"),
        ("ekb", EKB.objects.filter(tenant_id=tenant_id, is_active=True), "gecerlilik_tarihi", "EKB geçerlilik tarihi"),
        ("proje", Proje.objects.filter(tenant_id=tenant_id, is_active=True), "sozlesme_bitis_tarihi", "Proje sözleşme bitişi"),
        ("taseron", TaseronSozlesi.objects.filter(tenant_id=tenant_id), "teminat_bitis_tarihi", "Taşeron teminat bitişi"),
        ("hakedis", Hakedis.objects.filter(tenant_id=tenant_id), "odeme_vadesi", "Hakediş ödeme vadesi"),
        ("tedarikci_teklifi", TedarikciTeklifi.objects.filter(tenant_id=tenant_id, is_active=True), "gecerlilik_tarihi", "Teklif geçerlilik tarihi"),
        ("riskli_yapi", RiskStructure.objects.filter(tenant_id=tenant_id), "sonraki_adim_tarihi", "Riskli yapı sonraki adımı"),
    )


def hatirlatmalari_uret(tenant_id: int, bugun: date | None = None) -> int:
    """Aktif kurallara göre eksik bekleyen hatırlatmaları üretir."""
    bugun = bugun or timezone.localdate()
    varsayilan_kurallari_olustur(tenant_id)
    kurallar = HatirlatmaKurali.objects.filter(tenant_id=tenant_id, aktif_mi=True)
    kurallar_by_module = {}
    for kural in kurallar:
        kurallar_by_module.setdefault((kural.ilgili_modul, kural.tetikleyici), []).append(kural)

    uretilen = 0
    for modul, kayitlar, alan, aciklama in _kayitlar(tenant_id):
        for kayit in kayitlar:
            tarih = getattr(kayit, alan, None)
            if not tarih:
                continue
            for kural in kurallar_by_module.get((modul, alan), []):
                hedef = tarih - timedelta(days=kural.once_gun_sayisi)
                if hedef != bugun:
                    continue
                defaults = {
                    "aciklama": f"{aciklama}: {tarih.isoformat()}",
                    "ilgili_kayit_tipi": kayit.__class__.__name__,
                    "seviye": kural.seviye,
                    "durum": Hatirlatma.Durum.BEKLIYOR,
                }
                _, created = Hatirlatma.objects.get_or_create(
                    tenant_id=tenant_id,
                    baslik=f"{modul.replace('_', ' ').title()} — {kural.once_gun_sayisi} gün kaldı",
                    ilgili_modul=modul,
                    ilgili_kayit_id=kayit.pk,
                    hatirlatma_tarihi=bugun,
                    defaults=defaults,
                )
                uretilen += int(created)
    return uretilen


def gunluk_getir(tenant_id: int, bugun: date | None = None):
    bugun = bugun or timezone.localdate()
    hatirlatmalari_uret(tenant_id, bugun)
    return Hatirlatma.objects.filter(
        tenant_id=tenant_id,
        hatirlatma_tarihi=bugun,
    ).exclude(durum__in=[Hatirlatma.Durum.TAMAMLANDI, Hatirlatma.Durum.IPTAL])
