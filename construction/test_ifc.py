from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User, UserRole

from .models import IFCImportJob, IFCQuantityDraft, Poz, PozGrubu, Proje


class IFCImportApiTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="A", slug="a")
        self.other = Tenant.objects.create(name="B", slug="b")
        self.user = User.objects.create_user(
            username="ifc-a", password="test-pass-123", tenant=self.tenant,
            role=UserRole.MALIYET_MUHENDISI, email="ifc-a@example.com",
        )
        self.other_user = User.objects.create_user(
            username="ifc-b", password="test-pass-123", tenant=self.other,
            role=UserRole.MALIYET_MUHENDISI, email="ifc-b@example.com",
        )
        self.project = Proje.objects.create(tenant=self.tenant, proje_kodu="P-A", ad="A")
        self.other_project = Proje.objects.create(tenant=self.other, proje_kodu="P-B", ad="B")
        group = PozGrubu.objects.create(tenant=self.tenant, kod="BET", ad="Beton")
        self.poz = Poz.objects.create(
            tenant=self.tenant, poz_no="P-1001", ad="Beton", birim="m3", grup=group
        )
        self.ifc = b"""ISO-10303-21;\n#10=IFCQUANTITYVOLUME('P-1001',$,$,2.5);\nEND-ISO-10303-21;"""

    def _client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_upload_processes_mapped_draft_without_plan_mutation(self):
        response = self._client(self.user).post(
            "/api/v1/construction/ifc-importlari/",
            {"project": self.project.pk, "year": 2026, "file": SimpleUploadedFile("model.ifc", self.ifc, "application/octet-stream")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        job = IFCImportJob.objects.get(pk=response.json()["data"]["id"])
        processed = self._client(self.user).post(f"/api/v1/construction/ifc-importlari/{job.pk}/process/")
        self.assertEqual(processed.status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.status, IFCImportJob.Status.COMPLETED)
        self.assertEqual(job.parser_mode, "step-quantities")
        row = IFCQuantityDraft.objects.get(job=job)
        self.assertEqual(row.poz_id, self.poz.pk)
        self.assertFalse(job.project.poz_planlari.exists())

    def test_tenant_isolation_and_invalid_extension(self):
        denied = self._client(self.other_user).get("/api/v1/construction/ifc-importlari/")
        self.assertEqual(denied.status_code, 200)
        self.assertEqual(denied.json()["data"]["count"], 0)
        bad = self._client(self.user).post(
            "/api/v1/construction/ifc-importlari/",
            {"project": self.project.pk, "year": 2026, "file": SimpleUploadedFile("model.txt", b"x", "text/plain")},
            format="multipart",
        )
        self.assertEqual(bad.status_code, 400)

    def test_invalid_ifc_records_validation_error(self):
        response = self._client(self.user).post(
            "/api/v1/construction/ifc-importlari/",
            {"project": self.project.pk, "year": 2026, "file": SimpleUploadedFile("bad.ifc", b"not-ifc", "application/octet-stream")},
            format="multipart",
        )
        job = IFCImportJob.objects.get(pk=response.json()["data"]["id"])
        self._client(self.user).post(f"/api/v1/construction/ifc-importlari/{job.pk}/process/")
        job.refresh_from_db()
        self.assertEqual(job.status, IFCImportJob.Status.FAILED)
        self.assertTrue(job.validation_errors)


class IFCHardeningTests(IFCImportApiTests):
    """FAZ 6F-1 — IFC upload/process/approve negative senaryoları."""

    def _yukle(self, ad, icerik, mime="application/octet-stream", proje=None):
        return self._client(self.user).post(
            "/api/v1/construction/ifc-importlari/",
            {"project": (proje or self.project).pk, "year": 2026,
             "file": SimpleUploadedFile(ad, icerik, mime)},
            format="multipart",
        )

    def test_dosya_yok_400(self):
        yanit = self._client(self.user).post(
            "/api/v1/construction/ifc-importlari/",
            {"project": self.project.pk, "year": 2026},
            format="multipart",
        )
        self.assertEqual(yanit.status_code, 400)

    def test_bos_dosya_400_kayit_yok(self):
        sayi = IFCImportJob.objects.count()
        yanit = self._yukle("bos.ifc", b"")
        self.assertEqual(yanit.status_code, 400)
        self.assertEqual(IFCImportJob.objects.count(), sayi)

    def test_cok_buyuk_dosya_400(self):
        from django.test import override_settings

        sayi = IFCImportJob.objects.count()
        with override_settings(IFC_UPLOAD_MAX_BYTES=10):
            yanit = self._yukle("buyuk.ifc", b"x" * 20)
        self.assertEqual(yanit.status_code, 400)
        self.assertEqual(IFCImportJob.objects.count(), sayi)
        self.assertNotIn("Traceback", yanit.content.decode())

    def test_yanlis_mime_400(self):
        yanit = self._yukle("model.ifc", self.ifc, mime="text/html")
        self.assertEqual(yanit.status_code, 400)

    def test_ifczip_desteklenmiyor_400(self):
        yanit = self._yukle("model.ifczip", b"PK\x03\x04")
        self.assertEqual(yanit.status_code, 400)

    def test_path_traversal_normalize_edilir(self):
        for ad in ("../../secret.ifc", "..\\..\\secret.ifc", "/abs/secret.ifc"):
            yanit = self._yukle(ad, self.ifc)
            self.assertEqual(yanit.status_code, 201, ad)
            job = IFCImportJob.objects.get(pk=yanit.json()["data"]["id"])
            self.assertEqual(job.file_name, "secret.ifc")
            self.assertNotIn("..", job.file.name)
            self.assertTrue(job.file.name.endswith(".ifc"))

    def test_bozuk_ifc_kismi_kayit_birakmaz(self):
        yanit = self._yukle("bozuk.ifc", b"not-ifc-at-all")
        job = IFCImportJob.objects.get(pk=yanit.json()["data"]["id"])
        isle = self._client(self.user).post(
            f"/api/v1/construction/ifc-importlari/{job.pk}/process/"
        )
        self.assertEqual(isle.status_code, 200)
        job.refresh_from_db()
        self.assertEqual(job.status, IFCImportJob.Status.FAILED)
        self.assertEqual(IFCQuantityDraft.objects.filter(job=job).count(), 0)
        self.assertFalse(self.project.poz_planlari.exists())

    def test_tenant_disi_process_approve_404(self):
        yanit = self._yukle("model.ifc", self.ifc)
        pk = yanit.json()["data"]["id"]
        istemci = self._client(self.other_user)
        self.assertEqual(
            istemci.post(f"/api/v1/construction/ifc-importlari/{pk}/process/").status_code,
            404,
        )
        self.assertEqual(
            istemci.post(
                f"/api/v1/construction/ifc-importlari/{pk}/approve/",
                {"create_plan": True}, format="json",
            ).status_code,
            404,
        )

    def test_tekrar_process_duplicate_uretmez(self):
        yanit = self._yukle("model.ifc", self.ifc)
        job = IFCImportJob.objects.get(pk=yanit.json()["data"]["id"])
        self._client(self.user).post(f"/api/v1/construction/ifc-importlari/{job.pk}/process/")
        sayi = IFCQuantityDraft.objects.filter(job=job).count()
        self.assertGreater(sayi, 0)
        tekrar = self._client(self.user).post(
            f"/api/v1/construction/ifc-importlari/{job.pk}/process/"
        )
        self.assertEqual(tekrar.status_code, 400)
        self.assertEqual(IFCQuantityDraft.objects.filter(job=job).count(), sayi)

    def test_onaysiz_job_approve_400(self):
        yanit = self._yukle("model.ifc", self.ifc)
        pk = yanit.json()["data"]["id"]
        red = self._client(self.user).post(
            f"/api/v1/construction/ifc-importlari/{pk}/approve/",
            {"create_plan": True}, format="json",
        )
        self.assertEqual(red.status_code, 400)
        self.assertFalse(self.project.poz_planlari.exists())
