from __future__ import annotations

import os
import shutil
import subprocess
import hashlib
import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

from django.conf import settings
from django.db import connection, transaction
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response


logger = logging.getLogger(__name__)

class IsSuperUser(BasePermission):
    message = "Bu alan yalnızca süper admin kullanıcılarına açıktır."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.is_superuser)


READ_ONLY_FIELDS = {
    "id", "tenant_id", "created_at", "updated_at", "password", "last_login",
    "date_joined", "cari_hareket_id", "muhasebe_fisi_id", "onaylayan_id",
    "onay_tarihi", "created_by_id",
}
HIDDEN_FIELDS = {"password"}
MAX_PAGE_SIZE = 100
EXCEL_MAX_ROWS = 10000


def _backup_dir() -> Path:
    directory = Path(getattr(settings, "DB_BACKUP_DIR", settings.BASE_DIR / "backups"))
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _database_options() -> dict[str, str]:
    db = connection.settings_dict
    return {
        "dbname": str(db.get("NAME", "")),
        "user": str(db.get("USER", "")),
        "host": str(db.get("HOST", "localhost")),
        "port": str(db.get("PORT", "5432")),
        "password": str(db.get("PASSWORD", "")),
    }


def _tool_path(setting_name: str, executable: str) -> str:
    configured = getattr(settings, setting_name, "")
    if configured and Path(configured).exists():
        return str(configured)
    found = shutil.which(executable)
    if found:
        return found
    common = Path("C:/Program Files/PostgreSQL")
    if common.exists():
        matches = sorted(common.glob(f"*/bin/{executable}.exe"), reverse=True)
        if matches:
            return str(matches[0])
    raise RuntimeError(f"{executable} bulunamadı. {setting_name} ayarını tanımlayın.")


