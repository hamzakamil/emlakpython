from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User, UserRole

from .models import (
    Hakedis,
    HakedisSatiri,
    Malzeme,
    Poz,
    PozFiyat,
    PozGrubu,
    PozMalzemeIliskisi,
    PozPlan,
    Proje,
    YapiSinifiBirimMaliyet,
    SantiyeCheckIn,
    MalzemeHareketi,
    Tedarikci,
    TedarikciTeklifi,
    EKB,
    Mahal,
    MahalElemani,
)
from .services import (
    gantt_verisi,
    hakedis_onayla,
    hakedis_satirlari_olustur,
    hakedis_toplami,
    poz_birim_fiyati,
    poz_toplam_tutar,
    s_egrisi_raporu,
    proje_kar_zarar,
    metraj_kontrolu,
    fiyat_anomalilerini_bul,
)

import os
from io import StringIO
from tempfile import NamedTemporaryFile

from django.core.management import call_command
from django.core.management.base import CommandError

from .imports import (
    ImportHatasi,
    csv_satirlari_oku,
    import_poz_verisi,
    import_yapi_sinifi_verisi,
    normalize_yapi_sinifi,
)


class ConstructionBase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="İnşaat A.Ş.", slug="insaat")
        import uuid
        unique = uuid.uuid4().hex[:8]
        self.editor = User.objects.create_user(
            username=f"maliyet_{unique}", password="x", email=f"maliyet_{unique}@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )
        self.reader = User.objects.create_user(
            username=f"santiye_{unique}", password="x", email=f"santiye_{unique}@example.com",
            tenant=self.tenant, role=UserRole.SANTIYE_SEFI,
        )
        self.grup = PozGrubu.objects.create(tenant=self.tenant, kod="BET", ad="Beton İşleri")
        self.poz = Poz.objects.create(
            tenant=self.tenant, poz_no="P-1001", ad="C30 Beton dökümü", birim="m³", grup=self.grup
        )
        self.malzeme = Malzeme.objects.create(
            tenant=self.tenant, malzeme_kodu="CMNT", ad="Çimento", birim="ton"
        )


class ModelConstraintTests(ConstructionBase):
    def test_ekb_tarihleri_dogrulanir(self):
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="EKB-1", ad="Enerji Projesi")
        belge = EKB(
            tenant=self.tenant, proje=proje, belge_no="EKB-001",
            duzenlenme_tarihi=date(2026, 9, 10), gecerlilik_tarihi=date(2026, 9, 1),
        )
        with self.assertRaises(ValidationError):
            belge.full_clean()

    def test_ekb_belge_no_tenant_icinde_unique(self):
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="EKB-2", ad="Enerji Projesi")
        EKB.objects.create(tenant=self.tenant, proje=proje, belge_no="EKB-002")
        with self.assertRaises(IntegrityError):
            EKB.objects.create(tenant=self.tenant, proje=proje, belge_no="EKB-002")

    def test_miktar_negatif_db_reddeder(self):
        with self.assertRaises(IntegrityError):
            PozMalzemeIliskisi.objects.create(
                tenant=self.tenant, poz=self.poz, malzeme=self.malzeme, miktar=Decimal("-1.0000")
            )

    def test_poz_no_tenant_icinde_unique(self):
        with self.assertRaises(IntegrityError):
            Poz.objects.create(
                tenant=self.tenant, poz_no="P-1001", ad="Tekrar", birim="m", grup=self.grup
            )

    def test_yapi_sinifi_yil_unique(self):
        YapiSinifiBirimMaliyet.objects.create(
            tenant=self.tenant, sinif_kodu="IV-A", yil=2026, birim_maliyet=Decimal("15000.00")
        )
        with self.assertRaises(IntegrityError):
            YapiSinifiBirimMaliyet.objects.create(
                tenant=self.tenant, sinif_kodu="IV-A", yil=2026, birim_maliyet=Decimal("16000.00")
            )


class ServiceTests(ConstructionBase):
    def test_poz_birim_fiyati_aktif_alir(self):
        PozFiyat.objects.create(
            tenant=self.tenant, poz=self.poz, yil=2026, birim_fiyat=Decimal("1250.50")
        )
        self.assertEqual(poz_birim_fiyati(self.poz, 2026), Decimal("1250.50"))
        self.assertIsNone(poz_birim_fiyati(self.poz, 2025))

    def test_poz_toplam_tutar_decimal_hesaplar(self):
        PozFiyat.objects.create(
            tenant=self.tenant, poz=self.poz, yil=2026, birim_fiyat=Decimal("1250.50")
        )
        self.assertEqual(poz_toplam_tutar(self.poz, 2026, Decimal("10")), Decimal("12505.00"))

    def test_poz_toplam_tutar_fiyat_yoksa_none(self):
        self.assertIsNone(poz_toplam_tutar(self.poz, 2026, Decimal("10")))

    def test_poz_toplam_tutar_float_reddedilir(self):
        with self.assertRaises(TypeError):
            poz_toplam_tutar(self.poz, 2026, 10.0)

    def test_poz_toplam_tutar_sifir_reddedilir(self):
        with self.assertRaises(ValueError):
            poz_toplam_tutar(self.poz, 2026, Decimal("0"))


