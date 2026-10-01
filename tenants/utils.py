"""Kiracı (Tenant) yardımcı fonksiyonları — PostgreSQL RLS (Row Level Security) desteği."""

import logging
from contextlib import contextmanager
from django.db import connection, OperationalError

logger = logging.getLogger(__name__)


@contextmanager
def tenant_baglam(tenant):
    """
    PostgreSQL RLS (Row Level Security) için kiracı bağlamını ayarlar.

    Management komutları, cron jobları, Celery görevleri veya arka plan işlemlerinde
    kiracı (tenant) izolasyonunu korumak için kullanılır.

    Kullanım:
        from tenants.utils import tenant_baglam

        # Kiracı modeli örneği ile
        with tenant_baglam(tenant_nesnesi):
            # Bu blokta RLS aktif — sadece ilgili kiracının verisi görünür
            queryset = Model.objects.all()

        # Kiracı ID (int/str) ile
        with tenant_baglam(123):
            pass

        # Kiracı bağlamı sıfırlanır (global görünüm)
        with tenant_baglam(None):
            pass

    Parametreler:
        tenant: Kiracı modeli örneği (id özelliği olmalı), kiracı ID (int/str) veya None.

    Not:
        - PostgreSQL'de `app.current_tenant_id` ayarı RLS policy'leri tarafından okunur.
        - `SET LOCAL` kullanıldığı için işlem (transaction) sınırında kalır.
        - Blok bittiğinde (hata olsa bile) bağlam otomatik sıfırlanır.
    """
    if tenant is None:
        tenant_id = ""
    else:
        # Kiracı modeli örneği ise id'sini al, zaten ID ise doğrudan kullan
        tenant_id = getattr(tenant, "id", tenant)

    # Kiracı ID'sini string'e çevir
    tenant_id_str = str(tenant_id) if tenant_id else ""

    try:
        with connection.cursor() as cursor:
            if tenant_id_str:
                # SET LOCAL — sadece mevcut işlem (transaction) içinde geçerli
                # RLS policy'leri bu değeri `current_setting('app.current_tenant_id')` ile okur
                cursor.execute(
                    "SET LOCAL app.current_tenant_id = %s",
                    [tenant_id_str],
                )
                logger.debug("Kiracı bağlamı ayarlandı: tenant_id=%s", tenant_id_str)
            else:
                # Kiracı None ise mevcut ayarı temizle (global görünüm)
                cursor.execute("SET LOCAL app.current_tenant_id = ''")
                logger.debug("Kiracı bağlamı temizlendi (global görünüm)")
    except OperationalError as exc:
        logger.error("Kiracı bağlamı ayarlanırken hata: %s", exc)
        raise

    try:
        yield
    finally:
        # Blok bittiğinde (başarılı veya hata) bağlamı temizle
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL app.current_tenant_id = ''")
                logger.debug("Kiracı bağlamı sıfırlandı")
        except OperationalError as exc:
            logger.warning("Kiracı bağlamı sıfırlanırken hata: %s", exc)


def tenant_id_al():
    """
    Mevcut veritabanı bağlantısından aktif kiracı ID'sini okur.

    Returns:
        str | None: Aktif kiracı ID'si veya None (global görünüm).
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW app.current_tenant_id")
            sonuc = cursor.fetchone()
            return sonuc[0] if sonuc and sonuc[0] else None
    except OperationalError:
        return None


def kiracı_kapsamlı_sorgu(queryset, tenant):
    """
    Verilen queryset'i kiracı kapsamına göre filtreler.

    Args:
        queryset: Django QuerySet (TenantAwareModel olmalı)
        tenant: Kiracı modeli örneği veya ID

    Returns:
        Filtrelenmiş QuerySet
    """
    if tenant is None:
        return queryset.none()

    tenant_id = getattr(tenant, "id", tenant)
    if tenant_id is None:
        return queryset.none()

    return queryset.filter(tenant_id=tenant_id)