def _run_db_tool(command: list[str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    options = _database_options()
    environment = os.environ.copy()
    environment["PGPASSWORD"] = options.pop("password")
    environment["PGCONNECT_TIMEOUT"] = "10"
    return subprocess.run(
        command,
        env=environment,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _db_args() -> list[str]:
    options = _database_options()
    return [
        "--dbname", options["dbname"], "--username", options["user"],
        "--host", options["host"], "--port", options["port"],
    ]


def _safe_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return "<binary>"
    return value


def _table_names() -> set[str]:
    with connection.cursor() as cursor:
        tables = connection.introspection.get_table_list(cursor)
    return {
        item.name for item in tables
        if item.type == "t" and not item.name.startswith("pg_")
    }


def _table_info(table_name: str) -> tuple[str, list[Any], str | None]:
    if table_name not in _table_names():
        raise Http404("Tablo bulunamadı.")
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
        constraints = connection.introspection.get_constraints(cursor, table_name)
    primary_key = next(
        (
            data.get("columns", [None])[0]
            for data in constraints.values()
            if data.get("primary_key") and data.get("columns")
        ),
        None,
    )
    return table_name, description, primary_key


def _column_payload(column: Any, primary_key: str | None) -> dict[str, Any]:
    name = column.name
    return {
        "name": name,
        "type": str(column.type_code),
        "internal_size": column.internal_size,
        "null_ok": column.null_ok,
        "primary_key": name == primary_key,
        "editable": name not in READ_ONLY_FIELDS and name != primary_key,
        "sensitive": name in HIDDEN_FIELDS,
    }


def _table_payload(table_name: str, include_count: bool = True) -> dict[str, Any]:
    _, description, primary_key = _table_info(table_name)
    count = None
    if include_count:
        quoted = connection.ops.quote_name(table_name)
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {quoted}")
            count = cursor.fetchone()[0]
    return {
        "name": table_name,
        "label": table_name.replace("_", " ").title(),
        "row_count": count,
        "primary_key": primary_key,
        "columns": [_column_payload(column, primary_key) for column in description],
    }


def _excel_columns(table_name: str) -> list[Any]:
    _, description, primary_key = _table_info(table_name)
    return [
        column for column in description
        if column.name not in READ_ONLY_FIELDS
        and column.name != primary_key
        and column.name not in HIDDEN_FIELDS
    ]


def _selected_tables(raw: Any) -> list[str]:
    if isinstance(raw, str):
        raw = [item.strip() for item in raw.split(",") if item.strip()]
    if not isinstance(raw, list) or not raw:
        raise ValueError("En az bir tablo seçilmelidir.")
    available = _table_names()
    selected = []
    for table_name in raw:
        if not isinstance(table_name, str) or table_name not in available:
            raise ValueError(f"Geçersiz tablo: {table_name}")
        if table_name not in selected:
            selected.append(table_name)
    return selected


def _selected_fields(raw: Any, table_names: list[str]) -> dict[str, list[str]]:
    selected_fields: dict[str, list[str]] = {}
    raw = raw if isinstance(raw, dict) else {}
    for table_name in table_names:
        available = [column.name for column in _excel_columns(table_name)]
        requested = raw.get(table_name, available)
        if not isinstance(requested, list) or not requested:
            raise ValueError(f"{table_name}: En az bir alan seçilmelidir.")
        invalid = [field for field in requested if field not in available]
        if invalid:
            raise ValueError(f"{table_name}: Geçersiz alanlar: {', '.join(invalid)}")
        selected_fields[table_name] = list(dict.fromkeys(requested))
    return selected_fields


def _excel_workbook(table_names: list[str], selected_fields: dict[str, list[str]]) -> Workbook:
    workbook = Workbook()
    instructions = workbook.active
    instructions.title = "Talimatlar"
    instructions.append(["Emlak ERP Excel Veri Şablonu"])
    instructions.append(["Bu dosyada yalnız seçtiğiniz tabloların sayfaları bulunur."])
    instructions.append(["İd, tenant, parola ve sistem tarih alanları otomatik yönetilir; bu alanları değiştirmeyin."])
    instructions.append(["İlişkili alanlarda ilgili kaydın id değerini kullanın. Boş hücre NULL olarak değerlendirilir."])
    instructions.append(["Yükleme sırasında tüm sayfalar tek transaction içinde işlenir; hata olursa hiçbir kayıt yazılmaz."])
    instructions["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    instructions["A1"].fill = PatternFill("solid", fgColor="0F6973")
    instructions.column_dimensions["A"].width = 120
    mapping = workbook.create_sheet(title="__TabloEsleme")
    mapping.append(["sayfa", "tablo", "alanlar"])
    mapping.sheet_state = "hidden"
    for table_name in table_names:
        sheet_title = table_name if len(table_name) <= 31 else f"{table_name[:25]}_{hashlib.sha1(table_name.encode()).hexdigest()[:5]}"
        mapping.append([sheet_title, table_name, ",".join(selected_fields[table_name])])
        sheet = workbook.create_sheet(title=sheet_title)
        columns = [column for column in _excel_columns(table_name) if column.name in selected_fields[table_name]]
        headers = [column.name for column in columns]
        sheet.append(headers)
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="0F6973")
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = f"A1:{chr(64 + min(len(headers), 26))}1" if headers else "A1"
        for index, column in enumerate(headers, start=1):
            sheet.column_dimensions[chr(64 + index) if index <= 26 else "A"].width = max(14, min(32, len(column) + 4))
        sheet.append([None] * len(headers))
    return workbook


def _workbook_response(workbook: Workbook, filename: str) -> FileResponse:
    from io import BytesIO

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return FileResponse(
        stream,
        as_attachment=True,
        filename=filename,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# FAZ 6E — streaming export sabitleri/yardımcıları.
EXCEL_EXPORT_CHUNK = 5000


def _write_only_header(sheet: Any, headers: list[str]) -> None:
    """Write-only sayfaya şablonla aynı stilli başlık satırı yazar."""
    from openpyxl.cell import WriteOnlyCell

    hucreler = []
    for baslik in headers:
        hucre = WriteOnlyCell(sheet, value=baslik)
        hucre.font = Font(bold=True, color="FFFFFF")
        hucre.fill = PatternFill("solid", fgColor="0F6973")
        hucreler.append(hucre)
    sheet.append(hucreler)


def _excel_workbook_stream(
    table_names: list[str], selected_fields: dict[str, list[str]]
) -> Any:
    """Export için write-only çalışma kitabı (şablonla aynı sayfa/başlık/stil).

    İçerik (sayfalar, kolonlar, sıra, başlıklar) `_excel_workbook` ile birebir
    aynıdır; yalnızca hücre yazım modu farklıdır (bellek sabitlenir).
    """
    from openpyxl import Workbook as _Workbook

    workbook = _Workbook(write_only=True)
    talimat = workbook.create_sheet(title="Talimatlar")
    for satir in (
        ["Emlak ERP Excel Veri Şablonu"],
        ["Bu dosyada yalnız seçtiğiniz tabloların sayfaları bulunur."],
        ["İd, tenant, parola ve sistem tarih alanları otomatik yönetilir; bu alanları değiştirmeyin."],
        ["İlişkili alanlarda ilgili kaydın id değerini kullanın. Boş hücre NULL olarak değerlendirilir."],
        ["Yükleme sırasında tüm sayfalar tek transaction içinde işlenir; hata olursa hiçbir kayıt yazılmaz."],
    ):
        talimat.append(satir)
    talimat.column_dimensions["A"].width = 120
    esleme = workbook.create_sheet(title="__TabloEsleme")
    esleme.sheet_state = "hidden"
    esleme.append(["sayfa", "tablo", "alanlar"])
    for table_name in table_names:
        sheet_title = table_name if len(table_name) <= 31 else f"{table_name[:25]}_{hashlib.sha1(table_name.encode()).hexdigest()[:5]}"
        esleme.append([sheet_title, table_name, ",".join(selected_fields[table_name])])
        sheet = workbook.create_sheet(title=sheet_title)
        headers = selected_fields[table_name]
        _write_only_header(sheet, headers)
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = f"A1:{chr(64 + min(len(headers), 26))}1" if headers else "A1"
        for index, column in enumerate(headers, start=1):
            sheet.column_dimensions[chr(64 + index) if index <= 26 else "A"].width = max(14, min(32, len(column) + 4))
    return workbook


def _stream_table_rows(table_name: str, columns: list[str], sheet: Any) -> int:
    """Tablo satırlarını server-side cursor ile parça parça sayfaya yazar.

    Tüm tabloyu RAM'e almaz; dönen değer yazılan satır sayısıdır.
    """
    quoted_table = connection.ops.quote_name(table_name)
    quoted_columns = ", ".join(connection.ops.quote_name(name) for name in columns)
    sayi = 0
    # Server-side cursor transaction ister; export salt-okunur olduğundan güvenlidir.
    with transaction.atomic():
        ham = connection.connection
        with ham.cursor(name=f"excel_export_{table_name[:40]}") as imlec:
            imlec.itersize = EXCEL_EXPORT_CHUNK
            imlec.execute(f"SELECT {quoted_columns} FROM {quoted_table}")
            for satir in imlec:
                sheet.append([_safe_value(deger) for deger in satir])
                sayi += 1
    return sayi


@api_view(["GET"])
@permission_classes([IsSuperUser])
def overview(request):
    try:
        tables = sorted(_table_names())
        return Response({
            "database": connection.settings_dict.get("NAME"),
            "engine": connection.settings_dict.get("ENGINE"),
            "table_count": len(tables),
            "tables": [_table_payload(name) for name in tables],
            "backup_count": len(list(_backup_dir().glob("*.sql"))),
        })
    except Exception:
        logger.exception("Veritabanı genel görünümü oluşturulamadı.")
        return Response(
            {"detail": "Veritabanı şeması okunamadı. Backend günlüklerini kontrol edin."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["POST"])
@permission_classes([IsSuperUser])
@parser_classes([JSONParser])
def excel_template(request):
    try:
        table_names = _selected_tables(request.data.get("tables"))
        selected_fields = _selected_fields(request.data.get("fields"), table_names)
        workbook = _excel_workbook(table_names, selected_fields)
        stamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        return _workbook_response(workbook, f"emlak_erp_veri_sablonu_{stamp}.xlsx")
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=400)


@api_view(["POST"])
@permission_classes([IsSuperUser])
@parser_classes([JSONParser])
def excel_export(request):
    import time as _zaman

    baslangic = _zaman.perf_counter()
    try:
        table_names = _selected_tables(request.data.get("tables"))
        selected_fields = _selected_fields(request.data.get("fields"), table_names)
        workbook = _excel_workbook_stream(table_names, selected_fields)
        toplam_satir = 0
        # Write-only sayfalar okunamaz; sayfa adları seçimden bilinir.
        for table_name in table_names:
            columns = selected_fields[table_name]
            sheet_title = table_name if len(table_name) <= 31 else f"{table_name[:25]}_{hashlib.sha1(table_name.encode()).hexdigest()[:5]}"
            sheet = workbook[sheet_title]
            toplam_satir += _stream_table_rows(table_name, columns, sheet)
        stamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        yanit = _workbook_response(workbook, f"emlak_erp_veri_export_{stamp}.xlsx")
        sure_ms = (_zaman.perf_counter() - baslangic) * 1000
        logger.info(
            "event=export tablolar=%s satir=%s sure_ms=%.0f",
            ",".join(table_names), toplam_satir, sure_ms,
            extra={"operation": "export.excel", "resource_id": "-"},
        )
        return yanit
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=400)
    except Exception as exc:
        logger.exception("event=export_hata tablolar=%s", request.data.get("tables"))
        return Response({"detail": f"Excel dışa aktarma başarısız: {str(exc)[:500]}"}, status=400)


def _excel_cell_value(value: Any) -> Any:
    if value == "":
        return None
    return value


@api_view(["POST"])
@permission_classes([IsSuperUser])
@parser_classes([MultiPartParser])
def excel_import(request):
    uploaded = request.FILES.get("workbook")
    if not uploaded or not uploaded.name.lower().endswith((".xlsx", ".xlsm")):
        return Response({"detail": "Yalnızca .xlsx veya .xlsm dosyası yüklenebilir."}, status=400)
    if uploaded.size > 100 * 1024 * 1024:
        return Response({"detail": "Excel dosyası 100 MB sınırını aşamaz."}, status=400)
    try:
        target_tenant = int(request.data.get("tenant_id")) if request.data.get("tenant_id") else None
    except (TypeError, ValueError):
        return Response({"detail": "Tenant seçimi sayısal olmalıdır."}, status=400)
    try:
        from io import BytesIO

        workbook = load_workbook(filename=BytesIO(uploaded.read()), read_only=True, data_only=True)
        mapping = {}
        field_mapping: dict[str, list[str]] = {}
        if "__TabloEsleme" in workbook.sheetnames:
            for row in workbook["__TabloEsleme"].iter_rows(min_row=2, values_only=True):
                if row[0] and row[1]:
                    mapping[str(row[0])] = str(row[1])
                    if row[2]:
                        field_mapping[str(row[0])] = [field.strip() for field in str(row[2]).split(",") if field.strip()]
        sheet_names = [name for name in workbook.sheetnames if name not in {"Talimatlar", "__TabloEsleme"}]
        sheet_tables = [(name, mapping.get(name, name)) for name in sheet_names]
        if not sheet_names:
            return Response({"detail": "Excel dosyasında veri sayfası bulunamadı."}, status=400)
        available = _table_names()
        unknown = [table_name for _, table_name in sheet_tables if table_name not in available]
        if unknown:
            return Response({"detail": f"Bilinmeyen tablo sayfaları: {', '.join(unknown)}"}, status=400)
        tenant_tables = [table_name for _, table_name in sheet_tables if "tenant_id" in {column.name for column in _table_info(table_name)[1]}]
        if tenant_tables and not target_tenant:
            return Response({"detail": "Tenant alanı olan tablolar için hedef tenant seçilmelidir."}, status=400)
        tenant_ids = set()
        if target_tenant:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM tenants_tenant WHERE id = %s", [target_tenant])
                if cursor.fetchone() is None:
                    return Response({"detail": "Hedef tenant bulunamadı."}, status=400)
            tenant_ids.add(target_tenant)

        report = {"dry_run": request.data.get("dry_run") in ("1", "true", "True"), "sheets": [], "total_rows": 0, "inserted": 0}
        with transaction.atomic():
            for sheet_name, table_name in sheet_tables:
                sheet = workbook[sheet_name]
                rows = sheet.iter_rows(values_only=True)
                headers = next(rows, None)
                expected = field_mapping.get(sheet_name, [column.name for column in _excel_columns(table_name)])
                allowed_fields = {column.name for column in _excel_columns(table_name)}
                if not expected or any(field not in allowed_fields for field in expected):
                    raise ValueError(f"{table_name}: Şablondaki alan eşlemesi geçersiz.")
                actual = [str(value).strip() if value is not None else "" for value in (headers or [])]
                if actual != expected:
                    raise ValueError(f"{table_name}: Kolon başlıkları şablonla aynı olmalıdır.")
                table_columns = [column.name for column in _table_info(table_name)[1]]
                insert_columns = list(expected)
                if "tenant_id" in table_columns and "tenant_id" not in insert_columns:
                    insert_columns.append("tenant_id")
                system_values: dict[str, Any] = {}
                if "created_at" in table_columns:
                    insert_columns.append("created_at")
                    system_values["created_at"] = timezone.now()
                if "updated_at" in table_columns:
                    insert_columns.append("updated_at")
                    system_values["updated_at"] = timezone.now()
                if "created_by_id" in table_columns:
                    insert_columns.append("created_by_id")
                    system_values["created_by_id"] = request.user.id
                quoted_table = connection.ops.quote_name(table_name)
                quoted_columns = ", ".join(connection.ops.quote_name(column) for column in insert_columns)
                placeholders = ", ".join(["%s"] * len(insert_columns))
                sheet_report = {"table": sheet_name, "rows": 0, "inserted": 0}
                for excel_row_number, values in enumerate(rows, start=2):
                    if excel_row_number > EXCEL_MAX_ROWS + 1:
                        raise ValueError(f"{table_name}: En fazla {EXCEL_MAX_ROWS} veri satırı yüklenebilir.")
                    if not any(value not in (None, "") for value in values):
                        continue
                    values = list(values[:len(expected)])
                    if len(values) < len(expected):
                        values.extend([None] * (len(expected) - len(values)))
                    params = [_excel_cell_value(value) for value in values]
                    if "tenant_id" in insert_columns:
                        params.append(target_tenant)
                    params.extend(system_values[column] for column in insert_columns if column in system_values)
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(
                                f"INSERT INTO {quoted_table} ({quoted_columns}) VALUES ({placeholders})",
                                params,
                            )
                    except Exception as exc:
                        raise ValueError(f"{table_name} satır {excel_row_number}: {str(exc)[:300]}") from exc
                    sheet_report["rows"] += 1
                    sheet_report["inserted"] += 1
                sheet_report["table"] = table_name
                report["sheets"].append(sheet_report)
            report["total_rows"] = sum(item["rows"] for item in report["sheets"])
            report["inserted"] = sum(item["inserted"] for item in report["sheets"])
            if report["dry_run"]:
                transaction.set_rollback(True)
        workbook.close()
        return Response(report)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=400)
    except Exception as exc:
        return Response({"detail": f"Excel içe aktarma başarısız: {str(exc)[:500]}"}, status=400)


@api_view(["GET"])
@permission_classes([IsSuperUser])
def table_rows(request, table_name: str):
    try:
        table_name, description, primary_key = _table_info(table_name)
        try:
            page = max(1, int(request.query_params.get("page", "1")))
            page_size = min(MAX_PAGE_SIZE, max(1, int(request.query_params.get("page_size", "25"))))
        except ValueError:
            return Response({"detail": "Sayfa parametreleri sayısal olmalıdır."}, status=400)
        search = request.query_params.get("search", "").strip()
        columns = [column.name for column in description]
        quoted_table = connection.ops.quote_name(table_name)
        quoted_columns = ", ".join(connection.ops.quote_name(name) for name in columns)
        where = ""
        params: list[Any] = []
        if search:
            searchable = [name for name in columns if name not in HIDDEN_FIELDS]
            if searchable:
                where = " WHERE " + " OR ".join(
                    f"CAST({connection.ops.quote_name(name)} AS text) ILIKE %s" for name in searchable
                )
                params.extend([f"%{search}%"] * len(searchable))
        order = connection.ops.quote_name(primary_key or columns[0])
        offset = (page - 1) * page_size
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {quoted_table}{where}", params)
            total = cursor.fetchone()[0]
            cursor.execute(
                f"SELECT {quoted_columns} FROM {quoted_table}{where} ORDER BY {order} DESC LIMIT %s OFFSET %s",
                [*params, page_size, offset],
            )
            rows = cursor.fetchall()
        hidden_indexes = {index for index, column in enumerate(columns) if column in HIDDEN_FIELDS}
        payload_rows = [
            {
                column: ("••••••••" if index in hidden_indexes else _safe_value(value))
                for index, (column, value) in enumerate(zip(columns, row))
            }
            for row in rows
        ]
        return Response({
            "table": _table_payload(table_name, include_count=False),
            "columns": [_column_payload(column, primary_key) for column in description],
            "rows": payload_rows,
            "count": total,
            "page": page,
            "page_size": page_size,
        })
    except Http404:
        raise
    except Exception:
        logger.exception("Tablo satırları okunamadı: %s", table_name)
        return Response(
            {"detail": f"{table_name} tablosundaki kayıtlar okunamadı."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["PATCH"])
@permission_classes([IsSuperUser])
@parser_classes([JSONParser])
def update_row(request, table_name: str, row_id: int):
    table_name, description, primary_key = _table_info(table_name)
    if not primary_key:
        return Response({"detail": "Birincil anahtarı olmayan tablo düzenlenemez."}, status=400)
    allowed = {column.name for column in description if column.name not in READ_ONLY_FIELDS and column.name != primary_key}
    changes = {key: value for key, value in request.data.items() if key in allowed}
    if not changes:
        return Response({"detail": "Düzenlenebilir alan gönderilmedi."}, status=400)
    unknown = set(request.data) - allowed
    if unknown:
        return Response({"detail": f"Düzenlenemeyen alanlar: {', '.join(sorted(unknown))}"}, status=400)
    assignments = ", ".join(f"{connection.ops.quote_name(key)} = %s" for key in changes)
    quoted_table = connection.ops.quote_name(table_name)
    quoted_pk = connection.ops.quote_name(primary_key)
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {quoted_table} SET {assignments} WHERE {quoted_pk} = %s",
            [*changes.values(), row_id],
        )
        if cursor.rowcount != 1:
            raise Http404("Kayıt bulunamadı.")
    return Response({"success": True, "message": "Kayıt güncellendi."})


@api_view(["GET"])
@permission_classes([IsSuperUser])
def backups(request):
    items = []
    for path in sorted(_backup_dir().glob("*.sql"), reverse=True):
        stat = path.stat()
        items.append({"name": path.name, "size": stat.st_size, "created_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat()})
    return Response(items)


@api_view(["POST"])
@permission_classes([IsSuperUser])
def create_backup(request):
    try:
        pg_dump = _tool_path("PG_DUMP_PATH", "pg_dump")
        filename = f"emlak_erp_{timezone.now().strftime('%Y%m%d_%H%M%S')}.sql"
        target = _backup_dir() / filename
        result = _run_db_tool([
            pg_dump, *_db_args(), "--format=plain", "--clean", "--if-exists",
            "--no-owner", "--no-privileges", "--file", str(target),
        ])
        if result.returncode != 0:
            target.unlink(missing_ok=True)
            return Response({"detail": result.stderr[-2000:]}, status=500)
        return Response({"name": filename, "size": target.stat().st_size}, status=status.HTTP_201_CREATED)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return Response({"detail": str(exc)}, status=500)


@api_view(["GET"])
@permission_classes([IsSuperUser])
def download_backup(request, filename: str):
    path = (_backup_dir() / filename).resolve()
    if path.parent != _backup_dir().resolve() or path.suffix != ".sql" or not path.exists():
        raise Http404("Yedek bulunamadı.")
    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name, content_type="application/sql")


@api_view(["POST"])
@permission_classes([IsSuperUser])
@parser_classes([MultiPartParser])
def restore_backup(request):
    if request.data.get("confirmation") != "RESTORE DATABASE":
        return Response({"detail": "Geri yükleme için RESTORE DATABASE onayı zorunludur."}, status=400)
    uploaded = request.FILES.get("backup")
    if not uploaded or not uploaded.name.lower().endswith(".sql"):
        return Response({"detail": "Yalnızca .sql yedek dosyası yüklenebilir."}, status=400)
    if uploaded.size > 500 * 1024 * 1024:
        return Response({"detail": "Yedek dosyası 500 MB sınırını aşamaz."}, status=400)
    try:
        pg_dump = _tool_path("PG_DUMP_PATH", "pg_dump")
        psql = _tool_path("PSQL_PATH", "psql")
        safety_name = f"pre_restore_{timezone.now().strftime('%Y%m%d_%H%M%S')}.sql"
        safety_path = _backup_dir() / safety_name
        backup_result = _run_db_tool([
            pg_dump, *_db_args(), "--format=plain", "--clean", "--if-exists",
            "--no-owner", "--no-privileges", "--file", str(safety_path),
        ])
        if backup_result.returncode != 0:
            return Response({"detail": "Geri dönüş öncesi güvenlik yedeği alınamadı."}, status=500)
        uploaded_path = _backup_dir() / f"restore_{timezone.now().strftime('%Y%m%d_%H%M%S')}.sql"
        with uploaded_path.open("wb") as destination:
            for chunk in uploaded.chunks():
                destination.write(chunk)
        result = _run_db_tool([psql, *_db_args(), "--single-transaction", "--file", str(uploaded_path)], timeout=600)
        uploaded_path.unlink(missing_ok=True)
        if result.returncode != 0:
            return Response({"detail": result.stderr[-3000:], "safety_backup": safety_name}, status=500)
        return Response({"message": "Veritabanı geri yüklendi.", "safety_backup": safety_name})
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return Response({"detail": str(exc)}, status=500)
