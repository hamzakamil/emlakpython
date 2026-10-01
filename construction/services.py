"""
Maliyet motoru — metraj → poz → fiyat, PozPlan snapshot, S-eğrisi raporu (Faz 2).

Kural: tüm hesaplamalar Decimal'dir (01-GELISTIRME-KURALLARI.md §4).
"""

from decimal import Decimal
from typing import TypedDict

from .models import Hakedis, HakedisSatiri, Poz, PozFiyat, PozPlan, Proje, ProjePozFiyat, YfkFiyat
from .services.malzeme_fiyat import FiyatSonucu, etkin_poz_malzeme, malzeme_etkin_fiyati, proje_poz_etkin_fiyati

#: Para tutarları için quantize hedefi (2 ondalık).
PARA_ONDALIK = Decimal("0.01")
#: Metraj miktarları için quantize hedefi (4 ondalık).
METRAJ_ONDALIK = Decimal("0.0001")


def poz_birim_fiyati(poz: Poz, yil: int) -> Decimal | None:
    """Belirli yıl için pozun aktif birim fiyatını döner; yoksa None."""
    fiyat = (
        PozFiyat.objects.filter(poz=poz, yil=yil, is_active=True)
        .order_by("-created_at")
        .first()
    )
    return fiyat.birim_fiyat if fiyat else None


def poz_etkin_fiyati(proje: Proje | None, poz: Poz, yil: int) -> Decimal | None:
    """
    Pozun etkin birim fiyatını fallback zinciriyle çözer.

    FAZ 2: Yeni proje bazlı malzeme sistemini kullanır.
    Eski fallback zinciri (ProjePozFiyat → PozFiyat → YfkFiyat) korundu
    ancak proje bazlı poz analizi artık malzeme alternatiflerini dikkate alır.

    Args:
        proje: Proje instance (None ise proje özel fiyat atlanır)
        poz: Poz instance
        yil: Fiyat yılı

    Returns:
        Decimal birim fiyat veya None (hiçbir kaynaktan fiyat bulunamazsa)
    """
    if proje is not None:
        # Yeni proje bazlı poz etkin fiyatı (malzeme alternatifleri dahil)
        return proje_poz_etkin_fiyati(proje, poz, yil)

    # Proje yoksa eski fallback zinciri
    genel_fiyat = poz_birim_fiyati(poz, yil)
    if genel_fiyat is not None:
        return genel_fiyat

    yfk_fiyat = (
        YfkFiyat.objects.filter(
            poz_versiyon__poz_no=poz.poz_no,
            yil=yil,
            is_active=True,
        )
        .select_related("poz_versiyon")
        .order_by("-created_at")
        .first()
    )
    if yfk_fiyat:
        return yfk_fiyat.birim_fiyat

    return None


def poz_toplam_tutar(poz: Poz, yil: int, metraj_miktari: Decimal) -> Decimal | None:
    """Metraj bütünlüğü: miktar pozitif olmalı; fiyat yoksa None döner.

    > `metraj_miktari`: Decimal olarak verilmelidir (float asla kabul edilmez).
    """
    if not isinstance(metraj_miktari, Decimal):
        raise TypeError("metraj_miktari Decimal olmalıdır (float yasak).")
    if metraj_miktari <= 0:
        raise ValueError("Metraj miktarı sıfırdan büyük olmalıdır.")
    birim = poz_birim_fiyati(poz, yil)
    if birim is None:
        return None
    return (metraj_miktari * birim).quantize(Decimal("0.01"))


class PozPlanSatir(TypedDict):
    """S-eğrisi rapor satırı (frontend tipine denk)."""

    poz_no: str
    poz_ad: str
    grup_kodu: str | None
    planlanan_miktar: str
    gercek_miktar: str
    birim: str
    birim_fiyat: str
    plan_deger: str
    gercek_deger: str
    sapma_tutar: str
    sapma_yuzde: str


class SEkgirsiRaporu(TypedDict):
    """Poz bazlı planlanan / gerçekleşen maliyet karşılaştırma raporu."""

    proje_kodu: str
    yil: int
    toplam_plan_miktar: str
    toplam_gercek_miktar: str
    toplam_plan_deger: str
    toplam_gercek_deger: str
    toplam_sapma_tutar: str
    toplam_sapma_yuzde: str
    pozlar: list[PozPlanSatir]


class NakitAkisiAyi(TypedDict):
    donem: str
    planlanan_gider: str
    gerceklesen_gider: str
    gelir: str
    net: str
    kümülatif_net: str


