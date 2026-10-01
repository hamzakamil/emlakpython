"""FAZ 6A — Gerçek paralel (thread) concurrency testleri.

Sıralı sahte-concurrency yok: iki thread bariyerde buluşup aynı anda girer.
TransactionTestCase kullanılır (TestCase atomic'i thread'leri kör ederdi).
"""

import threading
import uuid
from decimal import Decimal

from django.test import TransactionTestCase
from rest_framework.test import APIClient

from cari.models import Cari
from construction.models import (
    Malzeme,
    Poz,
    PozGrubu,
    Proje,
    Tedarikci,
    TedarikciTeklifi,
)
from tenants.models import Tenant
from users.models import User, UserRole

from purchasing.models import (
    BelgeTipi,
    Depo,
    MalKabul,
    SatinAlmaSiparisi,
    SatinAlmaTalebi,
    SatinAlmaTalebiKalemi,
    StokHareketi,
)
from purchasing.services import (
    belge_numarasi_uret,
    mal_kabul_durum_gecis,
    mal_kabul_olustur,
    siparis_durum_gecis,
    talepten_siparis_olustur,
)


def _paralel_kos(fnler):
    """İki+ callable'ı bariyerli thread'lerde koşturur, sonuçları döner."""
    bariyer = threading.Barrier(len(fnler), timeout=60)
    sonuclar, hatalar = [], []

    def sar(fn, i):
        try:
            bariyer.wait(timeout=60)
            sonuclar.append((i, fn()))
        except Exception as exc:  # noqa: BLE001 — test sonucu olarak saklanır
            hatalar.append((i, exc))
        finally:
            # Thread bağlantısını kapat (yoksa test DB DROP edilemez).
            from django.db import connection as _baglanti

            _baglanti.close()

    threadler = [threading.Thread(target=sar, args=(fn, i)) for i, fn in enumerate(fnler)]
    for t in threadler:
        t.start()
    for t in threadler:
        t.join(timeout=120)
    return sonuclar, hatalar


