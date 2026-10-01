"""FAZ 5 E2E — metraj/maliyet/plan/IFC entegrasyonları + IV-A proje senaryosu."""

import uuid
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User, UserRole

from .imports import normalize_yapi_sinifi
from .models import (
    IFCImportJob,
    IFCQuantityDraft,
    Mahal,
    MahalElemani,
    Malzeme,
    Metraj,
    Poz,
    PozFiyat,
    PozGrubu,
    PozPlan,
    Proje,
    YaklasikMaliyet,
    YaklasikMaliyetSatiri,
    YapiSinifiBirimMaliyet,
)
from .services import (
    metraj_kontrolu,
    proje_kar_zarar,
    proje_poz_etkin_fiyati,
    s_egrisi_raporu,
)
from .services.mahal_metraj import (
    mahal_elemanlarindan_yaklasik_maliyet_uret,
    mahal_metraj_uret,
)
from .services.metraj_entegrasyon import (
    ifc_drafttan_metraj_uret,
    metraj_satirlarini_yenile,
    metrajdan_gercek_miktar_ata,
    metrajdan_maliyet_satiri,
)

IFC_ORNEK = b"""ISO-10303-21;\n#10=IFCQUANTITYVOLUME('P-1001',$,$,2.5);\nEND-ISO-10303-21;"""


class Faz5Base(TestCase):
    def setUp(self):
        unique = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name="FAZ5 A.Ş.", slug=f"faz5-{unique}")
        self.editor = User.objects.create_user(
            username=f"faz5_{unique}", password="x", email=f"faz5_{unique}@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )
        self.grup = PozGrubu.objects.create(tenant=self.tenant, kod="BET", ad="Beton")
        self.poz = Poz.objects.create(
            tenant=self.tenant, poz_no="P-1001", ad="C30 Beton", birim="m³", grup=self.grup
        )
        PozFiyat.objects.create(
            tenant=self.tenant, poz=self.poz, yil=2026, birim_fiyat=Decimal("1250.50")
        )

    def _istemci(self):
        istemci = APIClient()
        istemci.force_authenticate(user=self.editor)
        return istemci


class MetrajMaliyetEntegrasyonTests(Faz5Base):
    def test_metrajdan_satir_idempotent(self):
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="M-1", ad="M")
        ym = YaklasikMaliyet.objects.create(tenant=self.tenant, proje=proje, yil=2026)
        metraj = Metraj.objects.create(
            tenant=self.tenant, ad="M-1 metraj", ifade="10", sonuc=Decimal("10"),
        )
        satir1, olustu1 = metrajdan_maliyet_satiri(ym, metraj, self.poz)
        satir2, olustu2 = metrajdan_maliyet_satiri(ym, metraj, self.poz)
        self.assertTrue(olustu1)
        self.assertFalse(olustu2)
        self.assertEqual(satir1.pk, satir2.pk)
        self.assertEqual(satir1.miktar, Decimal("10.0000"))
        self.assertEqual(satir1.birim_fiyat_snapshot, Decimal("1250.50"))
        self.assertEqual(
            YaklasikMaliyetSatiri.objects.filter(yaklasik_maliyet=ym).count(), 1
        )

    def test_metraj_degisim_satiri_yeniler(self):
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="M-2", ad="M")
        ym = YaklasikMaliyet.objects.create(tenant=self.tenant, proje=proje, yil=2026)
        metraj = Metraj.objects.create(
            tenant=self.tenant, ad="M-2 metraj", ifade="10", sonuc=Decimal("10"),
        )
        metrajdan_maliyet_satiri(ym, metraj, self.poz)
        metraj.sonuc = Decimal("15")
        metraj.save(update_fields=["sonuc"])
        self.assertEqual(metraj_satirlarini_yenile(metraj), 1)
        satir = YaklasikMaliyetSatiri.objects.get(yaklasik_maliyet=ym)
        self.assertEqual(satir.miktar, Decimal("15.0000"))
        self.assertEqual(satir.toplam_tutar, Decimal("18757.50"))

    def test_metrajdan_gercek_miktar_deterministik(self):
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="M-3", ad="M")
        plan = PozPlan.objects.create(
            tenant=self.tenant, proje=proje, poz=self.poz, yil=2026,
            planlanan_miktar=Decimal("20"),
        )
        metraj = Metraj.objects.create(
            tenant=self.tenant, ad="M-3 metraj", ifade="8", sonuc=Decimal("8"),
        )
        metrajdan_gercek_miktar_ata(plan, metraj)
        plan.refresh_from_db()
        self.assertEqual(plan.gercek_miktar, Decimal("8.0000"))
        self.assertEqual(plan.metraj, metraj)
        metrajdan_gercek_miktar_ata(plan, metraj)
        plan.refresh_from_db()
        self.assertEqual(plan.gercek_miktar, Decimal("8.0000"))
        rapor = s_egrisi_raporu(proje, 2026)
        self.assertEqual(rapor["toplam_gercek_deger"], "10004.00")

    def test_metraj_degisim_miktari_yayar_fiyati_korur(self):
        """FAZ 6C — Metraj miktar değişimi yayılır (tasarım), fiyat snapshot'ı sabit kalır."""
        from construction.models import YaklasikMaliyetSatiri

        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="M-4", ad="M")
        ym = YaklasikMaliyet.objects.create(tenant=self.tenant, proje=proje, yil=2026)
        metraj = Metraj.objects.create(
            tenant=self.tenant, ad="M-4 metraj", ifade="10", sonuc=Decimal("10"),
        )
        metrajdan_maliyet_satiri(ym, metraj, self.poz)
        metraj.sonuc = Decimal("20")
        metraj.save(update_fields=["sonuc"])
        self.assertEqual(metraj_satirlarini_yenile(metraj), 1)
        satir = YaklasikMaliyetSatiri.objects.get(yaklasik_maliyet=ym)
        self.assertEqual(satir.miktar, Decimal("20.0000"))
        self.assertEqual(satir.birim_fiyat_snapshot, Decimal("1250.50"))


