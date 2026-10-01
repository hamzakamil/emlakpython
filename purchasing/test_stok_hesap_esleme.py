"""FAZ 7R testleri — StokHesapEsleme CRUD, validasyon, tenant izolasyonu."""

import uuid

from django.test import TestCase
from rest_framework.test import APIClient

from accounting.models import HesapPlani
from construction.models import Malzeme
from tenants.models import Tenant
from users.models import User, UserRole

URL = "/api/v1/purchase-stok-hesap-esleme/"


class StokHesapEslemeBase(TestCase):
    def setUp(self):
        unique = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name="Eşleme A.Ş.", slug=f"esleme-{unique}")
        self.diger = Tenant.objects.create(name="Diğer A.Ş.", slug=f"esleme-diger-{unique}")
        self.editor = User.objects.create_user(
            username=f"esleme_{unique}", password="x", email=f"esleme_{unique}@example.com",
            tenant=self.tenant, role=UserRole.MALIYET_MUHENDISI,
        )
        self.reader = User.objects.create_user(
            username=f"esleme_okur_{unique}", password="x", email=f"esleme_okur_{unique}@example.com",
            tenant=self.tenant, role=UserRole.SANTIYE_SEFI,
        )
        self.hesap = HesapPlani.objects.create(
            tenant=self.tenant, kod="150", ad="Stok Hesabı"
        )
        self.malzeme = Malzeme.objects.create(
            tenant=self.tenant, malzeme_kodu="ESL-M", ad="Eşleme Malzemesi", birim="adet"
        )
        self.istemci = APIClient()
        self.istemci.force_authenticate(user=self.editor)

    def _kayit_ac(self, **ek):
        veri = {"hesap_turu": "stok", "hesap": self.hesap.pk, **ek}
        return self.istemci.post(URL, veri, format="json")


class StokHesapEslemeTests(StokHesapEslemeBase):
    def test_liste_bos(self):
        yanit = self.istemci.get(URL)
        self.assertEqual(yanit.status_code, 200)

    def test_varsayilan_olustur(self):
        yanit = self._kayit_ac()
        self.assertEqual(yanit.status_code, 201, yanit.content[:300])
        self.assertIsNone(yanit.json()["data"]["malzeme_kodu"])

    def test_malzemeli_olustur_gorunum_alanlari(self):
        yanit = self._kayit_ac(malzeme=self.malzeme.pk)
        self.assertEqual(yanit.status_code, 201, yanit.content[:300])
        veri = yanit.json()["data"]
        self.assertEqual(veri["malzeme_kodu"], "ESL-M")
        self.assertEqual(veri["hesap_kodu"], "150")

    def test_ayni_varsayilan_ikinci_kez_400(self):
        self.assertEqual(self._kayit_ac().status_code, 201)
        yanit = self._kayit_ac()
        self.assertEqual(yanit.status_code, 400)

    def test_baska_tenant_hesap_400(self):
        yabanci = HesapPlani.objects.create(tenant=self.diger, kod="150", ad="Yabancı")
        yanit = self._kayit_ac(hesap=yabanci.pk)
        self.assertEqual(yanit.status_code, 400)

    def test_okur_yazamaz(self):
        okur_istemci = APIClient()
        okur_istemci.force_authenticate(user=self.reader)
        self.assertEqual(okur_istemci.get(URL).status_code, 200)
        yanit = okur_istemci.post(
            URL, {"hesap_turu": "kdv", "hesap": self.hesap.pk}, format="json"
        )
        self.assertEqual(yanit.status_code, 403)

    def test_guncelle(self):
        kayit_id = self._kayit_ac().json()["data"]["id"]
        yanit = self.istemci.patch(
            f"{URL}{kayit_id}/", {"hesap_turu": "kdv"}, format="json"
        )
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["data"]["hesap_turu"], "kdv")

    def test_sil_204_ve_kayit_gider(self):
        from .models import StokHesapEsleme

        kayit_id = self._kayit_ac().json()["data"]["id"]
        yanit = self.istemci.delete(f"{URL}{kayit_id}/")
        self.assertEqual(yanit.status_code, 204)
        self.assertFalse(StokHesapEsleme.objects.filter(pk=kayit_id).exists())
