"""Finansal kayıtlar için read-only mutabakat ve baseline raporu."""

from __future__ import annotations

import json
import time
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce

from accounting.models import FisSatiri, MuhasebeFisi
from cari.models import CariHareket
from finance.models import Fatura, FinansalIslem
from tenants.models import Tenant


ZERO = Value(Decimal("0"), output_field=DecimalField(max_digits=15, decimal_places=2))


def _decimal(value: Decimal | None) -> str:
    return str(value or Decimal("0.00"))


class Command(BaseCommand):
    help = (
        "Finansal kayıtları değiştirmeden tenant bazlı mutabakat ve "
        "performans baseline raporu üretir."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-id",
            type=int,
            help="Yalnızca belirtilen tenant için rapor üretir.",
        )
        parser.add_argument(
            "--format",
            choices=("table", "json"),
            default="table",
            dest="output_format",
            help="Çıktı biçimi (varsayılan: table).",
        )

    def handle(self, *args, **options):
        started = time.perf_counter()
        tenant_id = options.get("tenant_id")
        tenants = Tenant.objects.filter(is_active=True).order_by("id")
        if tenant_id is not None:
            tenants = tenants.filter(pk=tenant_id)
            if not tenants.exists():
                raise CommandError(f"Aktif tenant bulunamadı: {tenant_id}")

        report = {
            "read_only": True,
            "tenant_filter": tenant_id,
            "generated_at": time.time(),
            "tenants": [self._tenant_report(tenant) for tenant in tenants],
            "global_checks": self._global_checks(tenant_id),
        }
        report["elapsed_seconds"] = round(time.perf_counter() - started, 4)

        if options["output_format"] == "json":
            self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            self._write_table(report)

    def _tenant_report(self, tenant: Tenant) -> dict:
        fatura = Fatura.objects.filter(tenant_id=tenant.id)
        cari_hareket = CariHareket.objects.filter(tenant_id=tenant.id)
        finansal_islem = FinansalIslem.objects.filter(tenant_id=tenant.id)
        fis = MuhasebeFisi.objects.filter(tenant_id=tenant.id)

        fatura_totals = fatura.aggregate(
            toplam=Coalesce(Sum("tutar"), ZERO),
            odenen=Coalesce(Sum("odenen_tutar"), ZERO),
        )
        cari_totals = cari_hareket.filter(is_cancelled=False).aggregate(
            borc=Coalesce(
                Sum("tutar", filter=Q(yon=CariHareket.Yon.BORC)), ZERO
            ),
            alacak=Coalesce(
                Sum("tutar", filter=Q(yon=CariHareket.Yon.ALACAK)), ZERO
            ),
        )
        finans_totals = finansal_islem.filter(is_cancelled=False).aggregate(
            gelir=Coalesce(
                Sum("tutar", filter=Q(yon=FinansalIslem.Yon.GELIR)), ZERO
            ),
            gider=Coalesce(
                Sum("tutar", filter=Q(yon=FinansalIslem.Yon.GIDER)), ZERO
            ),
            transfer=Coalesce(
                Sum("tutar", filter=Q(yon=FinansalIslem.Yon.TRANSFER)), ZERO
            ),
        )
        fis_totals = FisSatiri.objects.filter(fis__tenant_id=tenant.id).aggregate(
            borc=Coalesce(Sum("borc"), ZERO),
            alacak=Coalesce(Sum("alacak"), ZERO),
        )

        return {
            "id": tenant.id,
            "name": tenant.name,
            "counts": {
                "fatura": fatura.count(),
                "cari_hareket": cari_hareket.count(),
                "finansal_islem": finansal_islem.count(),
                "muhasebe_fisi": fis.count(),
            },
            "totals": {
                "fatura_tutar": _decimal(fatura_totals["toplam"]),
                "fatura_odenen": _decimal(fatura_totals["odenen"]),
                "cari_borc": _decimal(cari_totals["borc"]),
                "cari_alacak": _decimal(cari_totals["alacak"]),
                "finansal_gelir": _decimal(finans_totals["gelir"]),
                "finansal_gider": _decimal(finans_totals["gider"]),
                "finansal_transfer": _decimal(finans_totals["transfer"]),
                "muhasebe_borc": _decimal(fis_totals["borc"]),
                "muhasebe_alacak": _decimal(fis_totals["alacak"]),
            },
            "checks": {
                "unbalanced_vouchers": self._unbalanced_voucher_count(fis),
                "cross_tenant_invoices": fatura.filter(
                    Q(cari__isnull=False) & ~Q(cari__tenant_id=F("tenant_id"))
                ).count(),
                "cross_tenant_financial_transactions": finansal_islem.filter(
                    Q(hesap__isnull=False) & ~Q(hesap__tenant_id=F("tenant_id"))
                ).count(),
                "cross_tenant_cari_transactions": cari_hareket.filter(
                    ~Q(cari__tenant_id=F("tenant_id"))
                ).count(),
                "cross_tenant_voucher_lines": FisSatiri.objects.filter(
                    fis__tenant_id=tenant.id
                ).exclude(hesap__tenant_id=F("fis__tenant_id")).count(),
            },
        }

    def _global_checks(self, tenant_id: int | None) -> dict:
        invoices = Fatura.objects.all()
        if tenant_id is not None:
            invoices = invoices.filter(tenant_id=tenant_id)
        return {
            "invoice_without_cari": invoices.filter(cari__isnull=True).count(),
            "invoice_without_line_items": invoices.filter(kalemler__isnull=True).distinct().count(),
            "linkage_gaps": [
                "Fatura-CariHareket ve Fatura-MuhasebeFisi arasında kaynak FK bulunmadığı için "
                "otomatik eşleşme bu raporda kanıtlanamaz.",
            ],
        }

    @staticmethod
    def _unbalanced_voucher_count(vouchers) -> int:
        rows = (
            FisSatiri.objects.filter(fis__in=vouchers)
            .values("fis_id")
            .annotate(
                borc=Coalesce(Sum("borc"), ZERO),
                alacak=Coalesce(Sum("alacak"), ZERO),
            )
            .filter(~Q(borc=F("alacak")))
        )
        return rows.count()

    def _write_table(self, report: dict) -> None:
        self.stdout.write("Finansal mutabakat raporu (READ-ONLY)")
        self.stdout.write(f"Süre: {report['elapsed_seconds']} sn")
        for tenant in report["tenants"]:
            totals = tenant["totals"]
            checks = tenant["checks"]
            self.stdout.write(
                f"\n[{tenant['id']}] {tenant['name']}\n"
                f"  Kayıtlar: {tenant['counts']}\n"
                f"  Fatura: {totals['fatura_tutar']} | Ödenen: {totals['fatura_odenen']}\n"
                f"  Cari borç/alacak: {totals['cari_borc']} / {totals['cari_alacak']}\n"
                f"  Fiş borç/alacak: {totals['muhasebe_borc']} / {totals['muhasebe_alacak']}\n"
                f"  Kontroller: {checks}"
            )
        self.stdout.write(f"\nGenel kontroller: {report['global_checks']}")
