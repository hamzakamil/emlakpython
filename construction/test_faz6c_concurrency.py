"""FAZ 6C — Hakediş onayında gerçek paralel (thread) idempotency testi.

Aynı hakediş için 10 paralel ONAYLA isteği (aynı Idempotency-Key):
tek onay, tek cari hareket, tek fiş; 500/IntegrityError yok.
Desen: purchasing/test_faz6a_concurrency.py (TransactionTestCase + bariyer).
"""

import uuid
from decimal import Decimal

from django.test import TransactionTestCase
from rest_framework.test import APIClient

from cari.models import Cari, CariHareket
from tenants.models import Tenant
from users.models import User, UserRole

from purchasing.test_faz6a_concurrency import _paralel_kos

from .models import Hakedis, Poz, PozFiyat, PozGrubu, PozPlan, Proje
from .services import hakedis_satirlari_olustur


class Faz6cConcurrencyBase(TransactionTestCase):
    @classmethod
    def _fixture_teardown(cls):
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
        self.tenant = Tenant.objects.create(name="Hakediş Yarış A.Ş.", slug=f"hd-yaris-{unique}")
        self.editor = User.objects.create_user(
            username=f"hd_{unique}", password="x", email=f"hd_{unique}@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )
        self.proje = Proje.objects.create(
            tenant=self.tenant, proje_kodu=f"HD-{unique}", ad="Yarış Projesi"
        )
        grup = PozGrubu.objects.create(tenant=self.tenant, kod="HD", ad="Hakediş")
        self.poz = Poz.objects.create(
            tenant=self.tenant, poz_no="HD-100", ad="Yarış Pozu", birim="m",
            grup=grup,
        )
        PozFiyat.objects.create(
            tenant=self.tenant, poz=self.poz, yil=2026, birim_fiyat=Decimal("100.00")
        )
        PozPlan.objects.create(
            tenant=self.tenant, proje=self.proje, poz=self.poz, yil=2026,
            planlanan_miktar=Decimal("100.0000"), gercek_miktar=Decimal("40.0000"),
        )
        self.cari = Cari.objects.create(
            tenant=self.tenant, ad="Yarış Taşeron", tip="taseron", tur="kurumsal"
        )
        self.hakedis = Hakedis.objects.create(
            tenant=self.tenant, proje=self.proje, donem="2026-03", cari=self.cari
        )
        hakedis_satirlari_olustur(self.hakedis)


class ParalelHakedisOnayTests(Faz6cConcurrencyBase):
    def test_paralel_onay_tek_zincir(self):
        from accounting.models import MuhasebeFisi

        istemci = APIClient()
        istemci.force_authenticate(user=self.editor)
        gonder = {"HTTP_IDEMPOTENCY_KEY": f"hd-paralel-{uuid.uuid4().hex[:8]}"}

        def onayla():
            return istemci.post(
                f"/api/v1/construction/hakedisler/{self.hakedis.pk}/onayla/",
                **gonder,
            ).status_code

        sonuclar, hatalar = _paralel_kos([onayla for _ in range(10)])
        self.assertEqual(hatalar, [])
        self.assertEqual(len(sonuclar), 10)
        for _, kod in sonuclar:
            self.assertIn(kod, (200, 400))
        self.assertEqual(
            CariHareket.objects.filter(tenant=self.tenant, cari=self.cari).count(), 1
        )
        self.assertEqual(
            MuhasebeFisi.objects.filter(
                tenant=self.tenant,
                fis_no=f"HD-{self.proje.proje_kodu}-2026-03",
            ).count(),
            1,
        )
        self.hakedis.refresh_from_db()
        self.assertEqual(self.hakedis.durum, Hakedis.Durum.ONAYLANDI)