class ProjeNakitAkisi(TypedDict):
    proje_kodu: str
    yil: int
    planlanan_gider: str
    gerceklesen_gider: str
    gelir: str
    net: str
    veri_notu: str
    aylar: list[NakitAkisiAyi]


class ProjeKarZarar(TypedDict):
    proje_kodu: str
    yil: int
    butcelenen_maliyet: str
    gerceklesen_maliyet: str
    maliyet_sapmasi: str
    maliyet_sapmasi_yuzde: str
    gelir: str
    net_sonuc: str
    veri_notu: str
    pozlar: list[dict[str, str]]


class PortfoyProjeSatiri(TypedDict):
    id: int
    proje_kodu: str
    proje_adi: str
    durum: str
    yapisinif_kodu: str | None
    butce: str
    gerceklesen: str
    sapma: str
    sapma_yuzde: str
    net_sonuc: str


class PortfoyKarsilastirma(TypedDict):
    yil: int
    proje_sayisi: int
    toplam_butce: str
    toplam_gerceklesen: str
    toplam_sapma: str
    toplam_net_sonuc: str
    veri_notu: str
    projeler: list[PortfoyProjeSatiri]


class TeknikSartnameKalemi(TypedDict):
    poz_no: str
    poz_ad: str
    birim: str
    grup: str
    malzemeler: list[dict[str, str]]


class TeknikSartnameTaslagi(TypedDict):
    baslik: str
    proje_kodu: str
    proje_adi: str
    yil: int
    uretim_notu: str
    kalem_sayisi: int
    malzeme_sayisi: int
    kalemler: list[TeknikSartnameKalemi]
    markdown: str


def portfoy_karsilastirmasi(projeler, yil: int) -> PortfoyKarsilastirma:
    """Proje bazlı kâr/zarar raporlarını yönetici karşılaştırmasına dönüştürür."""
    satirlar: list[PortfoyProjeSatiri] = []
    toplam_butce = Decimal("0")
    toplam_gerceklesen = Decimal("0")
    toplam_net = Decimal("0")
    for proje in projeler:
        rapor = proje_kar_zarar(proje, yil)
        butce = Decimal(rapor["butcelenen_maliyet"])
        gerceklesen = Decimal(rapor["gerceklesen_maliyet"])
        toplam_butce += butce
        toplam_gerceklesen += gerceklesen
        toplam_net += Decimal(rapor["net_sonuc"])
        satirlar.append(
            PortfoyProjeSatiri(
                id=proje.pk,
                proje_kodu=proje.proje_kodu,
                proje_adi=proje.ad,
                durum=proje.get_durum_display(),
                yapisinif_kodu=(
                    proje.yapisinif_maliyet.sinif_kodu
                    if proje.yapisinif_maliyet
                    else None
                ),
                butce=str(butce.quantize(PARA_ONDALIK)),
                gerceklesen=str(gerceklesen.quantize(PARA_ONDALIK)),
                sapma=str((gerceklesen - butce).quantize(PARA_ONDALIK)),
                sapma_yuzde=rapor["maliyet_sapmasi_yuzde"],
                net_sonuc=rapor["net_sonuc"],
            )
        )
    toplam_butce = toplam_butce.quantize(PARA_ONDALIK)
    toplam_gerceklesen = toplam_gerceklesen.quantize(PARA_ONDALIK)
    return PortfoyKarsilastirma(
        yil=yil,
        proje_sayisi=len(satirlar),
        toplam_butce=str(toplam_butce),
        toplam_gerceklesen=str(toplam_gerceklesen),
        toplam_sapma=str((toplam_gerceklesen - toplam_butce).quantize(PARA_ONDALIK)),
        toplam_net_sonuc=str(toplam_net.quantize(PARA_ONDALIK)),
        veri_notu="Tutarlar aktif poz planları ve onaylı hakedişlerden hesaplanır; projeye bağlı gelir modeli yoktur.",
        projeler=satirlar,
    )


