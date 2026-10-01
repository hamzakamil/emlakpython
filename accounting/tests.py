"""Muhasebe modülü testleri — çift kayıt, satır değişmezliği, mizan, tenant izolasyonu."""

from datetime import date
from decimal import Decimal
import importlib

from django.apps import apps
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User, UserRole

from .models import FisSatiri, HesapPlani, MuhasebeFisi, NormalBakiye


class AccountingBase(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Muhasebe A.Ş.", slug="muhasebe-as")
        self.diger = Tenant.objects.create(name="Komşu Muh. Ltd.", slug="komsu-muh")
        import uuid
        unique = uuid.uuid4().hex[:8]
        self.muhasebeci = User.objects.create_user(
            username=f"muhasebe_{unique}", password="x", email=f"m_{unique}@a.com",
            tenant=self.tenant, role=UserRole.MUHASEBE,
        )
        self.finansci = User.objects.create_user(
            username=f"finans_{unique}", password="x", email=f"f_{unique}@a.com",
            tenant=self.tenant, role=UserRole.FINANS,
        )
        self.kasa = HesapPlani.objects.create(
            tenant=self.tenant, kod="100", ad="Kasa", tip="aktif",
        )
        self.satici = HesapPlani.objects.create(
            tenant=self.tenant, kod="320", ad="Satıcılar", tip="pasif",
        )

    def _istemci(self, kullanici):
        istemci = APIClient()
        istemci.force_authenticate(user=kullanici)
        return istemci

    def _fis_payload(self, borc="100.00", alacak="100.00", fis_no="F-2026-001"):
        return {
            "fis_no": fis_no,
            "fis_tarihi": "2026-03-01",
            "aciklama": "Test fişi",
            "satirlar": [
                {"hesap": self.kasa.pk, "borc": borc, "alacak": "0.00"},
                {"hesap": self.satici.pk, "borc": "0.00", "alacak": alacak},
            ],
        }


class ModelTests(AccountingBase):
    def test_hesap_kodu_tenant_icinde_unique(self):
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            HesapPlani.objects.create(tenant=self.tenant, kod="100", ad="Kopya")

    def test_fis_borc_alacak_esit_degil_reddedilir(self):
        fis = MuhasebeFisi.objects.create(
            tenant=self.tenant, fis_no="F-X1", fis_tarihi=date(2026, 3, 1),
        )
        FisSatiri.objects.create(fis=fis, hesap=self.kasa, borc=Decimal("100.00"))
        FisSatiri.objects.create(fis=fis, hesap=self.satici, alacak=Decimal("90.00"))
        with self.assertRaises(ValidationError):
            fis.full_clean()

    def test_satir_hem_borc_hem_alacak_reddedilir(self):
        fis = MuhasebeFisi.objects.create(
            tenant=self.tenant, fis_no="F-X2", fis_tarihi=date(2026, 3, 1),
        )
        satir = FisSatiri(fis=fis, hesap=self.kasa, borc=Decimal("10"), alacak=Decimal("10"))
        with self.assertRaises(ValidationError):
            satir.full_clean()


class HesapPlaniHiyerarsiTests(AccountingBase):
    def test_td_hp_tum_siniflar_ve_ana_hesaplar_yukludur(self):
        temel_migration = importlib.import_module("accounting.migrations.0003_td_hesaplari")
        temel_migration.yukle_td_hp(apps, None)
        migration = importlib.import_module("accounting.migrations.0004_td_hesaplari_tamamla")
        migration.yukle_ek_td_hp(apps, None)
        grup_migration = importlib.import_module("accounting.migrations.0005_td_hesap_gruplari")
        grup_migration.yukle_td_hp_gruplari(apps, None)

        beklenen_siniflar = {str(i) for i in range(1, 10)}
        self.assertSetEqual(
            set(
                HesapPlani.objects.filter(
                    tenant=self.tenant, kod__in=beklenen_siniflar
                ).values_list("kod", flat=True)
            ),
            beklenen_siniflar,
        )
        for kod in ("104", "123", "170", "350", "391", "701", "799"):
            self.assertTrue(
                HesapPlani.objects.filter(tenant=self.tenant, kod=kod).exists(),
                kod,
            )

    def test_mevcut_smoke_kaydi_korunur_ve_tdhp_idempotent_yuklenir(self):
        smoke = HesapPlani.objects.create(
            tenant=self.tenant, kod="100.SMOKE", ad="Kasa Hesabı", tip="aktif"
        )
        migration = importlib.import_module("accounting.migrations.0003_td_hesaplari")
        migration.yukle_td_hp(apps, None)
        migration.yukle_td_hp(apps, None)

        smoke.refresh_from_db()
        kasa = HesapPlani.objects.get(tenant=self.tenant, kod="100")
        self.assertEqual(smoke.ad, "Kasa Hesabı")
        self.assertEqual(kasa.normal_bakiye, NormalBakiye.BORC)
        self.assertEqual(kasa.ust_hesap.kod, "10")
        self.assertEqual(kasa.ust_hesap.ust_hesap.kod, "1")
        self.assertEqual(HesapPlani.objects.filter(tenant=self.tenant, kod="100").count(), 1)

    def test_fis_satiri_hesap_fk_hiyerarsi_alaniyla_calismaya_devam_eder(self):
        fis = MuhasebeFisi.objects.create(
            tenant=self.tenant, fis_no="F-HIY-1", fis_tarihi=date(2026, 9, 18)
        )
        satir = FisSatiri.objects.create(
            fis=fis, hesap=self.kasa, borc=Decimal("25.00")
        )
        self.assertEqual(satir.hesap_id, self.kasa.id)
        self.assertEqual(FisSatiri.objects.get(pk=satir.pk).hesap.kod, "100")


class MizanEsitlikTests(AccountingBase):
    """FAZ 6E — mizan DB aggregation ile birebir aynı sonucu verir."""

    def _mizan_ac(self):
        kdv = HesapPlani.objects.create(
            tenant=self.tenant, kod="191", ad="KDV", tip="aktif",
        )
        fis1 = MuhasebeFisi.objects.create(
            tenant=self.tenant, fis_no="M-001", fis_tarihi=date(2026, 3, 1),
            durum=MuhasebeFisi.Durum.KAYITLI,
        )
        FisSatiri.objects.create(fis=fis1, hesap=self.kasa, borc=Decimal("1000.00"))
        FisSatiri.objects.create(fis=fis1, hesap=kdv, borc=Decimal("200.00"))
        FisSatiri.objects.create(
            fis=fis1, hesap=self.satici, alacak=Decimal("1200.00")
        )
        fis2 = MuhasebeFisi.objects.create(
            tenant=self.tenant, fis_no="M-002", fis_tarihi=date(2026, 3, 2),
            durum=MuhasebeFisi.Durum.KAYITLI,
        )
        FisSatiri.objects.create(fis=fis2, hesap=self.kasa, borc=Decimal("50.00"))
        FisSatiri.objects.create(fis=fis2, hesap=self.satici, alacak=Decimal("50.00"))
        iptal = MuhasebeFisi.objects.create(
            tenant=self.tenant, fis_no="M-IPT", fis_tarihi=date(2026, 3, 3),
            durum=MuhasebeFisi.Durum.IPTAL,
        )
        FisSatiri.objects.create(fis=iptal, hesap=self.kasa, borc=Decimal("9999.00"))
        FisSatiri.objects.create(
            fis=iptal, hesap=self.satici, alacak=Decimal("9999.00")
        )

    def test_mizan_toplamlari_ve_iptal_haric(self):
        self._mizan_ac()
        veri = self._istemci(self.muhasebeci).get(
            "/api/v1/accounting/fisler/mizan/"
        ).json()["data"]
        self.assertEqual(
            veri,
            [
                {"hesap_kodu": "100", "hesap_adi": "Kasa",
                 "borc": "1050.00", "alacak": "0.00", "bakiye": "1050.00"},
                {"hesap_kodu": "191", "hesap_adi": "KDV",
                 "borc": "200.00", "alacak": "0.00", "bakiye": "200.00"},
                {"hesap_kodu": "320", "hesap_adi": "Satıcılar",
                 "borc": "0.00", "alacak": "1250.00", "bakiye": "-1250.00"},
            ],
        )
        borc = sum(Decimal(s["borc"]) for s in veri)
        alacak = sum(Decimal(s["alacak"]) for s in veri)
        self.assertEqual(borc, alacak)
