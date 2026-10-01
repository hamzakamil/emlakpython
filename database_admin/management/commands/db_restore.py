"""FAZ 6F-3 — korumalı geri yükleme (DR).

Kullanım:
    python manage.py db_restore --dosya=...sql[.fernet] \\
        --hedef-db-adi=<ayarlı DB adı> --onay=EVET-EMINIM

Kurallar:
- --hedef-db-adi ayarlardaki DB adıyla birebir eşleşmezse DURUR.
- --onay verilmezse DURUR (kuru çalıştırma bilgisi yazılır).
- Manifest varsa sha256 doğrulanır; .fernet ise BACKUP_ENCRYPTION_KEY ile çözülür.
- Restore psql --single-transaction ile tek işlemde yapılır.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

log = logging.getLogger("erp.backup")
ONAY_KELIMESI = "EVET-EMINIM"


class Command(BaseCommand):
    help = "Yedekten geri yükleme (çift onay korumalı)."

    def add_arguments(self, parser):
        parser.add_argument("--dosya", required=True, help="Yedek dosya yolu")
        parser.add_argument("--hedef-db-adi", required=True, help="Ayarlı DB adı")
        parser.add_argument("--onay", default="", help="Onay kelimesi")

    def handle(self, *args, **kwargs):
        from database_admin.api import _database_options, _run_db_tool, _tool_path
        from database_admin.management.commands.db_yedekle import (
            b64_sha256,
            fernet_coz,
        )

        kaynak = Path(kwargs["dosya"])
        if not kaynak.is_file():
            raise CommandError(f"Yedek bulunamadı: {kaynak}")
        gercek_ad = connection.settings_dict.get("NAME", "")
        if kwargs["hedef_db_adi"] != str(gercek_ad):
            raise CommandError(
                "Hedef DB adı ayarlarla eşleşmiyor; geri yükleme DURDURULDU."
            )
        if kwargs["onay"] != ONAY_KELIMESI:
            raise CommandError(
                f"Onay gerekli (--onay={ONAY_KELIMESI}). Hiçbir işlem yapılmadı."
            )
        manifest = kaynak.parent / f"{kaynak.name}.manifest.json"
        if manifest.is_file():
            try:
                bilgi = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise CommandError(f"Manifest okunamadı: {exc}") from exc
            ozet, _ = b64_sha256(kaynak)
            if bilgi.get("sha256") and bilgi["sha256"] != ozet:
                raise CommandError("sha256 uyuşmuyor; yedek bütünlüğü BOZUK.")
        sql_dosya = kaynak
        geciciler: list = []
        try:
            if kaynak.suffixes[-2:] == [".sql", ".fernet"] or kaynak.name.endswith(".fernet"):
                anahtar = getattr(settings, "BACKUP_ENCRYPTION_KEY", "") or ""
                if not anahtar:
                    raise CommandError("Şifreli yedek için BACKUP_ENCRYPTION_KEY gerekli.")
                fd, gecici_ad = tempfile.mkstemp(suffix=".sql")
                os.close(fd)
                gecici = Path(gecici_ad)
                geciciler.append(gecici)
                fernet_coz(kaynak, gecici, anahtar)
                sql_dosya = gecici
            uyumlu = _surum_uyumlulugu(sql_dosya)
            if uyumlu != sql_dosya:
                geciciler.append(uyumlu)
                sql_dosya = uyumlu
            try:
                psql = _tool_path("PSQL_PATH", "psql")
            except RuntimeError as exc:
                log.error("event=restore_hata sebep=arac_yok")
                raise CommandError(str(exc)) from exc
            secenek = _database_options()
            sonuc = _run_db_tool(
                [psql, "--dbname", secenek["dbname"], "--username", secenek["user"],
                 "--host", secenek["host"], "--port", secenek["port"],
                 "-v", "ON_ERROR_STOP=1",
                 "--single-transaction", "--file", str(sql_dosya)],
                timeout=900,
            )
            if sonuc.returncode != 0:
                log.error(
                    "event=restore_hata rc=%s", sonuc.returncode,
                    extra={"operation": "backup.restore", "resource_id": "-"},
                )
                raise CommandError(f"psql restore başarısız (rc={sonuc.returncode}).")
        finally:
            for gecici in geciciler:
                try:
                    gecici.unlink(missing_ok=True)
                except OSError:
                    pass
        log.info(
            "event=restore_ok dosya=%s", kaynak.name,
            extra={"operation": "backup.restore", "resource_id": "-"},
        )
        self.stdout.write(f"RESTORE TAMAM: {kaynak.name}")


def _surum_uyumlulugu(sql_dosya: Path) -> Path:
    """pg_dump istemcisi sunucudan yeniyse bilinmeyen SET satırlarını ayıklar.

    Örn. pg_dump 18 `SET transaction_timeout = 0` yazar; PG16 tanımaz ve
    --single-transaction içinde tüm restore'u bozar. Satır anlamsızdır
    (timeout kapalı) ve yalnızca eski sunucuda, uyarıyla ayıklanır.
    """
    try:
        with connection.cursor() as imlec:
            imlec.execute("SHOW server_version_num")
            surum = int(imlec.fetchone()[0])
    except Exception:  # noqa: BLE001 — belirlenemezse dosyaya dokunma
        return sql_dosya
    if surum >= 170000:
        return sql_dosya
    try:
        metin = sql_dosya.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return sql_dosya
    import re

    temiz, sayi = re.subn(
        r"(?m)^\s*SET\s+transaction_timeout\s*=[^;]*;\s*\n", "", metin
    )
    if not sayi:
        return sql_dosya
    import tempfile as _tmp

    fd, gecici_ad = _tmp.mkstemp(suffix=".sql")
    os.close(fd)
    gecici = Path(gecici_ad)
    gecici.write_text(temiz, encoding="utf-8")
    log.warning(
        "event=restore_uyumluluk ayiklanan=transaction_timeout",
        extra={"operation": "backup.restore", "resource_id": "-"},
    )
    return gecici