def teknik_sartname_taslagi(proje: Proje, yil: int) -> TeknikSartnameTaslagi:
    """Projenin aktif poz ve TS/TS EN referanslarından şartname taslağı üretir."""
    planlar = (
        PozPlan.objects.filter(proje=proje, yil=yil, is_active=True)
        .select_related("poz", "poz__grup")
        .prefetch_related("poz__malzeme_kalemleri__malzeme")
        .order_by("poz__grup__kod", "poz__poz_no")
    )
    kalemler: list[TeknikSartnameKalemi] = []
    malzeme_sayisi = 0
    for plan in planlar:
        malzemeler = [
            {
                "kod": iliski.malzeme.malzeme_kodu,
                "ad": iliski.malzeme.ad,
                "birim": iliski.malzeme.birim,
                "miktar": str(iliski.miktar),
                "ts_no": iliski.malzeme.ts_no or "Belirtilmemiş",
            }
            for iliski in plan.poz.malzeme_kalemleri.all()
            if iliski.malzeme.is_active
        ]
        malzeme_sayisi += len(malzemeler)
        kalemler.append(
            TeknikSartnameKalemi(
                poz_no=plan.poz.poz_no,
                poz_ad=plan.poz.ad,
                birim=plan.poz.birim,
                grup=plan.poz.grup.ad,
                malzemeler=malzemeler,
            )
        )
    baslik = f"{proje.ad} — Teknik Şartname Taslağı ({yil})"
    satirlar = [
        f"# {baslik}",
        "",
        f"**Proje kodu:** {proje.proje_kodu}  ",
        f"**Dönem:** {yil}  ",
        "",
        "> Bu belge, aktif poz planları ve malzeme kartlarındaki TS/TS EN referanslarından otomatik oluşturulan taslaktır. Uygulama öncesi yetkili teknik ekip tarafından kontrol edilmelidir.",
        "",
    ]
    for sira, kalem in enumerate(kalemler, 1):
        satirlar.extend(
            [
                f"## {sira}. {kalem['poz_no']} — {kalem['poz_ad']}",
                f"- **Poz grubu:** {kalem['grup']}",
                f"- **Ölçü birimi:** {kalem['birim']}",
            ]
        )
        if kalem["malzemeler"]:
            satirlar.append("- **Malzeme ve standartlar:**")
            for malzeme in kalem["malzemeler"]:
                satirlar.append(
                    f"  - {malzeme['kod']} — {malzeme['ad']} | "
                    f"{malzeme['miktar']} {malzeme['birim']}/poz | TS/TS EN: {malzeme['ts_no']}"
                )
        else:
            satirlar.append("- **Malzeme ve standartlar:** Bu poz için aktif malzeme referansı bulunamadı.")
        satirlar.append("")
    return TeknikSartnameTaslagi(
        baslik=baslik,
        proje_kodu=proje.proje_kodu,
        proje_adi=proje.ad,
        yil=yil,
        uretim_notu="Bu taslak otomatik üretilmiştir; teknik onay ve mevzuat kontrolü gerektirir.",
        kalem_sayisi=len(kalemler),
        malzeme_sayisi=malzeme_sayisi,
        kalemler=kalemler,
        markdown="\n".join(satirlar),
    )


class MetrajKontrolOnerisi(TypedDict):
    poz_no: str
    poz_ad: str
    seviye: str
    kod: str
    mesaj: str
    onerilen_aksiyon: str


class MetrajKontrolRaporu(TypedDict):
    proje_kodu: str
    yil: int
    kontrol_edilen_poz: int
    kritik: int
    uyari: int
    bilgi: int
    oneriler: list[MetrajKontrolOnerisi]


class FiyatAnomalisi(TypedDict):
    poz_no: str
    poz_ad: str
    yil: int
    seviye: str
    kod: str
    mevcut_fiyat: str
    referans_fiyat: str
    degisim_yuzde: str
    mesaj: str
    onerilen_aksiyon: str


class FiyatAnomaliRaporu(TypedDict):
    proje_kodu: str
    yil: int
    kontrol_edilen_poz: int
    kritik: int
    uyari: int
    anomaliler: list[FiyatAnomalisi]


