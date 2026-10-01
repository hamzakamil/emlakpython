from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("construction", "0007_ekb"),
        ("tenants", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IFCImportJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveSmallIntegerField(verbose_name="Plan Yılı")),
                ("file", models.FileField(blank=True, null=True, upload_to="construction/ifc/%Y/%m/")),
                ("file_name", models.CharField(max_length=255, verbose_name="Dosya Adı")),
                ("file_size", models.PositiveBigIntegerField(default=0, verbose_name="Dosya Boyutu")),
                ("content_type", models.CharField(blank=True, max_length=100)),
                ("source_reference", models.CharField(blank=True, max_length=500)),
                ("checksum", models.CharField(blank=True, db_index=True, max_length=64)),
                ("status", models.CharField(choices=[("queued", "Kuyrukta"), ("processing", "İşleniyor"), ("completed", "Tamamlandı"), ("failed", "Başarısız")], default="queued", max_length=20)),
                ("parser_mode", models.CharField(blank=True, max_length=40)),
                ("validation_errors", models.JSONField(blank=True, default=list)),
                ("processing_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ifc_import_jobs", to="construction.proje")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ifc_import_jobs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="IFCQuantityDraft",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveSmallIntegerField()),
                ("source_name", models.CharField(max_length=255)),
                ("quantity", models.DecimalField(decimal_places=4, max_digits=18)),
                ("unit", models.CharField(max_length=30)),
                ("ifc_entity_type", models.CharField(blank=True, max_length=80)),
                ("mapping_status", models.CharField(choices=[("mapped", "Eşleşti"), ("unmapped", "Eşleşmedi"), ("invalid", "Geçersiz")], max_length=20)),
                ("validation_message", models.CharField(blank=True, max_length=500)),
                ("raw_data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="draft_rows", to="construction.ifcimportjob")),
                ("poz", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to="construction.poz")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="construction.proje")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="tenants.tenant")),
            ],
            options={"ordering": ["mapping_status", "source_name", "id"]},
        ),
        migrations.AddIndex(model_name="ifcimportjob", index=models.Index(fields=["tenant", "project", "year", "status"], name="constructio_tenant__eda721_idx")),
        migrations.AddIndex(model_name="ifcquantitydraft", index=models.Index(fields=["tenant", "job", "mapping_status"], name="constructio_tenant__ec634a_idx")),
    ]
