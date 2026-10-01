from __future__ import annotations

from datetime import date, timedelta

from django.utils import timezone

from construction.models import EKB, LeaseAssistance, Proje, TaseronSozlesi, TedarikciTeklifi
from finance.models import CekSenet, Fatura

from ..models import Hatirlatma, HatirlatmaKurali

KURAL_SEED = (
    ("finance", "Fatura", "vade_tarihi", (3,), "uyari", "Fatura vadesine {gun} gün kaldı"),
    ("finance", "CekSenet", "vade_tarihi", (3,), "uyari", "Çek/Senet vadesine {gun} gün kaldı"),
    ("construction", "EKB", "gecerlilik_tarihi", (90, 60, 30, 15, 7), "kritik", "EKB geçerliliğine {gun} gün kaldı"),
    ("construction", "LeaseAssistance", "bitis_tarihi", (60, 30, 7), "kritik", "Kira desteği bitişine {gun} gün kaldı"),
    ("construction", "TaseronSozlesi", "tarih_bitis", (15,), "uyari", "Taşeron sözleşmesi bitişine {gun} gün kaldı"),
    ("construction", "Proje", "sozlesme_bitis_tarihi", (30,), "uyari", "Proje sözleşmesi bitişine {gun} gün kaldı"),
    ("construction", "TedarikciTeklifi", "gecerlilik_tarihi", (3,), "bilgi", "Tedarikçi teklifi geçerliliğine {gun} gün kaldı"),
)

KAYNAKLAR = {
    ("finance", "Fatura"): (Fatura, "vade_tarihi"),
    ("finance", "CekSenet"): (CekSenet, "vade_tarihi"),
    ("construction", "EKB"): (EKB, "gecerlilik_tarihi"),
    ("construction", "LeaseAssistance"): (LeaseAssistance, "bitis_tarihi"),
    ("construction", "TaseronSozlesi"): (TaseronSozlesi, "tarih_bitis"),
    ("construction", "Proje"): (Proje, "sozlesme_bitis_tarihi"),
    ("construction", "TedarikciTeklifi"): (TedarikciTeklifi, "gecerlilik_tarihi"),
}


def kurallari_seed_et(tenant_id: int) -> None:
    for app, model, alan, gunler, seviye, sablon in KURAL_SEED:
        for gun in gunler:
            HatirlatmaKurali.objects.get_or_create(
                tenant_id=tenant_id,
                ilgili_app=app,
                ilgili_model=model,
                tetikleyici_alan=alan,
                once_gun=gun,
                defaults={
                    "seviye": seviye,
                    "baslik_sablonu": sablon,
                    "aktif_mi": True,
                    "created_at": timezone.now(),
                    "updated_at": timezone.now(),
                },
            )


def hatirlatmalari_uret(tenant_id: int, bugun: date | None = None) -> int:
    bugun = bugun or timezone.localdate()
    kurallari_seed_et(tenant_id)
    uretilen = 0
    kurallar = HatirlatmaKurali.objects.filter(tenant_id=tenant_id, aktif_mi=True)
    for kural in kurallar:
        kaynak = KAYNAKLAR.get((kural.ilgili_app, kural.ilgili_model))
        if not kaynak:
            continue
        model, alan = kaynak
        for kayit in model.objects.filter(tenant_id=tenant_id):
            tarih = getattr(kayit, alan, None)
            if not tarih or tarih - timedelta(days=kural.once_gun) != bugun:
                continue
            baslik = (kural.baslik_sablonu or f"{kural.ilgili_model} hatırlatması").format(gun=kural.once_gun)
            _, created = Hatirlatma.objects.get_or_create(
                tenant_id=tenant_id,
                ilgili_app=kural.ilgili_app,
                ilgili_model=kural.ilgili_model,
                ilgili_kayit_id=kayit.pk,
                hatirlatma_tarihi=bugun,
                defaults={
                    "baslik": baslik,
                    "aciklama": f"{alan}: {tarih.isoformat()}",
                    "seviye": kural.seviye,
                    "durum": "bekliyor",
                    "tekrarlama": "yok",
                    "tekrarlama_gun": 0,
                    "created_at": timezone.now(),
                    "updated_at": timezone.now(),
                },
            )
            uretilen += int(created)
    return uretilen


def gunluk_getir(kullanici, bugun: date | None = None):
    bugun = bugun or timezone.localdate()
    tenant_id = getattr(kullanici, "tenant_id", None)
    if not tenant_id:
        return Hatirlatma.objects.none()
    hatirlatmalari_uret(tenant_id, bugun)
    kullanici_id = getattr(kullanici, "pk", None)
    return Hatirlatma.objects.filter(
        tenant_id=tenant_id,
        hatirlatma_tarihi=bugun,
        durum="bekliyor",
    ).filter(
        sorumlu_kullanici_id__isnull=True,
    ) | Hatirlatma.objects.filter(
        tenant_id=tenant_id,
        hatirlatma_tarihi=bugun,
        durum="bekliyor",
        sorumlu_kullanici_id=kullanici_id,
    )
