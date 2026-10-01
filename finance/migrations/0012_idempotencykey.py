from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0011_faturakalemi_genisletme"),
    ]

    operations = [
        migrations.CreateModel(
            name="IdempotencyKey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=255)),
                ("operation", models.CharField(max_length=100)),
                ("request_hash", models.CharField(blank=True, max_length=64)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("processing", "İşleniyor"),
                            ("completed", "Tamamlandı"),
                            ("failed", "Başarısız"),
                        ],
                        default="processing",
                        max_length=20,
                    ),
                ),
                ("response_data", models.JSONField(blank=True, default=dict)),
                ("resource_type", models.CharField(blank=True, max_length=100)),
                ("resource_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=models.deletion.PROTECT,
                        related_name="+",
                        to="tenants.tenant",
                        verbose_name="Tenant",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["tenant", "operation", "status"], name="finance_ide_tenant__c6ba6b_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="idempotencykey",
            constraint=models.UniqueConstraint(
                fields=("tenant", "operation", "key"),
                name="uniq_idempotency_tenant_operation_key",
            ),
        ),
    ]