def metraj_kontrolu(proje: Proje, yil: int) -> MetrajKontrolRaporu:
    """Poz planlarını kural tabanlı akıllı kontrollerden geçirir.

    Bu ilk sürüm dış bir model kullanmaz; açıklanabilir eşikler üretir ve
    ileride çizim/listeden gelen AI önerileri için aynı çıktı sözleşmesini korur.
    """
    oneriler: list[MetrajKontrolOnerisi] = []
    planlar = (
        PozPlan.objects.select_related("poz")
        .filter(proje=proje, yil=yil, is_active=True)
        .order_by("poz__poz_no")
    )
    for plan in planlar:
        oran = plan.gercek_miktar / plan.planlanan_miktar
        ortak = {"poz_no": plan.poz.poz_no, "poz_ad": plan.poz.ad}
        if oran > Decimal("1.10"):
            oneriler.append(MetrajKontrolOnerisi(
                **ortak, seviye="kritik", kod="FAZLA_METRAJ",
                mesaj=f"Gerçekleşen metraj planın %{(oran * 100).quantize(Decimal('0.1'))} seviyesinde.",
                onerilen_aksiyon="Şantiye ölçümünü ve hakediş satırını kontrol edin; gerekiyorsa plan revizyonu açın.",
            ))
        elif plan.gercek_miktar == 0:
            oneriler.append(MetrajKontrolOnerisi(
                **ortak, seviye="uyari", kod="GERCEKLESME_YOK",
                mesaj="Planlanan metraj var ancak henüz gerçekleşme girilmemiş.",
                onerilen_aksiyon="Saha ölçümünü girin veya iş kaleminin başlangıç tarihini güncelleyin.",
            ))
        elif oran < Decimal("0.25"):
            oneriler.append(MetrajKontrolOnerisi(
                **ortak, seviye="bilgi", kod="DUSUK_GERCEKLESME",
                mesaj=f"Gerçekleşme planın %{(oran * 100).quantize(Decimal('0.1'))} seviyesinde.",
                onerilen_aksiyon="İş programı ve tedarik durumunu gözden geçirin.",
            ))
    return MetrajKontrolRaporu(
        proje_kodu=proje.proje_kodu, yil=yil, kontrol_edilen_poz=planlar.count(),
        kritik=sum(x["seviye"] == "kritik" for x in oneriler),
        uyari=sum(x["seviye"] == "uyari" for x in oneriler),
        bilgi=sum(x["seviye"] == "bilgi" for x in oneriler),
        oneriler=oneriler,
    )


def fiyat_anomalilerini_bul(proje: Proje, yil: int) -> FiyatAnomaliRaporu:
    """Proje snapshot fiyatını önceki yıl fiyatıyla açıklanabilir eşikte karşılaştırır."""
    anomaliler: list[FiyatAnomalisi] = []
    planlar = PozPlan.objects.select_related("poz").filter(
        proje=proje, yil=yil, is_active=True
    )
    for plan in planlar:
        onceki = (
            PozFiyat.objects.filter(
                tenant=proje.tenant, poz=plan.poz, yil=yil - 1, is_active=True
            ).order_by("-created_at").first()
        )
        if not onceki or onceki.birim_fiyat <= 0:
            continue
        degisim = ((plan.birim_fiyat_snapshot - onceki.birim_fiyat) / onceki.birim_fiyat * Decimal("100")).quantize(Decimal("0.1"))
        mutlak = abs(degisim)
        if mutlak < Decimal("30"):
            continue
        seviye = "kritik" if mutlak >= Decimal("75") else "uyari"
        anomaliler.append(FiyatAnomalisi(
            poz_no=plan.poz.poz_no, poz_ad=plan.poz.ad, yil=yil, seviye=seviye,
            kod="FIYAT_SAPMASI", mevcut_fiyat=str(plan.birim_fiyat_snapshot),
            referans_fiyat=str(onceki.birim_fiyat), degisim_yuzde=f"{degisim}%",
            mesaj=f"Birim fiyat önceki yıla göre %{degisim} değişmiş.",
            onerilen_aksiyon="Kaynak tebliğini ve fiyat snapshot'ını kontrol edin; gerekirse planı revize edin.",
        ))
    return FiyatAnomaliRaporu(
        proje_kodu=proje.proje_kodu, yil=yil, kontrol_edilen_poz=planlar.count(),
        kritik=sum(x["seviye"] == "kritik" for x in anomaliler),
        uyari=sum(x["seviye"] == "uyari" for x in anomaliler),
        anomaliler=anomaliler,
    )


