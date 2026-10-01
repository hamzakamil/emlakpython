from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Tenant
from users.models import User, UserRole

from accounting.models import HesapPlani
from cari.models import Cari

from .models import Fatura, FinansalOlay, FinansalOlayLog, IdempotencyKey, OutboxEvent
from .services.idempotency import complete_operation, idempotent_operation
from .services.finansal_olay import finansal_olay_olustur
from .services.shadow_posting import fatura_shadow_muhasebelestir
from .services.entegrasyon import (
    fatura_cari_hareketi_olustur,
    finansal_islem_muhasebelestir,
)
from .services.state_machine import fatura_durum_gecis
from .services.outbox import enqueue_outbox_event, process_outbox_events


class Faz05TemelTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(name="State A.Ş.", slug="state-as")
        self.user = User.objects.create_user(
            username="state-finans",
            password="secret",
            email="state@example.com",
            tenant=self.tenant,
            role=UserRole.FINANS,
        )
        self.fatura = Fatura.objects.create(
            tenant=self.tenant,
            No="STATE-001",
            tarih=date(2026, 9, 18),
            tutar=Decimal("100.00"),
        )
        self.borc_hesabi = HesapPlani.objects.create(
            tenant=self.tenant, kod="120", ad="Alıcılar", tip="aktif"
        )
        self.alacak_hesabi = HesapPlani.objects.create(
            tenant=self.tenant, kod="600", ad="Yurtiçi Satışlar", tip="gelir"
        )

    def test_fatura_gecis_matrisi_gecersiz_gecisi_reddeder(self):
        fatura_durum_gecis(
            self.fatura.pk,
            Fatura.DurumChoices.ACTIVE,
            tenant_id=self.tenant.pk,
        )
        with self.assertRaises(ValidationError):
            fatura_durum_gecis(
                self.fatura.pk,
                Fatura.DurumChoices.DRAFT,
                tenant_id=self.tenant.pk,
            )

    def test_idempotency_ayni_anahtari_tekrar_kullaninca_tamamlanan_sonucu_doner(self):
        with idempotent_operation(
            tenant_id=self.tenant.pk,
            operation="test.operation",
            key="same-key",
            payload={"fatura": self.fatura.pk},
        ) as operation:
            complete_operation(operation, response_data={"ok": True})

        with idempotent_operation(
            tenant_id=self.tenant.pk,
            operation="test.operation",
            key="same-key",
            payload={"fatura": self.fatura.pk},
        ) as operation:
            self.assertEqual(operation.status, IdempotencyKey.Durum.COMPLETED)
            self.assertEqual(operation.response_data, {"ok": True})

        self.assertEqual(
            IdempotencyKey.objects.filter(
                tenant=self.tenant,
                operation="test.operation",
                key="same-key",
            ).count(),
            1,
        )

    def test_durum_gecis_endpointi_idempotency_key_zorunlu(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.post(
            f"/api/v1/finance/faturalar/{self.fatura.pk}/durum-gecis/",
            {"durum": Fatura.DurumChoices.ACTIVE},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Idempotency-Key", response.json()["errors"])

    def test_finansal_olay_dengeli_satir_ve_log_olusturur(self):
        olay = finansal_olay_olustur(
            tenant_id=self.tenant.pk,
            olay_turu="fatura",
            kaynak_turu="finance.Fatura",
            kaynak_id=self.fatura.pk,
            olay_anahtari=f"fatura:{self.fatura.pk}:aktif",
            tarih=self.fatura.tarih,
            satirlar=[
                {"hesap_id": self.borc_hesabi.pk, "borc": "100.00", "alacak": "0"},
                {"hesap_id": self.alacak_hesabi.pk, "borc": "0", "alacak": "100.00"},
            ],
        )
        self.assertEqual(olay.durum, FinansalOlay.Durum.KAYITLI)
        self.assertEqual(olay.satirlar.count(), 2)
        self.assertEqual(FinansalOlayLog.objects.filter(olay=olay).count(), 1)

        tekrar = finansal_olay_olustur(
            tenant_id=self.tenant.pk,
            olay_turu="fatura",
            kaynak_turu="finance.Fatura",
            kaynak_id=self.fatura.pk,
            olay_anahtari=f"fatura:{self.fatura.pk}:aktif",
            tarih=self.fatura.tarih,
            satirlar=[],
        )
        self.assertEqual(tekrar.pk, olay.pk)

    def test_fatura_shadow_muhasebelestirme_finansal_olay_uret(self):
        satis_hesabi, _ = HesapPlani.objects.get_or_create(
            tenant=self.tenant,
            kod="600",
            defaults={"ad": "Satışlar", "tip": "gelir"},
        )
        self.fatura.alacakli = True
        self.fatura.save(update_fields=["alacakli"])
        olay = fatura_shadow_muhasebelestir(
            self.fatura,
            tenant_id=self.tenant.pk,
        )
        self.assertEqual(olay.olay_turu, "fatura_shadow_posting")
        self.assertEqual(olay.satirlar.count(), 2)
        self.assertEqual(
            olay.satirlar.get(hesap=self.borc_hesabi).borc,
            Decimal("100.00"),
        )
        self.assertEqual(
            olay.satirlar.get(hesap=satis_hesabi).alacak,
            Decimal("100.00"),
        )

    def test_fatura_cari_hareketi_idempotent_kaynakli_olur(self):
        cari = Cari.objects.create(
            tenant=self.tenant,
            ad="Entegrasyon Cari",
        )
        self.fatura.cari = cari
        self.fatura.save(update_fields=["cari"])
        ilk = fatura_cari_hareketi_olustur(self.fatura)
        ikinci = fatura_cari_hareketi_olustur(self.fatura)
        self.assertEqual(ilk.pk, ikinci.pk)
        self.assertEqual(cari.hareketler.count(), 1)

    def test_finansal_islem_muhasebe_fisine_bagli_olur(self):
        islem = self._create_finansal_islem()
        gider_hesabi, _ = HesapPlani.objects.get_or_create(
            tenant=self.tenant,
            kod="770",
            defaults={"ad": "Genel Yönetim Giderleri", "tip": "gider"},
        )
        fis = finansal_islem_muhasebelestir(
            islem,
            karsilik_hesap_id=gider_hesabi.pk,
        )
        islem.refresh_from_db()
        self.assertEqual(islem.muhasebe_fisi_id, fis.pk)
        self.assertEqual(fis.satirlar.count(), 2)

    def _create_finansal_islem(self):
        from .models import FinansalIslem, KasaBankaHesabi

        kasa = KasaBankaHesabi.objects.create(
            tenant=self.tenant,
            kod="K-ENTEGRASYON",
            ad="Entegrasyon Kasa",
        )
        return FinansalIslem.objects.create(
            tenant=self.tenant,
            hesap=kasa,
            yon=FinansalIslem.Yon.GIDER,
            tutar=Decimal("50.00"),
            islem_tarihi=date(2026, 9, 18),
        )

    def test_outbox_tekrar_calisma_ve_dead_letter(self):
        event = enqueue_outbox_event(
            tenant_id=self.tenant.pk,
            event_key="fatura:1:created",
            event_type="unknown",
            payload={"id": 1},
        )
        event.max_attempts = 1
        event.save(update_fields=["max_attempts"])
        result = process_outbox_events()
        event.refresh_from_db()
        self.assertEqual(result["dead_letter"], 1)
        self.assertEqual(event.status, OutboxEvent.Durum.DEAD_LETTER)
