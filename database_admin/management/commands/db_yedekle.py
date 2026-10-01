"""FAZ 6F-3 — zamanlanmış yedek: dump + sha256 + şifrele + retention + off-site.

Kullanım (scheduler: cron/systemd/Task Scheduler):
    python manage.py db_yedekle [--etiket gece]

Başarısızlıkta CommandError (sıfır-dışı çıkış) + ERROR log; parola/anahtar
asla loglanmaz. Mevcut API yedek mekanizması değiştirilmez.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

log = logging.getLogger("erp.backup")


def yedek_dizini() -> Path:
    dizin = Path(getattr(settings, "DB_BACKUP_DIR", settings.BASE_DIR / "backups"))
    dizin.mkdir(parents=True, exist_ok=True)
    return dizin


def b64_sha256(dosya: Path) -> tuple[str, int]:
    ozet = hashlib.sha256()
    boyut = 0
    with dosya.open("rb") as akim:
        while True:
            parca = akim.read(1024 * 1024)
            if not parca:
                break
            ozet.update(parca)
            boyut += len(parca)
    return ozet.hexdigest(), boyut


def fernet_sifrele(kaynak: Path, hedef: Path, anahtar: str) -> None:
    from cryptography.fernet import Fernet, InvalidToken  # noqa: F401

    try:
        sifre = Fernet(anahtar.encode())
    except Exception as exc:
        raise CommandError("BACKUP_ENCRYPTION_KEY geçersiz (Fernet anahtarı olmalı).") from exc
    with kaynak.open("rb") as giris:
        veri = giris.read()
    with hedef.open("wb") as cikis:
        cikis.write(sifre.encrypt(veri))


def fernet_coz(kaynak: Path, hedef: Path, anahtar: str) -> None:
    from cryptography.fernet import Fernet, InvalidToken

    try:
        sifre = Fernet(anahtar.encode())
    except Exception as exc:
        raise CommandError("BACKUP_ENCRYPTION_KEY geçersiz.") from exc
    with kaynak.open("rb") as giris:
        try:
            veri = sifre.decrypt(giris.read())
        except InvalidToken as exc:
            raise CommandError("Yedek şifresi çözülemedi (anahtar/veri uyumsuz).") from exc
    with hedef.open("wb") as cikis:
        cikis.write(veri)


class Command(BaseCommand):
    help = "Üretim yedeği: pg_dump + manifest + şifreleme + retention + off-site."

    def add_arguments(self, parser):
        parser.add_argument("--etiket", default="", help="Dosya adına ek etiket")

    def handle(self, *args, **kwargs):
        from database_admin.api import _database_options, _run_db_tool, _tool_path

        dizin = yedek_dizini()
        damga = timezone.now().strftime("%Y%m%d_%H%M%S")
        etiket = kwargs.get("etiket") or ""
        etiket = f"_{etiket}" if etiket else ""
        ad = f"emlak_erp_{damga}{etiket}.sql"
        ham = dizin / ad
        try:
            pg_dump = _tool_path("PG_DUMP_PATH", "pg_dump")
        except RuntimeError as exc:
            log.error("event=yedek_hata sebep=arac_yok")
            raise CommandError(str(exc)) from exc
        secenek = _database_options()
        sonuc = _run_db_tool(
            [pg_dump,
             "--dbname", secenek["dbname"], "--username", secenek["user"],
             "--host", secenek["host"], "--port", secenek["port"],
             "--format=plain", "--clean", "--if-exists",
             "--no-owner", "--no-privileges", "--file", str(ham)],
            timeout=600,
        )
        if sonuc.returncode != 0 or not ham.exists() or ham.stat().st_size == 0:
            if ham.exists():
                ham.unlink(missing_ok=True)
            log.error(
                "event=yedek_hata sebep=dump rc=%s", sonuc.returncode,
                extra={"operation": "backup.al", "resource_id": "-"},
            )
            raise CommandError(f"pg_dump başarısız (rc={sonuc.returncode}).")

        anahtar = getattr(settings, "BACKUP_ENCRYPTION_KEY", "") or ""
        nihai = ham
        sifreli = False
        if anahtar:
            nihai = ham.with_suffix(".sql.fernet")
            fernet_sifrele(ham, nihai, anahtar)
            ham.unlink(missing_ok=True)
            sifreli = True
        else:
            log.warning(
                "event=yedek_sifresiz dosya=%s", nihai.name,
                extra={"operation": "backup.al", "resource_id": "-"},
            )
        ozet, boyut = b64_sha256(nihai)
        bildirim = {
            "dosya": nihai.name,
            "sha256": ozet,
            "boyut": boyut,
            "olusturulma": timezone.now().isoformat(),
            "veritabani": secenek["dbname"],
            "sifreli": sifreli,
            "offsite": "",
        }
        offsite = getattr(settings, "BACKUP_OFFSITE_DIR", "") or ""
        if offsite:
            try:
                hedef_dizin = Path(offsite)
                hedef_dizin.mkdir(parents=True, exist_ok=True)
                shutil.copy2(nihai, hedef_dizin / nihai.name)
                bildirim["offsite"] = str(hedef_dizin / nihai.name)
            except OSError as exc:
                log.error("event=yedek_hata sebep=offsite")
                raise CommandError(f"Off-site kopya başarısız: {exc}") from exc
        else:
            log.warning(
                "event=yedek_offsite_yok",
                extra={"operation": "backup.al", "resource_id": "-"},
            )
        (dizin / f"{nihai.name}.manifest.json").write_text(
            json.dumps(bildirim, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._retention_temizle(dizin)
        log.info(
            "event=yedek_alindi dosya=%s boyut=%s sifreli=%s",
            nihai.name, boyut, sifreli,
            extra={"operation": "backup.al", "resource_id": "-"},
        )
        self.stdout.write(f"YEDEK: {nihai.name} ({boyut} bayt, sha256={ozet[:16]}…)")

    def _retention_temizle(self, dizin: Path) -> None:
        import time

        from django.conf import settings as _ayarlar

        gun = getattr(_ayarlar, "BACKUP_SAKLAMA_GUN", 30)
        esik = time.time() - gun * 86400
        adaylar = sorted(
            [p for p in dizin.glob("emlak_erp_*.sql*")
             if p.is_file() and not p.name.endswith(".manifest.json")],
            key=lambda p: p.stat().st_mtime,
        )
        # En güncel yedek her durumda korunur.
        korunacak = {adaylar[-1].name} if adaylar else set()
        for dosya in adaylar:
            if dosya.name in korunacak:
                continue
            if dosya.stat().st_mtime < esik:
                manifest = dizin / f"{dosya.name}.manifest.json"
                dosya.unlink(missing_ok=True)
                manifest.unlink(missing_ok=True)
                log.info(
                    "event=yedek_budama dosya=%s", dosya.name,
                    extra={"operation": "backup.retention", "resource_id": "-"},
                )