class IfcEntegrasyonTests(Faz5Base):
    def _is_yukle(self):
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="IFC-1", ad="IFC")
        yanit = self._istemci().post(
            "/api/v1/construction/ifc-importlari/",
            {"project": proje.pk, "year": 2026,
             "file": SimpleUploadedFile("m.ifc", IFC_ORNEK, "application/octet-stream")},
            format="multipart",
        )
        self.assertEqual(yanit.status_code, 201)
        job = IFCImportJob.objects.get(pk=yanit.json()["data"]["id"])
        self._istemci().post(f"/api/v1/construction/ifc-importlari/{job.pk}/process/")
        job.refresh_from_db()
        return job

    def test_process_tekrar_reddedilir(self):
        job = self._is_yukle()
        sayi = IFCQuantityDraft.objects.filter(job=job).count()
        self.assertGreater(sayi, 0)
        yanit = self._istemci().post(f"/api/v1/construction/ifc-importlari/{job.pk}/process/")
        self.assertEqual(yanit.status_code, 400)
        self.assertEqual(IFCQuantityDraft.objects.filter(job=job).count(), sayi)

    def test_approve_eslesmemis_raporlar_ve_metraj_uretir(self):
        job = self._is_yukle()
        # Eşleşmemiş taslak ekle (sessiz geçilmemeli, raporda görünmeli).
        IFCQuantityDraft.objects.create(
            tenant=self.tenant, job=job, project=job.project, year=2026,
            poz=None, source_name="BILINMEYEN-1", quantity=Decimal("1"),
            unit="m", mapping_status="unmapped",
        )
        yanit = self._istemci().post(
            f"/api/v1/construction/ifc-importlari/{job.pk}/approve/",
            {"create_plan": "true", "create_metraj": "true"},
            format="multipart",
        )
        self.assertEqual(yanit.status_code, 200)
        veri = yanit.json()["data"]
        self.assertEqual(veri["created"], 1)
        self.assertEqual(veri["metrajlar"], 1)
        self.assertEqual(len(veri["unmapped"]), 1)
        self.assertTrue(
            Metraj.objects.filter(
                tenant=self.tenant, ad__startswith=f"IFC-{job.pk}-"
            ).exists()
        )
        # İkinci onay: plan da metraj da artmaz.
        ikinci = self._istemci().post(
            f"/api/v1/construction/ifc-importlari/{job.pk}/approve/",
            {"create_plan": "true", "create_metraj": "true"},
            format="multipart",
        )
        self.assertEqual(ikinci.json()["data"]["created"], 0)
        self.assertEqual(ikinci.json()["data"]["metrajlar"], 0)
        self.assertEqual(
            Metraj.objects.filter(
                tenant=self.tenant, ad__startswith=f"IFC-{job.pk}-"
            ).count(),
            1,
        )

    def test_draft_metraj_idempotent(self):
        job = self._is_yukle()
        draft = job.draft_rows.filter(mapping_status="mapped").first()
        m1, o1 = ifc_drafttan_metraj_uret(draft)
        m2, o2 = ifc_drafttan_metraj_uret(draft)
        self.assertTrue(o1)
        self.assertFalse(o2)
        self.assertEqual(m1.pk, m2.pk)


