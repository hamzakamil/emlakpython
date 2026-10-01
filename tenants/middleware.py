"""Tenant bağlamı middleware'i — RLS için DB oturum değişkenini ayarlar.

PostgreSQL Row Level Security (bkz. docs/rls-plani.md + db/rls.sql) tabloları
``app.current_tenant`` oturum değişkenine göre filtreler. Bu middleware her
istekte değişkeni doğru tenant'a ayarlar:

1. Session auth (Django admin vb.) → AuthenticationMiddleware'den sonra
   çalıştığı için ``request.user`` hazırdır (``tenant_id`` doğrudan alınır).
2. JWT (DRF API) → ``Authorization`` başlığındaki access token çözülür;
   ``user_id`` → ``tenant_id`` sorgulanır. Süper admin ``X-Tenant-Id``
   başlığıyla kapsam daralttıysa RLS değişkeni de o kapsama ayarlanır
   (tenants.api.etkin_tenant_id ile aynı kural).

Anonim veya geçersiz isteklerde değişken boş bırakılır; RLS etkinken bu bağlamda
tenant satırları görünmez (güvenli varsayılan).

Not: Değişken oturum düzeyinde (``set_config(..., false)``) yazılır ve **her
istek başında yeniden yazılır** — kalıcı bağlantılarda (``CONN_MAX_AGE > 0``)
önceki isteğin tenant'ı sızamaz. Test DB'sinde policy'ler yoktur (pytest
``--no-migrations`` şemayı modellerden üretir); middleware yalnız değişkeni
ayarlar, sorgu sonuçlarını etkilemez.
"""

from __future__ import annotations

import contextvars
import json
import logging
import time
import uuid

from django.db import connection
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# FAZ 6F-2: istek bağlamı (log filtresi + audit korelasyonu için).
korelasyon_id = contextvars.ContextVar("erp_correlation_id", default="-")
baglam_tenant = contextvars.ContextVar("erp_tenant_id", default="-")
baglam_kullanici = contextvars.ContextVar("erp_user_id", default="-")


class BaglamFiltresi(logging.Filter):
    """Tüm kayıtlara bağlam alanlarını varsayılanlarıyla enjekte eder."""

    def filter(self, record) -> bool:
        record.correlation_id = korelasyon_id.get()
        record.tenant_id = baglam_tenant.get()
        record.user_id = baglam_kullanici.get()
        record.operation = getattr(record, "operation", "-")
        record.resource_id = getattr(record, "resource_id", "-")
        record.request_path = getattr(record, "request_path", "-")
        return True


