import json
from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from tenants.models import Tenant

from .models import Fatura, FinansalIslem, KasaBankaHesabi


class FinansalMutabakatCommandTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="Mutabakat A.Ş.", slug="mutabakat-as")
        self.diger = Tenant.objects.create(name="Diğer A.Ş.", slug="diger-as")
        self.kasa = KasaBankaHesabi.objects.create(
            tenant=self.tenant,
            kod="K-01",
            ad="Merkez Kasa",
        )
        Fatura.objects.create(
            tenant=self.tenant,
            No="M-001",
            tarih=date(2026, 9, 18),
            tutar=Decimal("100.00"),
        )
        FinansalIslem.objects.create(
            tenant=self.tenant,
            hesap=self.kasa,
            yon=FinansalIslem.Yon.GIDER,
            tutar=Decimal("25.00"),
            islem_tarihi=date(2026, 9, 18),
        )
        Fatura.objects.create(
            tenant=self.diger,
            No="D-001",
            tarih=date(2026, 9, 18),
            tutar=Decimal("900.00"),
        )

    def test_json_raporu_read_only_ve_tenant_filtreli(self):
        before = {
            "tenant": Tenant.objects.count(),
            "fatura": Fatura.objects.count(),
            "islem": FinansalIslem.objects.count(),
        }
        output = StringIO()
        call_command(
            "finansal_mutabakat",
            tenant_id=self.tenant.pk,
            output_format="json",
            stdout=output,
        )

        report = json.loads(output.getvalue())
        self.assertTrue(report["read_only"])
        self.assertEqual(len(report["tenants"]), 1)
        self.assertEqual(report["tenants"][0]["id"], self.tenant.pk)
        self.assertEqual(report["tenants"][0]["counts"]["fatura"], 1)
        self.assertEqual(report["tenants"][0]["totals"]["finansal_gider"], "25.00")
        self.assertEqual(
            before,
            {
                "tenant": Tenant.objects.count(),
                "fatura": Fatura.objects.count(),
                "islem": FinansalIslem.objects.count(),
            },
        )
