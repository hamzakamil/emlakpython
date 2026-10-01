"""İnşaat servisleri.

``services.py`` Paket 1/2'nin mevcut servislerini korur; bu paket de geriye
dönük olarak aynı isimleri dışa aktarırken yeni servisleri alt modüllerde tutar.
"""
import importlib.util
from pathlib import Path

_legacy_path = Path(__file__).parents[1] / "services.py"
_spec = importlib.util.spec_from_file_location("construction._legacy_services", _legacy_path)
_legacy = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_legacy)
for _name in dir(_legacy):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_legacy, _name)