class IstekBaglamMiddleware:
    """FAZ 6F-2: korelasyon ID + erişim logu (metriklerin ham kaynağı).

    Her istek tek satır: method/path/status/süre (Bilgi); 5xx veya yavaş
    istekler Uyarı. Gövde/secret asla loglanmaz.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.conf import settings
        from django.db import connection as _baglanti

        cid = (
            request.META.get("HTTP_X_CORRELATION_ID") or uuid.uuid4().hex[:16]
        )
        request.correlation_id = cid
        s1 = korelasyon_id.set(cid)
        s2 = baglam_tenant.set("-")
        s3 = baglam_kullanici.set("-")
        baslangic = time.perf_counter()
        db_ms, db_sayisi = 0.0, 0

        def _olcer(execute, sql, params, many, context):
            nonlocal db_ms, db_sayisi
            t0 = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                db_ms += (time.perf_counter() - t0) * 1000
                db_sayisi += 1

        try:
            with _baglanti.execute_wrapper(_olcer):
                yanit = self.get_response(request)
            durum = getattr(yanit, "status_code", 0)
        finally:
            sure_ms = (time.perf_counter() - baslangic) * 1000
            esik = getattr(settings, "SLOW_REQUEST_MS", 1000)
            db_esik = getattr(settings, "SLOW_DB_MS", 500)
            erisim = logging.getLogger("erp.access")
            ekstra = {
                "request_path": getattr(request, "path", "-"),
                "operation": "http",
                "resource_id": "-",
            }
            ileti = (
                f"{getattr(request, 'method', '-')} "
                f"{getattr(request, 'path', '-')} {durum} {sure_ms:.0f}ms "
                f"db={db_ms:.0f}ms/{db_sayisi}q"
            )
            if (
                (isinstance(durum, int) and durum >= 500)
                or sure_ms > esik
                or db_ms > db_esik
            ):
                erisim.warning("event=yavas_veya_hata %s", ileti, extra=ekstra)
            else:
                erisim.info("%s", ileti, extra=ekstra)
            korelasyon_id.reset(s1)
            baglam_tenant.reset(s2)
            baglam_kullanici.reset(s3)
        try:
            yanit["X-Correlation-ID"] = cid
        except Exception:  # noqa: BLE001 — başlık yazılamazsa yanıta dokunma
            pass
        return yanit


# Kural 36: Audit Trail kapsamında izlenecek modeller (gerçek etiketler).
# FAZ 6F-2: url-parçası → model eşlemesi (if/elif yerine tek sözlük).
KAYNAK_MODEL = {
    "cariler": "cari.Cari",
    "cari-hareketler": "cari.CariHareket",
    "hareketler": "cari.CariHareket",
    "faturalar": "finance.Fatura",
    "finansal-islemler": "finance.FinansalIslem",
    "cek-senetler": "finance.CekSenet",
    "kasa-banka-hesaplari": "finance.KasaBankaHesabi",
    "vergi-profilleri": "finance.VergiProfili",
    "hesap-plani": "accounting.HesapPlani",
    "accounts": "accounting.HesapPlani",
    "chart-of-accounts": "accounting.HesapPlani",
    "fisler": "accounting.MuhasebeFisi",
    "muhasebe-fisi": "accounting.MuhasebeFisi",
    "vouchers": "accounting.MuhasebeFisi",
    "purchase-requests": "purchasing.SatinAlmaTalebi",
    "purchase-request-items": "purchasing.SatinAlmaTalebiKalemi",
    "purchase-orders": "purchasing.SatinAlmaSiparisi",
    "purchase-order-items": "purchasing.SatinAlmaSiparisiKalemi",
    "purchase-mal-kabul": "purchasing.MalKabul",
    "purchase-mal-kabul-items": "purchasing.MalKabulKalemi",
    "purchase-stok-hareketleri": "purchasing.StokHareketi",
    "purchase-depolar": "purchasing.Depo",
    "hakedisler": "construction.Hakedis",
    "subcontractor-billings": "construction.Hakedis",
    "projeler": "construction.Proje",
    "poz-planlari": "construction.PozPlan",
    "yaklasik-maliyetler": "construction.YaklasikMaliyet",
    "yaklasik-maliyet-satirlari": "construction.YaklasikMaliyetSatiri",
    "metrajlar": "construction.Metraj",
    "pozlar": "construction.Poz",
    "malzemeler": "construction.Malzeme",
    "tedarikciler": "construction.Tedarikci",
}
AUDIT_MODELS = set(KAYNAK_MODEL.values())


class TenantBaglamMiddleware:
    """İstek başına ``app.current_tenant`` GUC'sünü ayarlar (RLS zemini)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = self._tenant_id_coz(request)
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT set_config('app.current_tenant', %s, false)",
                    [str(tenant_id) if tenant_id else ""],
                )
        except Exception:  # noqa: BLE001 — bağlam ayarlanamazsa istek DB hatasıyla zaten düşer
            logger.warning("app.current_tenant ayarlanamadı.", exc_info=True)
        return self.get_response(request)

    def _tenant_id_coz(self, request) -> int | None:
        """İstekten tenant pk'sını çözer; çözülemezse None (boş bağlam)."""
        # 1) Session auth (Django admin) — user AuthenticationMiddleware'de hazır.
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            if getattr(user, "is_superuser", False):
                from tenants.api import etkin_tenant_id

                return etkin_tenant_id(request)
            return user.tenant_id

        # 2) JWT (DRF API) — başlıktaki access token'ı doğrulayarak çöz.
        header = request.META.get("HTTP_AUTHORIZATION", "")
        if not header.lower().startswith("bearer "):
            return None
        try:
            from rest_framework_simplejwt.tokens import AccessToken

            user_id = AccessToken(header[7:].strip()).payload.get("user_id")
        except Exception:  # noqa: BLE001 — geçersiz/süresi dolmuş token normal durum
            return None

        if not user_id:
            return None

        from users.models import User

        user = User.objects.filter(id=user_id).only("tenant_id", "is_superuser").first()
        if user is None:
            return None
        if user.is_superuser:
            # Sahte request benzeri nesnede etkin_tenant_id request.headers/META
            # arar; gerçek request burada mevcut — başlığı doğrudan uygula.
            kapsam = request.META.get("HTTP_X_TENANT_ID")
            try:
                return int(kapsam) if kapsam not in (None, "") else None
            except (TypeError, ValueError):
                return None
        return user.tenant_id


