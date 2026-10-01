"""Mahal geometrisinden metraj ve yaklaşık maliyet üretimi.

Mahal modelinde uzunluk/genişlik alanları olmadığı için ölçüler servise
verilebilir. Ölçü verilmezse ``alan`` üzerinden kare mahal varsayımı yapılır;
bu, mevcut şemayı değiştirmeden güvenli ve deterministik bir geri dönüş sağlar.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction

from ..models import Mahal, MahalElemani, Metraj, Poz, YaklasikMaliyet, YaklasikMaliyetSatiri
from .yaklasik_maliyet import hesapla

M3 = Decimal("0.001")


def _d(value, default="0") -> Decimal:
    try:
        return Decimal(str(value if value is not None else default).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Ölçüler sayısal olmalıdır.") from exc


def _olcu(mahal, olculer=None, **kwargs):
    values = dict(olculer or {})
    values.update(kwargs)
    length = _d(values.get("uzunluk", values.get("boy")))
    width = _d(values.get("genislik", values.get("en")))
    height = _d(values.get("yukseklik", values.get("duvar_yuksekligi")), "2.80")
    if not length or not width:
        area = _d(values.get("alan", mahal.alan))
        if area <= 0:
            raise ValueError("Mahal için uzunluk/genişlik veya pozitif alan gereklidir.")
        side = area.sqrt()
        length = width = side
    if min(length, width, height) <= 0:
        raise ValueError("Mahal ölçüleri pozitif olmalıdır.")
    return length, width, height


def _kategori(eleman_tipi: str) -> str:
    value = (eleman_tipi or "").lower()
    if "kapı" in value or "kapi" in value:
        return "kapi"
    if "pencere" in value:
        return "pencere"
    if "doğrama" in value or "dograma" in value:
        return "dograma"
    return ""


def _kapi_genisligi(eleman: MahalElemani) -> Decimal:
    """Only subtract an explicitly supplied width; ``miktar`` is an adet."""
    text = eleman.aciklama or ""
    match = re.search(r"(?:geni[sş]lik|width)\s*[:=]\s*([0-9]+(?:[.,][0-9]+)?)", text, re.I)
    return _d(match.group(1)) * _d(eleman.miktar) if match else Decimal("0")


@transaction.atomic
def mahal_metraj_uret(mahal: Mahal, olculer=None, **kwargs):
    """Generate/update the six standard quantity snapshots for ``mahal``.

    Returns a dictionary containing Decimal values and the persisted Metraj rows.
    Existing rows are updated rather than duplicated (tenant + deterministic ad).
    """
    if not isinstance(mahal, Mahal):
        mahal = Mahal.objects.select_related("proje").get(pk=mahal)
    length, width, height = _olcu(mahal, olculer, **kwargs)
    perimeter = Decimal("2") * (length + width)
    elements = list(mahal.elemanlar.filter(tenant_id=mahal.tenant_id, is_active=True))
    counts = {"kapi": Decimal("0"), "pencere": Decimal("0"), "dograma": Decimal("0")}
    door_width = Decimal("0")
    for element in elements:
        category = _kategori(element.eleman_tipi)
        if category:
            counts[category] += _d(element.miktar)
        if category == "kapi":
            door_width += _kapi_genisligi(element)
    values = {
        "doseme": (length * width).quantize(M3),
        "tavan": (length * width).quantize(M3),
        "duvar": (perimeter * height).quantize(M3),
        "supurgelik": max(Decimal("0"), perimeter - door_width).quantize(M3),
        **{key: value.quantize(Decimal("0.01")) for key, value in counts.items()},
    }
    rows = []
    prefix = f"{mahal.proje.proje_kodu}-{mahal.kod}"
    labels = {
        "doseme": ("Döşeme alanı", "m2"), "tavan": ("Tavan alanı", "m2"),
        "duvar": ("Duvar alanı", "m2"), "supurgelik": ("Süpürgelik", "m"),
        "kapi": ("Kapı", "adet"), "pencere": ("Pencere", "adet"),
        "dograma": ("Doğrama", "adet"),
    }
    for key, value in values.items():
        label, unit = labels[key]
        row, _ = Metraj.objects.update_or_create(
            tenant_id=mahal.tenant_id, ad=f"{prefix} - {label}",
            defaults={"metraj_tipi": f"mahal_{key}", "ifade": str(value),
                      "sonuc": value, "birim": unit,
                      "aciklama": f"Mahal {mahal.pk} ({mahal.kod})", "is_active": True},
        )
        rows.append(row)
    aliases = {
        "doseme_alan_m2": values["doseme"], "tavan_alan_m2": values["tavan"],
        "duvar_alan_m2": values["duvar"], "supurgelik_m": values["supurgelik"],
        "kapi_adet": values["kapi"], "pencere_adet": values["pencere"],
        "dograma_adet": values["dograma"],
    }
    return {"mahal": mahal, "olculer": {"uzunluk": length, "genislik": width, "yukseklik": height},
            "metrajlar": values, "kayitlar": rows, **aliases}


@transaction.atomic
def mahal_elemanlarindan_yaklasik_maliyet_uret(yaklasik_maliyet, mahal=None,
                                                poz_eslestirme=None, olculer=None, **kwargs):
    """Create idempotent cost lines from generated mahal quantities.

    ``poz_eslestirme`` is a mapping of quantity key (or element type) to Poz
    instance/id. Entries without a mapping are intentionally skipped.
    """
    if not isinstance(yaklasik_maliyet, YaklasikMaliyet):
        yaklasik_maliyet = YaklasikMaliyet.objects.get(pk=yaklasik_maliyet)
    if yaklasik_maliyet.tenant_id != yaklasik_maliyet.proje.tenant_id:
        raise ValueError("Yaklaşık maliyet tenant bilgisi tutarsız.")
    if mahal is None:
        mahaller = Mahal.objects.filter(tenant_id=yaklasik_maliyet.tenant_id,
                                        proje_id=yaklasik_maliyet.proje_id, is_active=True)
    else:
        mahaller = [mahal if isinstance(mahal, Mahal) else Mahal.objects.get(pk=mahal)]
    mapping = poz_eslestirme or {}
    created = []
    for item in mahaller:
        if item.tenant_id != yaklasik_maliyet.tenant_id or item.proje_id != yaklasik_maliyet.proje_id:
            raise ValueError("Mahal yaklaşık maliyetin projesine ait değil.")
        result = mahal_metraj_uret(item, olculer, **kwargs)
        for key, quantity in result["metrajlar"].items():
            poz_ref = mapping.get(key)
            if not poz_ref or quantity <= 0:
                continue
            poz = poz_ref if isinstance(poz_ref, Poz) else Poz.objects.get(
                pk=poz_ref, tenant_id=yaklasik_maliyet.tenant_id)
            if poz.tenant_id != yaklasik_maliyet.tenant_id:
                raise ValueError("Poz başka bir firmaya ait.")
            line = YaklasikMaliyetSatiri.objects.filter(
                tenant_id=yaklasik_maliyet.tenant_id, yaklasik_maliyet=yaklasik_maliyet,
                mahal=item, poz=poz).first()
            if line:
                line.miktar = quantity
                line.save(update_fields=["miktar", "toplam_tutar", "updated_at"])
            else:
                line = YaklasikMaliyetSatiri.objects.create(
                    tenant_id=yaklasik_maliyet.tenant_id, yaklasik_maliyet=yaklasik_maliyet,
                    mahal=item, poz=poz, miktar=quantity, aciklama=f"{item.kod} / {key}",
                )
            created.append(line)
    hesapla(yaklasik_maliyet)
    return yaklasik_maliyet, created
