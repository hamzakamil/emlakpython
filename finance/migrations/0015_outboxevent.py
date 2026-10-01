from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0014_finansal_entegrasyon_kaynaklari"),
    ]

    operations = [
        migrations.CreateModel(
            name="OutboxEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_key", models.CharField(max_length=255)),
                ("event_type", models.CharField(max_length=100)),
                ("payload", models.JSONField(default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Bekliyor"),
                            ("processing", "İşleniyor"),
                            ("completed", "Tamamlandı"),
                            ("retry", "Tekrar Denenecek"),
                            ("dead_letter", "Dead Letter"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("max_attempts", models.PositiveIntegerField(default=5)),
                ("available_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="tenants.tenant",
                        verbose_name="Tenant",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["tenant", "status", "available_at"], name="finance_out_tenant__e1e596_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="outboxevent",
            constraint=models.UniqueConstraint(
                fields=("tenant", "event_key"),
                name="uniq_outbox_tenant_event_key",
            ),
        ),
    ]
