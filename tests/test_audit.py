from django.contrib.auth import get_user_model
from django.test import TestCase

from audit.models import AuditLog
from tenants.models import Tenant


class AuditModelTest(TestCase):
    def setUp(self):
        import uuid
        unique = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name="Audit A.Ş.", slug=f"audit-as-{unique}")
        self.user = get_user_model().objects.create_user(
            username=f"audit-user-{unique}", password="test", tenant=self.tenant,
            email=f"audit-user-{unique}@example.com",
        )

    def test_log_change_keeps_tenant_and_values(self):
        log = AuditLog.log_change(
            kullanıcı=self.user,
            islem_türü=AuditLog.IslemTürü.CREATE,
            nesne=self.user,
            yeni={"username": self.user.username},
            sebep="Test kaydi",
        )
        self.assertEqual(log.tenant_id, self.tenant.id)
        self.assertIn(self.user.username, log.yeni_değer)
        self.assertEqual(log.sebep, "Test kaydi")
