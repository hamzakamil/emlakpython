"""FAZ 3A testleri — talep/sipariş akışı, tenant izolasyonu, dönüşüm, yetkiler."""

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from construction.models import (
    Mahal,
    Malzeme,
    Poz,
    PozGrubu,
    Proje,
    Tedarikci,
    TedarikciTeklifi,
)
from tenants.models import Tenant
from users.models import User, UserRole

from .models import (
    BelgeTipi,
    MalKabul,
    SatinAlmaSiparisi,
    SatinAlmaTalebi,
)
from .services import belge_numarasi_uret, talepten_siparis_olustur


class SatinAlmaBase(TestCase):
    def setUp(self):
        unique = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name="Satın Alma A.Ş.", slug=f"satin-alma-{unique}")
        self.diger = Tenant.objects.create(name="Diğer A.Ş.", slug=f"diger-{unique}")
        self.editor = User.objects.create_user(
            username=f"satin_{unique}", password="x", email=f"satin_{unique}@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )
        self.reader = User.objects.create_user(
            username=f"saha_{unique}", password="x", email=f"saha_{unique}@example.com",
            tenant=self.tenant, role=UserRole.SANTIYE_SEFI,
        )
        self.proje = Proje.objects.create(
            tenant=self.tenant, proje_kodu="SAT-1", ad="Satın Alma Projesi"
        )
        self.grup = PozGrubu.objects.create(tenant=self.tenant, kod="SAT", ad="Satın Alma")
        self.poz = Poz.objects.create(
            tenant=self.tenant, poz_no="SAT-100", ad="Satın Alma Pozu", birim="adet",
            grup=self.grup,
        )
        self.malzeme = Malzeme.objects.create(
            tenant=self.tenant, malzeme_kodu="SAT-M", ad="Satın Alma Malzemesi", birim="adet"
        )
        self.mahal = Mahal.objects.create(
            tenant=self.tenant, proje=self.proje, kod="M-1", ad="Mahal 1"
        )
        self.tedarikci = Tedarikci.objects.create(
            tenant=self.tenant, firma_adi="Satıcı Ltd.", firma_kodu=f"SAT-{unique}"
        )
        self.teklif = TedarikciTeklifi.objects.create(
            tenant=self.tenant, proje=self.proje, malzeme=self.malzeme,
            tedarikci=self.tedarikci, miktar=Decimal("10"), birim_fiyat=Decimal("100"),
        )

    def _istemci(self, kullanici):
        istemci = APIClient()
        istemci.force_authenticate(user=kullanici)
        return istemci

    def _talep(self, **ek):
        veri = {"tenant": self.tenant, "proje": self.proje, "talep_sahibi": self.editor}
        veri.update(ek)
        if "talep_no" not in veri:
            veri["talep_no"] = belge_numarasi_uret(self.tenant.pk, BelgeTipi.TALEP)
        return SatinAlmaTalebi.objects.create(**veri)


class TalepTests(SatinAlmaBase):
    def test_talep_olusturma(self):
        talep = self._talep()
        self.assertTrue(talep.talep_no.startswith("ST-"))
        self.assertEqual(talep.durum, SatinAlmaTalebi.Durum.TASLAK)
        self.assertEqual(talep.talep_sahibi, self.editor)

    def test_talep_kalemi_olusturma(self):
        from .models import SatinAlmaTalebiKalemi

        talep = self._talep()
        kalem = SatinAlmaTalebiKalemi.objects.create(
            tenant=self.tenant, talep=talep, malzeme=self.malzeme, poz=self.poz,
            mahal=self.mahal, miktar=Decimal("5"),
        )
        self.assertEqual(kalem.birim, "adet")
        self.assertEqual(kalem.talep.proje, self.proje)

    def test_tenant_izolasyonu(self):
        self._talep()
        yabanci = self._istemci(self.editor).get("/api/v1/purchase-requests/")
        self.assertEqual(yabanci.json()["data"]["count"], 1)
        # Diğer tenant bu talebi göremez (ayrı kullanıcı gerekir; aynı kullanıcı
        # kendi tenant'ından çıkamaz).
        diger_kullanici = User.objects.create_user(
            username=f"diger_{uuid.uuid4().hex[:8]}", password="x",
            email=f"diger_{uuid.uuid4().hex[:8]}@example.com",
            tenant=self.diger, role=UserRole.MALIYET_MUHENDISI,
        )
        yanit = self._istemci(diger_kullanici).get("/api/v1/purchase-requests/")
        self.assertEqual(yanit.json()["data"]["count"], 0)

    def test_tenant_disi_kaynak_reddedilir(self):
        yabanci_malzeme = Malzeme.objects.create(
            tenant=self.diger, malzeme_kodu="YAB", ad="Yabancı", birim="adet"
        )
        talep = self._talep()
        yanit = self._istemci(self.editor).post(
            "/api/v1/purchase-request-items/",
            {"talep": talep.pk, "malzeme": yabanci_malzeme.pk, "miktar": "1"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 400)

    def test_teklif_secimi_ve_dogrulamasi(self):
        from .models import SatinAlmaTalebiKalemi

        talep = self._talep()
        kalem = SatinAlmaTalebiKalemi.objects.create(
            tenant=self.tenant, talep=talep, malzeme=self.malzeme,
            miktar=Decimal("5"), secili_teklif=self.teklif,
        )
        self.assertEqual(kalem.secili_teklif, self.teklif)
        # Uyumsuz teklif (başka malzeme) reddedilir.
        diger_malzeme = Malzeme.objects.create(
            tenant=self.tenant, malzeme_kodu="DIG", ad="Diğer", birim="adet"
        )
        with self.assertRaises(ValidationError):
            SatinAlmaTalebiKalemi.objects.create(
                tenant=self.tenant, talep=talep, malzeme=diger_malzeme,
                miktar=Decimal("1"), secili_teklif=self.teklif,
            )

    def test_talep_onay_akisi(self):
        talep = self._talep()
        istemci = self._istemci(self.editor)
        self.assertEqual(
            istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onaya-gonder/").status_code, 200
        )
        self.assertEqual(
            istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onayla/").status_code, 200
        )
        talep.refresh_from_db()
        self.assertEqual(talep.durum, SatinAlmaTalebi.Durum.ONAYLANDI)
        # Onaylı talepte doğrudan onay geçersizdir.
        self.assertEqual(
            istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onayla/").status_code, 400
        )

    def test_talep_reddi(self):
        talep = self._talep()
        istemci = self._istemci(self.editor)
        istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onaya-gonder/")
        self.assertEqual(
            istemci.post(f"/api/v1/purchase-requests/{talep.pk}/reddet/").status_code, 200
        )
        talep.refresh_from_db()
        self.assertEqual(talep.durum, SatinAlmaTalebi.Durum.REDDEDILDI)

    def test_iptal_islemi(self):
        talep = self._talep()
        yanit = self._istemci(self.editor).delete(f"/api/v1/purchase-requests/{talep.pk}/")
        self.assertEqual(yanit.status_code, 200)
        talep.refresh_from_db()
        self.assertEqual(talep.durum, SatinAlmaTalebi.Durum.IPTAL)
        self.assertTrue(SatinAlmaTalebi.objects.filter(pk=talep.pk).exists())

    def test_yetki_kontrolu_okur_yazamaz(self):
        talep = self._talep()
        okur = self._istemci(self.reader)
        self.assertEqual(okur.get("/api/v1/purchase-requests/").status_code, 200)
        self.assertEqual(
            okur.post(f"/api/v1/purchase-requests/{talep.pk}/onayla/").status_code, 403
        )


class DonusumTests(SatinAlmaBase):
    def _onayli_talep(self):
        from .models import SatinAlmaTalebiKalemi

        talep = self._talep(durum=SatinAlmaTalebi.Durum.ONAYLANDI)
        SatinAlmaTalebiKalemi.objects.create(
            tenant=self.tenant, talep=talep, malzeme=self.malzeme, poz=self.poz,
            miktar=Decimal("5"), secili_teklif=self.teklif,
        )
        return talep

    def test_talepten_siparis_olusur(self):
        talep = self._onayli_talep()
        yanit = self._istemci(self.editor).post(
            f"/api/v1/purchase-requests/{talep.pk}/talepten-siparis-olustur/",
            {"tedarikci": self.tedarikci.pk},
            format="json",
        )
        self.assertEqual(yanit.status_code, 200, yanit.content)
        veri = yanit.json()["data"]
        self.assertTrue(veri["siparis_no"].startswith("SS-"))
        self.assertEqual(veri["kaynak_talep"], talep.pk)
        kalem = veri["kalemler"][0]
        self.assertEqual(kalem["birim_fiyat"], "100.00")
        self.assertEqual(kalem["toplam_tutar"], "500.00")
        talep.refresh_from_db()
        self.assertEqual(talep.durum, SatinAlmaTalebi.Durum.SIPARISE_DONUSTU)

    def test_ikinci_donusum_engellenir(self):
        talep = self._onayli_talep()
        istemci = self._istemci(self.editor)
        govde = {"tedarikci": self.tedarikci.pk}
        self.assertEqual(
            istemci.post(
                f"/api/v1/purchase-requests/{talep.pk}/talepten-siparis-olustur/",
                govde, format="json",
            ).status_code,
            200,
        )
        ikinci = istemci.post(
            f"/api/v1/purchase-requests/{talep.pk}/talepten-siparis-olustur/",
            govde, format="json",
        )
        self.assertEqual(ikinci.status_code, 400)

    def test_onaysiz_talep_donusemez(self):
        talep = self._talep()
        yanit = self._istemci(self.editor).post(
            f"/api/v1/purchase-requests/{talep.pk}/talepten-siparis-olustur/",
            {"tedarikci": self.tedarikci.pk},
            format="json",
        )
        self.assertEqual(yanit.status_code, 400)

    def test_siparis_fiyati_korunur(self):
        talep = self._onayli_talep()
        siparis = talepten_siparis_olustur(
            talep.pk, tenant_id=self.tenant.pk, tedarikci_id=self.tedarikci.pk
        )
        kalem = siparis.kalemler.get()
        self.assertEqual(kalem.birim_fiyat, Decimal("100.00"))
        # Teklif fiyatı sonradan değişse bile sipariş kalemi değişmez.
        self.teklif.birim_fiyat = Decimal("999.00")
        self.teklif.save()
        kalem.refresh_from_db()
        self.assertEqual(kalem.birim_fiyat, Decimal("100.00"))
        self.assertEqual(kalem.toplam_tutar, Decimal("500.00"))

    def test_belge_numarasi_benzersizligi(self):
        no1 = belge_numarasi_uret(self.tenant.pk, BelgeTipi.TALEP)
        no2 = belge_numarasi_uret(self.tenant.pk, BelgeTipi.TALEP)
        self.assertNotEqual(no1, no2)
        no_siparis = belge_numarasi_uret(self.tenant.pk, BelgeTipi.SIPARIS)
        self.assertTrue(no_siparis.startswith("SS-"))

    def test_siparis_olusturma_ve_onay(self):
        istemci = self._istemci(self.editor)
        olustur = istemci.post(
            "/api/v1/purchase-orders/",
            {"tedarikci": self.tedarikci.pk, "proje": self.proje.pk},
            format="json",
        )
        self.assertEqual(olustur.status_code, 201, olustur.content)
        pk = olustur.json()["data"]["id"]
        self.assertEqual(
            istemci.post(f"/api/v1/purchase-orders/{pk}/onaya-gonder/").status_code, 200
        )
        self.assertEqual(
            istemci.post(f"/api/v1/purchase-orders/{pk}/onayla/").status_code, 200
        )
        siparis = SatinAlmaSiparisi.objects.get(pk=pk)
        self.assertEqual(siparis.durum, SatinAlmaSiparisi.Durum.ONAYLANDI)


class MalKabulBase(SatinAlmaBase):
    def setUp(self):
        super().setUp()
        from purchasing.models import Depo, SatinAlmaTalebiKalemi

        self.depo = Depo.objects.create(
            tenant=self.tenant, kod="ANA", ad="Ana Depo"
        )
        self.talep = SatinAlmaTalebi.objects.create(
            tenant=self.tenant, proje=self.proje, talep_sahibi=self.editor,
            talep_no=belge_numarasi_uret(self.tenant.pk, BelgeTipi.TALEP),
            durum=SatinAlmaTalebi.Durum.ONAYLANDI,
        )
        self.talep_kalemi = SatinAlmaTalebiKalemi.objects.create(
            tenant=self.tenant, talep=self.talep, malzeme=self.malzeme,
            miktar=Decimal("10"), secili_teklif=self.teklif,
        )
        self.siparis = talepten_siparis_olustur(
            self.talep.pk, tenant_id=self.tenant.pk, tedarikci_id=self.tedarikci.pk
        )
        from purchasing.services import siparis_durum_gecis
        from purchasing.models import SatinAlmaSiparisi as _Siparis

        siparis_durum_gecis(
            self.siparis.pk, _Siparis.Durum.ONAY_BEKLIYOR, tenant_id=self.tenant.pk
        )
        siparis_durum_gecis(
            self.siparis.pk, _Siparis.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        self.siparis.refresh_from_db()
        self.siparis_kalemi = self.siparis.kalemler.get()

    def _kabul_ac(self, kabul="10", red="0"):
        from purchasing.services import mal_kabul_olustur

        return mal_kabul_olustur(
            tenant_id=self.tenant.pk, siparis_id=self.siparis.pk, depo_id=self.depo.pk,
            created_by_id=self.editor.pk,
            kalemler=[{
                "siparis_kalemi_id": self.siparis_kalemi.pk,
                "kabul_miktari": kabul, "red_miktari": red,
            }],
        )


class MalKabulTests(MalKabulBase):
    def test_kabul_olusturma_ve_belge_no(self):
        kabul = self._kabul_ac()
        self.assertTrue(kabul.belge_no.startswith("MK-"))
        self.assertEqual(kabul.durum, MalKabul.Durum.TASLAK)

    def test_kismi_kabul_desteklenir(self):
        from purchasing.services import mal_kabul_durum_gecis

        kabul = self._kabul_ac(kabul="4")
        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        self.siparis.refresh_from_db()
        self.assertEqual(self.siparis.durum, SatinAlmaSiparisi.Durum.KISMI_TESLIM)

    def test_asiri_kabul_reddedilir(self):
        with self.assertRaises(ValidationError):
            self._kabul_ac(kabul="11")

    def test_onay_stok_hareketi_uretir(self):
        from purchasing.models import StokHareketi
        from purchasing.services import mal_kabul_durum_gecis

        kabul = self._kabul_ac(kabul="6")
        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        hareket = StokHareketi.objects.get(
            kaynak_belge_tipi="MalKabul", kaynak_belge_kalem_id=kabul.kalemler.get().pk
        )
        self.assertEqual(hareket.miktar, Decimal("6.0000"))
        self.assertEqual(hareket.maliyet, Decimal("100.00"))
        self.assertEqual(hareket.depo, self.depo)
        self.siparis.refresh_from_db()
        self.assertEqual(self.siparis.durum, SatinAlmaSiparisi.Durum.KISMI_TESLIM)

    def test_ikinci_stok_hareketi_olusmaz(self):
        from purchasing.models import StokHareketi
        from purchasing.services import mal_kabul_durum_gecis

        kabul = self._kabul_ac()
        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        sayi = StokHareketi.objects.filter(
            kaynak_belge_tipi="MalKabul", kaynak_belge_id=kabul.pk
        ).count()
        self.assertEqual(sayi, 1)
        # İptal → ters hareket; tekrar iptal girişimleri yeni hareket üretmez.
        mal_kabul_durum_gecis(kabul.pk, MalKabul.Durum.IPTAL, tenant_id=self.tenant.pk)
        cikis = StokHareketi.objects.filter(
            kaynak_belge_tipi="MalKabul_Iptal", kaynak_belge_id=kabul.pk
        ).count()
        self.assertEqual(cikis, 1)

    def test_tam_kabul_siparisi_tamamlar(self):
        from purchasing.services import mal_kabul_durum_gecis

        kabul = self._kabul_ac()
        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        self.siparis.refresh_from_db()
        self.assertEqual(self.siparis.durum, SatinAlmaSiparisi.Durum.TAMAMLANDI)

    def test_tenant_izolasyonu(self):
        diger_kullanici = User.objects.create_user(
            username=f"mkdiger_{uuid.uuid4().hex[:8]}", password="x",
            email=f"mkdiger_{uuid.uuid4().hex[:8]}@example.com",
            tenant=self.diger, role=UserRole.MALIYET_MUHENDISI,
        )
        yanit = self._istemci(diger_kullanici).get("/api/v1/purchase-mal-kabul/")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["data"]["count"], 0)

    def test_stok_hareketi_dogrudan_yazilamaz(self):
        istemci = self._istemci(self.editor)
        self.assertEqual(
            istemci.post(
                "/api/v1/purchase-stok-hareketleri/",
                {"depo": self.depo.pk, "malzeme": self.malzeme.pk, "miktar": "1"},
                format="json",
            ).status_code,
            400,
        )
        self.assertEqual(
            istemci.get("/api/v1/purchase-stok-hareketleri/").status_code, 200
        )

    def test_mal_kabul_api_akisi(self):
        istemci = self._istemci(self.editor)
        olustur = istemci.post(
            "/api/v1/purchase-mal-kabul/",
            {"siparis": self.siparis.pk, "depo": self.depo.pk, "proje": self.proje.pk},
            format="json",
        )
        self.assertEqual(olustur.status_code, 201, olustur.content)
        pk = olustur.json()["data"]["id"]
        kalem_yanit = istemci.post(
            "/api/v1/purchase-mal-kabul-items/",
            {
                "mal_kabul": pk, "siparis_kalemi": self.siparis_kalemi.pk,
                "malzeme": self.malzeme.pk, "siparis_miktari": "10.0000",
                "kabul_miktari": "10.0000", "red_miktari": "0.0000",
            },
            format="json",
        )
        self.assertEqual(kalem_yanit.status_code, 201, kalem_yanit.content)
        self.assertEqual(
            istemci.post(f"/api/v1/purchase-mal-kabul/{pk}/onayla/").status_code, 200
        )
        kabul = MalKabul.objects.get(pk=pk)
        self.assertEqual(kabul.durum, MalKabul.Durum.ONAYLANDI)


class StokBase(MalKabulBase):
    def setUp(self):
        super().setUp()
        from purchasing.models import Depo
        from purchasing.services import mal_kabul_durum_gecis

        self.depo2 = Depo.objects.create(
            tenant=self.tenant, kod="YEDEK", ad="Yedek Depo"
        )
        self.kabul = self._kabul_ac()
        mal_kabul_durum_gecis(
            self.kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        self.kabul_kalemi = self.kabul.kalemler.get()


class StokBakiyeTests(StokBase):
    def test_bakiye_hesaplama(self):
        from purchasing.services import stok_bakiye

        self.assertEqual(
            stok_bakiye(
                tenant_id=self.tenant.pk, depo_id=self.depo.pk,
                malzeme_id=self.malzeme.pk,
            ),
            Decimal("10.0000"),
        )

    def test_yetersiz_stok_reddedilir(self):
        from purchasing.services import stok_transfer

        with self.assertRaises(ValidationError):
            stok_transfer(
                tenant_id=self.tenant.pk, kaynak_depo_id=self.depo.pk,
                hedef_depo_id=self.depo2.pk, malzeme_id=self.malzeme.pk,
                miktar=Decimal("999"), created_by_id=self.editor.pk,
            )


class TransferTests(StokBase):
    def test_basarili_transfer(self):
        from purchasing.services import stok_bakiye, stok_transfer

        cikis, giris = stok_transfer(
            tenant_id=self.tenant.pk, kaynak_depo_id=self.depo.pk,
            hedef_depo_id=self.depo2.pk, malzeme_id=self.malzeme.pk,
            miktar=Decimal("4"), created_by_id=self.editor.pk,
        )
        self.assertEqual(
            stok_bakiye(
                tenant_id=self.tenant.pk, depo_id=self.depo.pk,
                malzeme_id=self.malzeme.pk,
            ),
            Decimal("6.0000"),
        )
        self.assertEqual(
            stok_bakiye(
                tenant_id=self.tenant.pk, depo_id=self.depo2.pk,
                malzeme_id=self.malzeme.pk,
            ),
            Decimal("4.0000"),
        )
        self.assertEqual(cikis.hareket_tipi, "cikis")
        self.assertEqual(giris.hareket_tipi, "giris")

    def test_transfer_rollback(self):
        from unittest.mock import patch

        from purchasing.models import StokHareketi
        from purchasing.services import stok_transfer

        gercek = StokHareketi.objects.create
        sayac = {"n": 0}

        def ikinci_cagirida_patlat(*a, **k):
            sayac["n"] += 1
            if sayac["n"] == 2:
                raise ValueError("bilerek patlatıldı")
            return gercek(*a, **k)

        with patch.object(StokHareketi.objects, "create", side_effect=ikinci_cagirida_patlat):
            with self.assertRaises(ValueError):
                stok_transfer(
                    tenant_id=self.tenant.pk, kaynak_depo_id=self.depo.pk,
                    hedef_depo_id=self.depo2.pk, malzeme_id=self.malzeme.pk,
                    miktar=Decimal("2"), created_by_id=self.editor.pk,
                )
        self.assertEqual(
            StokHareketi.objects.filter(
                kaynak_belge_tipi="Transfer", malzeme=self.malzeme
            ).count(),
            0,
        )


class TuketimTests(StokBase):
    def test_tuketim(self):
        from purchasing.services import stok_bakiye, stok_tuketim

        stok_tuketim(
            tenant_id=self.tenant.pk, depo_id=self.depo.pk,
            malzeme_id=self.malzeme.pk, miktar=Decimal("3"),
            proje_id=self.proje.pk, mahal_id=self.mahal.pk,
            created_by_id=self.editor.pk,
        )
        self.assertEqual(
            stok_bakiye(
                tenant_id=self.tenant.pk, depo_id=self.depo.pk,
                malzeme_id=self.malzeme.pk,
            ),
            Decimal("7.0000"),
        )

    def test_tuketim_proje_mahal_zorunlu(self):
        from purchasing.services import stok_tuketim

        with self.assertRaises((ValidationError, Exception)):
            stok_tuketim(
                tenant_id=self.tenant.pk, depo_id=self.depo.pk,
                malzeme_id=self.malzeme.pk, miktar=Decimal("1"),
                proje_id=self.proje.pk, mahal_id=999999,
                created_by_id=self.editor.pk,
            )


class IadeTests(StokBase):
    def test_iade(self):
        from purchasing.models import StokHareketi
        from purchasing.services import stok_bakiye, stok_iade

        stok_iade(
            tenant_id=self.tenant.pk, mal_kabul_kalemi_id=self.kabul_kalemi.pk,
            miktar=Decimal("2"), created_by_id=self.editor.pk,
        )
        hareket = StokHareketi.objects.get(
            kaynak_belge_tipi="Iade",
            kaynak_belge_kalem_id=self.kabul_kalemi.pk,
        )
        self.assertEqual(hareket.miktar, Decimal("2.0000"))
        self.assertEqual(hareket.maliyet, Decimal("100.00"))
        self.assertEqual(
            stok_bakiye(
                tenant_id=self.tenant.pk, depo_id=self.depo.pk,
                malzeme_id=self.malzeme.pk,
            ),
            Decimal("8.0000"),
        )

    def test_fazla_iade_reddedilir(self):
        from purchasing.services import stok_iade

        with self.assertRaises(ValidationError):
            stok_iade(
                tenant_id=self.tenant.pk, mal_kabul_kalemi_id=self.kabul_kalemi.pk,
                miktar=Decimal("11"), created_by_id=self.editor.pk,
            )

    def test_cift_iade_engeli(self):
        from purchasing.services import stok_iade

        stok_iade(
            tenant_id=self.tenant.pk, mal_kabul_kalemi_id=self.kabul_kalemi.pk,
            miktar=Decimal("10"), created_by_id=self.editor.pk,
        )
        with self.assertRaises(ValidationError):
            stok_iade(
                tenant_id=self.tenant.pk, mal_kabul_kalemi_id=self.kabul_kalemi.pk,
                miktar=Decimal("1"), created_by_id=self.editor.pk,
            )

    def test_tenant_izolasyonu(self):
        from purchasing.services import stok_bakiye

        self.assertEqual(
            stok_bakiye(
                tenant_id=self.diger.pk, depo_id=self.depo.pk,
                malzeme_id=self.malzeme.pk,
            ),
            Decimal("0"),
        )


class MuhasebeEntegrasyonTests(MalKabulBase):
    def setUp(self):
        super().setUp()
        from cari.models import Cari

        self.cari = Cari.objects.create(
            tenant=self.tenant, ad="Satıcı Cari", tip="tedarikci", tur="kurumsal"
        )
        self.tedarikci.cari = self.cari
        self.tedarikci.save(update_fields=["cari"])
        self.kabul = self._kabul_ac()
        from purchasing.services import mal_kabul_durum_gecis

        mal_kabul_durum_gecis(
            self.kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        self.kabul.refresh_from_db()

    def test_kabul_fatura_olusturur(self):
        from finance.models import Fatura

        fatura = Fatura.objects.get(No=f"SAT-{self.kabul.belge_no}")
        self.assertEqual(fatura.fatura_turu, "alis")
        self.assertFalse(fatura.alacakli)
        self.assertEqual(fatura.cari, self.cari)
        self.assertEqual(fatura.durum, "aktif")

    def test_fatura_cari_hareket_olusturur(self):
        from cari.models import CariHareket
        from finance.models import Fatura

        fatura = Fatura.objects.get(No=f"SAT-{self.kabul.belge_no}")
        hareket = CariHareket.objects.get(fatura=fatura)
        self.assertEqual(hareket.cari, self.cari)
        self.assertEqual(hareket.yon, CariHareket.Yon.ALACAK)

    def test_fatura_muhasebe_fisi_320_150_191(self):
        from accounting.models import FisSatiri, MuhasebeFisi
        from finance.models import Fatura

        fatura = Fatura.objects.get(No=f"SAT-{self.kabul.belge_no}")
        fis = MuhasebeFisi.objects.get(
            tenant=self.tenant, fis_no=f"MK-{self.kabul.belge_no}"
        )
        bacaklar = {s.hesap.kod: (s.borc, s.alacak) for s in fis.satirlar.all()}
        self.assertIn("320", bacaklar)
        self.assertIn("150", bacaklar)
        self.assertIn("191", bacaklar)
        self.assertEqual(bacaklar["150"][0], Decimal("1000.00"))
        self.assertEqual(bacaklar["191"][0], Decimal("200.00"))
        self.assertEqual(bacaklar["320"][1], Decimal("1200.00"))
        self.assertEqual(fatura.tutar, Decimal("1200.00"))

    def test_ikinci_onay_duplicate_uretmiyor(self):
        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket
        from finance.models import Fatura
        from purchasing.services import mal_kabul_durum_gecis

        with self.assertRaises(ValidationError):
            mal_kabul_durum_gecis(
                self.kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
            )
        fatura = Fatura.objects.get(No=f"SAT-{self.kabul.belge_no}")
        self.assertEqual(Fatura.objects.filter(No=fatura.No).count(), 1)
        self.assertEqual(
            CariHareket.objects.filter(fatura=fatura).count(), 1
        )
        self.assertEqual(
            MuhasebeFisi.objects.filter(
                tenant_id=self.tenant, fis_no=f"MK-{self.kabul.belge_no}"
            ).count(),
            1,
        )

    def test_tenant_izolasyonu_muhasebede(self):
        from finance.models import Fatura

        self.assertFalse(
            Fatura.objects.filter(
                No=f"SAT-{self.kabul.belge_no}"
            ).exclude(tenant=self.tenant).exists()
        )

    def test_iptal_reversal(self):
        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket
        from finance.models import Fatura
        from purchasing.services import mal_kabul_durum_gecis

        mal_kabul_durum_gecis(
            self.kabul.pk, MalKabul.Durum.IPTAL, tenant_id=self.tenant.pk
        )
        fatura = Fatura.objects.get(No=f"SAT-{self.kabul.belge_no}")
        hareket = CariHareket.objects.get(fatura=fatura)
        self.assertTrue(hareket.is_cancelled)
        ters = MuhasebeFisi.objects.get(
            tenant=self.tenant, fis_no=f"MKTR-{self.kabul.belge_no}"
        )
        self.assertEqual(
            MuhasebeFisi.objects.get(
                tenant_id=self.tenant, fis_no=f"MK-{self.kabul.belge_no}"
            ).durum,
            "iptal",
        )
        self.assertTrue(ters.pk)

    def test_iade_faturasi_baglanti(self):
        from finance.models import Fatura
        from finance.services.satin_alma_muhasebe import stok_iade_muhasebelestir
        from purchasing.models import StokHareketi
        from purchasing.services import stok_iade

        hareket = stok_iade(
            tenant_id=self.tenant.pk, mal_kabul_kalemi_id=self.kabul.kalemler.get().pk,
            miktar=Decimal("2"), created_by_id=self.editor.pk,
        )
        sonuc = stok_iade_muhasebelestir(hareket.pk, tenant_id=self.tenant.pk)
        iade = sonuc["fatura"]
        self.assertEqual(iade.fatura_turu, "iade")
        original = Fatura.objects.get(No=f"SAT-{self.kabul.belge_no}")
        self.assertEqual(iade.iade_faturasi, original)

    def test_rollback_butunluk(self):
        from unittest.mock import patch

        from accounting.models import MuhasebeFisi
        from finance.models import Fatura
        from purchasing.models import (
            BelgeTipi,
            MalKabul,
            SatinAlmaSiparisi,
            SatinAlmaSiparisiKalemi,
            StokHareketi,
        )
        from purchasing.services import (
            belge_numarasi_uret,
            mal_kabul_durum_gecis,
            mal_kabul_olustur,
            siparis_durum_gecis,
        )

        sip2 = SatinAlmaSiparisi.objects.create(
            tenant=self.tenant,
            siparis_no=belge_numarasi_uret(self.tenant.pk, BelgeTipi.SIPARIS),
            tedarikci=self.tedarikci, proje=self.proje,
        )
        siparis_durum_gecis(
            sip2.pk, SatinAlmaSiparisi.Durum.ONAY_BEKLIYOR, tenant_id=self.tenant.pk
        )
        siparis_durum_gecis(
            sip2.pk, SatinAlmaSiparisi.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        sk2 = SatinAlmaSiparisiKalemi.objects.create(
            tenant=self.tenant, siparis=sip2, malzeme=self.malzeme,
            miktar=Decimal("5"), birim_fiyat=Decimal("100"),
        )
        taslak = mal_kabul_olustur(
            tenant_id=self.tenant.pk, siparis_id=sip2.pk, depo_id=self.depo.pk,
            created_by_id=self.editor.pk,
            kalemler=[{
                "siparis_kalemi_id": sk2.pk, "kabul_miktari": "2", "red_miktari": "0",
            }],
        )
        with patch(
            "finance.services.satin_alma_muhasebe.FisSatiri.objects.create",
            side_effect=ValueError("bilerek patlatıldı"),
        ):
            with self.assertRaises(ValueError):
                mal_kabul_durum_gecis(
                    taslak.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
                )
        taslak.refresh_from_db()
        self.assertEqual(taslak.durum, MalKabul.Durum.TASLAK)
        self.assertFalse(
            Fatura.objects.filter(No=f"SAT-{taslak.belge_no}").exists()
        )
        self.assertFalse(
            MuhasebeFisi.objects.filter(
                tenant_id=self.tenant, fis_no=f"MK-{taslak.belge_no}"
            ).exists()
        )
        self.assertFalse(
            StokHareketi.objects.filter(
                kaynak_belge_tipi="MalKabul", kaynak_belge_id=taslak.pk
            ).exists()
        )


class IdempotencyTests(MalKabulBase):
    """Idempotency-Key: tekrar aynı yanıt, FAILED sonrası kurtarma."""

    def test_ayni_key_tekrarinda_ayni_yanit_tek_kayit(self):
        from finance.models import Fatura

        kabul = self._kabul_ac()
        istemci = self._istemci(self.editor)
        gonder = {"HTTP_IDEMPOTENCY_KEY": "sabit-key-1"}
        ilk = istemci.post(
            f"/api/v1/purchase-mal-kabul/{kabul.pk}/onayla/", **gonder
        )
        self.assertEqual(ilk.status_code, 200)
        ikinci = istemci.post(
            f"/api/v1/purchase-mal-kabul/{kabul.pk}/onayla/", **gonder
        )
        self.assertEqual(ikinci.status_code, 200)
        self.assertEqual(ikinci.json()["data"], ilk.json()["data"])
        self.assertEqual(
            Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").count(), 0
        )  # carisiz kurulum: muhasebesiz onay

    def test_failed_key_kurtarma(self):
        from cari.models import Cari
        from finance.models import Fatura, IdempotencyKey

        yabanci_cari = Cari.objects.create(
            tenant=self.diger, ad="Yabancı", tip="tedarikci", tur="kurumsal"
        )
        self.tedarikci.cari = yabanci_cari
        self.tedarikci.save(update_fields=["cari"])
        kabul = self._kabul_ac()
        istemci = self._istemci(self.editor)
        gonder = {"HTTP_IDEMPOTENCY_KEY": "sabit-key-2"}
        kotu = istemci.post(
            f"/api/v1/purchase-mal-kabul/{kabul.pk}/onayla/", **gonder
        )
        self.assertEqual(kotu.status_code, 400)
        self.assertEqual(
            IdempotencyKey.objects.get(
                tenant=self.tenant, operation="mal-kabul.onayla", key="sabit-key-2"
            ).status,
            IdempotencyKey.Durum.FAILED,
        )
        # Cari düzeltilince AYNI kabul + AYNI key yeniden işler.
        dogru = Cari.objects.create(
            tenant=self.tenant, ad="Dogru", tip="tedarikci", tur="kurumsal"
        )
        self.tedarikci.cari = dogru
        self.tedarikci.save(update_fields=["cari"])
        kabul.refresh_from_db()
        self.assertEqual(kabul.durum, MalKabul.Durum.TASLAK)
        iyi = istemci.post(
            f"/api/v1/purchase-mal-kabul/{kabul.pk}/onayla/", **gonder
        )
        self.assertEqual(iyi.status_code, 200)
        self.assertTrue(
            Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").exists()
        )


class MuhasebeRetryTests(MalKabulBase):
    def test_muhasebelestir_retry(self):
        from cari.models import Cari
        from finance.models import Fatura

        kabul = self._kabul_ac(kabul="9")
        istemci = self._istemci(self.editor)
        istemci.post(f"/api/v1/purchase-mal-kabul/{kabul.pk}/onayla/")
        self.assertFalse(
            Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").exists()
        )
        cari = Cari.objects.create(
            tenant=self.tenant, ad="Sonradan", tip="tedarikci", tur="kurumsal"
        )
        self.tedarikci.cari = cari
        self.tedarikci.save(update_fields=["cari"])
        yanit = istemci.post(
            f"/api/v1/purchase-mal-kabul/{kabul.pk}/muhasebelestir/"
        )
        self.assertEqual(yanit.status_code, 200)
        self.assertTrue(
            Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").exists()
        )
        # Taslak kabulde retry reddedilir.
        taslak = self._kabul_ac(kabul="1")
        self.assertEqual(
            istemci.post(
                f"/api/v1/purchase-mal-kabul/{taslak.pk}/muhasebelestir/"
            ).status_code,
            400,
        )


class KdvProfilTests(MalKabulBase):
    def test_vergi_profili_orani_kullanilir(self):
        from accounting.models import MuhasebeFisi
        from cari.models import Cari
        from finance.models import Fatura, VergiProfili
        from purchasing.services import mal_kabul_durum_gecis

        VergiProfili.objects.create(
            tenant=self.tenant, kod="VARSAYILAN", ad="Varsayılan",
            kdv_orani=Decimal("10"),
        )
        cari = Cari.objects.create(
            tenant=self.tenant, ad="Kdv Cari", tip="tedarikci", tur="kurumsal"
        )
        self.tedarikci.cari = cari
        self.tedarikci.save(update_fields=["cari"])
        kabul = self._kabul_ac()
        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        fatura = Fatura.objects.get(No=f"SAT-{kabul.belge_no}")
        self.assertEqual(fatura.tutar, Decimal("1100.00"))
        fis = MuhasebeFisi.objects.get(
            tenant=self.tenant, fis_no=f"MK-{kabul.belge_no}"
        )
        bacaklar = {s.hesap.kod: (s.borc, s.alacak) for s in fis.satirlar.all()}
        self.assertEqual(bacaklar["191"][0], Decimal("100.00"))


class IadeAtomicTests(MalKabulBase):
    def test_iade_atomic_tek_islem(self):
        from unittest.mock import patch

        from cari.models import Cari
        from purchasing.models import StokHareketi
        from purchasing.services import mal_kabul_durum_gecis

        cari = Cari.objects.create(
            tenant=self.tenant, ad="Iade Cari", tip="tedarikci", tur="kurumsal"
        )
        self.tedarikci.cari = cari
        self.tedarikci.save(update_fields=["cari"])
        kabul = self._kabul_ac()
        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        kalem = kabul.kalemler.get()
        istemci = self._istemci(self.editor)
        with patch(
            "finance.services.satin_alma_muhasebe.FaturaKalemi.objects.create",
            side_effect=ValueError("bilerek patlatıldı"),
        ):
            with self.assertRaises(ValueError):
                istemci.post(
                    "/api/v1/purchase-stok-hareketleri/iade-olustur/",
                    {"mal_kabul_kalemi": kalem.pk, "miktar": "2"},
                    format="json",
                )
        self.assertFalse(
            StokHareketi.objects.filter(
                kaynak_belge_tipi="Iade",
                kaynak_belge_kalem_id=kalem.pk,
            ).exists()
        )


class Faz5FinansalE2E(MalKabulBase):
    """FAZ 5 — MalKabul ONAY → stok + fatura + cari + fiş uçtan uca."""

    def _cari_bagla(self):
        from cari.models import Cari

        cari = Cari.objects.create(
            tenant=self.tenant, ad="E2E Cari", tip="tedarikci", tur="kurumsal"
        )
        self.tedarikci.cari = cari
        self.tedarikci.save(update_fields=["cari"])
        return cari

    def test_basarili_zincir_dort_kayit(self):
        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket
        from finance.models import Fatura
        from purchasing.models import StokHareketi
        from purchasing.services import mal_kabul_durum_gecis

        self._cari_bagla()
        kabul = self._kabul_ac()
        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        self.assertEqual(
            StokHareketi.objects.filter(
                kaynak_belge_tipi="MalKabul", kaynak_belge_id=kabul.pk
            ).count(),
            1,
        )
        fatura = Fatura.objects.get(No=f"SAT-{kabul.belge_no}")
        self.assertEqual(fatura.tutar, Decimal("1200.00"))
        self.assertTrue(CariHareket.objects.filter(fatura=fatura).exists())
        self.assertTrue(
            MuhasebeFisi.objects.filter(
                tenant=self.tenant, fis_no=f"MK-{kabul.belge_no}"
            ).exists()
        )

    def test_fatura_hatasi_rollback(self):
        from unittest.mock import patch

        from accounting.models import MuhasebeFisi
        from finance.models import Fatura
        from purchasing.models import StokHareketi
        from purchasing.services import mal_kabul_durum_gecis

        self._cari_bagla()
        kabul = self._kabul_ac()
        with patch(
            "finance.services.satin_alma_muhasebe.FaturaKalemi.objects.create",
            side_effect=ValueError("fatura patlatıldı"),
        ):
            with self.assertRaises(ValueError):
                mal_kabul_durum_gecis(
                    kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
                )
        kabul.refresh_from_db()
        self.assertEqual(kabul.durum, MalKabul.Durum.TASLAK)
        self.assertFalse(
            Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").exists()
        )
        self.assertFalse(
            StokHareketi.objects.filter(
                kaynak_belge_tipi="MalKabul", kaynak_belge_id=kabul.pk
            ).exists()
        )
        self.assertFalse(
            MuhasebeFisi.objects.filter(
                tenant_id=self.tenant, fis_no=f"MK-{kabul.belge_no}"
            ).exists()
        )

    def test_cari_hatasi_rollback(self):
        from unittest.mock import patch

        from finance.models import Fatura
        from purchasing.models import StokHareketi
        from purchasing.services import mal_kabul_durum_gecis

        self._cari_bagla()
        kabul = self._kabul_ac()
        with patch(
            "finance.services.satin_alma_muhasebe.fatura_cari_hareketi_olustur",
            side_effect=ValueError("cari patlatıldı"),
        ):
            with self.assertRaises(ValueError):
                mal_kabul_durum_gecis(
                    kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
                )
        kabul.refresh_from_db()
        self.assertEqual(kabul.durum, MalKabul.Durum.TASLAK)
        self.assertFalse(
            Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").exists()
        )
        self.assertFalse(
            StokHareketi.objects.filter(
                kaynak_belge_tipi="MalKabul", kaynak_belge_id=kabul.pk
            ).exists()
        )

    def test_ayni_key_tekrarinda_tek_zincir(self):
        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket
        from finance.models import Fatura
        from purchasing.models import StokHareketi

        self._cari_bagla()
        kabul = self._kabul_ac()
        istemci = self._istemci(self.editor)
        gonder = {"HTTP_IDEMPOTENCY_KEY": "e2e-key-1"}
        self.assertEqual(
            istemci.post(
                f"/api/v1/purchase-mal-kabul/{kabul.pk}/onayla/", **gonder
            ).status_code,
            200,
        )
        self.assertEqual(
            istemci.post(
                f"/api/v1/purchase-mal-kabul/{kabul.pk}/onayla/", **gonder
            ).status_code,
            200,
        )
        self.assertEqual(
            Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").count(), 1
        )
        self.assertEqual(
            CariHareket.objects.filter(
                fatura__No=f"SAT-{kabul.belge_no}"
            ).count(),
            1,
        )
        self.assertEqual(
            MuhasebeFisi.objects.filter(
                tenant=self.tenant, fis_no=f"MK-{kabul.belge_no}"
            ).count(),
            1,
        )
        self.assertEqual(
            StokHareketi.objects.filter(
                kaynak_belge_tipi="MalKabul", kaynak_belge_id=kabul.pk
            ).count(),
            1,
        )

    def test_kdv_matrah_1000_ornek(self):
        from finance.models import Fatura
        from purchasing.services import mal_kabul_durum_gecis

        self._cari_bagla()
        kabul = self._kabul_ac()  # 10 x 100 = 1000 matrah
        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        fatura = Fatura.objects.get(No=f"SAT-{kabul.belge_no}")
        kalem = fatura.kalemler.get()
        self.assertEqual(kalem.kdv_orani, Decimal("20.00"))
        self.assertEqual(kalem.kdv_tutari, Decimal("200.00"))
        self.assertEqual(fatura.tutar, Decimal("1200.00"))
        from accounting.models import MuhasebeFisi

        fis = MuhasebeFisi.objects.get(
            tenant=self.tenant, fis_no=f"MK-{kabul.belge_no}"
        )
        bacaklar = {s.hesap.kod: (s.borc, s.alacak) for s in fis.satirlar.all()}
        self.assertEqual(bacaklar["191"][0], Decimal("200.00"))
        self.assertEqual(
            bacaklar["320"][1], bacaklar["150"][0] + bacaklar["191"][0]
        )


class IadeMuhasebeTests(MalKabulBase):
    def setUp(self):
        super().setUp()
        from cari.models import Cari

        cari = Cari.objects.create(
            tenant=self.tenant, ad="Iade Cari", tip="tedarikci", tur="kurumsal"
        )
        self.tedarikci.cari = cari
        self.tedarikci.save(update_fields=["cari"])
        self.kabul = self._kabul_ac()
        from purchasing.services import mal_kabul_durum_gecis

        mal_kabul_durum_gecis(
            self.kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        self.kalem = self.kabul.kalemler.get()

    def _iade_ac(self, miktar):
        from purchasing.services import stok_iade

        return stok_iade(
            tenant_id=self.tenant.pk, mal_kabul_kalemi_id=self.kalem.pk,
            miktar=Decimal(miktar), created_by_id=self.editor.pk,
        )

    def test_tam_iade(self):
        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket
        from finance.models import Fatura
        from finance.services.satin_alma_muhasebe import stok_iade_muhasebelestir

        hareket = self._iade_ac("10")
        sonuc = stok_iade_muhasebelestir(hareket.pk, tenant_id=self.tenant.pk)
        iade = sonuc["fatura"]
        self.assertEqual(iade.fatura_turu, "iade")
        self.assertEqual(iade.tutar, Decimal("1200.00"))
        original = Fatura.objects.get(No=f"SAT-{self.kabul.belge_no}")
        self.assertEqual(iade.iade_faturasi, original)
        ch = sonuc["cari_hareket"]
        self.assertEqual(ch.yon, CariHareket.Yon.BORC)
        fis = sonuc["fis"]
        bacaklar = {s.hesap.kod: (s.borc, s.alacak) for s in fis.satirlar.all()}
        self.assertEqual(bacaklar["320"][0], Decimal("1200.00"))
        self.assertEqual(bacaklar["150"][1], Decimal("1000.00"))
        self.assertEqual(bacaklar["191"][1], Decimal("200.00"))
        self.assertTrue(fis.fis_no.startswith("MI-"))
        self.assertTrue(
            MuhasebeFisi.objects.filter(pk=fis.pk).exists()
        )

    def test_kismi_iade_kumulatif(self):
        from finance.models import Fatura
        from finance.services.satin_alma_muhasebe import stok_iade_muhasebelestir
        from purchasing.services import stok_iade

        h1 = stok_iade(
            tenant_id=self.tenant.pk, mal_kabul_kalemi_id=self.kalem.pk,
            miktar=Decimal("3"), created_by_id=self.editor.pk,
        )
        s1 = stok_iade_muhasebelestir(h1.pk, tenant_id=self.tenant.pk)
        h2 = stok_iade(
            tenant_id=self.tenant.pk, mal_kabul_kalemi_id=self.kalem.pk,
            miktar=Decimal("2"), created_by_id=self.editor.pk,
        )
        s2 = stok_iade_muhasebelestir(h2.pk, tenant_id=self.tenant.pk)
        self.assertEqual(s1["fatura"].tutar, Decimal("360.00"))
        self.assertEqual(s2["fatura"].tutar, Decimal("240.00"))
        self.assertNotEqual(s1["fatura"].No, s2["fatura"].No)
        self.assertEqual(s1["fatura"].iade_faturasi, s2["fatura"].iade_faturasi)
        with self.assertRaises(ValidationError):
            stok_iade(
                tenant_id=self.tenant.pk, mal_kabul_kalemi_id=self.kalem.pk,
                miktar=Decimal("6"), created_by_id=self.editor.pk,
            )

    def test_iade_kdv_snapshot(self):
        from finance.models import Fatura, VergiProfili
        from finance.services.satin_alma_muhasebe import stok_iade_muhasebelestir

        VergiProfili.objects.create(
            tenant=self.tenant, kod="VARSAYILAN", ad="V",
            kdv_orani=Decimal("10"),
        )
        # Mevcut kabul %20 ile faturalandı; iade kendi kaynağını kullanır.
        hareket = self._iade_ac("3")
        sonuc = stok_iade_muhasebelestir(hareket.pk, tenant_id=self.tenant.pk)
        kalem = sonuc["fatura"].kalemler.get()
        self.assertEqual(kalem.kdv_orani, Decimal("20.00"))
        self.assertEqual(sonuc["fatura"].tutar, Decimal("360.00"))
        self.assertEqual(
            Fatura.objects.get(No=f"SAT-{self.kabul.belge_no}").tutar,
            Decimal("1200.00"),
        )

    def test_iade_rollback(self):
        from unittest.mock import patch

        from accounting.models import MuhasebeFisi
        from finance.models import Fatura
        from purchasing.models import StokHareketi

        with patch(
            "finance.services.satin_alma_muhasebe.FisSatiri.objects.create",
            side_effect=ValueError("iade fisi patlatıldı"),
        ):
            with self.assertRaises(ValueError):
                self._istemci(self.editor).post(
                    "/api/v1/purchase-stok-hareketleri/iade-olustur/",
                    {"mal_kabul_kalemi": self.kalem.pk, "miktar": "2"},
                    format="json",
                )
        self.assertFalse(
            StokHareketi.objects.filter(
                kaynak_belge_tipi="Iade",
                kaynak_belge_kalem_id=self.kalem.pk,
            ).exists()
        )
        self.assertFalse(
            Fatura.objects.filter(No__startswith=f"IAD-{self.kabul.belge_no}").exists()
        )
        self.assertFalse(
            MuhasebeFisi.objects.filter(fis_no__startswith="MI-").exists()
        )

    def test_iade_idempotency_tekrar(self):
        from finance.models import Fatura

        istemci = self._istemci(self.editor)
        govde = {"mal_kabul_kalemi": self.kalem.pk, "miktar": "2"}
        gonder = {"HTTP_IDEMPOTENCY_KEY": "iade-key-1"}
        r1 = istemci.post(
            "/api/v1/purchase-stok-hareketleri/iade-olustur/", govde,
            format="json", **gonder
        )
        self.assertEqual(r1.status_code, 200)
        r2 = istemci.post(
            "/api/v1/purchase-stok-hareketleri/iade-olustur/", govde,
            format="json", **gonder
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r1.json()["data"], r2.json()["data"])
        self.assertEqual(
            Fatura.objects.filter(
                No=r1.json()["data"]["iade_fatura_no"]
            ).count(),
            1,
        )


class MuhasebeDengeTests(MalKabulBase):
    """FAZ 6B — her fiş tipinde borç == alacak + retry tekilliği."""

    def _dengeli_mi(self, fis):
        from django.db.models import Sum

        from accounting.models import FisSatiri

        ozet = FisSatiri.objects.filter(fis=fis).aggregate(
            borc=Sum("borc"), alacak=Sum("alacak")
        )
        return (ozet["borc"] or Decimal("0")) == (ozet["alacak"] or Decimal("0"))

    def _kurulum(self):
        from cari.models import Cari

        cari = Cari.objects.create(
            tenant=self.tenant, ad="Denge Cari", tip="tedarikci", tur="kurumsal"
        )
        self.tedarikci.cari = cari
        self.tedarikci.save(update_fields=["cari"])
        kabul = self._kabul_ac()
        from purchasing.services import mal_kabul_durum_gecis

        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        return kabul

    def test_tum_fis_tipleri_dengeli(self):
        from accounting.models import MuhasebeFisi
        from finance.services.satin_alma_muhasebe import stok_iade_muhasebelestir
        from purchasing.services import mal_kabul_durum_gecis, stok_iade

        kabul = self._kurulum()
        fisler = list(
            MuhasebeFisi.objects.filter(tenant=self.tenant).order_by("id")
        )
        self.assertGreaterEqual(len(fisler), 1)
        for fis in fisler:
            self.assertTrue(self._dengeli_mi(fis), fis.fis_no)
        # İade zinciri de dengeli olmalı.
        hareket = stok_iade(
            tenant_id=self.tenant.pk, mal_kabul_kalemi_id=kabul.kalemler.get().pk,
            miktar=Decimal("2"), created_by_id=self.editor.pk,
        )
        sonuc = stok_iade_muhasebelestir(hareket.pk, tenant_id=self.tenant.pk)
        for fis in (sonuc["fis"],):
            self.assertTrue(self._dengeli_mi(fis), fis.fis_no)
        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.IPTAL, tenant_id=self.tenant.pk
        )
        for fis in MuhasebeFisi.objects.filter(tenant=self.tenant):
            self.assertTrue(self._dengeli_mi(fis), fis.fis_no)

    def test_on_kez_muhasebelestir_tek_fis(self):
        from accounting.models import MuhasebeFisi
        from finance.models import Fatura
        from finance.services.satin_alma_muhasebe import satin_alma_muhasebe_olustur

        kabul = self._kurulum()
        for _ in range(10):
            satin_alma_muhasebe_olustur(kabul.pk, tenant_id=self.tenant.pk)
        self.assertEqual(
            Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").count(), 1
        )
        self.assertEqual(
            MuhasebeFisi.objects.filter(
                tenant_id=self.tenant, fis_no=f"MK-{kabul.belge_no}"
            ).count(),
            1,
        )

    def test_cross_tenant_muhasebe_reddi(self):
        from finance.services.satin_alma_muhasebe import satin_alma_muhasebe_olustur

        kabul = self._kurulum()
        with self.assertRaises(ValidationError):
            satin_alma_muhasebe_olustur(kabul.pk, tenant_id=self.diger.pk)


class SoDTests(SatinAlmaBase):
    """FAZ 6C — görev ayrılığı: FINANS/MUHASEBE satın alma yazamaz (onay dahil)."""

    def _rol_kullanicisi(self, rol, tenant=None):
        return User.objects.create_user(
            username=f"sod_{rol}_{uuid.uuid4().hex[:8]}", password="x",
            email=f"sod_{rol}_{uuid.uuid4().hex[:8]}@example.com",
            tenant=tenant or self.tenant, role=rol,
        )

    def _finansal_kayit_yok(self):
        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket
        from finance.models import Fatura

        self.assertFalse(Fatura.objects.filter(tenant=self.tenant).exists())
        self.assertFalse(CariHareket.objects.filter(tenant=self.tenant).exists())
        self.assertFalse(MuhasebeFisi.objects.filter(tenant=self.tenant).exists())

    def test_finans_satinalma_onaylayamaz(self):
        from .models import SatinAlmaTalebi

        talep = self._talep()
        istemci = self._istemci(self._rol_kullanicisi(UserRole.FINANS))
        self.assertEqual(
            istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onayla/").status_code, 403
        )
        self.assertEqual(
            istemci.post(
                "/api/v1/purchase-requests/",
                {"proje": self.proje.pk}, format="json",
            ).status_code, 403,
        )
        talep.refresh_from_db()
        self.assertEqual(talep.durum, SatinAlmaTalebi.Durum.TASLAK)
        self._finansal_kayit_yok()

    def test_muhasebe_satinalma_onaylayamaz(self):
        from .models import SatinAlmaTalebi

        talep = self._talep()
        istemci = self._istemci(self._rol_kullanicisi(UserRole.MUHASEBE))
        self.assertEqual(
            istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onayla/").status_code, 403
        )
        self.assertEqual(
            istemci.post(
                "/api/v1/purchase-requests/",
                {"proje": self.proje.pk}, format="json",
            ).status_code, 403,
        )
        talep.refresh_from_db()
        self.assertEqual(talep.durum, SatinAlmaTalebi.Durum.TASLAK)
        self._finansal_kayit_yok()

    def test_uygun_roller_onaylar(self):
        from .models import SatinAlmaTalebi

        for rol in (UserRole.MALIYET_MUHENDISI, UserRole.PROJE_YONETICISI):
            talep = self._talep()
            istemci = self._istemci(self._rol_kullanicisi(rol))
            self.assertEqual(
                istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onaya-gonder/").status_code,
                200,
            )
            self.assertEqual(
                istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onayla/").status_code,
                200,
            )
            talep.refresh_from_db()
            self.assertEqual(talep.durum, SatinAlmaTalebi.Durum.ONAYLANDI)

    def test_cross_tenant_finans_action_reddi(self):
        from .models import SatinAlmaTalebi

        yabanci = SatinAlmaTalebi.objects.create(
            tenant=self.diger, proje=Proje.objects.create(
                tenant=self.diger, proje_kodu=f"YB-{uuid.uuid4().hex[:6]}", ad="Yabancı",
            ),
            talep_sahibi=self._rol_kullanicisi(
                UserRole.MALIYET_MUHENDISI, tenant=self.diger,
            ),
            talep_no=f"YB-{uuid.uuid4().hex[:8]}",
        )
        istemci = self._istemci(self._rol_kullanicisi(UserRole.FINANS))
        kod = istemci.post(f"/api/v1/purchase-requests/{yabanci.pk}/onayla/").status_code
        self.assertIn(kod, (403, 404))
        yabanci.refresh_from_db()
        self.assertEqual(yabanci.durum, SatinAlmaTalebi.Durum.TASLAK)
        self._finansal_kayit_yok()


class KarmaKdvOrkestrasyonTests(MalKabulBase):
    """FAZ 6C — kalem-bazlı KDV: override → profil → %20; fiş snapshot okur."""

    def _cari_bagla(self):
        from cari.models import Cari

        cari = Cari.objects.create(
            tenant=self.tenant, ad="Karma Cari", tip="tedarikci", tur="kurumsal"
        )
        self.tedarikci.cari = cari
        self.tedarikci.save(update_fields=["cari"])
        return cari

    def _karma_kabul(self):
        """3 satır: 10x100 @20 (profil yok → %20), 5x100 @10, 2x100 @0."""
        from purchasing.models import MalKabulKalemi

        self._cari_bagla()
        kabul = self._kabul_ac()
        for miktar, oran in (("5", "10"), ("2", "0")):
            MalKabulKalemi.objects.create(
                tenant=self.tenant, mal_kabul=kabul,
                siparis_kalemi=self.siparis_kalemi, malzeme=self.malzeme,
                siparis_miktari=Decimal("10"), kabul_miktari=Decimal(miktar),
                kdv_orani=Decimal(oran),
            )
        return kabul

    def _onayla(self, kabul):
        from purchasing.services import mal_kabul_durum_gecis

        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )

    def test_karma_kdv_fatura_toplamlari(self):
        from finance.models import Fatura

        kabul = self._karma_kabul()
        self._onayla(kabul)
        fatura = Fatura.objects.get(No=f"SAT-{kabul.belge_no}")
        oranlar = sorted(
            fatura.kalemler.values_list("kdv_orani", flat=True)
        )
        self.assertEqual(oranlar, [Decimal("0"), Decimal("10"), Decimal("20")])
        self.assertEqual(fatura.tutar, Decimal("1950.00"))

    def test_karma_kdv_fis_fatura_ile_eslesir(self):
        from accounting.models import MuhasebeFisi

        kabul = self._karma_kabul()
        self._onayla(kabul)
        fis = MuhasebeFisi.objects.get(
            tenant=self.tenant, fis_no=f"MK-{kabul.belge_no}"
        )
        bacaklar = {s.hesap.kod: (s.borc, s.alacak) for s in fis.satirlar.all()}
        self.assertEqual(bacaklar["150"][0], Decimal("1700.00"))
        self.assertEqual(bacaklar["191"][0], Decimal("250.00"))
        self.assertEqual(bacaklar["320"][1], Decimal("1950.00"))
        self.assertEqual(bacaklar["320"][1], bacaklar["150"][0] + bacaklar["191"][0])

    def test_kalem_orani_profili_ezer(self):
        from finance.models import Fatura, VergiProfili
        from purchasing.models import MalKabulKalemi

        VergiProfili.objects.create(
            tenant=self.tenant, kod="VARSAYILAN", ad="Varsayılan",
            kdv_orani=Decimal("20"),
        )
        self._cari_bagla()
        kabul = self._kabul_ac()
        MalKabulKalemi.objects.create(
            tenant=self.tenant, mal_kabul=kabul,
            siparis_kalemi=self.siparis_kalemi, malzeme=self.malzeme,
            siparis_miktari=Decimal("10"), kabul_miktari=Decimal("5"),
            kdv_orani=Decimal("10"),
        )
        self._onayla(kabul)
        fatura = Fatura.objects.get(No=f"SAT-{kabul.belge_no}")
        oranlar = sorted(fatura.kalemler.values_list("kdv_orani", flat=True))
        self.assertEqual(oranlar, [Decimal("10"), Decimal("20")])
        # 1000@20 + 500@10 → 1750
        self.assertEqual(fatura.tutar, Decimal("1750.00"))

    def test_karma_kdv_iade_kaynagini_korur(self):
        from finance.services.satin_alma_muhasebe import stok_iade_muhasebelestir
        from purchasing.models import MalKabulKalemi
        from purchasing.services import stok_iade

        kabul = self._karma_kabul()
        self._onayla(kabul)
        onluk = MalKabulKalemi.objects.get(
            mal_kabul=kabul, kdv_orani=Decimal("10")
        )
        hareket = stok_iade(
            tenant_id=self.tenant.pk, mal_kabul_kalemi_id=onluk.pk,
            miktar=Decimal("2"), created_by_id=self.editor.pk,
        )
        sonuc = stok_iade_muhasebelestir(hareket.pk, tenant_id=self.tenant.pk)
        kalem = sonuc["fatura"].kalemler.get()
        self.assertEqual(kalem.kdv_orani, Decimal("10"))
        self.assertEqual(sonuc["fatura"].tutar, Decimal("220.00"))

    def test_profil_degisiminden_sonra_gecmis_fatura_sabit(self):
        from finance.models import Fatura, VergiProfili
        from finance.services.fatura_hesaplama import fatura_toplam_hesapla

        VergiProfili.objects.create(
            tenant=self.tenant, kod="VARSAYILAN", ad="Varsayılan",
            kdv_orani=Decimal("10"),
        )
        self._cari_bagla()
        kabul = self._kabul_ac()
        self._onayla(kabul)
        fatura = Fatura.objects.get(No=f"SAT-{kabul.belge_no}")
        self.assertEqual(fatura.tutar, Decimal("1100.00"))
        VergiProfili.objects.filter(
            tenant=self.tenant, kod="VARSAYILAN"
        ).update(kdv_orani=Decimal("25"))
        fatura.refresh_from_db()
        ozet = fatura_toplam_hesapla(fatura)
        self.assertEqual(ozet["matrah"], "1000.00")
        self.assertEqual(ozet["kdv"], "100.00")
        self.assertEqual(ozet["genel_toplam"], "1100.00")
        self.assertEqual(fatura.tutar, Decimal("1100.00"))


class SorguSabitlikTests(MalKabulBase):
    """FAZ 6E §9 — mal kabul / stok listelerinde satır-bağımsız query sayısı."""

    def _sorgu_sayisi(self, url):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            yanit = self._istemci(self.editor).get(url)
        self.assertEqual(yanit.status_code, 200)
        return len(ctx)

    def test_malkabul_liste_satir_artisinda_sorgu_sabiti(self):
        # Mevcut şekil: satır başına ~3 sorgu (muhasebe rozeti lookup'ları).
        # Bu test şekli kilitler; yeni satır-başı sorgu eklenirse patlar.
        self._kabul_ac(kabul="3")
        bir = self._sorgu_sayisi("/api/v1/purchase-mal-kabul/")
        self._kabul_ac(kabul="3")
        self._kabul_ac(kabul="3")
        uc = self._sorgu_sayisi("/api/v1/purchase-mal-kabul/")
        self.assertLessEqual(uc, bir + 7)

    def test_stok_liste_satir_artisinda_sorgu_sabiti(self):
        from purchasing.models import StokHareketi

        StokHareketi.objects.bulk_create([
            StokHareketi(
                tenant=self.tenant, depo=self.depo, malzeme=self.malzeme,
                hareket_tipi="giris", miktar=Decimal("1"), maliyet=Decimal("100"),
                created_by=self.editor,
            )
            for _ in range(100)
        ])
        yuz = self._sorgu_sayisi("/api/v1/purchase-stok-hareketleri/")
        StokHareketi.objects.bulk_create([
            StokHareketi(
                tenant=self.tenant, depo=self.depo, malzeme=self.malzeme,
                hareket_tipi="giris", miktar=Decimal("1"), maliyet=Decimal("100"),
                created_by=self.editor,
            )
            for _ in range(100)
        ])
        ikiyuz = self._sorgu_sayisi("/api/v1/purchase-stok-hareketleri/")
        self.assertEqual(yuz, ikiyuz)