def s_egrisi_raporu(proje: Proje, yil: int) -> SEkgirsiRaporu:
    """Poz bazlı gerçekleşen / planlanan maliyet karşılaştırma (S-eğrisi).

    PV = planlanan_miktar × birim_fiyat_snapshot
    AV = gercek_miktar × birim_fiyat_snapshot
    """
    planlar = (
        PozPlan.objects.select_related("poz__grup", "proje")
        .filter(proje=proje, yil=yil, is_active=True)
        .order_by("poz__poz_no")
    )

    Q = PARA_ONDALIK  # para quantize hedefi
    MM = METRAJ_ONDALIK  # metraj quantize hedefi
    toplam_plan_miktar = Decimal("0")
    toplam_gercek_miktar = Decimal("0")
    toplam_plan_deger = Decimal("0")
    toplam_gercek_deger = Decimal("0")
    satirlar: list[PozPlanSatir] = []

    for p in planlar:
        plan_deger = (p.planlanan_miktar * p.birim_fiyat_snapshot).quantize(Q)
        gercek_deger = (p.gercek_miktar * p.birim_fiyat_snapshot).quantize(Q)
        sapma_tutar = (gercek_deger - plan_deger).quantize(Q)
        sapma_yuzde = (
            (sapma_tutar / plan_deger * Decimal("100")).quantize(Q)
            if plan_deger > 0
            else Decimal("0")
        )

        toplam_plan_miktar += p.planlanan_miktar
        toplam_gercek_miktar += p.gercek_miktar
        toplam_plan_deger += plan_deger
        toplam_gercek_deger += gercek_deger

        satirlar.append(
            PozPlanSatir(
                poz_no=p.poz.poz_no,
                poz_ad=p.poz.ad,
                grup_kodu=p.poz.grup.kod if p.poz.grup else None,
                planlanan_miktar=str(p.planlanan_miktar),
                gercek_miktar=str(p.gercek_miktar),
                birim=p.poz.birim,
                birim_fiyat=str(p.birim_fiyat_snapshot),
                plan_deger=str(plan_deger),
                gercek_deger=str(gercek_deger),
                sapma_tutar=str(sapma_tutar),
                sapma_yuzde=f"{sapma_yuzde}%",
            )
        )

    toplam_sapma_tutar = (toplam_gercek_deger - toplam_plan_deger).quantize(Q)
    toplam_sapma_yuzde = (
        (toplam_sapma_tutar / toplam_plan_deger * Decimal("100")).quantize(Q)
        if toplam_plan_deger > 0
        else Decimal("0")
    )

    return SEkgirsiRaporu(
        proje_kodu=proje.proje_kodu,
        yil=yil,
        toplam_plan_miktar=str(toplam_plan_miktar.quantize(MM)),
        toplam_gercek_miktar=str(toplam_gercek_miktar.quantize(MM)),
        toplam_plan_deger=str(toplam_plan_deger.quantize(Q)),
        toplam_gercek_deger=str(toplam_gercek_deger.quantize(Q)),
        toplam_sapma_tutar=str(toplam_sapma_tutar.quantize(Q)),
        toplam_sapma_yuzde=f"{toplam_sapma_yuzde}%",
        pozlar=satirlar,
    )


def proje_nakit_akisi(proje: Proje, yil: int) -> ProjeNakitAkisi:
    """Proje bazlı yıllık nakit akışı özeti.

    Poz planı yıllık planlanan gideri, onaylanmış hakedişler ise dönemsel
    gerçekleşen gideri sağlar. Mevcut veri modelinde gelir kaydı projeye bağlı
    olmadığı için gelir bilinçli olarak sıfır döner; istemci bunu varsayımsal
    satış/kira geliri gibi gösteremez.
    """
    planlanan = sum(
        (p.planlanan_miktar * p.birim_fiyat_snapshot for p in PozPlan.objects.filter(
            proje=proje, yil=yil, is_active=True
        )),
        Decimal("0"),
    ).quantize(PARA_ONDALIK)
    hakedişler = Hakedis.objects.filter(
        proje=proje, donem__startswith=f"{yil}-", durum=Hakedis.Durum.ONAYLANDI
    ).prefetch_related("satirlar")
    aylik = {f"{ay:02d}": Decimal("0") for ay in range(1, 13)}
    for hakediş in hakedişler:
        aylik[hakediş.donem[-2:]] += hakedis_toplami(hakediş)
    gelir = Decimal("0")
    kumulatif = Decimal("0")
    aylar: list[NakitAkisiAyi] = []
    for ay in range(1, 13):
        donem = f"{yil}-{ay:02d}"
        gerceklesen = aylik[f"{ay:02d}"].quantize(PARA_ONDALIK)
        net = (gelir - gerceklesen).quantize(PARA_ONDALIK)
        kumulatif = (kumulatif + net).quantize(PARA_ONDALIK)
        aylar.append(
            NakitAkisiAyi(
                donem=donem,
                planlanan_gider="0.00",
                gerceklesen_gider=str(gerceklesen),
                gelir="0.00",
                net=str(net),
                kümülatif_net=str(kumulatif),
            )
        )
    net = (gelir - sum(aylik.values(), Decimal("0"))).quantize(PARA_ONDALIK)
    return ProjeNakitAkisi(
        proje_kodu=proje.proje_kodu,
        yil=yil,
        planlanan_gider=str(planlanan),
        gerceklesen_gider=str(sum(aylik.values(), Decimal("0")).quantize(PARA_ONDALIK)),
        gelir="0.00",
        net=str(net),
        veri_notu="Gelir kayıtları mevcut veri modelinde projeye bağlı olmadığı için bu raporda gelir 0 gösterilir.",
        aylar=aylar,
    )


