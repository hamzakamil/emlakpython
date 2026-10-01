"""ÇŞİDB poz / yapı sınıfı verisi içe aktarma (roadmap Faz 1 — "ÇŞİDB poz parser").

Kaynak veri: ÇŞİDB "Birim Fiyat ve Tarifleri" / "Yapı Yaklaşık Birim Maliyetleri
Tebliği" ve acikpoz benzeri veri setlerinin CSV'ye dönürülmüş hali (PDF → CSV
dönüştürme bu modülün dışındadır; dönüştürülmüş CSV aynı akışla içe alınır).

Kurallar (readme.md §52 + roadmap notları):
- Fiyat/maliyet her zaman Decimal'dir; float ve Türkçe virgüllü ("235,42") değer
  reddedilir — tahmini dönüşüm yasaktır (readme §52.6 madde 1).
- Parser yıllık çalıştırılabilir: aynı (tenant, poz_no) kartı güncellenir,
  fiyatlar yıl bazlı `PozFiyat` üzerinde version'lanır.
- Hiçbir kayıt fiziksel silinmez; eski yıl pozları `is_active=False` ile
  arşivlenir (roadmap notu: "aktif=false olarak arşivlenmeli, silinmemelidir").
- Yapı sınıfı girişleri normalize edilir: "4A" / "iv-a" / "IV A" → "IV-A"
  (readme §52.6 madde 5).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from django.db import transaction

from tenants.models import Tenant

from .models import Poz, PozFiyat, PozGrubu, YapiSinifiBirimMaliyet


class ImportHatasi(ValueError):
    """Import satır hatası — Türkçe mesaj taşır; tüm import rollback edilir."""


# readme §52.3: poz numaraları KK.GGG.SSSS biçiminde 3 bölmelidir
# (örn. 15.110.1001). Blok uzunlukları kaynaklar arasında değişebildiğinden
# 1-3 / 1-3 / 1-5 hane aralığı kabul edilir; biçim dışı poz numarası reddedilir.
POZ_NO_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,5}$")

# "4A", "4-A", "iv-a", "IV A", "V_e" → I, II, III, IV, V sınıfı + A-E grubu
_SINIF_RE = re.compile(
    r"^(?P<sinif>[1-5]|I{1,3}|IV|V)\s*[-._/ ]*\s*(?P<grup>[a-e])$", re.IGNORECASE
)
_SINIF_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}


def normalize_yapi_sinifi(deger: str) -> str:
    """Yapı sınıfı kodunu resmî gösterime çevirir ("4A" → "IV-A").

    Geçersiz girişte ValueError yükseltir; uydurma/kısmi kod üretilmez.
    """
    if not isinstance(deger, str):
        raise ValueError("Yapı sınıfı kodu metin olmalıdır.")
    eslesme = _SINIF_RE.match(deger.strip())
    if not eslesme:
        raise ValueError(
            f"Geçersiz yapı sınıfı kodu: {deger!r} (beklenen biçim: IV-A veya 4A)."
        )
    sinif = eslesme.group("sinif")
    sinif_roman = _SINIF_ROMAN[int(sinif)] if sinif.isdigit() else sinif.upper()
    return f"{sinif_roman}-{eslesme.group('grup').upper()}"


@dataclass
class ImportOzeti:
    """Import özeti — management komut çıktısı ve test doğrulaması içindir."""

    satir_sayisi: int = 0
    grup_olusturulan: int = 0
    poz_olusturulan: int = 0
    poz_guncellenen: int = 0
    fiyat_olusturulan: int = 0
    fiyat_guncellenen: int = 0
    arsivlenen_poz: int = 0
    arsivlenen_fiyat: int = 0
    sinif_olusturulan: int = 0
    sinif_guncellenen: int = 0

    def ozet_metni(self) -> str:
        satirlar = [
            f"İşlenen satır: {self.satir_sayisi}",
            f"Oluşturulan poz grubu: {self.grup_olusturulan}",
            f"Oluşturulan poz: {self.poz_olusturulan}",
            f"Güncellenen poz: {self.poz_guncellenen}",
            f"Oluşturulan fiyat (yıl bazlı): {self.fiyat_olusturulan}",
            f"Güncellenen fiyat (yıl bazlı): {self.fiyat_guncellenen}",
            f"Arşivlenen poz (is_active=False): {self.arsivlenen_poz}",
            f"Arşivlenen fiyat (is_active=False): {self.arsivlenen_fiyat}",
            f"Oluşturulan yapı sınıfı kaydı: {self.sinif_olusturulan}",
            f"Güncellenen yapı sınıfı kaydı: {self.sinif_guncellenen}",
        ]
        return "\n".join(f"— {satir}" for satir in satirlar)


def _satir_bos(satir: dict) -> bool:
    return not any(
        isinstance(deger, str) and deger.strip() for deger in satir.values()
    )


def _zorunlu_metin(satir: dict, alan: str, satir_no: int) -> str:
    deger = (satir.get(alan) or "").strip()
    if not deger:
        raise ImportHatasi(f"{satir_no}. satır: '{alan}' alanı boş olamaz.")
    return deger


def _pozitif_decimal(satir: dict, alan: str, satir_no: int) -> Decimal:
    """Sütun değerini Decimal'e çevirir; nokta dışı ondalık reddedilir.

    "235,42" gibi Türkçe virgüllü ya da bozuk değer uydurulup düzeltilmez;
    satır hata verir (readme §52.6 madde 1 — tahmini değer yasak).
    """
    ham = (satir.get(alan) or "").strip().replace(" ", "")
    if not ham:
        raise ImportHatasi(f"{satir_no}. satır: '{alan}' alanı boş olamaz.")
    try:
        deger = Decimal(ham)
    except InvalidOperation as exc:
        raise ImportHatasi(
            f"{satir_no}. satır: '{alan}' alanı ondalık sayı değil: {ham!r} "
            "(ondalık ayracı nokta olmalıdır, örn. 1234.56)."
        ) from exc
    if deger <= 0:
        raise ImportHatasi(
            f"{satir_no}. satır: '{alan}' sıfırdan büyük olmalıdır: {ham!r}"
        )
    return deger


def _yil_al(satir: dict, satir_no: int, varsayilan_yil: int | None) -> int:
    yil_metni = (satir.get("yil") or "").strip()
    if yil_metni:
        try:
            return int(yil_metni)
        except ValueError as exc:
            raise ImportHatasi(
                f"{satir_no}. satır: 'yil' alanı sayı olmalıdır: {yil_metni!r}"
            ) from exc
    if varsayilan_yil is not None:
        return varsayilan_yil
    raise ImportHatasi(
        f"{satir_no}. satır: 'yil' sütunu boş ve varsayılan yıl (--yil) verilmedi."
    )


def import_poz_verisi(
    tenant: Tenant,
    satirlar: list[dict],
    varsayilan_yil: int | None = None,
    varsayilan_kaynak: str = "",
    arsivlenecek_yil: int | None = None,
) -> ImportOzeti:
    """ÇŞİDB CSV satırlarını PozGrubu + Poz + yıl bazlı PozFiyat olarak alır.

    Satır sütunları: poz_no, grup_kodu, grup_adi, ad, birim, [tip], [yil],
    [birim_fiyat], [kaynak]. yil/kaynak sütunu boşsa varsayılan parametreler
    kullanılır. `birim_fiyat` sütunu boşsa yalnızca poz kartı alınır, fiyat
    kaydı oluşturulmaz (uydurma fiyat yasak — readme §52.6 madde 1).

    Tek transaction; bir satır hatalıysa tüm import geri alınır (fail-fast).
    `arsivlenecek_yil` verildiyse, o yıla ait aktif kayıtlardan bu importta
    gelmeyen pozlar `is_active=False` ile arşivlenir; hiçbir kayıt silinmez.
    """
    ozet = ImportOzeti(satir_sayisi=len(satirlar))
    if not satirlar:
        raise ValueError("İçe aktarılacak satır yok.")

    with transaction.atomic():
        import_edilen_poz_nolar: set[str] = set()

        for satir_no, satir in enumerate(satirlar, start=1):
            if _satir_bos(satir):
                continue

            poz_no = _zorunlu_metin(satir, "poz_no", satir_no)
            if not POZ_NO_RE.match(poz_no):
                raise ImportHatasi(
                    f"{satir_no}. satır: geçersiz poz numarası: {poz_no!r} "
                    "(beklenen biçim: KK.GGG.SSSS, örn. 15.110.1001)."
                )
            grup_kodu = _zorunlu_metin(satir, "grup_kodu", satir_no)
            grup_adi = _zorunlu_metin(satir, "grup_adi", satir_no)
            ad = _zorunlu_metin(satir, "ad", satir_no)
            birim = _zorunlu_metin(satir, "birim", satir_no)

            tip = (satir.get("tip") or "").strip() or Poz.PozTipi.YAPIM
            if tip not in Poz.PozTipi.values:
                raise ImportHatasi(f"{satir_no}. satır: geçersiz poz tipi: {tip!r}")

            yil = _yil_al(satir, satir_no, varsayilan_yil)
            kaynak = (satir.get("kaynak") or "").strip() or varsayilan_kaynak
            if not kaynak:
                raise ImportHatasi(
                    f"{satir_no}. satır: 'kaynak' sütunu boş ve "
                    "varsayılan kaynak (--kaynak) verilmedi."
                )

            grup, olustu = PozGrubu.objects.get_or_create(
                tenant=tenant, kod=grup_kodu, defaults={"ad": grup_adi}
            )
            if olustu:
                ozet.grup_olusturulan += 1
            elif grup.ad != grup_adi:
                grup.ad = grup_adi  # grup adı tebliğde güncellenebilir
                grup.save(update_fields=["ad", "updated_at"])

            poz, olustu = Poz.objects.get_or_create(
                tenant=tenant,
                poz_no=poz_no,
                defaults={"ad": ad, "birim": birim, "grup": grup, "tip": tip},
            )
            if olustu:
                ozet.poz_olusturulan += 1
            else:
                poz.ad = ad
                poz.birim = birim
                poz.grup = grup
                poz.tip = tip
                poz.save(update_fields=["ad", "birim", "grup", "tip", "updated_at"])
                ozet.poz_guncellenen += 1
            import_edilen_poz_nolar.add(poz_no)

            fiyat_metni = (satir.get("birim_fiyat") or "").strip()
            if fiyat_metni:
                birim_fiyat = _pozitif_decimal(satir, "birim_fiyat", satir_no)
                fiyat, olustu = PozFiyat.objects.update_or_create(
                    tenant=tenant,
                    poz=poz,
                    yil=yil,
                    defaults={
                        "birim_fiyat": birim_fiyat,
                        "kaynak": kaynak,
                        "is_active": True,
                    },
                )
                if olustu:
                    ozet.fiyat_olusturulan += 1
                else:
                    ozet.fiyat_guncellenen += 1

        if arsivlenecek_yil is not None:
            eski_fiyatlar = PozFiyat.objects.filter(
                tenant=tenant, yil=arsivlenecek_yil, is_active=True
            ).select_related("poz")
            for fiyat in eski_fiyatlar:
                if fiyat.poz.poz_no in import_edilen_poz_nolar:
                    continue
                fiyat.is_active = False
                fiyat.save(update_fields=["is_active"])
                ozet.arsivlenen_fiyat += 1
                if fiyat.poz.is_active:
                    fiyat.poz.is_active = False
                    fiyat.poz.save(update_fields=["is_active"])
                    ozet.arsivlenen_poz += 1

    return ozet


def import_yapi_sinifi_verisi(tenant: Tenant, satirlar: list[dict]) -> ImportOzeti:
    """Yapı sınıfı yıllık birim maliyet satırlarını içe aktarır.

    Satır sütunları: sinif_kodu, yil, birim_maliyet. sinif_kodu normalize
    edilir ("4A" → "IV-A"); aynı (sinif_kodu, yil) güncellenir, farklı yıl
    yeni versiyon kaydıdır. Tek transaction, fail-fast, silme yok.
    """
    ozet = ImportOzeti(satir_sayisi=len(satirlar))
    if not satirlar:
        raise ValueError("İçe aktarılacak satır yok.")

    with transaction.atomic():
        for satir_no, satir in enumerate(satirlar, start=1):
            if _satir_bos(satir):
                continue

            ham = _zorunlu_metin(satir, "sinif_kodu", satir_no)
            try:
                sinif_kodu = normalize_yapi_sinifi(ham)
            except ValueError as exc:
                raise ImportHatasi(f"{satir_no}. satır: {exc}") from exc

            yil_metni = _zorunlu_metin(satir, "yil", satir_no)
            try:
                yil = int(yil_metni)
            except ValueError as exc:
                raise ImportHatasi(
                    f"{satir_no}. satır: 'yil' alanı sayı olmalıdır: {yil_metni!r}"
                ) from exc
            birim_maliyet = _pozitif_decimal(satir, "birim_maliyet", satir_no)

            kayit, olustu = YapiSinifiBirimMaliyet.objects.update_or_create(
                tenant=tenant,
                sinif_kodu=sinif_kodu,
                yil=yil,
                defaults={"birim_maliyet": birim_maliyet, "is_active": True},
            )
            if olustu:
                ozet.sinif_olusturulan += 1
            else:
                ozet.sinif_guncellenen += 1

    return ozet


def csv_satirlari_oku(dosya_yolu: str, ayrac: str = ";") -> list[dict]:
    """CSV'yi utf-8-sig (Excel BOM toleranslı) okuyup satır sözlükleri döner."""
    from csv import DictReader

    with open(dosya_yolu, newline="", encoding="utf-8-sig") as fh:
        reader = DictReader(fh, delimiter=ayrac)
        if reader.fieldnames:
            reader.fieldnames = [name.strip() for name in reader.fieldnames]
        return list(reader)
