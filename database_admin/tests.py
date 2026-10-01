from django.db import connection
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

import os

from tenants.models import Tenant
from users.models import User, UserRole


class DatabaseAdminApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="Veri Firma", slug="veri-firma")
        import uuid
        unique = uuid.uuid4().hex[:8]
        self.user = User.objects.create_user(
            username=f"db-admin_{unique}",
            password="x",
            email=f"db-admin_{unique}@example.com",
            is_superuser=True,
            is_staff=True,
            role=UserRole.SUPER_ADMIN,
        )
        self.normal = User.objects.create_user(
            username=f"db-user_{unique}",
            password="x",
            email=f"db-user_{unique}@example.com",
            tenant=self.tenant,
            role=UserRole.KULLANICI,
        )

    def test_superuser_can_discover_tables(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/v1/database/overview/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("tenants_tenant", {table["name"] for table in response.data["tables"]})

    def test_normal_user_is_denied(self):
        self.client.force_authenticate(self.normal)
        response = self.client.get("/api/v1/database/overview/")
        self.assertEqual(response.status_code, 403)

    def test_row_update_allows_editable_field(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/v1/database/tables/tenants_tenant/rows/{self.tenant.pk}/",
            {"name": "Güncel Firma"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.name, "Güncel Firma")

    def test_row_update_rejects_tenant_change(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/v1/database/tables/tenants_tenant/rows/{self.tenant.pk}/",
            {"tenant_id": 999},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class ExportButunlukTests(TestCase):
    """FAZ 6E — streaming export içeriği (kolon/sıra/başlık/tipler) korunur."""

    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(name="İhracat Şirketi", slug="ihracat")
        import uuid
        unique = uuid.uuid4().hex[:8]
        self.user = User.objects.create_user(
            username=f"db-exp_{unique}", password="x",
            email=f"db-exp_{unique}@example.com",
            is_superuser=True, is_staff=True, role=UserRole.SUPER_ADMIN,
        )
        from cari.models import Cari

        Cari.objects.create(
            tenant=self.tenant, ad="Çağrı Ltd. Şti.", tip="tedarikci", tur="kurumsal",
        )
        Cari.objects.create(
            tenant=self.tenant, ad="Sade Ltd.", tip="musteri", tur="bireysel",
            telefon="05321234567",
        )

    def test_export_cari_icerik_butunlugu(self):
        from io import BytesIO

        from openpyxl import load_workbook

        self.client.force_authenticate(self.user)
        yanit = self.client.post(
            "/api/v1/database/excel/export/",
            {"tables": "cari_cari"},
            format="json",
        )
        self.assertEqual(yanit.status_code, 200)
        kitap = load_workbook(filename=BytesIO(b"".join(yanit.streaming_content)))
        self.assertIn("cari_cari", kitap.sheetnames)
        self.assertIn("__TabloEsleme", kitap.sheetnames)
        self.assertEqual(kitap["__TabloEsleme"].sheet_state, "hidden")
        sayfa = kitap["cari_cari"]
        basliklar = [hucre.value for hucre in sayfa[1]]
        self.assertIn("ad", basliklar)
        self.assertIn("tip", basliklar)
        satirlar = list(sayfa.iter_rows(min_row=2, values_only=True))
        adlar = {satir[basliklar.index("ad")] for satir in satirlar}
        self.assertIn("Çağrı Ltd. Şti.", adlar)
        self.assertIn("Sade Ltd.", adlar)
        # NULL/boş alan korunur.
        tipler = {satir[basliklar.index("tip")] for satir in satirlar}
        self.assertIn("tedarikci", tipler)


class YedekKomutTests(TransactionTestCase):
    """FAZ 6F-3 — db_yedekle: manifest, şifreleme, retention, hata kontrolü.

    NOT: pg_dump ayrı bağlantıdan okur; verinin dump'ta görünmesi için
    TransactionTestCase gerekir (TestCase transaction'ı dışa kapalıdır).
    """

    @classmethod
    def _fixture_teardown(cls):
        # PROTECT FK'li şemada TRUNCATE CASCADE'siz patlar (FAZ 6A deseni).
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' "
                "AND tablename NOT IN ('spatial_ref_sys', 'django_migrations')"
            )
            tables = [row[0] for row in cursor.fetchall()]
        if tables:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE %s CASCADE" % ", ".join(f'"{t}"' for t in tables))

    def setUp(self):
        import tempfile
        import uuid

        # Her test kendi tenant'ını açar (TransactionTestCase geri almaz).
        self.tenant = Tenant.objects.create(
            name="Yedek Firma", slug=f"yedek-{uuid.uuid4().hex[:8]}"
        )
        self.gecici = tempfile.TemporaryDirectory()
        self.addCleanup(self.gecici.cleanup)
        self.dizin = self.gecici.name
        from cryptography.fernet import Fernet

        self.anahtar = Fernet.generate_key().decode()

    def _yedekle(self, **ek):
        from django.core.management import call_command

        with self.settings(
            DB_BACKUP_DIR=self.dizin,
            BACKUP_ENCRYPTION_KEY=self.anahtar,
            BACKUP_OFFSITE_DIR="",
        ):
            call_command("db_yedekle", **ek)

    def _tek_yedek(self):
        import glob
        import os

        dosyalar = [
            p for p in glob.glob(os.path.join(self.dizin, "emlak_erp_*.sql*"))
            if not p.endswith(".manifest.json")
        ]
        self.assertEqual(len(dosyalar), 1)
        return dosyalar[0]

    def test_sifreli_yedek_manifest_bütünlüklü(self):
        import json
        import os

        self._yedekle()
        dosya = self._tek_yedek()
        self.assertTrue(dosya.endswith(".fernet"))
        with open(dosya + ".manifest.json", encoding="utf-8") as akim:
            bildirim = json.load(akim)
        self.assertTrue(bildirim["sifreli"])
        self.assertEqual(bildirim["dosya"], dosya.rsplit("\\", 1)[-1].rsplit("/", 1)[-1])
        from database_admin.management.commands.db_yedekle import b64_sha256
        from pathlib import Path

        ozet, _ = b64_sha256(Path(dosya))
        self.assertEqual(bildirim["sha256"], ozet)
        # Çözülen içerik gerçek veriyi taşır.
        from database_admin.management.commands.db_yedekle import fernet_coz as _coz

        hedef = os.path.join(self.dizin, "cozuldu.sql")
        _coz(Path(dosya), Path(hedef), self.anahtar)
        with open(hedef, encoding="utf-8") as akim:
            icerik = akim.read()
        self.assertIn(self.tenant.slug, icerik)

    def test_anahtarsiz_yedek_duz_metin_uyarir(self):
        import json
        from unittest import mock

        from django.core.management import call_command

        with self.settings(
            DB_BACKUP_DIR=self.dizin, BACKUP_ENCRYPTION_KEY="",
            BACKUP_OFFSITE_DIR="",
        ):
            with self.assertLogs("erp.backup", level="WARNING") as yakalanan:
                call_command("db_yedekle")
        dosya = self._tek_yedek()
        self.assertTrue(dosya.endswith(".sql"))
        with open(dosya + ".manifest.json", encoding="utf-8") as akim:
            self.assertFalse(json.load(akim)["sifreli"])
        self.assertTrue(
            any("yedek_sifresiz" in k.getMessage() for k in yakalanan.records)
        )

    def test_offsite_kopya_manifestte(self):
        import json
        import os

        offsite = os.path.join(self.dizin, "offsite")
        from django.core.management import call_command

        with self.settings(
            DB_BACKUP_DIR=self.dizin, BACKUP_ENCRYPTION_KEY=self.anahtar,
            BACKUP_OFFSITE_DIR=offsite,
        ):
            call_command("db_yedekle")
        dosya = self._tek_yedek()
        ad = dosya.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
        self.assertTrue(os.path.isfile(os.path.join(offsite, ad)))
        with open(dosya + ".manifest.json", encoding="utf-8") as akim:
            self.assertTrue(json.load(akim)["offsite"].endswith(ad))

    def test_retention_eskiyi_budar_yeniyi_korur(self):
        import os
        import time

        from django.core.management import call_command

        eski = os.path.join(self.dizin, "emlak_erp_20000101_000000.sql")
        with open(eski, "w") as akim:
            akim.write("-- eski")
        with open(eski + ".manifest.json", "w") as akim:
            akim.write("{}")
        eski_zaman = time.time() - 40 * 86400
        os.utime(eski, (eski_zaman, eski_zaman))
        os.utime(eski + ".manifest.json", (eski_zaman, eski_zaman))
        with self.settings(
            DB_BACKUP_DIR=self.dizin, BACKUP_ENCRYPTION_KEY="",
            BACKUP_OFFSITE_DIR="", BACKUP_SAKLAMA_GUN=30,
        ):
            call_command("db_yedekle")
        self.assertFalse(os.path.exists(eski))
        self.assertFalse(os.path.exists(eski + ".manifest.json"))
        self._tek_yedek()  # güncel yedek duruyor

    def test_arac_yoksa_command_error(self):
        from unittest import mock

        from django.core.management import CommandError, call_command

        with self.settings(DB_BACKUP_DIR=self.dizin):
            with mock.patch(
                "database_admin.api._tool_path",
                side_effect=RuntimeError("yok"),
            ):
                with self.assertRaises(CommandError):
                    call_command("db_yedekle")


class SistemKontrolTests(TestCase):
    """FAZ 6F-3 — sistem_kontrol: sağlıklı yol + smoke + hata yolları."""

    def setUp(self):
        import tempfile

        self.tenant = Tenant.objects.create(name="Kontrol A.Ş.", slug="kontrol-as")
        import uuid
        unique = uuid.uuid4().hex[:8]
        self.user = User.objects.create_user(
            username=f"kont_{unique}", password="x",
            email=f"kont_{unique}@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )
        self.gecici = tempfile.TemporaryDirectory()
        self.addCleanup(self.gecici.cleanup)

    def test_saglikli_kontrol_exit0(self):
        from django.core.management import call_command

        with self.settings(DB_BACKUP_DIR=self.gecici.name):
            call_command("sistem_kontrol")

    def test_smoke_kullanici_okuma(self):
        from django.core.management import call_command

        with self.settings(DB_BACKUP_DIR=self.gecici.name):
            call_command("sistem_kontrol", kullanici=self.user.username)

    def test_smoke_bilinmeyen_kullanici_hata(self):
        from django.core.management import CommandError, call_command

        with self.settings(DB_BACKUP_DIR=self.gecici.name):
            with self.assertRaises(CommandError):
                call_command("sistem_kontrol", kullanici="yok-boyle-biri")

    def test_smoke_pasif_kullanici_hata(self):
        from django.core.management import CommandError, call_command

        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        with self.settings(DB_BACKUP_DIR=self.gecici.name):
            with self.assertRaises(CommandError):
                call_command("sistem_kontrol", kullanici=self.user.username)


class RestoreKorumaTests(TestCase):
    """FAZ 6F-3 — db_restore çift kilidi (DB'ye dokunmadan)."""

    def test_yanlis_hedef_db_reddedilir(self):
        from django.core.management import CommandError, call_command

        with self.assertRaises(CommandError):
            call_command(
                "db_restore", dosya="x.sql", hedef_db_adi="baska-db",
                onay="EVET-EMINIM",
            )

    def test_onaysiz_restore_reddedilir(self):
        from django.conf import settings
        from django.core.management import CommandError, call_command

        with self.assertRaises(CommandError):
            call_command(
                "db_restore", dosya="x.sql",
                hedef_db_adi=connection.settings_dict.get("NAME"),
            )

    def test_bozuk_sha_reddedilir(self):
        import json
        import tempfile

        from django.conf import settings
        from django.core.management import CommandError, call_command
        from django.db import connection

        with tempfile.TemporaryDirectory() as dizin:
            dosya = os.path.join(dizin, "y.sql")
            with open(dosya, "w") as akim:
                akim.write("-- bos\n")
            with open(dosya + ".manifest.json", "w") as akim:
                json.dump({"sha256": "0" * 64}, akim)
            with self.assertRaises(CommandError):
                call_command(
                    "db_restore", dosya=dosya,
                    hedef_db_adi=connection.settings_dict.get("NAME"),
                    onay="EVET-EMINIM",
                )

    def test_surum_uyumlulugu_eski_sunucuda_ayiklar(self):
        import tempfile

        from database_admin.management.commands.db_restore import _surum_uyumlulugu
        from django.db import connection
        from pathlib import Path

        with connection.cursor() as imlec:
            imlec.execute("SHOW server_version_num")
            surum = int(imlec.fetchone()[0])
        with tempfile.TemporaryDirectory() as dizin:
            dosya = Path(dizin) / "a.sql"
            dosya.write_text("SET transaction_timeout = 0;\nSELECT 1;\n")
            sonuc = _surum_uyumlulugu(dosya)
            metin = sonuc.read_text()
            if surum < 170000:
                self.assertNotIn("transaction_timeout", metin)
                self.assertIn("SELECT 1", metin)
            else:
                self.assertEqual(sonuc, dosya)