class TenantAuditMiddleware(MiddlewareMixin):
    """
    Kural 36: Audit Trail middleware'i (FAZ 6F-2).

    Belirli kaynaklar üzerinde yapılan CREATE/UPDATE/DELETE işlemlerini
    AuditLog modeline yazar: tenant + kullanıcı + zaman + action + model +
    nesne ID + değişen alanlar (önce/sonra) + korelasyon ID.

    İlke: best-effort — audit yazılamazsa ana işlem etkilenmez (finansal
    transaction sınırına audit yazımı dahil edilmez; bütünlük alan
    kısıtları + idempotency ile sağlanır).
    """

    def process_response(self, request, response):
        # Sadece mutating HTTP metodları için audit log
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return response

        # Kullanıcı doğrulaması
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return response

        # Tenant ID al
        tenant_id = getattr(user, "tenant_id", None)
        if not tenant_id:
            return response

        # Response başarılı mı?
        if response.status_code >= 400:
            return response

        try:
            from audit.loglama import fark_hesapla, guvenli_snapshot

            etiket, pk, onceki = None, None, {}
            if request.method in ("PUT", "PATCH", "DELETE"):
                sakli = getattr(request, "_audit_onceki", None)
                if not sakli:
                    return response
                etiket, pk, onceki = sakli
            else:  # POST: pk yanıttan (yoksa URL'den) çözülür
                etiket, nesne = self._nesne_coz(request.path_info, tenant_id)
                if not etiket or etiket not in AUDIT_MODELS:
                    return response
                pk = self._yanit_pk(response) or self._url_pk(request.path_info)
            if not etiket or etiket not in AUDIT_MODELS:
                return response

            from audit.models import AuditLog

            islem_turu = self._islem_turu_from_method(request.method)
            nesne, sonraki, fark = None, {}, {}
            if pk is not None:
                nesne = self._nesne_getir(etiket, pk, tenant_id)
            if nesne is not None:
                sonraki = guvenli_snapshot(nesne)
                fark = fark_hesapla(onceki, sonraki) if onceki else sonraki
            if nesne is None and not fark and not sonraki:
                return response
            if islem_turu == "UPDATE":
                eski, yeni = fark, fark
            else:
                eski, yeni = (onceki or {}), (sonraki or {})

            AuditLog.log_change(
                kullanıcı=user,
                islem_türü=islem_turu,
                nesne=nesne,
                eski=eski,
                yeni=yeni,
                sebep=f"{request.method} {request.path_info}"[:255],
                ip_adresi=self._client_ip(request),
                oturum_kişi=request.META.get("HTTP_USER_AGENT", "")[:100],
                correlation_id=getattr(request, "correlation_id", None),
            )
        except Exception:  # noqa: BLE001 — audit log hatası ana işlemi bozmamalı
            logger.exception("Audit log kaydedilemedi.")

        return response

    def _nesne_coz(self, path: str, tenant_id: int):
        """URL'den (etiket, tenant-kapsamlı nesne) döndürür."""
        etiket = self._model_from_path(path)
        if not etiket:
            return None, None
        pk = self._url_pk(path)
        if pk is None:
            return etiket, None
        return etiket, self._nesne_getir(etiket, pk, tenant_id)

    def _nesne_getir(self, etiket: str, pk: int, tenant_id: int):
        from django.apps import apps
        from django.core.exceptions import FieldError

        try:
            model = apps.get_model(etiket)
        except (LookupError, ValueError):
            return None
        try:
            return model.objects.filter(pk=pk, tenant_id=tenant_id).first()
        except FieldError:
            try:
                return model.objects.filter(pk=pk).first()
            except Exception:  # noqa: BLE001
                return None
        except Exception:  # noqa: BLE001
            return None

    def _model_from_path(self, path: str) -> str | None:
        """URL parçasından model etiketi (en uzun eşleşme öncelikli)."""
        segs = [s for s in (path or "").strip("/").lower().split("/") if s]
        for seg in segs:
            if seg in KAYNAK_MODEL:
                return KAYNAK_MODEL[seg]
        return None

    def _url_pk(self, path: str) -> int | None:
        for seg in (path or "").strip("/").split("/"):
            if seg.isdigit():
                return int(seg)
        return None

    def _yanit_pk(self, response) -> int | None:
        try:
            veri = getattr(response, "data", None)
            if isinstance(veri, dict):
                pk = veri.get("id")
                return int(pk) if pk is not None else None
        except (TypeError, ValueError):
            pass
        return None

    def _islem_turu_from_method(self, method: str) -> str:
        """HTTP metodundan işlem türünü çıkar."""
        mapping = {
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE",
        }
        return mapping.get(method, "UPDATE")

    def _client_ip(self, request) -> str | None:
        """İstemci IP adresini al."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