class IvAProjeE2ETests(Faz5Base):
    def test_iv_a_tam_proje_senaryosu(self):
        # 1-2. Tenant/proje + IV-A sınıfı ("4A" normalize olur).
        self.assertEqual(normalize_yapi_sinifi("4A"), "IV-A")
        proje = Proje.objects.create(tenant=self.tenant, proje_kodu="IVA-1", ad="IV-A Konut")
        YapiSinifiBirimMaliyet.objects.create(
            tenant=self.tenant, sinif_kodu="IV-A", yil=2026,
            birim_maliyet=Decimal("15000.00"),
        )
        # 3-4. Poz şablonu: grup + 2 poz + fiyatlar projeye kopyalanır gibi kurulur.
        grup2 = PozGrubu.objects.create(tenant=self.tenant, kod="INCE", ad="İnce")
        poz2 = Poz.objects.create(
            tenant=self.tenant, poz_no="P-1002", ad="Sıva", birim="m²", grup=grup2
        )
        PozFiyat.objects.create(
            tenant=self.tenant, poz=poz2, yil=2026, birim_fiyat=Decimal("98.70")
        )
        self.assertEqual(Proje.objects.filter(pk=proje.pk).count(), 1)
        self.assertEqual(Poz.objects.filter(tenant=self.tenant).count(), 2)
        # 5-6. Blok/kat/mahal (blok katmanı kod önekiyle).
        blok_mahal = Mahal.objects.create(
            tenant=self.tenant, proje=proje, kod="BLOKA-ZEMIN", ad="Blok A Zemin",
            kat="0", alan=Decimal("120.00"),
        )
        MahalElemani.objects.create(
            tenant=self.tenant, mahal=blok_mahal, eleman_tipi="Kapı", ad="D1",
            miktar=Decimal("2"), aciklama="genişlik: 0.9",
        )
        # 7. Metraj.
        sonuc = mahal_metraj_uret(blok_mahal, {"uzunluk": "10", "genislik": "12"})
        self.assertGreater(sonuc["metrajlar"]["duvar"], Decimal("0"))
        # 8. Etkin fiyat.
        self.assertEqual(proje_poz_etkin_fiyati(proje, self.poz, 2026), Decimal("1250.50"))
        # 9-10. Yaklaşık maliyet + poz planı.
        ym = YaklasikMaliyet.objects.create(tenant=self.tenant, proje=proje, yil=2026)
        ym, satirlar = mahal_elemanlarindan_yaklasik_maliyet_uret(
            ym, blok_mahal, poz_eslestirme={"duvar": self.poz.pk},
        )
        self.assertGreaterEqual(len(satirlar), 1)
        plan = PozPlan.objects.create(
            tenant=self.tenant, proje=proje, poz=self.poz, yil=2026,
            planlanan_miktar=Decimal("50"),
        )
        # 11. Gerçekleşen miktar.
        plan.gercek_miktar = Decimal("40")
        plan.save()
        # 12-15. Özetler.
        s_egri = s_egrisi_raporu(proje, 2026)
        self.assertEqual(s_egri["toplam_plan_deger"], "62525.00")
        kz = proje_kar_zarar(proje, 2026)
        self.assertEqual(kz["butcelenen_maliyet"], "62525.00")
        mk = metraj_kontrolu(proje, 2026)
        self.assertIn("kritik", mk)
        # 16. m² maliyet (toplam / blok alanı).
        m2 = (Decimal(s_egri["toplam_plan_deger"]) / blok_mahal.alan).quantize(Decimal("0.01"))
        self.assertEqual(m2, Decimal("521.04"))
        # 17-18. Tekrar + duplicate yok.
        ym2, satirlar2 = mahal_elemanlarindan_yaklasik_maliyet_uret(
            ym, blok_mahal, poz_eslestirme={"duvar": self.poz.pk},
        )
        self.assertEqual(
            YaklasikMaliyetSatiri.objects.filter(yaklasik_maliyet=ym).count(), len(satirlar)
        )
        self.assertEqual(YaklasikMaliyetSatiri.objects.filter(yaklasik_maliyet=ym).count(), len(satirlar2))
        with self.assertRaises(Exception):
            PozPlan.objects.create(
                tenant=self.tenant, proje=proje, poz=self.poz, yil=2026,
                planlanan_miktar=Decimal("5"),
            )
