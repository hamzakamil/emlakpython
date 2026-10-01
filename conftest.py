"""Pytest konfigürasyonu — Test ortamı izolasyonu."""

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv


# Proje kök dizini
PROJE_KOK = Path(__file__).parent


def pytest_configure(config):
    """Pytest başlangıcında test ortam değişkenlerini yükle."""
    env_test_path = PROJE_KOK / ".env.test"
    if env_test_path.exists():
        # .env.test dosyasını yükle — mevcut .env'yi ezmez, sadece eksik olanları doldurur
        load_dotenv(env_test_path, override=True)
        print(f"\nTest ortami yuklendi: {env_test_path}")
    else:
        print(f"\nUyari: {env_test_path} bulunamadi, varsayilan ayarlar kullaniliyor.")


def pytest_sessionstart(session):
    """Test oturumu başında Django ayarlarını yap."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
    
    # Django setup
    import django
    django.setup()
    
    # Test veritabanı kontrolü
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), inet_server_port()")
            db_name, port = cursor.fetchone()
            print(f"Test veritabani: {db_name} (port: {port})")
    except Exception as e:
        print(f"Veritabani baglantisi kontrol edilemedi: {e}")


def pytest_sessionfinish(session, exitstatus):
    """Test oturumu sonunda temizlik."""
    # Test medya dosyalarını temizle
    import shutil
    test_media = Path("/tmp/test_media")
    if test_media.exists():
        shutil.rmtree(test_media, ignore_errors=True)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Tüm testlere veritabanı erişimi ver."""
    pass


@pytest.fixture
def test_tenant(db):
    """Testler için örnek kiracı oluştur."""
    import uuid
    from tenants.models import Tenant
    unique_suffix = uuid.uuid4().hex[:8]
    return Tenant.objects.create(
        name="Test Kiracı",
        slug=f"test-kiraci-{unique_suffix}",
        is_active=True,
    )


@pytest.fixture
def test_user(db, test_tenant):
    """Testler için örnek kullanıcı oluştur."""
    import uuid
    from users.models import User
    unique_suffix = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"testuser_{unique_suffix}",
        email=f"testuser_{unique_suffix}@example.com",
        password="testpass123",
        tenant=test_tenant,
        first_name="Test",
        last_name="Kullanıcı",
    )


@pytest.fixture
def authenticated_client(test_user):
    """Kimlik doğrulamalı test istemcisi."""
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=test_user)
    return client