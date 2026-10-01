from decimal import Decimal, ROUND_HALF_UP


KURU_SIFIR = Decimal("0")
YUZ = Decimal("100")
IKI_HANE = Decimal("0.01")


def _yuvarla(deger: Decimal) -> Decimal:
    return Decimal(deger).quantize(IKI_HANE, rounding=ROUND_HALF_UP)


def kalem_hesapla(kalem, fatura=None) -> dict:
    brut = Decimal(kalem.miktar) * Decimal(kalem.birim_fiyat)
    iskonto_orani = Decimal(getattr(kalem, "iskonto_orani", 0) or 0)
    iskonto = brut * iskonto_orani / YUZ
    matrah = _yuvarla(brut - iskonto)

    # FAZ 6E: parent fatura verildiyse tekrar sorgulama (N+1).
    parent = fatura if fatura is not None else kalem.fatura
    kdv_orani = Decimal(kalem.kdv_orani)
    kdv_dahil_mi = bool(getattr(parent, "kdv_dahil_mi", False))
    if kdv_dahil_mi:
        kdv = _yuvarla(matrah - (matrah / (Decimal("1") + kdv_orani / YUZ)))
        matrah = _yuvarla(matrah - kdv)
    else:
        kdv = _yuvarla(matrah * kdv_orani / YUZ)

    tevkifat = _yuvarla(kdv * Decimal(kalem.tevkifat_orani) / YUZ)
    stopaj = _yuvarla(matrah * Decimal(kalem.stopaj_orani) / YUZ)
    satir_toplami = _yuvarla(matrah + kdv - tevkifat - stopaj)
    return {
        "brut": _yuvarla(brut),
        "iskonto": _yuvarla(iskonto),
        "matrah": matrah,
        "kdv": kdv,
        "tevkifat": tevkifat,
        "stopaj": stopaj,
        "satir_toplami": satir_toplami,
    }


def fatura_toplam_hesapla(fatura) -> dict:
    detaylar = [kalem_hesapla(kalem, fatura=fatura) for kalem in fatura.kalemler.all()]
    matrah = _yuvarla(sum((x["matrah"] for x in detaylar), KURU_SIFIR))
    kdv = _yuvarla(sum((x["kdv"] for x in detaylar), KURU_SIFIR))
    tevkifat = _yuvarla(sum((x["tevkifat"] for x in detaylar), KURU_SIFIR))
    stopaj = _yuvarla(sum((x["stopaj"] for x in detaylar), KURU_SIFIR))
    iskonto = _yuvarla(sum((x["iskonto"] for x in detaylar), KURU_SIFIR))
    belge_iskontosu = _yuvarla(Decimal(fatura.iskonto_tutari or 0))
    matrah = _yuvarla(max(matrah - belge_iskontosu, KURU_SIFIR))
    genel_toplam = _yuvarla(matrah + kdv - tevkifat - stopaj)
    odenen = _yuvarla(Decimal(fatura.odenen_tutar))
    kalan = _yuvarla(genel_toplam - odenen)
    kur = Decimal(fatura.kur or 1)
    return {
        "matrah": str(matrah),
        "kdv": str(kdv),
        "tevkifat": str(tevkifat),
        "stopaj": str(stopaj),
        "iskonto": str(_yuvarla(iskonto + belge_iskontosu)),
        "genel_toplam": str(genel_toplam),
        "odenecek": str(genel_toplam),
        "odenen": str(odenen),
        "kalan": str(kalan),
        "tl_karsiligi": str(_yuvarla(genel_toplam * kur)),
        "kalem_detaylari": [
            {anahtar: str(deger) for anahtar, deger in detay.items()}
            for detay in detaylar
        ],
    }