class Faz6aConcurrencyBase(TransactionTestCase):
    @classmethod
    def _fixture_teardown(cls):
        # Django TRUNCATE'i available_apps yoksa CASCADE'siz yapar; PROTECT
        # FK'li şemada patlar. Test DB disposable olduğundan CASCADE'li temizlik.
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' "
                "AND tablename NOT IN ('spatial_ref_sys', 'django_migrations')"
            )
            tables = [row[0] for row in cursor.fetchall()]
        if tables:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE %s CASCADE" % ", ".join(f'"{t}"' for t in tables))

    def setUp(self):
        unique = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name="Yarış A.Ş.", slug=f"yaris-{unique}")
        self.editor = User.objects.create_user(
            username=f"y_{unique}", password="x", email=f"y_{unique}@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )
        self.proje = Proje.objects.create(
            tenant=self.tenant, proje_kodu="YRS", ad="Yarış Projesi"
        )
        self.malzeme = Malzeme.objects.create(
            tenant=self.tenant, malzeme_kodu="YRM", ad="Yarış Malzemesi", birim="adet"
        )
        self.depo_a = Depo.objects.create(tenant=self.tenant, kod="A", ad="A Deposu")
        self.depo_b = Depo.objects.create(tenant=self.tenant, kod="B", ad="B Deposu")
        self.cari = Cari.objects.create(
            tenant=self.tenant, ad="Yarış Cari", tip="tedarikci", tur="kurumsal"
        )
        self.tedarikci = Tedarikci.objects.create(
            tenant=self.tenant, firma_adi="Yarış Ltd.", firma_kodu=f"YRS-{unique}",
            cari=self.cari,
        )
        self.teklif = TedarikciTeklifi.objects.create(
            tenant=self.tenant, proje=self.proje, malzeme=self.malzeme,
            tedarikci=self.tedarikci, miktar=Decimal("100"), birim_fiyat=Decimal("10"),
        )

    def _istemci(self):
        istemci = APIClient()
        istemci.force_authenticate(user=self.editor)
        return istemci

    def _onayli_siparis(self, miktar="100"):
        talep = SatinAlmaTalebi.objects.create(
            tenant=self.tenant, proje=self.proje, talep_sahibi=self.editor,
            talep_no=belge_numarasi_uret(self.tenant.pk, BelgeTipi.TALEP),
            durum=SatinAlmaTalebi.Durum.ONAYLANDI,
        )
        SatinAlmaTalebiKalemi.objects.create(
            tenant=self.tenant, talep=talep, malzeme=self.malzeme,
            miktar=Decimal(miktar), secili_teklif=self.teklif,
        )
        siparis = talepten_siparis_olustur(
            talep.pk, tenant_id=self.tenant.pk, tedarikci_id=self.tedarikci.pk
        )
        siparis_durum_gecis(
            siparis.pk, SatinAlmaSiparisi.Durum.ONAY_BEKLIYOR, tenant_id=self.tenant.pk
        )
        siparis_durum_gecis(
            siparis.pk, SatinAlmaSiparisi.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        siparis.refresh_from_db()
        return siparis

    def _onayli_kabul(self, siparis, miktar="100"):
        kabul = mal_kabul_olustur(
            tenant_id=self.tenant.pk, siparis_id=siparis.pk, depo_id=self.depo_a.pk,
            created_by_id=self.editor.pk,
            kalemler=[{
                "siparis_kalemi_id": siparis.kalemler.get().pk,
                "kabul_miktari": miktar, "red_miktari": "0",
            }],
        )
        mal_kabul_durum_gecis(
            kabul.pk, MalKabul.Durum.ONAYLANDI, tenant_id=self.tenant.pk
        )
        return MalKabul.objects.get(pk=kabul.pk)


class ParalelOnayTests(Faz6aConcurrencyBase):
    def test_paralel_onay_tek_zincir(self):
        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket
        from finance.models import Fatura

        siparis = self._onayli_siparis()
        kabul = mal_kabul_olustur(
            tenant_id=self.tenant.pk, siparis_id=siparis.pk, depo_id=self.depo_a.pk,
            created_by_id=self.editor.pk,
            kalemler=[{
                "siparis_kalemi_id": siparis.kalemler.get().pk,
                "kabul_miktari": "100", "red_miktari": "0",
            }],
        )

        def onayla():
            return self._istemci().post(
                f"/api/v1/purchase-mal-kabul/{kabul.pk}/onayla/"
            ).status_code

        sonuclar, hatalar = _paralel_kos([onayla, onayla])
        self.assertEqual(hatalar, [])
        kodlar = sorted(kod for _, kod in sonuclar)
        self.assertEqual(kodlar, [200, 400])
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

    def test_paralel_onay_ayni_key_tek_zincir(self):
        from finance.models import Fatura

        siparis = self._onayli_siparis()
        kabul = mal_kabul_olustur(
            tenant_id=self.tenant.pk, siparis_id=siparis.pk, depo_id=self.depo_a.pk,
            created_by_id=self.editor.pk,
            kalemler=[{
                "siparis_kalemi_id": siparis.kalemler.get().pk,
                "kabul_miktari": "100", "red_miktari": "0",
            }],
        )
        gonder = {"HTTP_IDEMPOTENCY_KEY": "paralel-key-1"}

        def onayla():
            return self._istemci().post(
                f"/api/v1/purchase-mal-kabul/{kabul.pk}/onayla/", **gonder
            ).status_code

        sonuclar, hatalar = _paralel_kos([onayla, onayla])
        self.assertEqual(hatalar, [])
        for _, kod in sonuclar:
            self.assertIn(kod, (200, 400))
        self.assertEqual(
            Fatura.objects.filter(No=f"SAT-{kabul.belge_no}").count(), 1
        )


class ParalelKabulIadeTests(Faz6aConcurrencyBase):
    def _kucuk_onayli_kabul(self, siparis):
        return self._onayli_kabul(siparis, miktar="10")
    def test_paralel_kabul_toplam_asamaz(self):
        from purchasing.services import mal_kabul_olustur as _olustur

        siparis = self._onayli_siparis()
        kalem_pk = siparis.kalemler.get().pk
        sonuclar, hatalar = _paralel_kos([
            lambda: _olustur(
                tenant_id=self.tenant.pk, siparis_id=siparis.pk, depo_id=self.depo_a.pk,
                created_by_id=self.editor.pk,
                kalemler=[{"siparis_kalemi_id": kalem_pk, "kabul_miktari": "60",
                           "red_miktari": "0"}],
            ).pk,
            lambda: _olustur(
                tenant_id=self.tenant.pk, siparis_id=siparis.pk, depo_id=self.depo_a.pk,
                created_by_id=self.editor.pk,
                kalemler=[{"siparis_kalemi_id": kalem_pk, "kabul_miktari": "60",
                           "red_miktari": "0"}],
            ).pk,
        ])
        self.assertEqual(len(sonuclar), 1)
        self.assertEqual(len(hatalar), 1)
        from purchasing.models import MalKabulKalemi

        toplam = sum(
            k.kabul_miktari
            for k in MalKabulKalemi.objects.filter(siparis_kalemi_id=kalem_pk)
        )
        self.assertLessEqual(toplam, Decimal("100"))

    def test_paralel_iade_kumulatif_asamaz(self):
        from purchasing.services import stok_iade

        siparis = self._onayli_siparis()
        kabul = self._kucuk_onayli_kabul(siparis)
        kalem_pk = kabul.kalemler.get().pk
        sonuclar, hatalar = _paralel_kos([
            lambda: stok_iade(
                tenant_id=self.tenant.pk, mal_kabul_kalemi_id=kalem_pk,
                miktar=Decimal("7"), created_by_id=self.editor.pk).pk,
            lambda: stok_iade(
                tenant_id=self.tenant.pk, mal_kabul_kalemi_id=kalem_pk,
                miktar=Decimal("7"), created_by_id=self.editor.pk).pk,
        ])
        self.assertEqual(len(sonuclar), 1)
        self.assertEqual(len(hatalar), 1)
        toplam = sum(
            s.miktar for s in StokHareketi.objects.filter(
                kaynak_belge_tipi="Iade", kaynak_belge_kalem_id=kalem_pk)
        )
        self.assertLessEqual(toplam, Decimal("10"))


class ParalelTransferTests(Faz6aConcurrencyBase):
    def test_capraz_transfer_kilitsiz_kalmaz(self):
        from purchasing.services import stok_bakiye, stok_transfer

        siparis = self._onayli_siparis()
        self._onayli_kabul(siparis)
        sonuclar, hatalar = _paralel_kos([
            lambda: stok_transfer(
                tenant_id=self.tenant.pk, kaynak_depo_id=self.depo_a.pk,
                hedef_depo_id=self.depo_b.pk, malzeme_id=self.malzeme.pk,
                miktar=Decimal("3"), created_by_id=self.editor.pk),
            lambda: stok_transfer(
                tenant_id=self.tenant.pk, kaynak_depo_id=self.depo_a.pk,
                hedef_depo_id=self.depo_b.pk, malzeme_id=self.malzeme.pk,
                miktar=Decimal("4"), created_by_id=self.editor.pk),
        ])
        self.assertEqual(hatalar, [])
        self.assertEqual(
            stok_bakiye(
                tenant_id=self.tenant.pk, depo_id=self.depo_a.pk,
                malzeme_id=self.malzeme.pk,
            ),
            Decimal("93.0000"),
        )
        self.assertEqual(
            stok_bakiye(
                tenant_id=self.tenant.pk, depo_id=self.depo_b.pk,
                malzeme_id=self.malzeme.pk,
            ),
            Decimal("7.0000"),
        )

    def test_es_zamanli_sayac_tekil_numara(self):
        taze = Tenant.objects.create(
            name="Sayaç", slug=f"sayac-{uuid.uuid4().hex[:8]}"
        )
        sonuclar, hatalar = _paralel_kos([
            lambda: belge_numarasi_uret(taze.pk, BelgeTipi.TALEP),
            lambda: belge_numarasi_uret(taze.pk, BelgeTipi.TALEP),
        ])
        self.assertEqual(hatalar, [])
        nolar = sorted(no for _, no in sonuclar)
        self.assertEqual(len(set(nolar)), 2)


class ParalelWinnerTests(Faz6aConcurrencyBase):
    def test_paralel_kazanan_tek_secili(self):
        tedarikci_b = Tedarikci.objects.create(
            tenant=self.tenant, firma_adi="Yarış B Ltd.",
            firma_kodu=f"YRSB-{uuid.uuid4().hex[:8]}",
        )
        teklif_b = TedarikciTeklifi.objects.create(
            tenant=self.tenant, proje=self.proje, malzeme=self.malzeme,
            tedarikci=tedarikci_b, miktar=Decimal("100"), birim_fiyat=Decimal("9"),
        )

        def sec_a():
            return self._istemci().post(
                f"/api/v1/construction/tedarikci-teklifleri/{self.teklif.pk}/kazanan-sec/"
            ).status_code

        def sec_b():
            return self._istemci().post(
                f"/api/v1/construction/tedarikci-teklifleri/{teklif_b.pk}/kazanan-sec/"
            ).status_code

        sonuclar, hatalar = _paralel_kos([sec_a, sec_b])
        self.assertEqual(hatalar, [])
        self.assertEqual(sorted(k for _, k in sonuclar), [200, 200])
        self.assertEqual(
            TedarikciTeklifi.objects.filter(
                tenant=self.tenant, proje=self.proje, malzeme=self.malzeme,
                is_active=True, secildi=True,
            ).count(),
            1,
        )


class ParalelIadeMuhasebeTests(Faz6aConcurrencyBase):
    def test_paralel_iade_tek_muhasebe_zinciri(self):
        from accounting.models import MuhasebeFisi
        from cari.models import Cari, CariHareket
        from finance.models import Fatura

        cari = Cari.objects.create(
            tenant=self.tenant, ad="Paralel Iade Cari", tip="tedarikci",
            tur="kurumsal",
        )
        self.tedarikci.cari = cari
        self.tedarikci.save(update_fields=["cari"])
        siparis = self._onayli_siparis(miktar="10")
        kabul = self._onayli_kabul(siparis, miktar="10")
        kalem_pk = kabul.kalemler.get().pk
        sonuclar, hatalar = _paralel_kos([
            lambda: self._istemci().post(
                "/api/v1/purchase-stok-hareketleri/iade-olustur/",
                {"mal_kabul_kalemi": kalem_pk, "miktar": "7"},
                format="json",
            ).status_code,
            lambda: self._istemci().post(
                "/api/v1/purchase-stok-hareketleri/iade-olustur/",
                {"mal_kabul_kalemi": kalem_pk, "miktar": "7"},
                format="json",
            ).status_code,
        ])
        self.assertEqual(hatalar, [])
        self.assertEqual(len(sonuclar), 2)
        toplam_iade = sum(
            s.miktar for s in StokHareketi.objects.filter(
                kaynak_belge_tipi="Iade", kaynak_belge_kalem_id=kalem_pk)
        )
        self.assertLessEqual(toplam_iade, Decimal("10"))
        self.assertLessEqual(
            Fatura.objects.filter(fatura_turu="iade").count(), 2
        )


class ParalelOdemeIptalTests(Faz6aConcurrencyBase):
    def _odeme_ac(self):
        from datetime import date

        from accounting.models import HesapPlani
        from cari.models import Cari
        from finance.models import FinansalIslem
        from finance.services.entegrasyon import finansal_islem_muhasebelestir

        cari = Cari.objects.create(
            tenant=self.tenant, ad="Paralel Cari", tip="tedarikci", tur="kurumsal"
        )
        kasa = self._kasa_ac()
        karsilik, _ = HesapPlani.objects.get_or_create(
            tenant=self.tenant, kod="770",
            defaults={"ad": "Gider", "tip": "gider"},
        )
        islem = FinansalIslem.objects.create(
            tenant=self.tenant, hesap=kasa, cari=cari,
            yon=FinansalIslem.Yon.GIDER, tutar=Decimal("5000.00"),
            islem_tarihi=date(2026, 9, 18),
        )
        finansal_islem_muhasebelestir(islem, karsilik_hesap_id=karsilik.pk)
        return FinansalIslem.objects.get(pk=islem.pk)

    def _kasa_ac(self):
        from finance.models import KasaBankaHesabi

        kasa, _ = KasaBankaHesabi.objects.get_or_create(
            tenant=self.tenant, kod="PK-01",
            defaults={"ad": "Paralel Kasa", "tip": "kasa"},
        )
        return kasa

    def test_paralel_iptal_tek_ters_kayit(self):
        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket

        finans = User.objects.create_user(
            username=f"finpar_{uuid.uuid4().hex[:8]}", password="x",
            email=f"finpar_{uuid.uuid4().hex[:8]}@example.com",
            tenant=self.tenant, role=UserRole.FINANS,
        )
        istemci = APIClient()
        istemci.force_authenticate(user=finans)
        islem = self._odeme_ac()

        def iptal():
            return istemci.post(
                f"/api/v1/finance/finansal-islemler/{islem.pk}/iptal/"
            ).status_code

        sonuclar, hatalar = _paralel_kos([iptal, iptal])
        self.assertEqual(hatalar, [])
        for _, kod in sonuclar:
            self.assertIn(kod, (200, 400))
        self.assertEqual(
            CariHareket.objects.filter(finansal_islem=islem).count(), 1
        )
        self.assertEqual(
            MuhasebeFisi.objects.filter(
                tenant=self.tenant, fis_no=f"FINTR-{islem.pk}"
            ).count(),
            1,
        )


class ParalelYukTests(Faz6aConcurrencyBase):
    """FAZ 6E §11 — 10 paralel yük regresyonu (duplicate/500/deadlock yok)."""

    def _taslak_kabul(self, miktar="10"):
        from purchasing.services import mal_kabul_olustur as _olustur

        siparis = self._onayli_siparis(miktar=miktar)
        return _olustur(
            tenant_id=self.tenant.pk, siparis_id=siparis.pk, depo_id=self.depo_a.pk,
            created_by_id=self.editor.pk,
            kalemler=[{
                "siparis_kalemi_id": siparis.kalemler.get().pk,
                "kabul_miktari": miktar, "red_miktari": "0",
            }],
        )

    def test_on_paralel_malkabul_onay(self):
        from accounting.models import MuhasebeFisi
        from cari.models import CariHareket
        from finance.models import Fatura

        kabuller = [self._taslak_kabul() for _ in range(10)]
        istemci = self._istemci()

        def onayla(k):
            return istemci.post(
                f"/api/v1/purchase-mal-kabul/{k.pk}/onayla/"
            ).status_code

        sonuclar, hatalar = _paralel_kos([lambda k=k: onayla(k) for k in kabuller])
        self.assertEqual(hatalar, [])
        self.assertEqual(sorted(k for _, k in sonuclar), [200] * 10)
        nos = [f"SAT-{k.belge_no}" for k in kabuller]
        self.assertEqual(Fatura.objects.filter(No__in=nos).count(), 10)
        self.assertEqual(CariHareket.objects.filter(fatura__No__in=nos).count(), 10)
        self.assertEqual(
            MuhasebeFisi.objects.filter(
                tenant=self.tenant,
                fis_no__in=[f"MK-{k.belge_no}" for k in kabuller],
            ).count(),
            10,
        )

    def test_on_paralel_iade(self):
        from django.db.models import Sum

        from purchasing.models import StokHareketi

        kabul = self._onayli_kabul(self._onayli_siparis(), miktar="100")
        kalem_pk = kabul.kalemler.get().pk
        istemci = self._istemci()

        def iade():
            return istemci.post(
                "/api/v1/purchase-stok-hareketleri/iade-olustur/",
                {"mal_kabul_kalemi": kalem_pk, "miktar": "5"},
                format="json",
            ).status_code

        sonuclar, hatalar = _paralel_kos([iade for _ in range(10)])
        self.assertEqual(hatalar, [])
        self.assertEqual(sorted(k for _, k in sonuclar), [200] * 10)
        self.assertEqual(
            StokHareketi.objects.filter(
                tenant=self.tenant, kaynak_belge_tipi="Iade",
                kaynak_belge_kalem_id=kalem_pk,
            ).aggregate(t=Sum("miktar"))["t"],
            Decimal("50.0000"),
        )

    def test_on_paralel_muhasebelestir(self):
        from finance.models import Fatura

        self.tedarikci.cari = None
        self.tedarikci.save(update_fields=["cari"])
        kabuller = [self._taslak_kabul() for _ in range(10)]
        istemci = self._istemci()
        for k in kabuller:
            self.assertEqual(
                istemci.post(f"/api/v1/purchase-mal-kabul/{k.pk}/onayla/").status_code,
                200,
            )
        self.assertFalse(
            Fatura.objects.filter(
                No__in=[f"SAT-{k.belge_no}" for k in kabuller]
            ).exists()
        )
        self.tedarikci.cari = self.cari
        self.tedarikci.save(update_fields=["cari"])

        def muhasebelestir(k):
            return istemci.post(
                f"/api/v1/purchase-mal-kabul/{k.pk}/muhasebelestir/"
            ).status_code

        sonuclar, hatalar = _paralel_kos(
            [lambda k=k: muhasebelestir(k) for k in kabuller]
        )
        self.assertEqual(hatalar, [])
        self.assertEqual(sorted(k for _, k in sonuclar), [200] * 10)
        self.assertEqual(
            Fatura.objects.filter(
                No__in=[f"SAT-{k.belge_no}" for k in kabuller]
            ).count(),
            10,
        )