def proje_kar_zarar(proje: Proje, yil: int) -> ProjeKarZarar:
    """Proje bütçesi ile onaylı hakediş gerçekleşmesini karşılaştırır."""
    planlar = PozPlan.objects.select_related("poz").filter(
        proje=proje, yil=yil, is_active=True
    )
    butce = sum(
        (p.planlanan_miktar * p.birim_fiyat_snapshot for p in planlar),
        Decimal("0"),
    ).quantize(PARA_ONDALIK)
    hakedişler = Hakedis.objects.filter(
        proje=proje, donem__startswith=f"{yil}-", durum=Hakedis.Durum.ONAYLANDI
    ).prefetch_related("satirlar__poz")
    gerceklesen = sum((hakedis_toplami(h) for h in hakedişler), Decimal("0")).quantize(PARA_ONDALIK)
    sapma = (gerceklesen - butce).quantize(PARA_ONDALIK)
    sapma_yuzde = (sapma / butce * Decimal("100")).quantize(PARA_ONDALIK) if butce else Decimal("0")
    pozlar = []
    for plan in planlar:
        plan_deger = (plan.planlanan_miktar * plan.birim_fiyat_snapshot).quantize(PARA_ONDALIK)
        gercek_deger = (plan.gercek_miktar * plan.birim_fiyat_snapshot).quantize(PARA_ONDALIK)
        pozlar.append({
            "poz_no": plan.poz.poz_no,
            "poz_ad": plan.poz.ad,
            "butce": str(plan_deger),
            "gerceklesen_metraj_degeri": str(gercek_deger),
            "sapma": str((gercek_deger - plan_deger).quantize(PARA_ONDALIK)),
        })
    return ProjeKarZarar(
        proje_kodu=proje.proje_kodu,
        yil=yil,
        butcelenen_maliyet=str(butce),
        gerceklesen_maliyet=str(gerceklesen),
        maliyet_sapmasi=str(sapma),
        maliyet_sapmasi_yuzde=f"{sapma_yuzde}%",
        gelir="0.00",
        net_sonuc=str(-gerceklesen),
        veri_notu="Projeye bağlı gelir modeli bulunmadığı için gelir 0 gösterilir; net sonuç yalnızca gerçekleşen maliyet görünümüdür.",
        pozlar=pozlar,
    )


# ---------------------------------------------------------------------------
# Hakediş — dönemsel hakediş hesaplama + onay (readme §52.6 madde 3-4)
# ---------------------------------------------------------------------------


def hakedis_satirlari_olustur(hakedis: Hakedis) -> int:
    """Hakediş satırlarını proje poz planlarından üretir (gerçekleşen metraj > 0).

    Her plan için (poz, gerçekleşen miktar, snapshot fiyat) satırı açılır;
    mevcut satırlar korunur (idempotent — aynı poz tekrar eklenmez).
    Dönen değer: eklenen satır sayısı.
    """
    planlar = PozPlan.objects.select_related("poz").filter(
        proje=hakedis.proje, is_active=True, gercek_miktar__gt=0,
    )
    # Dönem yılı filtresi: planın fiyat yılı, dönem yılıyla eşleşmeli
    # (snapshot fiyatın hangi yıla ait olduğu bellidir).
    donem_yil = int(hakedis.donem.split("-")[0])
    planlar = planlar.filter(yil=donem_yil)

    mevcut_pozlar = set(hakedis.satirlar.values_list("poz_id", flat=True))
    eklenen = 0
    for plan in planlar:
        if plan.poz_id in mevcut_pozlar:
            continue
        HakedisSatiri.objects.create(
            hakedis=hakedis, poz=plan.poz,
            miktar=plan.gercek_miktar, birim_fiyat=plan.birim_fiyat_snapshot,
        )
        mevcut_pozlar.add(plan.poz_id)
        eklenen += 1
    return eklenen


