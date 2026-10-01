"""Small, dependency-free IFC quantity draft extractor.

This is intentionally conservative. It understands common STEP quantity
entities and otherwise records a deterministic metadata fallback rather than
pretending that geometry was parsed.
"""
from __future__ import annotations

import hashlib
import re
from decimal import Decimal, InvalidOperation

from .models import IFCImportJob, IFCQuantityDraft, Poz

_QUANTITY = re.compile(
    r"#(?P<id>\d+)\s*=\s*IFCQUANTITY(?P<kind>LENGTH|AREA|VOLUME|COUNT)"
    r"\s*\(\s*'(?P<name>[^']*)'.*?,\s*(?P<value>-?\d+(?:\.\d+)?)\s*\)",
    re.IGNORECASE,
)
_UNIT = {"LENGTH": "m", "AREA": "m²", "VOLUME": "m³", "COUNT": "adet"}


def _read(job: IFCImportJob) -> bytes:
    if not job.file:
        return b""
    job.file.open("rb")
    try:
        return job.file.read()
    finally:
        job.file.close()


def process_ifc_job(job: IFCImportJob) -> IFCImportJob:
    """Process one job synchronously, never changing active PozPlan records.

    FAZ 5: tamamlanmış işin tekrar işlenmesi reddedilir (duplicate draft yok).
    """
    from django.utils import timezone

    if job.status == IFCImportJob.Status.COMPLETED:
        from django.core.exceptions import ValidationError

        raise ValidationError("Tamamlanmış içe aktarım tekrar işlenemez.")
    job.status = IFCImportJob.Status.PROCESSING
    job.started_at = timezone.now()
    job.validation_errors = []
    job.save(update_fields=["status", "started_at", "validation_errors", "updated_at"])
    payload = _read(job)
    job.file_size = len(payload)
    job.checksum = hashlib.sha256(payload).hexdigest()
    try:
        text = payload.decode("utf-8-sig", errors="replace")
        if not payload:
            raise ValueError("IFC file is empty.")
        if not ("ISO-10303-21" in text[:500] or re.search(r"\bIFC[A-Z0-9_]+\s*\(", text[:20000], re.IGNORECASE)):
            raise ValueError("File does not contain an IFC STEP header.")
        matches = list(_QUANTITY.finditer(text))
        mode = "step-quantities" if matches else "fallback-metadata"
        if not matches:
            job.processing_message = (
                "Geometri ayrıştırılmadı; güvenli fallback kullanıldı. "
                "IFCQUANTITY* varlıkları bulunamadı."
            )
        pozlar = list(Poz.objects.filter(tenant_id=job.tenant_id, is_active=True))
        drafts = []
        for match in matches:
            name = match.group("name").strip() or f"IFC #{match.group('id')}"
            quantity = Decimal(match.group("value"))
            if quantity <= 0:
                status = IFCQuantityDraft.MappingStatus.INVALID
                message = "Miktar sıfırdan büyük olmalıdır."
                poz = None
            else:
                normalized = name.casefold()
                poz = next(
                    (p for p in pozlar if p.poz_no.casefold() == normalized),
                    next((p for p in pozlar if normalized in p.ad.casefold()), None),
                )
                status = IFCQuantityDraft.MappingStatus.MAPPED if poz else IFCQuantityDraft.MappingStatus.UNMAPPED
                message = "" if poz else "Aktif Poz ile eşleşme bulunamadı."
            drafts.append(IFCQuantityDraft(
                tenant_id=job.tenant_id, job=job, project=job.project, year=job.year,
                poz=poz, source_name=name, quantity=quantity, unit=_UNIT[match.group("kind").upper()],
                ifc_entity_type=f"IFCQUANTITY{match.group('kind').upper()}",
                mapping_status=status, validation_message=message,
                raw_data={"entity_id": int(match.group("id"))},
            ))
        IFCQuantityDraft.objects.bulk_create(drafts)
        job.status = IFCImportJob.Status.COMPLETED
        job.parser_mode = mode
        job.processing_message = job.processing_message or f"{len(drafts)} miktar taslağı üretildi."
    except (ValueError, InvalidOperation) as exc:
        job.status = IFCImportJob.Status.FAILED
        job.validation_errors = [str(exc)]
        job.processing_message = "Doğrulama başarısız."
    except Exception as exc:  # keep job diagnostics available to operators
        job.status = IFCImportJob.Status.FAILED
        job.validation_errors = [f"İşleme hatası: {exc}"]
        job.processing_message = "İşleme sırasında beklenmeyen hata oluştu."
    job.finished_at = timezone.now()
    job.save(update_fields=[
        "status", "parser_mode", "file_size", "checksum", "processing_message",
        "validation_errors", "finished_at", "updated_at",
    ])
    return job
