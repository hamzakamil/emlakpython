from django.urls import path

from . import api

urlpatterns = [
    path("overview/", api.overview, name="database-overview"),
    path("excel/template/", api.excel_template, name="database-excel-template"),
    path("excel/export/", api.excel_export, name="database-excel-export"),
    path("excel/import/", api.excel_import, name="database-excel-import"),
    path("backups/", api.backups, name="database-backups"),
    path("backups/create/", api.create_backup, name="database-backup-create"),
    path("backups/<str:filename>/download/", api.download_backup, name="database-backup-download"),
    path("backups/restore/", api.restore_backup, name="database-backup-restore"),
    path("tables/<str:table_name>/rows/", api.table_rows, name="database-table-rows"),
    path("tables/<str:table_name>/rows/<int:row_id>/", api.update_row, name="database-row-update"),
]
