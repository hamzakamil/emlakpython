from decimal import Decimal

from django.test import TestCase

from tenants.models import Tenant

from .models import Mahal, MahalElemani, Poz, PozFiyat, PozGrubu, Proje, YaklasikMaliyet
from .services.mahal_metraj import mahal_elemanlarindan_yaklasik_maliyet_uret, mahal_metraj_uret


class MahalMetrajTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Metraj A", slug="metraj-a")
        self.proje = Proje.objects.create(tenant=self.tenant, proje_kodu="P4", ad="Paket 4")
        self.mahal = Mahal.objects.create(
            tenant=self.tenant, proje=self.proje, kod="B01", ad="Banyo", alan=Decimal("20")
        )

    def test_dort_bes_banyo_metrajlari(self):
        MahalElemani.objects.create(
            tenant=self.tenant, mahal=self.mahal, eleman_tipi="kapı", miktar=1,
            aciklama="genişlik=0.90",
        )
        result = mahal_metraj_uret(self.mahal, uzunluk=4, genislik=5, yukseklik=2.8)
        self.assertEqual(result["metrajlar"]["doseme"], Decimal("20.000"))
        self.assertEqual(result["metrajlar"]["tavan"], Decimal("20.000"))
        self.assertEqual(result["metrajlar"]["duvar"], Decimal("50.400"))
        self.assertEqual(result["metrajlar"]["supurgelik"], Decimal("17.100"))
        self.assertEqual(result["metrajlar"]["kapi"], Decimal("1.00"))
        # Re-running is idempotent despite Metraj.ad being tenant-unique.
        mahal_metraj_uret(self.mahal, uzunluk=4, genislik=5, yukseklik=2.8)
        self.assertEqual(result["kayitlar"][0].__class__.objects.filter(tenant=self.tenant).count(), 7)

    def test_metrajdan_yaklasik_maliyet_end_to_end(self):
        grup = PozGrubu.objects.create(tenant=self.tenant, kod="B", ad="Banyo")
        poz = Poz.objects.create(tenant=self.tenant, poz_no="B-01", ad="Seramik", birim="m2", grup=grup)
        PozFiyat.objects.create(tenant=self.tenant, poz=poz, yil=2026, birim_fiyat=Decimal("100"))
        maliyet = YaklasikMaliyet.objects.create(tenant=self.tenant, proje=self.proje, yil=2026)
        mahal_elemanlarindan_yaklasik_maliyet_uret(
            maliyet, self.mahal, {"doseme": poz}, {"uzunluk": 4, "genislik": 5, "yukseklik": 2.8}
        )
        maliyet.refresh_from_db()
        self.assertEqual(maliyet.satirlar.count(), 1)
        self.assertEqual(maliyet.toplam_tutar, Decimal("2000.00"))
        mahal_elemanlarindan_yaklasik_maliyet_uret(
            maliyet, self.mahal, {"doseme": poz}, {"uzunluk": 4, "genislik": 5, "yukseklik": 2.8}
        )
        self.assertEqual(maliyet.satirlar.count(), 1)