def hakedis_toplami(hakedis: Hakedis) -> Decimal:
    """Hakediş toplam tutarı (satır tutarları toplamı, 2 ondalık)."""
    return sum((s.satir_tutar for s in hakedis.satirlar.all()), Decimal("0")).quantize(
        PARA_ONDALIK
    )


def hakedis_onayla(hakedis: Hakedis, onaylayan) -> Hakedis:
    """Taslak hakedişi onaylar: Cari Hareket + Muhasebe Fişi üretir (tek transaction).

    - Cari yoksa ValidationError (hareketin işleneceği taraf belli olmalı).
    - Satır yoksa / toplam 0 ise ValidationError.
    - Tekrar onay (durum != taslak) engellenir.
    - Hesap planında 740/120 kodları yoksa otomatik açılır (tenant'a izole).
    """
    from django.core.exceptions import ValidationError as DjangoValidationError
    from django.db import transaction
    from django.utils import timezone

    if hakedis.durum != Hakedis.Durum.TASLAK:
        raise DjangoValidationError("Yalnızca taslak hakediş onaylanabilir.")
    if hakedis.cari_id is None:
        raise DjangoValidationError("Onay için yüklenici cari kartı seçilmelidir.")
    toplam = hakedis_toplami(hakedis)
    if toplam <= 0:
        raise DjangoValidationError("Onay için en az bir hakediş satırı gereklidir.")

    from accounting.models import FisSatiri, HesapPlani, MuhasebeFisi
    from cari.models import CariHareket

    with transaction.atomic():
        hakedis = Hakedis.objects.select_for_update().get(pk=hakedis.pk)
        if hakedis.durum != Hakedis.Durum.TASLAK:
            raise DjangoValidationError("Hakediş zaten işleme alınmış.")
        tenant = hakedis.tenant
        # Gider (740 Hizmet Üretim Maliyeti) / Alıcılar (120) — yoksa açılır.
        gider_hesap, _ = HesapPlani.objects.get_or_create(
            tenant=tenant, kod="740",
            defaults={"ad": "Hizmet Üretim Maliyeti", "tip": "gider"},
        )
        alacak_hesap, _ = HesapPlani.objects.get_or_create(
            tenant=tenant, kod="120",
            defaults={"ad": "Alıcılar", "tip": "aktif"},
        )
        fis_no = f"HD-{hakedis.proje.proje_kodu}-{hakedis.donem}"
        fis, olustu = MuhasebeFisi.objects.get_or_create(
            tenant=tenant, fis_no=fis_no,
            defaults={
                "fis_tarihi": timezone.localdate(),
                "aciklama": f"Hakediş {hakedis.proje.proje_kodu} / {hakedis.donem}",
                "durum": MuhasebeFisi.Durum.KAYITLI,
            },
        )
        if olustu:
            FisSatiri(fis=fis, hesap=gider_hesap, borc=toplam).full_clean()
            FisSatiri(fis=fis, hesap=alacak_hesap, alacak=toplam).full_clean()
            FisSatiri.objects.create(fis=fis, hesap=gider_hesap, borc=toplam)
            FisSatiri.objects.create(fis=fis, hesap=alacak_hesap, alacak=toplam)
        else:
            # Aynı fiş no ile kayıtlı fiş varsa tutar uyumu aranır (çift onay koruması).
            fis_borc = sum((s.borc for s in fis.satirlar.all()), Decimal("0"))
            if fis_borc != toplam:
                raise DjangoValidationError(
                    f"{fis_no} fişi zaten {fis_borc} ₺ ile kayıtlı; hakediş toplamı {toplam} ₺."
                )
        hareket = CariHareket.objects.create(
            tenant=tenant, cari=hakedis.cari, yon=CariHareket.Yon.BORC,
            tutar=toplam, islem_tarihi=timezone.localdate(),
            aciklama=f"Hakediş {hakedis.proje.proje_kodu} / {hakedis.donem}",
        )
        hakedis.cari_hareket = hareket
        hakedis.muhasebe_fisi = fis
        hakedis.onaylayan = onaylayan
        hakedis.onay_tarihi = timezone.now()
        hakedis.durum = Hakedis.Durum.ONAYLANDI
        hakedis.full_clean(exclude=("cari_hareket", "muhasebe_fisi", "onaylayan", "onay_tarihi"))
        hakedis.save()
    import logging

    logging.getLogger("erp.hakedis").info(
        "event=hakedis_onay proje=%s donem=%s toplam=%s",
        hakedis.proje.proje_kodu, hakedis.donem, toplam,
        extra={"tenant_id": hakedis.tenant_id, "operation": "hakedis.onayla",
               "resource_id": hakedis.pk},
    )
    return hakedis


