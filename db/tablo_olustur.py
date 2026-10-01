"""Eksik tabloları Django şema oluşturucuyla açar (migration KULLANILMAZ).

Kullanım (proje kökünden):

    .venv\\Scripts\\python.exe db\\tablo_olustur.py construction.PozPlan

- Yalnızca DB'de **var olmayan** tabloları oluşturur (idempotent).
- Oluşturduktan sonra `db/schema.sql` pg_dump ile tazelenmeli ve
  `db/rls.sql` (tenant policy'leri) yeniden uygulanmalıdır.
"""

from __future__ import annotations

import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()  # noqa: E402

from django.apps import apps  # noqa: E402
from django.db import connection  # noqa: E402


def model_bul(etiket: str):
    """`app.Model` etiketini model sınıfına çevirir."""
    try:
        return apps.get_model(etiket)
    except LookupError as exc:  # pragma: no cover - kullanıcı hatası
        raise SystemExit(f"Model bulunamadı: {etiket} ({exc})")


def main(arguments: list[str]) -> int:
    if not arguments:
        print(__doc__)
        return 1

    mevcut = set(connection.introspection.table_names())
    olusturulan: list[str] = []
    atlanan: list[str] = []

    for etiket in arguments:
        model = model_bul(etiket)
        tablo = model._meta.db_table
        if tablo in mevcut:
            atlanan.append(tablo)
            continue
        with connection.schema_editor() as editor:
            editor.create_model(model)
        mevcut.add(tablo)
        olusturulan.append(tablo)

    for tablo in olusturulan:
        print(f"Oluşturuldu: {tablo}")
    for tablo in atlanan:
        print(f"Zaten mevcut (atlandı): {tablo}")
    if olusturulan:
        print(
            "\nSıradaki adımlar: db/rls.sql uygula (tenant policy) → "
            "db/schema.sql'i pg_dump ile tazele."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))