class ApiTests(ConstructionBase):
    def _auth_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def _poz_payload(self):
        return {
            "poz_no": "P-2001",
            "ad": "Demir işçiliği",
            "birim": "kg",
            "grup": self.grup.pk,
            "tenant": self.tenant.pk,
        }

    def test_santiye_sefi_okur(self):
        client = self._auth_client(self.reader)
        response = client.get("/api/v1/construction/pozlar/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertIn("results", body["data"])

    def test_santiye_sefi_yazamaz(self):
        client = self._auth_client(self.reader)
        response = client.post("/api/v1/construction/pozlar/", self._poz_payload(), format="json")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()["success"])

    def test_maliyet_muhendisi_yazar(self):
        client = self._auth_client(self.editor)
        response = client.post("/api/v1/construction/pozlar/", self._poz_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["poz_no"], "P-2001")
        # tenant, istek sahibinden atanır (izole ViewSet)
        self.assertEqual(body["data"]["tenant"], self.tenant.pk)

    def test_anasayfa_unauth_401(self):
        client = APIClient()
        response = client.get("/api/v1/construction/pozlar/")
        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])

    def test_ekb_olustur_filtrele_ve_arsivle(self):
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="EKB-API", ad="EKB API Projesi")
        client = self._auth_client(self.editor)
        response = client.post(
            "/api/v1/construction/ekb/",
            {
                "proje": proje.pk, "belge_no": "EKB-API-001", "durum": "onaylandi",
                "enerji_sinifi": "B", "duzenlenme_tarihi": "2026-01-01",
                "gecerlilik_tarihi": "2031-01-01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        belge_id = response.json()["data"]["id"]
        self.assertEqual(
            client.get("/api/v1/construction/ekb/?enerji_sinifi=B").json()["data"]["count"], 1
        )
        self.assertEqual(client.delete(f"/api/v1/construction/ekb/{belge_id}/").status_code, 200)
        self.assertFalse(EKB.objects.get(pk=belge_id).is_active)

    def test_ekb_arsiv_varsayilan_gizli_ve_ozet_doner(self):
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="EKB-KPI", ad="KPI Projesi")
        EKB.objects.create(
            tenant=self.tenant, proje=proje, belge_no="EKB-AKTIF",
            durum="onaylandi", gecerlilik_tarihi=date.today() + timedelta(days=10),
        )
        EKB.objects.create(
            tenant=self.tenant, proje=proje, belge_no="EKB-ARSIV", is_active=False,
        )
        client = self._auth_client(self.editor)
        self.assertEqual(client.get("/api/v1/construction/ekb/").json()["data"]["count"], 1)
        ozet = client.get("/api/v1/construction/ekb/ozet/").json()["data"]
        self.assertEqual(ozet["toplam"], 1)
        self.assertEqual(ozet["onayli"], 1)
        self.assertEqual(ozet["otuz_gun_icinde"], 1)
        self.assertEqual(
            client.get("/api/v1/construction/ekb/?is_active=false").json()["data"]["count"], 1
        )

    def test_qr_malzeme_hareketi_ve_tenant_izolasyonu(self):
        client = self._auth_client(self.editor)
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="P-QR", ad="QR Şantiye")
        response = client.post(
            "/api/v1/construction/malzeme-hareketleri/",
            {
                "proje": proje.pk, "yon": "giris", "miktar": "2.5000",
                "qr_kodu": self.malzeme.qr_kodu,
                "gerceklesme_zamani": "2026-09-18T10:00:00Z",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["malzeme"], self.malzeme.pk)
        self.assertEqual(response.json()["data"]["birim"], "ton")

    def test_checkin_kullanici_istekten_atanir(self):
        client = self._auth_client(self.reader)
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="P-IN", ad="Mobil Şantiye")
        response = client.post(
            "/api/v1/construction/santiye-checkinleri/",
            {"proje": proje.pk, "giris_zamani": "2026-09-18T08:00:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        client = self._auth_client(self.editor)
        response = client.post(
            "/api/v1/construction/santiye-checkinleri/",
            {"proje": proje.pk, "giris_zamani": "2026-09-18T08:00:00Z"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["kullanici"], self.editor.pk)


class TedarikciTeklifiApiTests(ConstructionBase):
    def setUp(self):
        super().setUp()
        self.proje = Proje.objects.create(
            tenant=self.tenant, proje_kodu="P-TEKLIF", ad="Teklif Projesi"
        )
        self.tedarikci_a = Tedarikci.objects.create(
            tenant=self.tenant, firma_adi="A Tedarik", firma_kodu="TED-A"
        )
        self.tedarikci_b = Tedarikci.objects.create(
            tenant=self.tenant, firma_adi="B Tedarik", firma_kodu="TED-B"
        )

    def _client(self, user=None):
        client = APIClient()
        client.force_authenticate(user=user or self.editor)
        return client

    def _payload(self, tedarikci=None, fiyat="125.50"):
        return {
            "proje": self.proje.pk,
            "malzeme": self.malzeme.pk,
            "tedarikci": (tedarikci or self.tedarikci_a).pk,
            "miktar": "10.0000",
            "birim_fiyat": fiyat,
            "durum": "geldi",
            "gecerlilik_tarihi": "2026-12-31",
            "notlar": "Nakliye dahil",
        }

    def test_create_list_tenant_isolation_and_total(self):
        response = self._client().post(
            "/api/v1/construction/tedarikci-teklifleri/",
            self._payload(),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["toplam_tutar"], "1255.00")

        other_tenant = Tenant.objects.create(name="Diğer A.Ş.", slug="teklif-diger")
        other_user = User.objects.create_user(
            username="teklif-diger", password="test-pass", email="diger@example.com",
            tenant=other_tenant, role=UserRole.MALIYET_MUHENDISI,
        )
        other_malzeme = Malzeme.objects.create(
            tenant=other_tenant, malzeme_kodu="DIGER", ad="Diğer Malzeme", birim="adet"
        )
        other_proje = Proje.objects.create(
            tenant=other_tenant, proje_kodu="P-DIGER", ad="Diğer Proje"
        )
        other_tedarikci = Tedarikci.objects.create(
            tenant=other_tenant, firma_adi="Diğer Tedarik", firma_kodu="TED-DIGER"
        )
        TedarikciTeklifi.objects.create(
            tenant=other_tenant, proje=other_proje, malzeme=other_malzeme,
            tedarikci=other_tedarikci, miktar=1, birim_fiyat=99,
        )

        response = self._client().get("/api/v1/construction/tedarikci-teklifleri/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["count"], 1)
        self.assertEqual(response.json()["data"]["results"][0]["tenant"], self.tenant.pk)

        response = self._client(other_user).get(
            "/api/v1/construction/tedarikci-teklifleri/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["count"], 1)
        self.assertEqual(response.json()["data"]["results"][0]["tenant"], other_tenant.pk)

    def test_winner_action_preserves_other_offer(self):
        first = self._client().post(
            "/api/v1/construction/tedarikci-teklifleri/",
            self._payload(self.tedarikci_a, "125.50"),
            format="json",
        )
        second = self._client().post(
            "/api/v1/construction/tedarikci-teklifleri/",
            self._payload(self.tedarikci_b, "119.00"),
            format="json",
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)

        response = self._client().post(
            f"/api/v1/construction/tedarikci-teklifleri/{second.json()['data']['id']}/kazanan-sec/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"]["secildi"])
        self.assertEqual(response.json()["data"]["durum"], "kabul")
        self.assertTrue(
            TedarikciTeklifi.objects.get(pk=second.json()["data"]["id"]).secildi
        )
        other = TedarikciTeklifi.objects.get(pk=first.json()["data"]["id"])
        self.assertTrue(other.is_active)
        self.assertFalse(other.secildi)

    def test_delete_soft_archives_offer(self):
        created = self._client().post(
            "/api/v1/construction/tedarikci-teklifleri/",
            self._payload(),
            format="json",
        )
        teklif_id = created.json()["data"]["id"]

        response = self._client().delete(
            f"/api/v1/construction/tedarikci-teklifleri/{teklif_id}/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["data"]["is_active"])
        self.assertFalse(TedarikciTeklifi.objects.get(pk=teklif_id).is_active)


# ---------------------------------------------------------------------------
# ÇŞİDB poz / yapı sınıfı import (roadmap Faz 1 kalanlar)
# ---------------------------------------------------------------------------

POZ_SATIRLARI = [
    {
        "poz_no": "15.110.1001",
        "grup_kodu": "KAZI",
        "grup_adi": "Kazı ve Zemin İşleri",
        "ad": "Kazı makine ile yumuşak zeminde",
        "birim": "m³",
        "yil": "2026",
        "birim_fiyat": "235.42",
        "tip": "yapim",
        "kaynak": "ÇŞİDB 2026 tebliği",
    },
    {
        "poz_no": "15.275.1102",
        "grup_kodu": "INCE",
        "grup_adi": "İnce İnşaat İşleri",
        "ad": "Kireç/çimento karışımı iç cephe sıvası",
        "birim": "m²",
        "yil": "2026",
        "birim_fiyat": "98.70",
        "tip": "iscilik",
        "kaynak": "ÇŞİDB 2026 tebliği",
    },
]


class YapiSinifiNormalizeTests(TestCase):
    def test_4a_resmi_gostime_donusturulur(self):
        self.assertEqual(normalize_yapi_sinifi("4A"), "IV-A")

    def test_ayrac_bosluk_kucuk_harf_toleransli(self):
        self.assertEqual(normalize_yapi_sinifi("iv-a"), "IV-A")
        self.assertEqual(normalize_yapi_sinifi("IV A"), "IV-A")
        self.assertEqual(normalize_yapi_sinifi("4 - a"), "IV-A")
        self.assertEqual(normalize_yapi_sinifi("III.d"), "III-D")
        self.assertEqual(normalize_yapi_sinifi("V_e"), "V-E")

    def test_gecerli_roma_kodu_oldugu_gibi_kalir(self):
        self.assertEqual(normalize_yapi_sinifi("II-E"), "II-E")

    def test_gecersiz_kod_reddedilir(self):
        for ham in ("", "6A", "X-9", "IV-K", "abc", "VIII-A"):
            with self.assertRaises(ValueError):
                normalize_yapi_sinifi(ham)


class PozImportTests(ConstructionBase):
    def test_poz_grup_ve_fiyat_olusturur(self):
        ozet = import_poz_verisi(self.tenant, POZ_SATIRLARI)
        self.assertEqual(ozet.poz_olusturulan, 2)
        self.assertEqual(ozet.grup_olusturulan, 2)
        self.assertEqual(ozet.fiyat_olusturulan, 2)
        fiyat = PozFiyat.objects.get(
            tenant=self.tenant, poz__poz_no="15.110.1001", yil=2026
        )
        self.assertEqual(fiyat.birim_fiyat, Decimal("235.42"))
        self.assertEqual(fiyat.kaynak, "ÇŞİDB 2026 tebliği")
        self.assertTrue(fiyat.is_active)

    def test_tekrar_import_idempotent(self):
        import_poz_verisi(self.tenant, POZ_SATIRLARI)
        ozet = import_poz_verisi(self.tenant, POZ_SATIRLARI)
        self.assertEqual(ozet.poz_olusturulan, 0)
        self.assertEqual(ozet.poz_guncellenen, 2)
        self.assertEqual(ozet.fiyat_guncellenen, 2)
        # 2 import + setUp'taki P-1001; kayıt sayısı artmaz (update deseni)
        self.assertEqual(Poz.objects.filter(tenant=self.tenant).count(), 3)
        self.assertEqual(PozFiyat.objects.filter(tenant=self.tenant).count(), 2)

    def test_varsayilan_yil_ve_kaynak_kullanilir(self):
        satir = {k: v for k, v in POZ_SATIRLARI[0].items() if k not in ("yil", "kaynak")}
        ozet = import_poz_verisi(
            self.tenant,
            [satir],
            varsayilan_yil=2026,
            varsayilan_kaynak="ÇŞİDB 2026 tebliği",
        )
        fiyat = PozFiyat.objects.get(tenant=self.tenant, poz__poz_no="15.110.1001")
        self.assertEqual(fiyat.yil, 2026)
        self.assertEqual(fiyat.kaynak, "ÇŞİDB 2026 tebliği")

    def test_gecersiz_poz_no_tum_import_geri_alinir(self):
        hatali = [dict(POZ_SATIRLARI[0]), dict(POZ_SATIRLARI[1], poz_no="15-275-1102")]
        with self.assertRaises(ImportHatasi):
            import_poz_verisi(self.tenant, hatali)
        # fail-fast + atomic: hiçbir poz oluşmamalıdır
        self.assertFalse(
            Poz.objects.filter(tenant=self.tenant, poz_no__startswith="15.").exists()
        )

    def test_turkce_virgullu_fiyat_reddedilir(self):
        hatali = [dict(POZ_SATIRLARI[0], birim_fiyat="235,42")]
        with self.assertRaises(ImportHatasi):
            import_poz_verisi(self.tenant, hatali)

    def test_fiyatsiz_satir_poz_alir_fiyat_olusturmaz(self):
        satirlar = [dict(POZ_SATIRLARI[0], birim_fiyat="")]
        ozet = import_poz_verisi(
            self.tenant, satirlar, varsayilan_yil=2026, varsayilan_kaynak="ÇŞİDB"
        )
        self.assertEqual(ozet.poz_olusturulan, 1)
        self.assertEqual(ozet.fiyat_olusturulan, 0)
        self.assertFalse(
            PozFiyat.objects.filter(
                tenant=self.tenant, poz__poz_no="15.110.1001"
            ).exists()
        )

    def test_eski_yil_arsivlenir_silinmez(self):
        eski_fiyat = PozFiyat.objects.create(
            tenant=self.tenant, poz=self.poz, yil=2025, birim_fiyat=Decimal("100.00")
        )
        ozet = import_poz_verisi(self.tenant, POZ_SATIRLARI, arsivlenecek_yil=2025)
        eski_fiyat.refresh_from_db()
        self.poz.refresh_from_db()
        self.assertFalse(eski_fiyat.is_active)
        self.assertFalse(self.poz.is_active)
        self.assertEqual(ozet.arsivlenen_poz, 1)
        self.assertEqual(ozet.arsivlenen_fiyat, 1)
        # fiziksel silme yok — kayıtlar hâlâ mevcut
        self.assertTrue(PozFiyat.objects.filter(pk=eski_fiyat.pk).exists())
        # import edilen pozlar arşivlenmez
        self.assertTrue(
            Poz.objects.get(tenant=self.tenant, poz_no="15.110.1001").is_active
        )


class YapiSinifiImportTests(ConstructionBase):
    def test_kod_normalize_edilerek_olusturulur(self):
        ozet = import_yapi_sinifi_verisi(
            self.tenant,
            [{"sinif_kodu": "4A", "yil": "2026", "birim_maliyet": "15000.00"}],
        )
        kayit = YapiSinifiBirimMaliyet.objects.get(tenant=self.tenant, yil=2026)
        self.assertEqual(kayit.sinif_kodu, "IV-A")
        self.assertEqual(kayit.birim_maliyet, Decimal("15000.00"))
        self.assertEqual(ozet.sinif_olusturulan, 1)

    def test_ayni_yil_guncellenir_yeni_kayit_acilmaz(self):
        import_yapi_sinifi_verisi(
            self.tenant,
            [{"sinif_kodu": "IV-A", "yil": "2026", "birim_maliyet": "15000.00"}],
        )
        ozet = import_yapi_sinifi_verisi(
            self.tenant,
            [{"sinif_kodu": "4a", "yil": "2026", "birim_maliyet": "15600.25"}],
        )
        self.assertEqual(ozet.sinif_guncellenen, 1)
        self.assertEqual(
            YapiSinifiBirimMaliyet.objects.filter(tenant=self.tenant, yil=2026).count(),
            1,
        )
        self.assertEqual(
            YapiSinifiBirimMaliyet.objects.get(tenant=self.tenant, yil=2026).birim_maliyet,
            Decimal("15600.25"),
        )

    def test_farkli_yil_yeni_versiyon_kaydi(self):
        import_yapi_sinifi_verisi(
            self.tenant,
            [
                {"sinif_kodu": "IV-A", "yil": "2025", "birim_maliyet": "13000.00"},
                {"sinif_kodu": "IV-A", "yil": "2026", "birim_maliyet": "15000.00"},
            ],
        )
        self.assertEqual(
            YapiSinifiBirimMaliyet.objects.filter(
                tenant=self.tenant, sinif_kodu="IV-A"
            ).count(),
            2,
        )

    def test_gecersiz_sinif_tum_import_geri_alinir(self):
        with self.assertRaises(ImportHatasi):
            import_yapi_sinifi_verisi(
                self.tenant,
                [
                    {"sinif_kodu": "IV-A", "yil": "2026", "birim_maliyet": "15000.00"},
                    {"sinif_kodu": "VIII-A", "yil": "2026", "birim_maliyet": "15000.00"},
                ],
            )
        self.assertFalse(
            YapiSinifiBirimMaliyet.objects.filter(tenant=self.tenant).exists()
        )


class ImportCommandTests(ConstructionBase):
    POZ_CSV = (
        "poz_no;grup_kodu;grup_adi;ad;birim;yil;birim_fiyat;tip;kaynak\n"
        "15.110.1001;KAZI;Kazı ve Zemin İşleri;"
        "Kazı makine ile yumuşak zeminde;m³;2026;235.42;yapim;ÇŞİDB 2026 tebliği\n"
    )
    SINIF_CSV = "sinif_kodu;yil;birim_maliyet\n4A;2026;15000.00\n"

    def setUp(self):
        super().setUp()
        self.gecici_dosyalar: list[str] = []

    def tearDown(self):
        for yol in self.gecici_dosyalar:
            if os.path.exists(yol):
                os.unlink(yol)
        super().tearDown()

    def _csv_yaz(self, icerik: str) -> str:
        with NamedTemporaryFile(
            "w", suffix=".csv", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(icerik)
            self.gecici_dosyalar.append(fh.name)
            return fh.name

    def test_import_pozlar_komutu(self):
        yol = self._csv_yaz(self.POZ_CSV)
        cikti = StringIO()
        call_command("import_pozlar", tenant=self.tenant.slug, dosya=yol, stdout=cikti)
        self.assertIn("İçe aktarma tamamlandı", cikti.getvalue())
        self.assertTrue(
            Poz.objects.filter(tenant=self.tenant, poz_no="15.110.1001").exists()
        )

    def test_import_pozlar_arsivle_bayragi(self):
        PozFiyat.objects.create(
            tenant=self.tenant, poz=self.poz, yil=2025, birim_fiyat=Decimal("100.00")
        )
        yol = self._csv_yaz(self.POZ_CSV)
        cikti = StringIO()
        call_command(
            "import_pozlar",
            tenant=self.tenant.slug,
            dosya=yol,
            arsivle=2025,
            stdout=cikti,
        )
        self.poz.refresh_from_db()
        self.assertFalse(self.poz.is_active)
        self.assertIn("Arşivlenen poz (is_active=False): 1", cikti.getvalue())

    def test_import_yapi_sinifi_komutu(self):
        yol = self._csv_yaz(self.SINIF_CSV)
        cikti = StringIO()
        call_command(
            "import_yapi_sinifi", tenant=self.tenant.slug, dosya=yol, stdout=cikti
        )
        kayit = YapiSinifiBirimMaliyet.objects.get(tenant=self.tenant, yil=2026)
        self.assertEqual(kayit.sinif_kodu, "IV-A")
        self.assertEqual(kayit.birim_maliyet, Decimal("15000.00"))

    def test_olmayan_tenant_command_error(self):
        yol = self._csv_yaz(self.POZ_CSV)
        with self.assertRaises(CommandError):
            call_command(
                "import_pozlar", tenant="yok-boyle-tenant", dosya=yol, stdout=StringIO()
            )


class YapiSinifiApiNormalizeTests(ConstructionBase):
    def test_api_4a_girisini_iv_a_olarak_kaydeder(self):
        client = APIClient()
        client.force_authenticate(user=self.editor)
        response = client.post(
            "/api/v1/construction/yapi-sinifi-birim-maliyetleri/",
            {"sinif_kodu": "4A", "yil": 2026, "birim_maliyet": "15000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["sinif_kodu"], "IV-A")

    def test_api_gecersiz_sinif_400(self):
        client = APIClient()
        client.force_authenticate(user=self.editor)
        response = client.post(
            "/api/v1/construction/yapi-sinifi-birim-maliyetleri/",
            {"sinif_kodu": "VIII-A", "yil": 2026, "birim_maliyet": "15000.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
# ---------------------------------------------------------------------------
# Faz 2 — Poz maliyet planı (metraj) + S-eğrisi raporu
# ---------------------------------------------------------------------------


class PozPlanBase(ConstructionBase):
    def setUp(self):
        super().setUp()
        self.proje = Proje.objects.create(
            tenant=self.tenant, proje_kodu="PRJ-1", ad="Örnek Konut Projesi"
        )
        self.fiyat = PozFiyat.objects.create(
            tenant=self.tenant, poz=self.poz, yil=2026, birim_fiyat=Decimal("1250.50")
        )


class PozPlanModelTests(PozPlanBase):
    def test_snapshot_pozfiyattan_otomatik_alinir(self):
        plan = PozPlan.objects.create(
            tenant=self.tenant,
            proje=self.proje,
            poz=self.poz,
            yil=2026,
            planlanan_miktar=Decimal("10.0000"),
        )
        self.assertEqual(plan.birim_fiyat_snapshot, Decimal("1250.50"))

    def test_planlanan_miktar_sifir_reddedilir(self):
        plan = PozPlan(
            tenant=self.tenant,
            proje=self.proje,
            poz=self.poz,
            yil=2026,
            planlanan_miktar=Decimal("0.0000"),
        )
        with self.assertRaises(ValidationError):
            plan.save()

    def test_fiyat_yoksa_validation_error(self):
        """2025 yılı için PozFiyat yok → snapshot 0 kalır, kayıt reddedilir."""
        plan = PozPlan(
            tenant=self.tenant,
            proje=self.proje,
            poz=self.poz,
            yil=2025,
            planlanan_miktar=Decimal("10.0000"),
        )
        with self.assertRaises(ValidationError):
            plan.save()

    def test_ayni_proje_poz_yil_tekrar_edemez(self):
        PozPlan.objects.create(
            tenant=self.tenant,
            proje=self.proje,
            poz=self.poz,
            yil=2026,
            planlanan_miktar=Decimal("10.0000"),
        )
        with self.assertRaises(IntegrityError):
            PozPlan.objects.create(
                tenant=self.tenant,
                proje=self.proje,
                poz=self.poz,
                yil=2026,
                planlanan_miktar=Decimal("5.0000"),
            )


class SEkgirsiServiceTests(PozPlanBase):
    def _plan(self, planlanan: str, gercek: str, yil: int = 2026):
        return PozPlan.objects.create(
            tenant=self.tenant,
            proje=self.proje,
            poz=self.poz,
            yil=yil,
            planlanan_miktar=Decimal(planlanan),
            gercek_miktar=Decimal(gercek),
        )

    def test_s_egrisi_decimal_degerleri_dondurur(self):
        self._plan("10.0000", "8.0000")
        rapor = s_egrisi_raporu(self.proje, 2026)

        self.assertEqual(rapor["proje_kodu"], "PRJ-1")
        self.assertEqual(rapor["yil"], 2026)
        self.assertEqual(rapor["toplam_plan_deger"], "12505.00")
        self.assertEqual(rapor["toplam_gercek_deger"], "10004.00")
        self.assertEqual(rapor["toplam_sapma_tutar"], "-2501.00")
        self.assertEqual(rapor["toplam_sapma_yuzde"], "-20.00%")
        self.assertEqual(len(rapor["pozlar"]), 1)

        satir = rapor["pozlar"][0]
        self.assertEqual(satir["poz_no"], "P-1001")
        self.assertEqual(satir["plan_deger"], "12505.00")
        self.assertEqual(satir["gercek_deger"], "10004.00")
        self.assertEqual(satir["sapma_yuzde"], "-20.00%")

    def test_gerceklesme_yoksa_sapma_sifir(self):
        self._plan("4.0000", "0")
        rapor = s_egrisi_raporu(self.proje, 2026)
        self.assertEqual(rapor["toplam_gercek_deger"], "0.00")
        self.assertEqual(rapor["toplam_sapma_tutar"], "-5002.00")
        self.assertEqual(rapor["toplam_sapma_yuzde"], "-100.00%")

    def test_baska_yil_bos_rapor(self):
        self._plan("10.0000", "8.0000")
        rapor = s_egrisi_raporu(self.proje, 2030)
        self.assertEqual(rapor["pozlar"], [])
        self.assertEqual(rapor["toplam_plan_deger"], "0.00")
        self.assertEqual(rapor["toplam_sapma_yuzde"], "0%")

    def test_baska_tenant_plani_rapora_girmez(self):
        diger_tenant = Tenant.objects.create(name="Diğer A.Ş.", slug="diger")
        diger_proje = Proje.objects.create(
            tenant=diger_tenant, proje_kodu="PRJ-1", ad="Yabancı Proje"
        )
        PozPlan.objects.create(
            tenant=self.tenant,
            proje=self.proje,
            poz=self.poz,
            yil=2026,
            planlanan_miktar=Decimal("10.0000"),
        )
        rapor = s_egrisi_raporu(diger_proje, 2026)
        self.assertEqual(rapor["pozlar"], [])

    def test_proje_kar_zarar_butce_sapmasini_hesaplar(self):
        self._plan("10.0000", "8.0000")
        rapor = proje_kar_zarar(self.proje, 2026)
        self.assertEqual(rapor["butcelenen_maliyet"], "12505.00")
        self.assertEqual(rapor["gerceklesen_maliyet"], "0.00")
        self.assertEqual(rapor["maliyet_sapmasi"], "-12505.00")
        self.assertEqual(rapor["gelir"], "0.00")

    def test_metraj_kontrolu_aciklanabilir_oneriler_uretir(self):
        self._plan("10.0000", "12.0000")
        rapor = metraj_kontrolu(self.proje, 2026)
        self.assertEqual(rapor["kritik"], 1)
        self.assertEqual(rapor["oneriler"][0]["kod"], "FAZLA_METRAJ")

    def test_fiyat_anomalisi_onceki_yila_gore_uyari_uretir(self):
        self._plan("10.0000", "1.0000")
        PozFiyat.objects.create(
            tenant=self.tenant, poz=self.poz, yil=2025, birim_fiyat=Decimal("100.00")
        )
        rapor = fiyat_anomalilerini_bul(self.proje, 2026)
        self.assertEqual(rapor["kritik"], 1)
        self.assertEqual(rapor["anomaliler"][0]["kod"], "FIYAT_SAPMASI")


class PozPlanApiTests(PozPlanBase):
    def _client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def _payload(self, **degisiklik):
        veri = {
            "proje": self.proje.pk,
            "poz": self.poz.pk,
            "yil": 2026,
            "planlanan_miktar": "10.0000",
            "gercek_miktar": "8.0000",
        }
        veri.update(degisiklik)
        return veri

    def test_editor_plan_olusturur_snapshot_otomatik(self):
        response = self._client(self.editor).post(
            "/api/v1/construction/poz-planlari/", self._payload(), format="json"
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()["data"]
        self.assertEqual(data["birim_fiyat_snapshot"], "1250.50")
        self.assertEqual(data["plan_deger"], "12505.00")
        self.assertEqual(data["gercek_deger"], "10004.00")
        self.assertEqual(data["tenant"], self.tenant.pk)
        self.assertEqual(data["poz_no"], "P-1001")

    def test_plan_silme_istegi_pasife_ceker(self):
        response = self._client(self.editor).post(
            "/api/v1/construction/poz-planlari/", self._payload(), format="json"
        )
        plan_id = response.json()["data"]["id"]
        silme = self._client(self.editor).delete(
            f"/api/v1/construction/poz-planlari/{plan_id}/"
        )
        self.assertEqual(silme.status_code, 200)
        self.assertFalse(PozPlan.objects.get(pk=plan_id).is_active)
        self.assertEqual(
            self._client(self.editor).delete(
                f"/api/v1/construction/poz-planlari/{plan_id}/"
            ).status_code,
            400,
        )

    def test_santiye_sefi_plan_yazamaz(self):
        response = self._client(self.reader).post(
            "/api/v1/construction/poz-planlari/", self._payload(), format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_santiye_sefi_planlari_okur(self):
        response = self._client(self.reader).get("/api/v1/construction/poz-planlari/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_negatif_gercek_miktar_400(self):
        response = self._client(self.editor).post(
            "/api/v1/construction/poz-planlari/",
            self._payload(gercek_miktar="-1.0000"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_fiyatsiz_yil_400(self):
        response = self._client(self.editor).post(
            "/api/v1/construction/poz-planlari/", self._payload(yil=2025), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("poz", response.json()["errors"])

    def test_s_egrisi_endpoint_rapor_dondurur(self):
        self._client(self.editor).post(
            "/api/v1/construction/poz-planlari/", self._payload(), format="json"
        )
        response = self._client(self.editor).get(
            f"/api/v1/construction/poz-planlari/s-egrisi/?proje={self.proje.pk}&yil=2026"
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["toplam_plan_deger"], "12505.00")
        self.assertEqual(body["data"]["toplam_sapma_yuzde"], "-20.00%")

    def test_kar_zarar_endpoint_rapor_dondurur(self):
        self._client(self.editor).post(
            "/api/v1/construction/poz-planlari/", self._payload(), format="json"
        )
        response = self._client(self.editor).get(
            f"/api/v1/construction/poz-planlari/kar-zarar/?proje={self.proje.pk}&yil=2026"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["butcelenen_maliyet"], "12505.00")

    def test_portfoy_karsilastirma_filtreli_rapor_dondurur(self):
        self._client(self.editor).post(
            "/api/v1/construction/poz-planlari/", self._payload(), format="json"
        )
        ikinci = Proje.objects.create(
            tenant=self.tenant, proje_kodu="PRJ-2", ad="İkinci Proje", durum=Proje.Durum.DEVAM
        )
        response = self._client(self.editor).get(
            "/api/v1/construction/projeler/portfoy-ozeti/?yil=2026&durum=devam"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["proje_sayisi"], 1)
        self.assertEqual(data["projeler"][0]["proje_kodu"], "PRJ-2")
        self.assertEqual(data["toplam_butce"], "0.00")

    def test_teknik_sartname_poz_ve_ts_referanslarini_dondurur(self):
        PozMalzemeIliskisi.objects.create(
            tenant=self.tenant,
            poz=self.poz,
            malzeme=self.malzeme,
            miktar=Decimal("1.2500"),
        )
        self.malzeme.ts_no = "TS EN 206"
        self.malzeme.save(update_fields=["ts_no"])
        self._client(self.editor).post(
            "/api/v1/construction/poz-planlari/", self._payload(), format="json"
        )
        response = self._client(self.editor).get(
            f"/api/v1/construction/projeler/teknik-sartname/?proje={self.proje.pk}&yil=2026"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["kalem_sayisi"], 1)
        self.assertEqual(data["malzeme_sayisi"], 1)
        self.assertEqual(data["kalemler"][0]["malzemeler"][0]["ts_no"], "TS EN 206")
        self.assertIn("TS EN 206", data["markdown"])

    def test_metraj_kontrolu_endpoint_rapor_dondurur(self):
        self._client(self.editor).post(
            "/api/v1/construction/poz-planlari/", self._payload(gercek_miktar="12.0000"), format="json"
        )
        response = self._client(self.editor).get(
            f"/api/v1/construction/poz-planlari/metraj-kontrolu/?proje={self.proje.pk}&yil=2026"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["kritik"], 1)

    def test_s_egrisi_parametre_eksikse_400(self):
        response = self._client(self.editor).get(
            "/api/v1/construction/poz-planlari/s-egrisi/"
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_baska_tenant_projesi_s_egrisi_404(self):
        diger_tenant = Tenant.objects.create(name="Diğer A.Ş.", slug="diger")
        diger_proje = Proje.objects.create(
            tenant=diger_tenant, proje_kodu="PRJ-9", ad="Yabancı Proje"
        )
        response = self._client(self.editor).get(
            f"/api/v1/construction/poz-planlari/s-egrisi/?proje={diger_proje.pk}&yil=2026"
        )
        self.assertEqual(response.status_code, 404)

    def test_baska_tenant_plani_listelenmez(self):
        diger_tenant = Tenant.objects.create(name="Diğer A.Ş.", slug="diger")
        diger_proje = Proje.objects.create(
            tenant=diger_tenant, proje_kodu="PRJ-2", ad="Yabancı Proje"
        )
        PozFiyat.objects.create(
            tenant=diger_tenant, poz=self.poz, yil=2026, birim_fiyat=Decimal("1250.50")
        )
        PozPlan.objects.create(
            tenant=diger_tenant,
            proje=diger_proje,
            poz=self.poz,
            yil=2026,
            planlanan_miktar=Decimal("3.0000"),
        )
        response = self._client(self.editor).get("/api/v1/construction/poz-planlari/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["count"], 0)
# ---------------------------------------------------------------------------
# Faz 2 — Gantt şeması (iş kalemi bazlı zaman çizelgesi)
# ---------------------------------------------------------------------------


class PozPlanTarihTests(PozPlanBase):
    def _plan(self, **ek):
        veri = {
            "tenant": self.tenant,
            "proje": self.proje,
            "poz": self.poz,
            "yil": 2026,
            "planlanan_miktar": Decimal("10.0000"),
        }
        veri.update(ek)
        return PozPlan.objects.create(**veri)

    def test_bitis_baslangictan_once_olamaz(self):
        from django.core.exceptions import ValidationError as DjangoValidationError

        plan = PozPlan(
            tenant=self.tenant,
            proje=self.proje,
            poz=self.poz,
            yil=2026,
            planlanan_miktar=Decimal("10.0000"),
            planlanan_baslangic=date(2026, 5, 10),
            planlanan_bitis=date(2026, 5, 1),
        )
        with self.assertRaises(DjangoValidationError):
            plan.save()

    def test_tarih_sirasi_db_kisiti_ile_korunur(self):
        plan = self._plan(
            planlanan_baslangic=date(2026, 5, 10), planlanan_bitis=date(2026, 5, 20)
        )
        with self.assertRaises(IntegrityError):
            PozPlan.objects.filter(pk=plan.pk).update(planlanan_bitis=date(2026, 5, 1))

    def test_tarihler_opsiyonel(self):
        plan = self._plan()
        self.assertIsNone(plan.planlanan_baslangic)
        self.assertIsNone(plan.planlanan_bitis)


class GanttServiceTests(PozPlanBase):
    def _plan(self, planlanan, gercek, baslangic=None, bitis=None, poz=None, yil=2026):
        return PozPlan.objects.create(
            tenant=self.tenant,
            proje=self.proje,
            poz=poz or self.poz,
            yil=yil,
            planlanan_miktar=Decimal(planlanan),
            gercek_miktar=Decimal(gercek),
            planlanan_baslangic=baslangic,
            planlanan_bitis=bitis,
        )

    def test_tarih_yoksa_cubuk_tarihsiz_doner(self):
        self._plan("10.0000", "2.0000")
        rapor = gantt_verisi(self.proje, 2026)
        self.assertEqual(rapor["proje_kodu"], "PRJ-1")
        self.assertEqual(rapor["tarihsiz_sayi"], 1)
        self.assertIsNone(rapor["en_erken"])
        self.assertIsNone(rapor["en_gec"])
        cubuk = rapor["cubuklar"][0]
        self.assertFalse(cubuk["tarih_atandi"])
        self.assertIsNone(cubuk["baslangic"])
        self.assertEqual(cubuk["ilerleme_yuzde"], "20.00%")

    def test_eksen_araligi_ve_ilerleme(self):
        poz2 = Poz.objects.create(
            tenant=self.tenant, poz_no="P-1002", ad="İkinci poz", birim="m²", grup=self.grup
        )
        PozFiyat.objects.create(
            tenant=self.tenant, poz=poz2, yil=2026, birim_fiyat=Decimal("100.00")
        )
        self._plan(
            "10.0000", "8.0000", baslangic=date(2026, 3, 1), bitis=date(2026, 4, 15)
        )
        self._plan(
            "5.0000",
            "0.0000",
            baslangic=date(2026, 2, 1),
            bitis=date(2026, 2, 20),
            poz=poz2,
        )
        rapor = gantt_verisi(self.proje, 2026)
        self.assertEqual(rapor["en_erken"], "2026-02-01")
        self.assertEqual(rapor["en_gec"], "2026-04-15")
        self.assertEqual(rapor["tarihsiz_sayi"], 0)
        self.assertEqual(len(rapor["cubuklar"]), 2)
        self.assertEqual(rapor["cubuklar"][0]["poz_no"], "P-1001")
        self.assertEqual(rapor["cubuklar"][0]["ilerleme_yuzde"], "80.00%")
        self.assertEqual(rapor["cubuklar"][0]["plan_deger"], "12505.00")
        self.assertEqual(rapor["cubuklar"][1]["poz_no"], "P-1002")
        self.assertEqual(rapor["cubuklar"][1]["ilerleme_yuzde"], "0.00%")

    def test_yalniz_baslangic_girilirse_tek_gunluk_cubuk(self):
        self._plan("10.0000", "1.0000", baslangic=date(2026, 6, 1))
        cubuk = gantt_verisi(self.proje, 2026)["cubuklar"][0]
        self.assertTrue(cubuk["tarih_atandi"])
        self.assertEqual(cubuk["baslangic"], "2026-06-01")
        self.assertEqual(cubuk["bitis"], "2026-06-01")

    def test_yil_filtresi_uygulanir(self):
        self._plan("10.0000", "1.0000", baslangic=date(2026, 6, 1))
        self.assertEqual(len(gantt_verisi(self.proje, 2026)["cubuklar"]), 1)
        self.assertEqual(gantt_verisi(self.proje, 2030)["cubuklar"], [])
        self.assertEqual(len(gantt_verisi(self.proje, None)["cubuklar"]), 1)

    def test_baska_tenant_plani_gantta_girmez(self):
        diger_tenant = Tenant.objects.create(name="Diğer A.Ş.", slug="diger")
        diger_proje = Proje.objects.create(
            tenant=diger_tenant, proje_kodu="PRJ-7", ad="Yabancı Proje"
        )
        self._plan("10.0000", "1.0000", baslangic=date(2026, 6, 1))
        rapor = gantt_verisi(diger_proje, 2026)
        self.assertEqual(rapor["cubuklar"], [])
        self.assertEqual(rapor["tarihsiz_sayi"], 0)
class GanttApiTests(PozPlanBase):
    def _client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def _payload(self, **degisiklik):
        veri = {
            "proje": self.proje.pk,
            "poz": self.poz.pk,
            "yil": 2026,
            "planlanan_miktar": "10.0000",
            "gercek_miktar": "8.0000",
            "planlanan_baslangic": "2026-03-01",
            "planlanan_bitis": "2026-04-15",
        }
        veri.update(degisiklik)
        return veri

    def test_tarihler_kaydedilir(self):
        response = self._client(self.editor).post(
            "/api/v1/construction/poz-planlari/", self._payload(), format="json"
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()["data"]
        self.assertEqual(data["planlanan_baslangic"], "2026-03-01")
        self.assertEqual(data["planlanan_bitis"], "2026-04-15")

    def test_tarih_sirasi_hatali_400(self):
        response = self._client(self.editor).post(
            "/api/v1/construction/poz-planlari/",
            self._payload(planlanan_baslangic="2026-04-20", planlanan_bitis="2026-04-01"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("planlanan_bitis", response.json()["errors"])

    def test_gantt_endpoint_veri_dondurur(self):
        client = self._client(self.editor)
        client.post("/api/v1/construction/poz-planlari/", self._payload(), format="json")
        response = client.get(
            f"/api/v1/construction/poz-planlari/gantt/?proje={self.proje.pk}&yil=2026"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["proje_kodu"], "PRJ-1")
        self.assertEqual(data["en_erken"], "2026-03-01")
        self.assertEqual(data["en_gec"], "2026-04-15")
        self.assertEqual(len(data["cubuklar"]), 1)
        cubuk = data["cubuklar"][0]
        self.assertEqual(cubuk["poz_no"], "P-1001")
        self.assertEqual(cubuk["ilerleme_yuzde"], "80.00%")
        self.assertTrue(cubuk["tarih_atandi"])

    def test_gantt_yilsiz_tum_planlar(self):
        client = self._client(self.editor)
        client.post("/api/v1/construction/poz-planlari/", self._payload(), format="json")
        response = client.get(
            f"/api/v1/construction/poz-planlari/gantt/?proje={self.proje.pk}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["data"]["yil"])
        self.assertEqual(len(response.json()["data"]["cubuklar"]), 1)

    def test_gantt_proje_parametresi_zorunlu_400(self):
        response = self._client(self.editor).get(
            "/api/v1/construction/poz-planlari/gantt/"
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_gantt_gecersiz_yil_400(self):
        response = self._client(self.editor).get(
            f"/api/v1/construction/poz-planlari/gantt/?proje={self.proje.pk}&yil=abc"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("yil", response.json()["errors"])

    def test_gantt_baska_tenant_projesi_404(self):
        diger_tenant = Tenant.objects.create(name="Diğer A.Ş.", slug="diger")
        diger_proje = Proje.objects.create(
            tenant=diger_tenant, proje_kodu="PRJ-8", ad="Yabancı Proje"
        )
        response = self._client(self.editor).get(
            f"/api/v1/construction/poz-planlari/gantt/?proje={diger_proje.pk}"
        )
        self.assertEqual(response.status_code, 404)

    def test_gantt_santiye_sefi_okur(self):
        response = self._client(self.reader).get(
            f"/api/v1/construction/poz-planlari/gantt/?proje={self.proje.pk}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])


# ---------------------------------------------------------------------------
# Hakediş — dönemsel hakediş hesabı + onay akışı (roadmap Faz 2)
# ---------------------------------------------------------------------------

from accounting.models import HesapPlani, MuhasebeFisi  # noqa: E402
from cari.models import Cari, CariHareket  # noqa: E402


class HakedisBase(ConstructionBase):
    """Hakediş akışı ortak fikstürleri — proje + fiyat + plan + cari."""

    def setUp(self):
        super().setUp()
        self.proje = Proje.objects.create(
            tenant=self.tenant, proje_kodu="PRJ-H1", ad="Hakediş Test Projesi"
        )
        PozFiyat.objects.create(
            tenant=self.tenant, poz=self.poz, yil=2026, birim_fiyat=Decimal("100.00")
        )
        self.plan = PozPlan.objects.create(
            tenant=self.tenant, proje=self.proje, poz=self.poz, yil=2026,
            planlanan_miktar=Decimal("100.0000"), gercek_miktar=Decimal("40.0000"),
        )
        self.cari = Cari.objects.create(
            tenant=self.tenant, ad="Taşeron Ltd.", tip="taseron", tur="kurumsal"
        )
        self.hakedis = Hakedis.objects.create(
            tenant=self.tenant, proje=self.proje, donem="2026-03", cari=self.cari
        )

    def _istemci(self, kullanici):
        istemci = APIClient()
        istemci.force_authenticate(user=kullanici)
        return istemci


class HakedisServiceTests(HakedisBase):
    def test_satirlari_olustur_gercek_metraji_alir(self):
        eklenen = hakedis_satirlari_olustur(self.hakedis)
        self.assertEqual(eklenen, 1)
        satir = self.hakedis.satirlar.get()
        self.assertEqual(satir.poz, self.poz)
        self.assertEqual(satir.miktar, Decimal("40.0000"))
        self.assertEqual(satir.birim_fiyat, Decimal("100.00"))
        self.assertEqual(satir.satir_tutar, Decimal("4000.00"))

    def test_satirlari_olustur_idempotent(self):
        hakedis_satirlari_olustur(self.hakedis)
        eklenen = hakedis_satirlari_olustur(self.hakedis)
        self.assertEqual(eklenen, 0)
        self.assertEqual(self.hakedis.satirlar.count(), 1)

    def test_satirlari_olustur_doner_yili_disini_alinmaz(self):
        PozFiyat.objects.create(
            tenant=self.tenant, poz=self.poz, yil=2025, birim_fiyat=Decimal("50.00")
        )
        PozPlan.objects.create(
            tenant=self.tenant, proje=self.proje, poz=self.poz, yil=2025,
            planlanan_miktar=Decimal("10.0000"), gercek_miktar=Decimal("5.0000"),
        )
        # Dönem 2026-03 → yalnızca yil=2026 planı satıra dönüşür.
        eklenen = hakedis_satirlari_olustur(self.hakedis)
        self.assertEqual(eklenen, 1)
        self.assertEqual(self.hakedis.satirlar.get().poz.poz_no, self.poz.poz_no)

    def test_toplami_satir_tutarlari_toplar(self):
        hakedis_satirlari_olustur(self.hakedis)
        self.assertEqual(hakedis_toplami(self.hakedis), Decimal("4000.00"))

    def test_onayla_cari_hareket_ve_fis_uretir(self):
        hakedis_satirlari_olustur(self.hakedis)
        onaylanan = hakedis_onayla(self.hakedis, onaylayan=self.editor)
        self.assertEqual(onaylanan.durum, Hakedis.Durum.ONAYLANDI)
        self.assertEqual(onaylanan.onaylayan, self.editor)
        hareket = onaylanan.cari_hareket
        self.assertEqual(hareket.yon, CariHareket.Yon.BORC)
        self.assertEqual(hareket.tutar, Decimal("4000.00"))
        fis = onaylanan.muhasebe_fisi
        borc = sum((s.borc for s in fis.satirlar.all()), Decimal("0"))
        alacak = sum((s.alacak for s in fis.satirlar.all()), Decimal("0"))
        self.assertEqual(borc, Decimal("4000.00"))
        self.assertEqual(alacak, Decimal("4000.00"))  # çift kayıt: borç == alacak
        # Hesap planı otomatik açıldı (740 gider / 120 alıcılar)
        self.assertTrue(HesapPlani.objects.filter(tenant=self.tenant, kod="740").exists())
        self.assertTrue(HesapPlani.objects.filter(tenant=self.tenant, kod="120").exists())

    def test_onayla_cari_yok_reddedilir(self):
        hakedis = Hakedis.objects.create(tenant=self.tenant, proje=self.proje, donem="2026-04")
        HakedisSatiri.objects.create(
            hakedis=hakedis, poz=self.poz,
            miktar=Decimal("10.0000"), birim_fiyat=Decimal("100.00"),
        )
        with self.assertRaises(ValidationError):
            hakedis_onayla(hakedis, onaylayan=self.editor)

    def test_onayla_satir_yok_reddedilir(self):
        with self.assertRaises(ValidationError):
            hakedis_onayla(self.hakedis, onaylayan=self.editor)

    def test_onayla_tekrar_reddedilir(self):
        hakedis_satirlari_olustur(self.hakedis)
        hakedis_onayla(self.hakedis, onaylayan=self.editor)
        with self.assertRaises(ValidationError):
            hakedis_onayla(self.hakedis, onaylayan=self.editor)

    def test_onayli_hakedis_donem_degisemez(self):
        hakedis_satirlari_olustur(self.hakedis)
        onaylanan = hakedis_onayla(self.hakedis, onaylayan=self.editor)
        onaylanan.donem = "2026-05"
        with self.assertRaises(ValidationError):
            onaylanan.full_clean()

class HakedisApiTests(HakedisBase):
    def test_taslak_olusturma_nested_satirla(self):
        yanit = self._istemci(self.editor).post(
            "/api/v1/construction/hakedisler/",
            {
                "proje": self.proje.pk, "donem": "2026-04", "cari": self.cari.pk,
                "satirlar": [
                    {"poz": self.poz.pk, "miktar": "10.0000", "birim_fiyat": "100.00"},
                ],
            },
            format="json",
        )
        self.assertEqual(yanit.status_code, 201)
        veri = yanit.json()["data"]
        self.assertEqual(veri["durum"], "taslak")
        self.assertEqual(veri["toplam_tutar"], "1000.00")
        self.assertEqual(len(veri["satirlar"]), 1)

    def test_satirlari_olustur_endpoint(self):
        yanit = self._istemci(self.editor).post(
            f"/api/v1/construction/hakedisler/{self.hakedis.pk}/satirlari-olustur/",
            format="json",
        )
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["data"]["eklenen_satir"], 1)

    def test_onayla_akisi_zarfla_doner(self):
        hakedis_satirlari_olustur(self.hakedis)
        yanit = self._istemci(self.editor).post(
            f"/api/v1/construction/hakedisler/{self.hakedis.pk}/onayla/",
            format="json",
        )
        self.assertEqual(yanit.status_code, 200)
        veri = yanit.json()
        self.assertTrue(veri["success"])
        self.assertEqual(veri["data"]["durum"], "onaylandi")
        self.assertIsNotNone(veri["data"]["muhasebe_fisi"])

    def test_onay_cari_yoksa_400(self):
        hakedis = Hakedis.objects.create(tenant=self.tenant, proje=self.proje, donem="2026-04")
        HakedisSatiri.objects.create(
            hakedis=hakedis, poz=self.poz,
            miktar=Decimal("10.0000"), birim_fiyat=Decimal("100.00"),
        )
        yanit = self._istemci(self.editor).post(
            f"/api/v1/construction/hakedisler/{hakedis.pk}/onayla/", format="json",
        )
        self.assertEqual(yanit.status_code, 400)
        self.assertFalse(yanit.json()["success"])

    def test_onayli_hakedis_degistirilemez(self):
        hakedis_satirlari_olustur(self.hakedis)
        hakedis_onayla(self.hakedis, onaylayan=self.editor)
        istemci = self._istemci(self.editor)
        # Açıklama güncellenebilir
        ok = istemci.patch(
            f"/api/v1/construction/hakedisler/{self.hakedis.pk}/",
            {"aciklama": "Onay sonrası not"}, format="json",
        )
        self.assertEqual(ok.status_code, 200)
        # Dönem değişimi reddedilir
        engel = istemci.patch(
            f"/api/v1/construction/hakedisler/{self.hakedis.pk}/",
            {"donem": "2026-05"}, format="json",
        )
        self.assertEqual(engel.status_code, 400)

    def test_taslak_iptale_cekilir_onayli_silinemez(self):
        istemci = self._istemci(self.editor)
        yanit = istemci.delete(f"/api/v1/construction/hakedisler/{self.hakedis.pk}/")
        self.assertEqual(yanit.status_code, 200)
        self.hakedis.refresh_from_db()
        self.assertEqual(self.hakedis.durum, Hakedis.Durum.IPTAL)
        # Onaylı hakediş silinemez
        diger = Hakedis.objects.create(
            tenant=self.tenant, proje=self.proje, donem="2026-05", cari=self.cari
        )
        HakedisSatiri.objects.create(
            hakedis=diger, poz=self.poz,
            miktar=Decimal("10.0000"), birim_fiyat=Decimal("100.00"),
        )
        hakedis_onayla(diger, onaylayan=self.editor)
        self.assertEqual(
            istemci.delete(f"/api/v1/construction/hakedisler/{diger.pk}/").status_code, 400,
        )

    def test_santiye_sefi_okur_yazamaz(self):
        istemci = self._istemci(self.reader)
        self.assertEqual(istemci.get("/api/v1/construction/hakedisler/").status_code, 200)
        self.assertEqual(
            istemci.post(
                "/api/v1/construction/hakedisler/",
                {"proje": self.proje.pk, "donem": "2026-04"}, format="json",
            ).status_code, 403,
        )

    def test_tenant_izolasyonu(self):
        diger_tenant = Tenant.objects.create(name="Komşu Ltd.", slug="komsu-ins")
        diger = Hakedis.objects.create(tenant=diger_tenant, proje=self.proje, donem="2026-04")
        istemci = self._istemci(self.editor)
        veri = istemci.get("/api/v1/construction/hakedisler/").json()["data"]
        self.assertEqual(veri["count"], 1)
        self.assertEqual(
            istemci.get(f"/api/v1/construction/hakedisler/{diger.pk}/").status_code, 404,
        )


class MahalApiTests(ConstructionBase):
    def _client(self):
        client = APIClient()
        client.force_authenticate(user=self.editor)
        return client

    def test_mahal_crud_and_nested_elemanlar(self):
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="M-API", ad="Mahal Projesi")
        client = self._client()
        response = client.post(
            "/api/v1/construction/mahaller/",
            {"proje": proje.pk, "kod": "SALON", "ad": "Salon"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        mahal_id = response.json()["data"]["id"]
        response = client.post(
            f"/api/v1/construction/mahaller/{mahal_id}/elemanlar/",
            {"eleman_tipi": "Kapı", "ad": "Giriş Kapısı"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            client.get(f"/api/v1/construction/mahaller/{mahal_id}/elemanlar/").json()["data"][0]["eleman_tipi"],
            "Kapı",
        )

    def test_mahal_sablonu_oda_elemanlarini_olusturur(self):
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="M-SABLON", ad="Şablon")
        response = self._client().post(
            f"/api/v1/construction/projeler/{proje.pk}/mahal-sablondan-olustur/",
            {"kod": "ODA-1", "ad": "Yatak Odası"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        mahal = Mahal.objects.get(pk=response.json()["data"]["id"])
        self.assertEqual(mahal.elemanlar.count(), 5)

    def test_mahal_listesi_tenant_ile_izole(self):
        diger = Tenant.objects.create(name="Diğer", slug="diger-mahal")
        proje = Proje.objects.create(tenant=diger, proje_kodu="DIGER", ad="Diğer")
        Mahal.objects.create(tenant=diger, proje=proje, kod="D-1", ad="Gizli")
        response = self._client().get("/api/v1/construction/mahaller/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["count"], 0)


class HakedisSnapshotTests(HakedisBase):
    """FAZ 6C — onaylı/iptal hakediş snapshot değişmezliği (API + ORM + serializer + admin)."""

    def _onayli_satir(self):
        hakedis_satirlari_olustur(self.hakedis)
        hakedis_onayla(self.hakedis, onaylayan=self.editor)
        self.hakedis.refresh_from_db()
        return self.hakedis.satirlar.get()

    def test_onayli_satir_fiyat_orm_kilitli(self):
        satir = self._onayli_satir()
        satir.birim_fiyat = Decimal("999.00")
        with self.assertRaises(ValidationError):
            satir.save()
        satir.refresh_from_db()
        self.assertEqual(satir.birim_fiyat, Decimal("100.00"))

    def test_onayli_satir_miktar_orm_kilitli(self):
        satir = self._onayli_satir()
        satir.miktar = Decimal("99.0000")
        with self.assertRaises(ValidationError):
            satir.save()
        satir.refresh_from_db()
        self.assertEqual(satir.miktar, Decimal("40.0000"))

    def test_onayli_satir_serializer_kilitli(self):
        from .serializers import HakedisSatiriSerializer

        satir = self._onayli_satir()
        ser = HakedisSatiriSerializer(
            instance=satir, data={"miktar": "99.0000"}, partial=True,
        )
        self.assertFalse(ser.is_valid())

    def test_onayli_hakedis_nested_satir_patch_reddi(self):
        self._onayli_satir()
        yanit = self._istemci(self.editor).patch(
            f"/api/v1/construction/hakedisler/{self.hakedis.pk}/",
            {"satirlar": [{"poz": self.poz.pk, "miktar": "99.0000",
                            "birim_fiyat": "999.00"}]},
            format="json",
        )
        self.assertEqual(yanit.status_code, 400)
        self.assertEqual(self.hakedis.satirlar.get().birim_fiyat, Decimal("100.00"))

    def test_iptal_hakedis_satir_kilitli(self):
        hakedis_satirlari_olustur(self.hakedis)
        self._istemci(self.editor).delete(
            f"/api/v1/construction/hakedisler/{self.hakedis.pk}/"
        )
        self.hakedis.refresh_from_db()
        self.assertEqual(self.hakedis.durum, Hakedis.Durum.IPTAL)
        satir = self.hakedis.satirlar.get()
        satir.birim_fiyat = Decimal("555.00")
        with self.assertRaises(ValidationError):
            satir.save()
        satir.refresh_from_db()
        self.assertEqual(satir.birim_fiyat, Decimal("100.00"))

    def test_taslak_satir_duzenlenebilir(self):
        hakedis_satirlari_olustur(self.hakedis)
        satir = self.hakedis.satirlar.get()
        satir.miktar = Decimal("41.0000")
        satir.save()
        satir.refresh_from_db()
        self.assertEqual(satir.miktar, Decimal("41.0000"))
        self.assertEqual(satir.satir_tutar, Decimal("4100.00"))

    def test_admin_onayli_satir_readonly(self):
        from .admin import HakedisSatiriadmin

        satir = self._onayli_satir()
        readonly = HakedisSatiriadmin(HakedisSatiri, None).get_readonly_fields(
            None, obj=satir
        )
        self.assertIn("miktar", readonly)
        self.assertIn("birim_fiyat", readonly)

    def test_pozplan_snapshot_fiyat_degisiminden_etkilenmez(self):
        plan = PozPlan.objects.get(pk=self.plan.pk)
        self.assertEqual(plan.birim_fiyat_snapshot, Decimal("100.00"))
        PozFiyat.objects.filter(
            tenant=self.tenant, poz=self.poz, yil=2026
        ).update(birim_fiyat=Decimal("777.00"))
        plan.refresh_from_db()
        self.assertEqual(plan.birim_fiyat_snapshot, Decimal("100.00"))
        # ORM bypass denemesi geri alınır.
        plan.birim_fiyat_snapshot = Decimal("5.00")
        plan.save()
        plan.refresh_from_db()
        self.assertEqual(plan.birim_fiyat_snapshot, Decimal("100.00"))


class HakedisIdempotencyTests(HakedisBase):
    """FAZ 6C — hakediş onayında Idempotency-Key: 10x aynı key, FAILED retry, duplicate engeli."""

    def _zincir_sayilari(self):
        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket

        return (
            CariHareket.objects.filter(tenant=self.tenant, cari=self.cari).count(),
            MuhasebeFisi.objects.filter(
                tenant=self.tenant,
                fis_no=f"HD-{self.proje.proje_kodu}-{self.hakedis.donem}",
            ).count(),
        )

    def test_basarili_onay_tek_zincir(self):
        hakedis_satirlari_olustur(self.hakedis)
        yanit = self._istemci(self.editor).post(
            f"/api/v1/construction/hakedisler/{self.hakedis.pk}/onayla/"
        )
        self.assertEqual(yanit.status_code, 200)
        self.hakedis.refresh_from_db()
        self.assertEqual(self.hakedis.durum, Hakedis.Durum.ONAYLANDI)
        self.assertEqual(self._zincir_sayilari(), (1, 1))

    def test_ayni_key_on_kez_tek_zincir(self):
        hakedis_satirlari_olustur(self.hakedis)
        istemci = self._istemci(self.editor)
        gonder = {"HTTP_IDEMPOTENCY_KEY": "hakedis-sabit-1"}
        ilk = None
        for _ in range(10):
            yanit = istemci.post(
                f"/api/v1/construction/hakedisler/{self.hakedis.pk}/onayla/",
                **gonder,
            )
            self.assertEqual(yanit.status_code, 200)
            if ilk is None:
                ilk = yanit.json()["data"]
            self.assertEqual(yanit.json()["data"], ilk)
        self.assertEqual(self._zincir_sayilari(), (1, 1))

    def test_failed_retry_ikinci_zincir_olusturmaz(self):
        from finance.models import IdempotencyKey

        hakedis = Hakedis.objects.create(
            tenant=self.tenant, proje=self.proje, donem="2026-04"
        )
        HakedisSatiri.objects.create(
            hakedis=hakedis, poz=self.poz,
            miktar=Decimal("10.0000"), birim_fiyat=Decimal("100.00"),
        )
        istemci = self._istemci(self.editor)
        gonder = {"HTTP_IDEMPOTENCY_KEY": "hakedis-sabit-2"}
        kotu = istemci.post(
            f"/api/v1/construction/hakedisler/{hakedis.pk}/onayla/", **gonder
        )
        self.assertEqual(kotu.status_code, 400)
        self.assertEqual(
            IdempotencyKey.objects.get(
                tenant=self.tenant, operation="hakedis.onayla",
                key="hakedis-sabit-2",
            ).status,
            IdempotencyKey.Durum.FAILED,
        )
        hakedis.cari = self.cari
        hakedis.save(update_fields=["cari", "updated_at"])
        iyi = istemci.post(
            f"/api/v1/construction/hakedisler/{hakedis.pk}/onayla/", **gonder
        )
        self.assertEqual(iyi.status_code, 200)
        hakedis.refresh_from_db()
        self.assertEqual(hakedis.durum, Hakedis.Durum.ONAYLANDI)
        from cari.models import CariHareket

        self.assertEqual(
            CariHareket.objects.filter(tenant=self.tenant, cari=self.cari).count(), 1
        )

    def test_duplicate_cari_ve_fis_engeli(self):
        hakedis_satirlari_olustur(self.hakedis)
        istemci = self._istemci(self.editor)
        self.assertEqual(
            istemci.post(
                f"/api/v1/construction/hakedisler/{self.hakedis.pk}/onayla/",
                **{"HTTP_IDEMPOTENCY_KEY": "hakedis-ilk"},
            ).status_code,
            200,
        )
        tekrar = istemci.post(
            f"/api/v1/construction/hakedisler/{self.hakedis.pk}/onayla/",
            **{"HTTP_IDEMPOTENCY_KEY": "hakedis-ikinci"},
        )
        self.assertEqual(tekrar.status_code, 400)
        self.assertEqual(self._zincir_sayilari(), (1, 1))


class HakedisSorguTests(HakedisBase):
    """FAZ 6E §9 — hakediş endpointlerinde satır-bağımsız query sayısı (yeni N+1 yok)."""

    def _sorgu_sayisi(self, url):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            yanit = self._istemci(self.editor).get(url)
        self.assertEqual(yanit.status_code, 200)
        return len(ctx)

    def _ek_hakedis(self, donem):
        diger = Hakedis.objects.create(
            tenant=self.tenant, proje=self.proje, donem=donem, cari=self.cari
        )
        HakedisSatiri.objects.create(
            hakedis=diger, poz=self.poz,
            miktar=Decimal("5.0000"), birim_fiyat=Decimal("100.00"),
        )
        return diger

    def test_liste_satir_artisinda_sorgu_sabiti(self):
        # FAZ 6D BULGU (6E kapsam dışı): satır başına 3 sorgu (satırlar×2 + poz).
        # Bu test mevcut şekli kilitler; yeni satır-başı sorgu eklenirse patlar.
        hakedis_satirlari_olustur(self.hakedis)
        bir = self._sorgu_sayisi("/api/v1/construction/hakedisler/")
        self._ek_hakedis("2026-04")
        self._ek_hakedis("2026-05")
        self._ek_hakedis("2026-06")
        uc = self._sorgu_sayisi("/api/v1/construction/hakedisler/")
        self.assertLessEqual(uc, bir + 10)

    def test_detay_sorgu_sinirli(self):
        hakedis_satirlari_olustur(self.hakedis)
        sayi = self._sorgu_sayisi(
            f"/api/v1/construction/hakedisler/{self.hakedis.pk}/"
        )
        self.assertLessEqual(sayi, 10)
