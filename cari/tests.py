from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User, UserRole

from .models import Cari, CariHareket


class CariBase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Cari A.Ş.", slug="cari-as")
        self.diger = Tenant.objects.create(name="Komşu Ltd.", slug="komsu")
        import uuid
        unique = uuid.uuid4().hex[:8]
        self.muhasebeci = User.objects.create_user(
            username=f"muhasebe_{unique}", password="x", email=f"m_{unique}@c.com",
            tenant=self.tenant, role=UserRole.MUHASEBE,
        )
        self.satisci = User.objects.create_user(
            username=f"satis_{unique}", password="x", email=f"s_{unique}@c.com",
            tenant=self.tenant, role=UserRole.SATIS,
        )
        self.cari = Cari.objects.create(
            tenant=self.tenant, ad="Yüklenici Ltd.", tip="taseron", tur="kurumsal",
        )


class CariModelTests(CariBase):
    def test_vergi_no_10_hane_zorunlu(self):
        kart = Cari(tenant=self.tenant, ad="X", vergi_no="123")
        with self.assertRaises(Exception):
            kart.full_clean()

    def test_ad_tenant_icinde_unique(self):
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Cari.objects.create(tenant=self.tenant, ad="Yüklenici Ltd.")


class CariApiTests(CariBase):
    def _istemci(self, kullanici):
        istemci = APIClient()
        istemci.force_authenticate(user=kullanici)
        return istemci

    def test_satis_okur_ama_yazamaz(self):
        istemci = self._istemci(self.satisci)
        self.assertEqual(istemci.get("/api/v1/cari/cariler/").status_code, 200)
        yanit = istemci.post(
            "/api/v1/cari/cariler/", {"ad": "Yeni"}, format="json",
        )
        self.assertEqual(yanit.status_code, 403)

    def test_muhasebe_cari_acar_telefon_maskeli_doner(self):
        istemci = self._istemci(self.muhasebeci)
        yanit = istemci.post(
            "/api/v1/cari/cariler/",
            {"ad": "Maskeli A.Ş.", "telefon": "05321234567", "iban": "TR120001000000000000000001"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 201)
        veri = yanit.json()["data"]
        self.assertNotIn("telefon", veri)
        self.assertEqual(veri["telefon_maskeli"], "05*******67")
        self.assertTrue(veri["iban_maskeli"].startswith("TR12"))

    def test_hareket_silinemez_iptal_edilir(self):
        istemci = self._istemci(self.muhasebeci)
        hareket = CariHareket.objects.create(
            tenant=self.tenant, cari=self.cari, yon="borc",
            tutar=Decimal("1000.00"), islem_tarihi=date(2026, 3, 1),
        )
        self.assertEqual(
            istemci.delete(f"/api/v1/cari/cari-hareketler/{hareket.pk}/").status_code, 400
        )
        yanit = istemci.post(
            f"/api/v1/cari/cari-hareketler/{hareket.pk}/iptal/",
            {"iptal_nedeni": "Yanlış cari"}, format="json",
        )
        self.assertEqual(yanit.status_code, 200)
        hareket.refresh_from_db()
        self.assertTrue(hareket.is_cancelled)

    def test_tenant_izolasyonu(self):
        Cari.objects.create(tenant=self.diger, ad="Yüklenici Ltd.")
        istemci = self._istemci(self.muhasebeci)
        veri = istemci.get("/api/v1/cari/cariler/").json()["data"]
        self.assertEqual(veri["count"], 1)

    def test_tenantsiz_super_admin_firma_secmeden_cari_acamaz(self):
        admin = User.objects.create_superuser(
            username="global-admin", password="admin123", email="admin@c.com"
        )
        istemci = self._istemci(admin)
        yanit = istemci.post(
            "/api/v1/cari/cariler/", {"ad": "Firma Seçilmeden"}, format="json"
        )
        self.assertEqual(yanit.status_code, 400)
        self.assertIn("tenant", yanit.json()["errors"])

    def test_tenantsiz_super_admin_secili_firmaya_cari_acar(self):
        admin = User.objects.create_superuser(
            username="scoped-admin", password="admin123", email="scoped@c.com"
        )
        istemci = self._istemci(admin)
        yanit = istemci.post(
            "/api/v1/cari/cariler/",
            {"ad": "Seçili Firmaya Cari", "tur": "kurumsal"},
            format="json",
            HTTP_X_TENANT_ID=str(self.tenant.pk),
        )
        self.assertEqual(yanit.status_code, 201)
        self.assertEqual(yanit.json()["data"]["tenant"], self.tenant.pk)


class HareketPaginationTests(CariBase):
    """FAZ 6E — cari-hareketler sayfalı döner (standart contract)."""

    def _istemci(self, kullanici):
        istemci = APIClient()
        istemci.force_authenticate(user=kullanici)
        return istemci

    def _hareket_ac(self, n=150):
        CariHareket.objects.bulk_create([
            CariHareket(
                tenant=self.tenant, cari=self.cari,
                yon="borc" if i % 2 == 0 else "alacak",
                tutar=Decimal("100.00"), islem_tarihi=date(2026, 3, 1),
            )
            for i in range(n)
        ])

    def test_hareketler_sayfali_contract(self):
        self._hareket_ac()
        veri = self._istemci(self.muhasebeci).get(
            f"/api/v1/cari/cariler/{self.cari.pk}/hareketler/"
        ).json()["data"]
        self.assertEqual(veri["count"], 150)
        self.assertEqual(len(veri["results"]), 25)
        self.assertIsNotNone(veri["next"])
        self.assertIsNone(veri["previous"])

    def test_hareketler_ikinci_sayfa_ve_siralama(self):
        self._hareket_ac()
        istemci = self._istemci(self.muhasebeci)
        sayfa1 = istemci.get(
            f"/api/v1/cari/cariler/{self.cari.pk}/hareketler/"
        ).json()["data"]["results"]
        sayfa2 = istemci.get(
            f"/api/v1/cari/cariler/{self.cari.pk}/hareketler/?page=2"
        ).json()["data"]["results"]
        self.assertEqual(len(sayfa2), 25)
        idler1 = {s["id"] for s in sayfa1}
        idler2 = [s["id"] for s in sayfa2]
        self.assertTrue(idler1.isdisjoint(idler2))
        self.assertEqual(idler2, sorted(idler2, reverse=True))

    def test_hareketler_tenant_kapsamli(self):
        self._hareket_ac(n=30)
        yabanci = Cari.objects.create(tenant=self.diger, ad="Yabancı")
        CariHareket.objects.create(
            tenant=self.diger, cari=yabanci, yon="borc",
            tutar=Decimal("1.00"), islem_tarihi=date(2026, 3, 1),
        )
        veri = self._istemci(self.muhasebeci).get(
            f"/api/v1/cari/cariler/{self.cari.pk}/hareketler/"
        ).json()["data"]
        self.assertEqual(veri["count"], 30)


class OzetEsitlikTests(CariBase):
    """FAZ 6E — cari özet DB aggregation ile birebir aynı sonucu verir."""

    def _istemci(self, kullanici):
        istemci = APIClient()
        istemci.force_authenticate(user=kullanici)
        return istemci

    def test_ozet_karisik_yon_iptal_haric(self):
        for i, (yon, tutar) in enumerate([
            ("borc", "1000.00"), ("alacak", "400.00"), ("borc", "250.50"),
            ("alacak", "100.25"), ("borc", "75.00"),
        ]):
            CariHareket.objects.create(
                tenant=self.tenant, cari=self.cari, yon=yon,
                tutar=Decimal(tutar), islem_tarihi=date(2026, 3, 1),
            )
        CariHareket.objects.create(
            tenant=self.tenant, cari=self.cari, yon="borc",
            tutar=Decimal("9999.00"), islem_tarihi=date(2026, 3, 1),
            is_cancelled=True,
        )
        veri = self._istemci(self.muhasebeci).get(
            f"/api/v1/cari/cariler/{self.cari.pk}/ozet/"
        ).json()["data"]
        self.assertEqual(veri["borc"], "1325.50")
        self.assertEqual(veri["alacak"], "500.25")
        self.assertEqual(veri["bakiye"], "825.25")

    def test_ozet_hareketsiz_cari_sifir(self):
        veri = self._istemci(self.muhasebeci).get(
            f"/api/v1/cari/cariler/{self.cari.pk}/ozet/"
        ).json()["data"]
        self.assertEqual(veri, {"borc": "0", "alacak": "0", "bakiye": "0"})


class ListeSabitlikTests(CariBase):
    """FAZ 6E §9 — cari hareket listesinde satır-bağımsız query sayısı."""

    def _istemci(self, kullanici):
        istemci = APIClient()
        istemci.force_authenticate(user=kullanici)
        return istemci

    def test_carihareket_liste_satir_artisinda_sorgu_sabiti(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        CariHareket.objects.bulk_create([
            CariHareket(
                tenant=self.tenant, cari=self.cari, yon="borc",
                tutar=Decimal("10.00"), islem_tarihi=date(2026, 3, 1),
            )
            for _ in range(50)
        ])

        def say():
            with CaptureQueriesContext(connection) as ctx:
                yanit = self._istemci(self.muhasebeci).get(
                    "/api/v1/cari/cari-hareketler/"
                )
            self.assertEqual(yanit.status_code, 200)
            return len(ctx)

        elli = say()
        CariHareket.objects.bulk_create([
            CariHareket(
                tenant=self.tenant, cari=self.cari, yon="borc",
                tutar=Decimal("10.00"), islem_tarihi=date(2026, 3, 1),
            )
            for _ in range(50)
        ])
        self.assertEqual(say(), elli)
