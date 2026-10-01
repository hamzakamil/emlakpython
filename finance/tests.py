"""Finans modülü testleri — kasa/banka, işlem iptal deseni, tenant izolasyonu."""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User, UserRole

from .models import CekSenet, Fatura, FaturaKalemi, FinansalIslem, KasaBankaHesabi, VergiProfili


class FinanceBase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Finans A.Ş.", slug="finans-as")
        self.diger = Tenant.objects.create(name="Komşu Fin. Ltd.", slug="komsu-fin")
        import uuid
        unique = uuid.uuid4().hex[:8]
        self.finansci = User.objects.create_user(
            username=f"finans_{unique}", password="x", email=f"fin_{unique}@f.com",
            tenant=self.tenant, role=UserRole.FINANS,
        )
        self.satisci = User.objects.create_user(
            username=f"satis_{unique}", password="x", email=f"sat_{unique}@f.com",
            tenant=self.tenant, role=UserRole.SATIS,
        )
        self.kasa = KasaBankaHesabi.objects.create(
            tenant=self.tenant, kod="K-01", ad="Merkez Kasa", tip="kasa",
        )

    def _istemci(self, kullanici):
        istemci = APIClient()
        istemci.force_authenticate(user=kullanici)
        return istemci


class KasaTests(FinanceBase):
    def test_kasa_iban_maskeli_doner(self):
        istemci = self._istemci(self.finansci)
        yanit = istemci.post(
            "/api/v1/finance/kasa-banka-hesaplari/",
            {"kod": "B-01", "ad": "Ziraat", "tip": "banka",
             "iban": "TR120001000000000000000001"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 201)
        veri = yanit.json()["data"]
        self.assertNotIn("iban", veri)
        self.assertTrue(veri["iban_maskeli"].startswith("TR12"))

    def test_kasa_kodu_tenant_icinde_unique(self):
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            KasaBankaHesabi.objects.create(tenant=self.tenant, kod="K-01", ad="Kopya")


class IslemTests(FinanceBase):
    def test_islem_olustur_iptal_et_silinemez(self):
        istemci = self._istemci(self.finansci)
        yanit = istemci.post(
            "/api/v1/finance/finansal-islemler/",
            {"hesap": self.kasa.pk, "yon": "gider", "tutar": "500.00",
             "islem_tarihi": "2026-03-05", "aciklama": "Akaryakıt"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 201)
        islem_id = yanit.json()["data"]["id"]
        self.assertEqual(
            istemci.delete(f"/api/v1/finance/finansal-islemler/{islem_id}/").status_code, 400,
        )
        iptal = istemci.post(f"/api/v1/finance/finansal-islemler/{islem_id}/iptal/", format="json")
        self.assertEqual(iptal.status_code, 200)
        islem = FinansalIslem.objects.get(pk=islem_id)
        self.assertTrue(islem.is_cancelled)
        # İptal edilmiş işlem tekrar iptal edilemez
        self.assertEqual(
            istemci.post(f"/api/v1/finance/finansal-islemler/{islem_id}/iptal/").status_code, 400,
        )

    def test_satis_rolu_islem_acamaz(self):
        yanit = self._istemci(self.satisci).post(
            "/api/v1/finance/finansal-islemler/",
            {"hesap": self.kasa.pk, "yon": "gelir", "tutar": "10.00",
             "islem_tarihi": "2026-03-05"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 403)

    def test_tenant_izolasyonu(self):
        diger_kasa = KasaBankaHesabi.objects.create(tenant=self.diger, kod="K-01", ad="Kasa")
        FinansalIslem.objects.create(
            tenant=self.diger, hesap=diger_kasa, yon="gelir",
            tutar=Decimal("999.00"), islem_tarihi=date(2026, 3, 1),
        )
        istemci = self._istemci(self.finansci)
        veri = istemci.get("/api/v1/finance/finansal-islemler/").json()["data"]
        self.assertEqual(veri["count"], 0)
        kasalar = istemci.get("/api/v1/finance/kasa-banka-hesaplari/").json()["data"]
        self.assertEqual(kasalar["count"], 1)


class CekSenetTests(FinanceBase):
    def test_cek_senet_olusturulur_ve_iptal_fiziksel_silme_yoktur(self):
        istemci = self._istemci(self.finansci)
        yanit = istemci.post(
            "/api/v1/finance/cek-senetler/",
            {
                "tur": "cek",
                "numara": "CK-001",
                "tutar": "12500.00",
                "vade_tarihi": "2026-12-15",
                "durum": "bekliyor",
            },
            format="json",
        )
        self.assertEqual(yanit.status_code, 201, yanit.content)
        kayit_id = yanit.json()["data"]["id"]
        silme = istemci.delete(f"/api/v1/finance/cek-senetler/{kayit_id}/")
        self.assertEqual(silme.status_code, 200)
        self.assertEqual(CekSenet.objects.get(pk=kayit_id).durum, CekSenet.Durum.IPTAL)


class FaturaVergiTests(FinanceBase):
    def test_kdv_tevkifat_ve_stopaj_satir_toplamina_yansir(self):
        fatura = Fatura.objects.create(
            tenant=self.tenant, No="F-VERGI-001", tarih=date(2026, 3, 5),
            tutar=Decimal("1.00"),
        )
        kalem = FaturaKalemi.objects.create(
            fatura=fatura, aciklama="İnşaat hizmeti", miktar=Decimal("10"),
            birim_fiyat=Decimal("100"), kdv_orani=Decimal("20"),
            tevkifat_orani=Decimal("50"), stopaj_orani=Decimal("10"),
        )
        self.assertEqual(kalem.ara_toplam, Decimal("1000.00"))
        self.assertEqual(kalem.kdv_tutari, Decimal("200.00"))
        self.assertEqual(kalem.tevkifat_tutari, Decimal("100.00"))
        self.assertEqual(kalem.stopaj_tutari, Decimal("100.00"))
        self.assertEqual(kalem.satir_toplami, Decimal("1000.00"))

    def test_vergi_profili_tenant_izole_listelenir_ve_pasife_alinir(self):
        VergiProfili.objects.create(
            tenant=self.tenant, kod="CUSTOM", ad="Özel profil",
            kdv_orani=Decimal("20"), tevkifat_orani=Decimal("50"),
        )
        VergiProfili.objects.create(
            tenant=self.diger, kod="DIGER", ad="Diğer profil",
        )
        istemci = self._istemci(self.finansci)
        veri = istemci.get("/api/v1/finance/vergi-profilleri/").json()["data"]
        self.assertEqual(veri["count"], 4)
        profil_id = next(x["id"] for x in veri["results"] if x["kod"] == "CUSTOM")
        silme = istemci.delete(f"/api/v1/finance/vergi-profilleri/{profil_id}/")
        self.assertEqual(silme.status_code, 200)
        self.assertFalse(VergiProfili.objects.get(pk=profil_id).is_active)


class DogalDilRaporTests(FinanceBase):
    def test_gelir_gider_sorusuna_tenant_kapsamli_ozet_doner(self):
        FinansalIslem.objects.create(
            tenant=self.tenant, hesap=self.kasa, yon="gelir",
            tutar=Decimal("1250.00"), islem_tarihi=date(2026, 9, 18),
        )
        FinansalIslem.objects.create(
            tenant=self.tenant, hesap=self.kasa, yon="gider",
            tutar=Decimal("250.00"), islem_tarihi=date(2026, 9, 18),
        )
        yanit = self._istemci(self.finansci).post(
            "/api/v1/finance/raporlar/dogal-dil/",
            {"soru": "Gelir ve gider durumum nedir?"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["data"]["metrikler"]["net"], "1000.00")

    def test_desteklenmeyen_soru_acik_hata_doner(self):
        yanit = self._istemci(self.finansci).post(
            "/api/v1/finance/raporlar/dogal-dil/",
            {"soru": "Stok seviyesi nedir?"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 400)
        self.assertIn("soru", yanit.json()["errors"])


class OdemeIptalTests(FinanceBase):
    """FAZ 6B — ödeme muhasebesi + iptal ters kayıtları."""

    def _odeme_ac(self, tutar="10000.00"):
        from datetime import date

        from cari.models import Cari

        from .models import FinansalIslem
        from .services.entegrasyon import finansal_islem_muhasebelestir

        cari = Cari.objects.create(
            tenant=self.tenant, ad="Ödeme Cari", tip="tedarikci", tur="kurumsal"
        )
        karsilik = self._karsilik_hesap()
        islem = FinansalIslem.objects.create(
            tenant=self.tenant, hesap=self.kasa, cari=cari,
            yon=FinansalIslem.Yon.GIDER, tutar=Decimal(tutar),
            islem_tarihi=date(2026, 9, 18),
        )
        finansal_islem_muhasebelestir(islem, karsilik_hesap_id=karsilik.pk)
        islem.refresh_from_db()
        return islem

    def _karsilik_hesap(self):
        from accounting.models import HesapPlani

        hesap, _ = HesapPlani.objects.get_or_create(
            tenant=self.tenant, kod="770",
            defaults={"ad": "Genel Yönetim Giderleri", "tip": "gider"},
        )
        return hesap

    def test_odeme_muhasebesi(self):
        from accounting.models import MuhasebeFisi

        islem = self._odeme_ac()
        fis = MuhasebeFisi.objects.get(pk=islem.muhasebe_fisi_id)
        bacaklar = {s.hesap.kod: (s.borc, s.alacak) for s in fis.satirlar.all()}
        self.assertEqual(bacaklar["K-01"][1], Decimal("10000.00"))
        self.assertEqual(bacaklar["770"][0], Decimal("10000.00"))

    def test_odeme_iptali_ters_kayit(self):
        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket

        islem = self._odeme_ac()
        yanit = self._istemci(self.finansci).post(
            f"/api/v1/finance/finansal-islemler/{islem.pk}/iptal/"
        )
        self.assertEqual(yanit.status_code, 200)
        islem.refresh_from_db()
        self.assertTrue(islem.is_cancelled)
        ters_cari = CariHareket.objects.get(finansal_islem=islem)
        self.assertEqual(ters_cari.yon, CariHareket.Yon.BORC)
        self.assertEqual(ters_cari.tutar, Decimal("10000.00"))
        ters_fis = MuhasebeFisi.objects.get(
            tenant=self.tenant, fis_no=f"FINTR-{islem.pk}"
        )
        bacaklar = {s.hesap.kod: (s.borc, s.alacak) for s in ters_fis.satirlar.all()}
        self.assertEqual(bacaklar["K-01"][0], Decimal("10000.00"))
        self.assertEqual(bacaklar["770"][1], Decimal("10000.00"))
        original = MuhasebeFisi.objects.get(pk=islem.muhasebe_fisi_id)
        self.assertEqual(original.durum, "iptal")

    def test_ikinci_iptal_reddedilir(self):
        from cari.models import CariHareket

        islem = self._odeme_ac()
        istemci = self._istemci(self.finansci)
        self.assertEqual(
            istemci.post(f"/api/v1/finance/finansal-islemler/{islem.pk}/iptal/").status_code,
            200,
        )
        ikinci = istemci.post(f"/api/v1/finance/finansal-islemler/{islem.pk}/iptal/")
        self.assertEqual(ikinci.status_code, 400)
        self.assertEqual(
            CariHareket.objects.filter(finansal_islem=islem).count(), 1
        )

    def test_iptal_rollback(self):
        from unittest.mock import patch

        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket

        islem = self._odeme_ac()
        with patch(
            "finance.services.entegrasyon.FisSatiri.objects.create",
            side_effect=ValueError("iptal fisi patlatıldı"),
        ):
            with self.assertRaises(ValueError):
                self._istemci(self.finansci).post(
                    f"/api/v1/finance/finansal-islemler/{islem.pk}/iptal/"
                )
        islem.refresh_from_db()
        self.assertFalse(islem.is_cancelled)
        self.assertFalse(
            CariHareket.objects.filter(finansal_islem=islem).exists()
        )
        self.assertFalse(
            MuhasebeFisi.objects.filter(
                tenant=self.tenant, fis_no=f"FINTR-{islem.pk}"
            ).exists()
        )


class KarmaKdvTests(FinanceBase):
    """FAZ 6C — fatura kalemi bazında karışık KDV oranları (API seviyesi)."""

    def _fatura_ac(self, kalemler, no):
        yanit = self._istemci(self.finansci).post(
            "/api/v1/finance/faturalar/",
            {"No": no, "tarih": "2026-03-05", "tutar": "1.00",
             "kalemler": kalemler},
            format="json",
        )
        self.assertEqual(yanit.status_code, 201, yanit.content)
        return yanit.json()["data"]

    def test_tek_oran_yirmi(self):
        veri = self._fatura_ac(
            [{"aciklama": "K1", "miktar": "1", "birim_fiyat": "1000.00",
              "kdv_orani": "20"}],
            "KDV-20",
        )
        self.assertEqual(veri["matrah"], "1000.00")
        self.assertEqual(veri["kdv"], "200.00")
        self.assertEqual(veri["odenecek"], "1200.00")

    def test_tek_oran_on(self):
        veri = self._fatura_ac(
            [{"aciklama": "K1", "miktar": "1", "birim_fiyat": "500.00",
              "kdv_orani": "10"}],
            "KDV-10",
        )
        self.assertEqual(veri["matrah"], "500.00")
        self.assertEqual(veri["kdv"], "50.00")
        self.assertEqual(veri["odenecek"], "550.00")

    def test_tek_oran_sifir(self):
        veri = self._fatura_ac(
            [{"aciklama": "K1", "miktar": "1", "birim_fiyat": "200.00",
              "kdv_orani": "0"}],
            "KDV-0",
        )
        self.assertEqual(veri["matrah"], "200.00")
        self.assertEqual(veri["kdv"], "0.00")
        self.assertEqual(veri["odenecek"], "200.00")

    def test_karisik_yirmi_on(self):
        veri = self._fatura_ac(
            [{"aciklama": "K1", "miktar": "1", "birim_fiyat": "1000.00",
              "kdv_orani": "20"},
             {"aciklama": "K2", "miktar": "1", "birim_fiyat": "500.00",
              "kdv_orani": "10"}],
            "KDV-20-10",
        )
        self.assertEqual(veri["matrah"], "1500.00")
        self.assertEqual(veri["kdv"], "250.00")
        self.assertEqual(veri["odenecek"], "1750.00")

    def test_karisik_yirmi_on_sifir(self):
        veri = self._fatura_ac(
            [{"aciklama": "K1", "miktar": "1", "birim_fiyat": "1000.00",
              "kdv_orani": "20"},
             {"aciklama": "K2", "miktar": "1", "birim_fiyat": "500.00",
              "kdv_orani": "10"},
             {"aciklama": "K3", "miktar": "1", "birim_fiyat": "200.00",
              "kdv_orani": "0"}],
            "KDV-20-10-0",
        )
        self.assertEqual(veri["matrah"], "1700.00")
        self.assertEqual(veri["kdv"], "250.00")
        self.assertEqual(veri["odenecek"], "1950.00")

    def test_acik_oran_profili_ezer(self):
        VergiProfili.objects.create(
            tenant=self.tenant, kod="VARSAYILAN", ad="Varsayılan",
            kdv_orani=Decimal("10"),
        )
        veri = self._fatura_ac(
            [{"aciklama": "K1", "miktar": "1", "birim_fiyat": "1000.00",
              "kdv_orani": "20"}],
            "KDV-OVERRIDE",
        )
        self.assertEqual(veri["kdv"], "200.00")
        self.assertEqual(veri["odenecek"], "1200.00")

    def test_profil_degisiminden_sonra_gecmis_fatura_ve_iade_sabit(self):
        veri = self._fatura_ac(
            [{"aciklama": "K1", "miktar": "1", "birim_fiyat": "1000.00",
              "kdv_orani": "10"}],
            "KDV-SNAPSHOT",
        )
        fatura_id = veri["id"]
        VergiProfili.objects.create(
            tenant=self.tenant, kod="VARSAYILAN", ad="Varsayılan",
            kdv_orani=Decimal("25"),
        )
        taze = self._istemci(self.finansci).get(
            f"/api/v1/finance/faturalar/{fatura_id}/"
        ).json()["data"]
        self.assertEqual(taze["matrah"], "1000.00")
        self.assertEqual(taze["kdv"], "100.00")
        self.assertEqual(taze["odenecek"], "1100.00")
        iade = self._istemci(self.finansci).post(
            f"/api/v1/finance/faturalar/{fatura_id}/iade-olustur/", format="json"
        )
        self.assertEqual(iade.status_code, 201, iade.content)
        self.assertEqual(iade.json()["data"]["kdv"], "100.00")
        self.assertEqual(iade.json()["data"]["odenecek"], "1100.00")


class FaturaSorguTests(FinanceBase):
    """FAZ 6E — fatura N+1 regresyonu: sabit query sayısı + sonuç doğruluğu."""

    def _faturalar_ac(self, n=30, kalem=3):
        faturas = [
            Fatura(
                tenant=self.tenant, No=f"Q-{i:04d}", tarih=date(2026, 3, 5),
                tutar=Decimal("360.00"),
            )
            for i in range(n)
        ]
        Fatura.objects.bulk_create(faturas)
        faturas = list(Fatura.objects.filter(tenant=self.tenant).order_by("id"))
        FaturaKalemi.objects.bulk_create([
            FaturaKalemi(
                fatura=f, aciklama=f"K{k}", miktar=Decimal("1"),
                birim="ADET", birim_fiyat=Decimal("100"),
                kdv_orani=Decimal("20"),
            )
            for f in faturas for k in range(kalem)
        ])
        return faturas

    def test_liste_query_sabiti(self):
        self._faturalar_ac()
        with self.assertNumQueries(4):
            yanit = self._istemci(self.finansci).get("/api/v1/finance/faturalar/")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["data"]["count"], 30)

    def test_liste_sonuclari_dogru(self):
        self._faturalar_ac(n=5, kalem=2)
        veri = self._istemci(self.finansci).get(
            "/api/v1/finance/faturalar/"
        ).json()["data"]["results"]
        self.assertEqual(len(veri), 5)
        for satir in veri:
            self.assertEqual(satir["matrah"], "200.00")
            self.assertEqual(satir["kdv"], "40.00")
            self.assertEqual(satir["odenecek"], "240.00")
            self.assertEqual(len(satir["kalemler"]), 2)

    def test_detay_query_sabiti_ve_dogruluk(self):
        (fatura,) = self._faturalar_ac(n=1, kalem=3)
        with self.assertNumQueries(3):
            yanit = self._istemci(self.finansci).get(
                f"/api/v1/finance/faturalar/{fatura.pk}/"
            )
        self.assertEqual(yanit.status_code, 200)
        veri = yanit.json()["data"]
        self.assertEqual(veri["matrah"], "300.00")
        self.assertEqual(veri["kdv"], "60.00")
        self.assertEqual(veri["odenecek"], "360.00")
