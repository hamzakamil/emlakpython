from django.test import TestCase

"""Gayrimenkul modülü testleri — model + API + tenant izolasyonu."""

from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from construction.models import Proje
from tenants.models import Tenant
from users.models import User, UserRole

from .models import Ada, KatKarsiligiSenaryo, MalikMutabakati, Parsel, RealEstate


class RealEstateBase(TestCase):
    def setUp(self):
        self.t1 = Tenant.objects.create(name="Firma 1", slug="re-firma-1")
        self.t2 = Tenant.objects.create(name="Firma 2", slug="re-firma-2")
        self.user = User.objects.create_user(
            username="re-u1", password="x", email="re-u1@example.com",
            tenant=self.t1, role=UserRole.PROJE_YONETICISI,
        )
        self.proje = Proje.objects.create(
            tenant=self.t1, proje_kodu="PRJ-1", ad="Erciyes Konut"
        )

    def _auth(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        return client


class ModelTests(RealEstateBase):
    def test_konum_tenant_icinde_unique(self):
        RealEstate.objects.create(
            tenant=self.t1, proje=self.proje, blok="A", kat="3", daire_no="12"
        )
        with self.assertRaises(IntegrityError):
            RealEstate.objects.create(
                tenant=self.t1, proje=self.proje, blok="A", kat="3", daire_no="12"
            )


class ApiTests(RealEstateBase):
    def test_proje_ile_iliski_kurulur(self):
        payload = {
            "ad": "Daire-12",
            "proje": self.proje.pk,
            "blok": "A",
            "kat": "3",
            "daire_no": "12",
            "brut_m2": "95.50",
            "durum": "available",
        }
        response = self._auth().post("/api/v1/real-estate/gayrimenkuller/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["proje_kodu"], "PRJ-1")
        self.assertEqual(body["data"]["proje"], self.proje.pk)
        # tenant istek sahibinden atandı
        self.assertEqual(body["data"]["tenant"], self.t1.pk)

    def test_liste_zarf_ve_tenant(self):
        RealEstate.objects.create(tenant=self.t1, proje=self.proje, blok="A", kat="1", daire_no="1")
        RealEstate.objects.create(tenant=self.t2, proje=None, blok="B", kat="1", daire_no="1")
        response = self._auth().get("/api/v1/real-estate/gayrimenkuller/")
        self.assertEqual(response.status_code, 200)
        results = response.json()["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["blok"], "A")


class ParcelPhase3Tests(TestCase):
    def setUp(self):
        self.t1 = Tenant.objects.create(name="Ada Firması 1", slug="ada-firma-1")
        self.t2 = Tenant.objects.create(name="Ada Firması 2", slug="ada-firma-2")
        self.user = User.objects.create_user(
            username="ada-user",
            password="x",
            email="ada@example.com",
            tenant=self.t1,
            role=UserRole.PROJE_YONETICISI,
        )
        self.ada = Ada.objects.create(
            tenant=self.t1,
            ada_no="123",
            mahalle="Kızılay",
            ilce="Çankaya",
            il="Ankara",
        )

    def _auth(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        return client

    def test_parsel_ada_ve_tenant_bicimi_kayit_edilir(self):
        payload = {
            "ada": self.ada.pk,
            "parsel_no": "25",
            "pafta": "A-1",
            "alan_m2": "650.00",
            "imar_durumu": "imara_uygun",
            "kat_karsiligi_orani": "35.00",
            "malik_sayisi": 3,
            "is_active": True,
        }
        response = self._auth().post("/api/v1/real-estate/parseller/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["tenant"], self.t1.pk)
        self.assertEqual(body["data"]["ada"], self.ada.pk)
        self.assertEqual(body["data"]["parsel_no"], "25")

    def test_ayni_parsel_aynı_ada_ve_tenant_icinde_benzersizdir(self):
        Parsel.objects.create(
            tenant=self.t1,
            ada=self.ada,
            parsel_no="25",
            pafta="A-1",
            alan_m2="650.00",
            imar_durumu="imara_uygun",
        )
        with self.assertRaises(IntegrityError):
            Parsel.objects.create(
                tenant=self.t1,
                ada=self.ada,
                parsel_no="25",
                pafta="A-1",
                alan_m2="700.00",
                imar_durumu="imarli",
            )

    def test_parsel_listesi_sadece_aktif_tenanti_gorur(self):
        Ada.objects.create(tenant=self.t2, ada_no="456", mahalle="Keçiören", ilce="Keçiören", il="Ankara")
        Parsel.objects.create(
            tenant=self.t1,
            ada=self.ada,
            parsel_no="25",
            pafta="A-1",
            alan_m2="650.00",
            imar_durumu="imara_uygun",
        )
        Parsel.objects.create(
            tenant=self.t2,
            ada=Ada.objects.get(tenant=self.t2, ada_no="456"),
            parsel_no="12",
            pafta="B-2",
            alan_m2="500.00",
            imar_durumu="imarli",
        )
        response = self._auth().get("/api/v1/real-estate/parseller/")
        self.assertEqual(response.status_code, 200)
        results = response.json()["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["parsel_no"], "25")


class KatKarsiligiSenaryoTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Kat Karşılığı A.Ş.", slug="kat-karsiligi")
        self.user = User.objects.create_user(
            username="kat-user",
            password="x",
            email="kat@example.com",
            tenant=self.tenant,
            role=UserRole.PROJE_YONETICISI,
        )
        self.ada = Ada.objects.create(
            tenant=self.tenant,
            ada_no="77",
            mahalle="Yenimahalle",
            ilce="Çankaya",
            il="Ankara",
        )
        self.parsel = Parsel.objects.create(
            tenant=self.tenant,
            ada=self.ada,
            parsel_no="10",
            pafta="PAFTA-3",
            alan_m2="1200.00",
            imar_durumu="imarli",
            kat_karsiligi_orani="35.00",
            malik_sayisi=4,
        )

    def _auth(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        return client

    def test_kat_karsiligi_senaryosu_olusturulur(self):
        payload = {
            "parsel": self.parsel.pk,
            "senaryo_adi": "Senaryo A",
            "arsa_pay_orani": "35.00",
            "kat_karsiligi_orani": "60.00",
            "bagimsiz_bolum_m2": "220.00",
            "toplam_birim_sayisi": 12,
            "is_active": True,
        }
        response = self._auth().post("/api/v1/real-estate/kat-karsiligi-senaryolari/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["parsel"], self.parsel.pk)
        self.assertEqual(body["data"]["senaryo_adi"], "Senaryo A")

    def test_senaryo_oran_ve_alan_dogrulamasi(self):
        response = self._auth().post(
            "/api/v1/real-estate/kat-karsiligi-senaryolari/",
            {
                "parsel": self.parsel.pk,
                "senaryo_adi": "Geçersiz",
                "arsa_pay_orani": "101",
                "kat_karsiligi_orani": "50",
                "bagimsiz_bolum_m2": "0",
                "toplam_birim_sayisi": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_malik_mutabakati_oy_durumu_kaydedilir(self):
        senaryo = KatKarsiligiSenaryo.objects.create(
            tenant=self.tenant,
            parsel=self.parsel,
            senaryo_adi="Senaryo B",
            arsa_pay_orani="35.00",
            kat_karsiligi_orani="65.00",
            bagimsiz_bolum_m2="240.00",
            toplam_birim_sayisi=10,
        )
        payload = {
            "senaryo": senaryo.pk,
            "malik_adi": "Ahmet Yılmaz",
            "pay_orani": "50.00",
            "oy_durumu": "kabul",
            "notlar": "Onay verdi.",
        }
        response = self._auth().post("/api/v1/real-estate/malik-mutabakatlari/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["malik_adi"], "Ahmet Yılmaz")
        self.assertEqual(body["data"]["oy_durumu"], "kabul")

    def test_malik_paylari_yuzde_yuzu_asamaz(self):
        senaryo = KatKarsiligiSenaryo.objects.create(
            tenant=self.tenant, parsel=self.parsel, senaryo_adi="Senaryo C",
            arsa_pay_orani="35.00", kat_karsiligi_orani="65.00",
            bagimsiz_bolum_m2="240.00", toplam_birim_sayisi=10,
        )
        MalikMutabakati.objects.create(
            tenant=self.tenant, senaryo=senaryo, malik_adi="Mevcut Malik",
            pay_orani="80.00",
        )
        response = self._auth().post(
            "/api/v1/real-estate/malik-mutabakatlari/",
            {"senaryo": senaryo.pk, "malik_adi": "Yeni Malik", "pay_orani": "20.01", "oy_durumu": "bekliyor"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
