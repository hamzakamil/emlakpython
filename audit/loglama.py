"""FAZ 6F-2 — audit snapshot/diff yardımcıları (best-effort, hassas-verisiz)."""

from __future__ import annotations

import json
from decimal import Decimal

# Asla audit'e yazılmayacak alan adları (alt dize eşleşmesi, küçük harf).
HASSAS_ALANLAR = (
    "password", "passwd", "secret", "token", "api_key", "apikey",
    "tckn", "tc_kimlik", "vkn", "vergi_no", "iban", "telefon", "gsm",
)


def hassas_mi(alan: str) -> bool:
    ad = (alan or "").lower()
    return any(iz in ad for iz in HASSAS_ALANLAR)


def guvenli_snapshot(nesne) -> dict:
    """Nesnenin sorgusuz (ilişkisiz) alan görüntüsü; hassas alanlar atılır."""
    goruntu: dict = {}
    try:
        alanlar = nesne._meta.fields
    except AttributeError:
        return goruntu
    for alan in alanlar:
        if not getattr(alan, "concrete", False):
            continue
        ad = alan.name
        if hassas_mi(ad):
            continue
        try:
            if getattr(alan, "is_relation", False):
                deger = getattr(nesne, alan.attname, None)
            else:
                deger = getattr(nesne, ad, None)
        except Exception:  # noqa: BLE001 — tek alan okunamazsa atla
            continue
        goruntu[ad] = _jsonlanabilir(deger)
    return goruntu


def _jsonlanabilir(deger):
    if isinstance(deger, (str, int, float, bool)) or deger is None:
        return deger
    if isinstance(deger, Decimal):
        return str(deger)
    try:
        return str(deger)
    except Exception:  # noqa: BLE001
        return "?"


def fark_hesapla(onceki: dict, sonraki: dict) -> dict:
    """Yalnızca değişen alanlar: {alan: {old, new}}."""
    fark: dict = {}
    for alan in sorted(set(onceki) | set(sonraki)):
        eski = onceki.get(alan)
        yeni = sonraki.get(alan)
        if eski != yeni:
            fark[alan] = {"old": eski, "new": yeni}
    return fark


def reddedilen_islemi_kaydet(
    request, model_etiketi: str, nesne_id, denenen: dict, neden: str = ""
) -> None:
    """Snapshot/validasyon reddini best-effort auditler (kullanıcılı bağlam)."""
    import logging

    try:
        from .models import AuditLog

        kullanici = getattr(request, "user", None)
        if not kullanici or not getattr(kullanici, "is_authenticated", False):
            return
        temiz = {
            alan: _jsonlanabilir(deger)
            for alan, deger in (denenen or {}).items()
            if not hassas_mi(str(alan))
        }
        AuditLog.objects.create(
            kullanıcı=kullanici,
            tenant_id=getattr(kullanici, "tenant_id", None),
            islem_türü=AuditLog.IslemTürü.REJECTED,
            içerik_türü=None,
            nesne_id=nesne_id if isinstance(nesne_id, int) else None,
            eski_değer=json.dumps({}, ensure_ascii=False),
            yeni_değer=json.dumps(
                {"model": model_etiketi, "denenen": temiz, "sonuc": "REDDI"},
                ensure_ascii=False,
            ),
            sebep=(neden or "Snapshot/validasyon reddi")[:255],
            ip_adresi=_istemci_ip(request),
            oturum_kişi=(request.META.get("HTTP_USER_AGENT", "") or "")[:100],
            correlation_id=getattr(request, "correlation_id", None),
        )
    except Exception:  # noqa: BLE001 — audit best-effort; asıl işlem etkilenmez
        logging.getLogger("erp.audit").exception("reddedilen işlem auditlenemedi")


def _istemci_ip(request) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def dumps(veri: dict) -> str:
    return json.dumps(veri or {}, ensure_ascii=False)
