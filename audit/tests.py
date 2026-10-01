"""FAZ 6F-2 — audit bütünlüğü, secret filtresi, korelasyon, erişim logu."""

import json
import uuid
from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User, UserRole

from .loglama import guvenli_snapshot, hassas_mi
from .models import AuditLog


class AuditBase(TestCase):
    def setUp(self):
        unique = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name="Denetim A.Ş.", slug=f"denetim-{unique}")
        self.editor = User.objects.create_user(
            username=f"den_{unique}", password="x", email=f"den_{unique}@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )
        self.muhasebeci = User.objects.create_user(
            username=f"muh_{unique}", password="x", email=f"muh_{unique}@example.com",
            tenant=self.tenant, role=UserRole.MUHASEBE,
        )

    def _istemci(self, kullanici):
        istemci = APIClient()
        istemci.force_authenticate(user=kullanici)
        return istemci


class AuditKayitTests(AuditBase):
    def test_fatura_olusturma_auditlenir(self):
        yanit = self._istemci(self.muhasebeci).post(
            "/api/v1/finance/faturalar/",
            {"No": "AUD-001", "tarih": "2026-03-05", "tutar": "120.00"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 201)
        kayit = AuditLog.objects.filter(tenant=self.tenant).latest("id")
        self.assertEqual(kayit.kullanıcı, self.muhasebeci)
        self.assertEqual(kayit.islem_türü, AuditLog.IslemTürü.CREATE)
        self.assertEqual(kayit.nesne_id, yanit.json()["data"]["id"])
        self.assertEqual(kayit.içerik_türü.app_label, "finance")
        self.assertEqual(kayit.içerik_türü.model, "fatura")
        yeni = json.loads(kayit.yeni_değer)
        self.assertEqual(yeni.get("No"), "AUD-001")
        self.assertEqual(kayit.correlation_id, yanit.headers.get("X-Correlation-ID"))
        self.assertTrue(kayit.correlation_id)

    def test_guncelleme_once_sonra_farki(self):
        from cari.models import Cari

        cari = Cari.objects.create(tenant=self.tenant, ad="Eski Ad")
        yanit = self._istemci(self.muhasebeci).patch(
            f"/api/v1/cari/cariler/{cari.pk}/", {"ad": "Yeni Ad"}, format="json"
        )
        self.assertEqual(yanit.status_code, 200)
        kayit = AuditLog.objects.filter(
            tenant=self.tenant, nesne_id=cari.pk,
            islem_türü=AuditLog.IslemTürü.UPDATE,
        ).latest("id")
        fark = json.loads(kayit.yeni_değer)
        self.assertEqual(fark["ad"], {"old": "Eski Ad", "new": "Yeni Ad"})

    def test_satinalma_onay_auditlenir(self):
        from construction.models import Proje
        from purchasing.models import SatinAlmaTalebi

        proje = Proje.objects.create(
            tenant=self.tenant, proje_kodu="AUD-P", ad="Audit Proje"
        )
        talep = SatinAlmaTalebi.objects.create(
            tenant=self.tenant, proje=proje, talep_sahibi=self.editor,
            talep_no=f"AUD-{uuid.uuid4().hex[:6]}",
        )
        istemci = self._istemci(self.editor)
        istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onaya-gonder/")
        self.assertEqual(
            istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onayla/").status_code,
            200,
        )
        kayit = AuditLog.objects.filter(
            tenant=self.tenant, nesne_id=talep.pk,
        ).latest("id")
        self.assertEqual(kayit.kullanıcı, self.editor)
        self.assertEqual(kayit.içerik_türü.app_label, "purchasing")
        self.assertEqual(kayit.içerik_türü.model, "satinalmatalebi")

    def test_reddedilen_snapshot_auditlenir(self):
        from construction.models import Hakedis, HakedisSatiri, Poz, PozGrubu, Proje
        from construction.services import hakedis_onayla, hakedis_satirlari_olustur
        from cari.models import Cari
        from construction.models import PozFiyat

        proje = Proje.objects.create(
            tenant=self.tenant, proje_kodu="AUD-H", ad="Audit Hakediş"
        )
        grup = PozGrubu.objects.create(tenant=self.tenant, kod="AH", ad="AH")
        poz = Poz.objects.create(
            tenant=self.tenant, poz_no="AH-1", ad="AH Poz", birim="m", grup=grup
        )
        PozFiyat.objects.create(
            tenant=self.tenant, poz=poz, yil=2026, birim_fiyat=Decimal("100.00")
        )
        from construction.models import PozPlan

        PozPlan.objects.create(
            tenant=self.tenant, proje=proje, poz=poz, yil=2026,
            planlanan_miktar=Decimal("10"), gercek_miktar=Decimal("5"),
        )
        cari = Cari.objects.create(
            tenant=self.tenant, ad="Audit Taşeron", tip="taseron", tur="kurumsal"
        )
        hakedis = Hakedis.objects.create(
            tenant=self.tenant, proje=proje, donem="2026-03", cari=cari
        )
        hakedis_satirlari_olustur(hakedis)
        hakedis_onayla(hakedis, onaylayan=self.editor)
        yanit = self._istemci(self.editor).patch(
            f"/api/v1/construction/hakedisler/{hakedis.pk}/",
            {"donem": "2026-05"}, format="json",
        )
        self.assertEqual(yanit.status_code, 400)
        kayit = AuditLog.objects.filter(
            tenant=self.tenant, islem_türü=AuditLog.IslemTürü.REJECTED
        ).latest("id")
        self.assertEqual(kayit.nesne_id, hakedis.pk)
        yeni = json.loads(kayit.yeni_değer)
        self.assertEqual(yeni["sonuc"], "REDDI")
        self.assertIn("donem", yeni["denenen"])


class SecretFiltreTests(TestCase):
    def test_hassas_alanlar_ayiklanir(self):
        for alan in ("password", "api_token", "SECRET_KEY", "tckn", "vkn", "iban", "telefon"):
            self.assertTrue(hassas_mi(alan), alan)
        for alan in ("ad", "tutar", "durum", "aciklama", "borc"):
            self.assertFalse(hassas_mi(alan), alan)

    def test_snapshot_hassas_alanlari_atlar(self):
        from users.models import User

        user = User(username="x")
        user.set_password("gizli-sifre-123")
        goruntu = guvenli_snapshot(user)
        birlesik = json.dumps(goruntu, ensure_ascii=False)
        self.assertNotIn("gizli-sifre-123", birlesik)
        self.assertNotIn("password", " ".join(goruntu.keys()))


class ErisimLogTests(AuditBase):
    def test_erisim_logu_ve_korelasyon_basligi(self):
        with self.assertLogs("erp.access", level="INFO") as yakalanan:
            yanit = self._istemci(self.editor).get("/api/v1/purchase-requests/")
        self.assertEqual(yanit.status_code, 200)
        self.assertTrue(yanit.headers.get("X-Correlation-ID"))
        self.assertTrue(
            any("purchase-requests" in kayit.getMessage() and " 200 " in kayit.getMessage()
                for kayit in yakalanan.records)
        )

    def test_finansal_event_logu(self):
        from construction.models import Proje
        from purchasing.models import SatinAlmaTalebi

        proje = Proje.objects.create(
            tenant=self.tenant, proje_kodu="LOG-P", ad="Log Proje"
        )
        talep = SatinAlmaTalebi.objects.create(
            tenant=self.tenant, proje=proje, talep_sahibi=self.editor,
            talep_no=f"LOG-{uuid.uuid4().hex[:6]}",
        )
        istemci = self._istemci(self.editor)
        with self.assertLogs("erp.purchasing", level="INFO") as yakalanan:
            istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onaya-gonder/")
            istemci.post(f"/api/v1/purchase-requests/{talep.pk}/onayla/")
        self.assertTrue(
            any("event=talep_durum" in kayit.getMessage() for kayit in yakalanan.records)
        )
