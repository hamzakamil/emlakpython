"""Güvenli metraj hesapları.

Bu modül ``eval`` kullanmaz; yalnızca sayılar ve dört temel işlemden oluşan
ifadeleri Decimal ile değerlendirir.
"""

from __future__ import annotations

import ast
import re
from decimal import Decimal, InvalidOperation, localcontext


class MetrajHesapHatasi(ValueError):
    """Geçersiz veya hesaplanamayan metraj girdisi."""


def ifade_hesapla(ifade: str | int | Decimal) -> Decimal:
    if isinstance(ifade, (int, Decimal)):
        return Decimal(str(ifade))
    if not isinstance(ifade, str) or not ifade.strip():
        raise MetrajHesapHatasi("Hesap ifadesi boş olamaz.")
    ifade = ifade.replace(",", ".")
    try:
        node = ast.parse(ifade, mode="eval").body
    except (SyntaxError, ValueError) as exc:
        raise MetrajHesapHatasi("Geçersiz hesap ifadesi.") from exc

    def evaluate(item: ast.AST) -> Decimal:
        if isinstance(item, ast.Constant) and isinstance(item.value, (int, float)):
            # float yalnızca kaynak metni AST'den geldiği için Decimal'e çevrilir.
            return Decimal(str(item.value))
        if isinstance(item, ast.UnaryOp) and isinstance(item.op, (ast.UAdd, ast.USub)):
            value = evaluate(item.operand)
            return value if isinstance(item.op, ast.UAdd) else -value
        if isinstance(item, ast.BinOp) and isinstance(item.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = evaluate(item.left), evaluate(item.right)
            if isinstance(item.op, ast.Add):
                return left + right
            if isinstance(item.op, ast.Sub):
                return left - right
            if isinstance(item.op, ast.Mult):
                return left * right
            if right == 0:
                raise MetrajHesapHatasi("Sıfıra bölme yapılamaz.")
            return left / right
        raise MetrajHesapHatasi("Yalnızca +, -, *, / ve parantez kullanılabilir.")

    try:
        with localcontext() as context:
            context.prec = 28
            result = evaluate(node)
    except (InvalidOperation, ZeroDivisionError, ValueError) as exc:
        if isinstance(exc, MetrajHesapHatasi):
            raise
        raise MetrajHesapHatasi("Hesap ifadesi değerlendirilemedi.") from exc
    if result < 0:
        raise MetrajHesapHatasi("Metraj sonucu negatif olamaz.")
    return result


_DEMIR_KG_METRE = {
    6: Decimal("0.222"), 8: Decimal("0.395"), 10: Decimal("0.617"),
    12: Decimal("0.888"), 14: Decimal("1.210"), 16: Decimal("1.580"),
    18: Decimal("2.000"), 20: Decimal("2.470"), 22: Decimal("2.980"),
    25: Decimal("3.850"), 28: Decimal("4.830"), 32: Decimal("6.310"),
}


def demir_metraji(cap: int | str, adet: int | str | Decimal = 1,
                  uzunluk: int | str | Decimal | None = None,
                  boy: int | str | Decimal | None = None) -> Decimal:
    """Donatı ağırlığını kg olarak hesaplar (kg/m tablosu, ``Ø12 × 10 × 12``)."""
    match = re.search(r"\d+(?:[.,]\d+)?", str(cap).replace("Ø", ""))
    if not match:
        raise MetrajHesapHatasi("Demir çapı geçersiz.")
    cap_i = int(Decimal(match.group().replace(",", ".")))
    try:
        kg_m = _DEMIR_KG_METRE[cap_i]
        adet_d = Decimal(str(adet))
        length_d = Decimal(str(uzunluk if uzunluk is not None else boy))
    except (KeyError, InvalidOperation, TypeError) as exc:
        raise MetrajHesapHatasi("Demir çapı veya uzunluğu geçersiz.") from exc
    if adet_d <= 0 or length_d <= 0:
        raise MetrajHesapHatasi("Adet ve uzunluk pozitif olmalıdır.")
    return (kg_m * adet_d * length_d).quantize(Decimal("0.01"))


_PROFIL_KG_METRE = {"IPE 80": "6.0", "IPE 100": "8.1", "IPE 200": "22.4", "HEA 200": "42.3"}


def profil_metraji(uzunluk: int | str | Decimal, adet: int | str | Decimal = 1,
                   kg_m: int | str | Decimal | None = None,
                   profil: str | None = None) -> Decimal:
    """Profil ağırlığını kg olarak hesaplar; kg/m tablo değeri veya açıkça verilebilir."""
    if kg_m is None and profil:
        kg_m = _PROFIL_KG_METRE.get(profil.strip().upper())
    if kg_m is None:
        raise MetrajHesapHatasi("Profil için kg/m veya bilinen profil adı gereklidir.")
    try:
        result = Decimal(str(uzunluk)) * Decimal(str(adet)) * Decimal(str(kg_m))
    except (InvalidOperation, TypeError) as exc:
        raise MetrajHesapHatasi("Profil ölçüleri geçersiz.") from exc
    if result <= 0:
        raise MetrajHesapHatasi("Profil ölçüleri pozitif olmalıdır.")
    return result.quantize(Decimal("0.01"))


def pursantaj_hesapla(
    tutar: int | str | Decimal | None = None,
    oran: int | str | Decimal | None = None,
    *,
    miktar: int | str | Decimal | None = None,
    pursantaj: int | str | Decimal | None = None,
) -> Decimal:
    """PozPlan/Hakedis tutarlarıyla uyumlu pursantaj tutarı."""
    try:
        result = Decimal(str(tutar if tutar is not None else miktar))
        result *= Decimal(str(oran if oran is not None else pursantaj)) / Decimal("100")
    except (InvalidOperation, TypeError, ZeroDivisionError) as exc:
        raise MetrajHesapHatasi("Tutar ve oran sayısal olmalıdır.") from exc
    if result < 0:
        raise MetrajHesapHatasi("Pursantaj sonucu negatif olamaz.")
    return result.quantize(Decimal("0.01"))


# Açık isimler; API ve dış servis entegrasyonlarında geriye dönük kullanım.
safe_expression = ifade_hesapla
metraj_hesapla = ifade_hesapla
