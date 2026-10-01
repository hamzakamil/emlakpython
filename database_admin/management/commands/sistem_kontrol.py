"""FAZ 6F-3 — deploy sonrası sistem kontrolü (liveness/readiness/smoke).

Kontroller:
  1. DB bağlantısı (SELECT 1)
  2. Bekleyen migration yokluğu
  3. Yedek tazeliği (son manifest yaşı <= BACKUP_MAX_YAS_SAAT; uyarı)
  4. Yedek dizini boş alan (1 GB altı uyarı)
  5. --kullanici ile smoke: kullanıcı/tenant aktifliği + örnek fatura/stok okuma

Sert hatalarda (1, 2, 5) CommandError → sıfır-dışı çıkış (güvenli duruş).
Uyarılar (3, 4) çıkışı bozmaz, açıkça işaretlenir.
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, connection
from django.utils import timezone

log = logging.getLogger("erp.health")


class Command(BaseCommand):
    help = "Deploy sonrası sistem kontrolü (db/migration/yedek/disk/smoke)."

    def add_arguments(self, parser):
        parser.add_argument("--kullanici", default="", help="Smoke testi kullanıcı adı")

    def handle(self, *args, **kwargs):
        uyari = []
        self._db_kontrol()
        self.stdout.write("DB: OK")
        bekleyen = self._bekleyen_migration()
        if bekleyen:
            raise CommandError(f"Bekleyen migration var: {bekleyen} (güvenli duruş).")
        self.stdout.write("MIGRATION: OK")
        yas = self._yedek_yasi_saat()
        if yas is None:
            uyari.append("YEDEK-YOK: hiç manifest bulunamadı.")
        elif yas > getattr(settings, "BACKUP_MAX_YAS_SAAT", 26):
            uyari.append(f"YEDEK-ESKI: son yedek {yas:.1f} saat önce.")
        else:
            self.stdout.write(f"YEDEK: OK ({yas:.1f} saat)")
        bosta = self._bosta_alan_gb()
        if bosta is not None and bosta < 1.0:
            uyari.append(f"DISK-DAR: yedek dizininde {bosta:.2f} GB boş.")
        else:
            self.stdout.write("DISK: OK")
        if kwargs.get("kullanici"):
            self._smoke(kwargs["kullanici"])
            self.stdout.write("SMOKE: OK")
        for satir in uyari:
            self.stdout.write(f"UYARI: {satir}")
            log.warning(
                "event=sistem_kontrol_uyari detay=%s", satir,
                extra={"operation": "sistem.kontrol", "resource_id": "-"},
            )
        log.info(
            "event=sistem_kontrol_ok",
            extra={"operation": "sistem.kontrol", "resource_id": "-"},
        )
        self.stdout.write("SISTEM KONTROL: TAMAM")

    def _db_kontrol(self) -> None:
        try:
            with connection.cursor() as imlec:
                imlec.execute("SELECT 1")
                imlec.fetchone()
        except OperationalError as exc:
            log.error("event=sistem_kontrol_hata sebep=db")
            raise CommandError(f"DB erişilemiyor: {exc}") from exc

    def _bekleyen_migration(self) -> int:
        from django.db.migrations.executor import MigrationExecutor

        try:
            calistirici = MigrationExecutor(connection)
            plan = calistirici.migration_plan(
                calistirici.loader.graph.leaf_nodes()
            )
            return len(plan)
        except Exception as exc:  # noqa: BLE001 — belirlenemezse güvenli duruş
            raise CommandError(f"Migration durumu belirlenemedi: {exc}") from exc

    def _yedek_yasi_saat(self) -> float | None:
        dizin = Path(getattr(settings, "DB_BACKUP_DIR", settings.BASE_DIR / "backups"))
        manifestler = sorted(
            dizin.glob("emlak_erp_*.manifest.json"),
            key=lambda p: p.stat().st_mtime,
        )
        if not manifestler:
            return None
        try:
            bilgi = json.loads(manifestler[-1].read_text(encoding="utf-8"))
            olusturulma = bilgi.get("olusturulma", "")
            from datetime import datetime

            zaman = datetime.fromisoformat(olusturulma)
            if timezone.is_naive(zaman):
                zaman = timezone.make_aware(zaman)
            return (timezone.now() - zaman).total_seconds() / 3600
        except (OSError, ValueError):
            return None

    def _bosta_alan_gb(self) -> float | None:
        try:
            dizin = Path(getattr(settings, "DB_BACKUP_DIR", settings.BASE_DIR / "backups"))
            dizin.mkdir(parents=True, exist_ok=True)
            return shutil.disk_usage(dizin).free / (1024 ** 3)
        except OSError:
            return None

    def _smoke(self, kullanici_adi: str) -> None:
        from users.models import User

        try:
            kullanici = User.objects.select_related("tenant").get(
                username=kullanici_adi
            )
        except User.DoesNotExist as exc:
            raise CommandError(f"Smoke kullanıcısı yok: {kullanici_adi}") from exc
        if not kullanici.is_active:
            raise CommandError("Smoke kullanıcısı pasif.")
        tenant = getattr(kullanici, "tenant", None)
        if tenant is not None and not tenant.is_active:
            raise CommandError("Smoke tenant'ı pasif.")
        if tenant is None:
            raise CommandError("Smoke kullanıcısının tenant'ı yok.")
        from finance.models import Fatura
        from purchasing.models import StokHareketi

        fatura_sayisi = Fatura.objects.filter(tenant=tenant).count()
        stok_sayisi = StokHareketi.objects.filter(tenant=tenant).count()
        self.stdout.write(
            f"SMOKE-DETAY: tenant={tenant.pk} fatura={fatura_sayisi} stok={stok_sayisi}"
        )