# ---------------------------------------------------------------------------
# Gantt şeması — iş kalemi (poz) bazlı zaman çizelgesi (roadmap Faz 2)
# ---------------------------------------------------------------------------


class GanttCubugu(TypedDict):
    """Gantt satırı (tek iş kalemi / poz planı)."""

    id: int
    poz_no: str
    poz_ad: str
    grup_kodu: str | None
    yil: int
    baslangic: str | None  # ISO tarih (YYYY-MM-DD)
    bitis: str | None
    tarih_atandi: bool
    planlanan_miktar: str
    gercek_miktar: str
    ilerleme_yuzde: str
    plan_deger: str
    gercek_deger: str


class GanttRaporu(TypedDict):
    """Proje için zaman çizelgesi verisi + eksen aralığı."""

    proje_kodu: str
    proje_ad: str
    yil: int | None
    en_erken: str | None
    en_gec: str | None
    tarihsiz_sayi: int
    cubuklar: list[GanttCubugu]


def gantt_verisi(proje: Proje, yil: int | None = None) -> GanttRaporu:
    """İş kalemi bazlı zaman çizelgesi verisi.

    - Çubuk tarihleri `planlanan_baslangic` / `planlanan_bitis` alanlarından gelir
      (girilmemişse çubuk ``tarih_atandi=False`` olarak döner ve eksene konmaz).
    - İlerleme yüzdesi = gerçekleşen metraj / planlanan metraj × 100.
    - Satırlar poz grubu koduna, sonra poz numarasına göre sıralanır.
    """
    planlar = PozPlan.objects.select_related("poz__grup", "proje").filter(
        proje=proje, is_active=True
    )
    if yil is not None:
        planlar = planlar.filter(yil=yil)
    planlar = planlar.order_by("poz__grup__kod", "poz__poz_no")

    Q = PARA_ONDALIK
    MM = METRAJ_ONDALIK
    cubuklar: list[GanttCubugu] = []
    tarihsiz = 0
    en_erken = None
    en_gec = None

    for p in planlar:
        if p.planlanan_baslangic and p.planlanan_bitis:
            baslangic, bitis, atandi = p.planlanan_baslangic, p.planlanan_bitis, True
        elif p.planlanan_baslangic:
            # Yalnızca başlangıç girilmişse tek günlük çubuk olarak gösterilir.
            baslangic, bitis, atandi = p.planlanan_baslangic, p.planlanan_baslangic, True
        elif p.planlanan_bitis:
            baslangic, bitis, atandi = p.planlanan_bitis, p.planlanan_bitis, True
        else:
            baslangic = bitis = None
            atandi = False
            tarihsiz += 1

        if atandi:
            en_erken = baslangic if en_erken is None or baslangic < en_erken else en_erken
            en_gec = bitis if en_gec is None or bitis > en_gec else en_gec

        ilerleme = (
            (p.gercek_miktar / p.planlanan_miktar * Decimal("100")).quantize(Q)
            if p.planlanan_miktar > 0
            else Decimal("0")
        )
        plan_deger = (p.planlanan_miktar * p.birim_fiyat_snapshot).quantize(Q)
        gercek_deger = (p.gercek_miktar * p.birim_fiyat_snapshot).quantize(Q)

        cubuklar.append(
            GanttCubugu(
                id=p.pk,
                poz_no=p.poz.poz_no,
                poz_ad=p.poz.ad,
                grup_kodu=p.poz.grup.kod if p.poz.grup else None,
                yil=p.yil,
                baslangic=baslangic.isoformat() if baslangic else None,
                bitis=bitis.isoformat() if bitis else None,
                tarih_atandi=atandi,
                planlanan_miktar=str(p.planlanan_miktar.quantize(MM)),
                gercek_miktar=str(p.gercek_miktar.quantize(MM)),
                ilerleme_yuzde=f"{ilerleme}%",
                plan_deger=str(plan_deger),
                gercek_deger=str(gercek_deger),
            )
        )

    return GanttRaporu(
        proje_kodu=proje.proje_kodu,
        proje_ad=proje.ad,
        yil=yil,
        en_erken=en_erken.isoformat() if en_erken else None,
        en_gec=en_gec.isoformat() if en_gec else None,
        tarihsiz_sayi=tarihsiz,
        cubuklar=cubuklar,
    )
