import { get, http, post } from './apiClient'
import type { DatabaseBackup, DatabaseOverview, DatabaseRows } from '@/types/database'

export const databaseApi = {
  overview: () => get<DatabaseOverview>('/database/overview/'),
  rows: (table: string, params?: Record<string, unknown>) => get<DatabaseRows>(`/database/tables/${encodeURIComponent(table)}/rows/`, params),
  updateRow: (table: string, id: number, values: Record<string, unknown>) => http.patch(`/database/tables/${encodeURIComponent(table)}/rows/${id}/`, values),
  backups: () => get<DatabaseBackup[]>('/database/backups/'),
  createBackup: () => post<{ name: string; size: number }>('/database/backups/create/'),
  excelTemplate: (tables: string[], fields: Record<string, string[]>) =>
    http.post('/database/excel/template/', { tables, fields }, { responseType: 'blob' }),
  excelExport: (tables: string[], fields: Record<string, string[]>) =>
    http.post('/database/excel/export/', { tables, fields }, { responseType: 'blob' }),
  excelImport: (file: File, tenantId: number | null, dryRun = false) => {
    const body = new FormData()
    body.append('workbook', file)
    if (tenantId) body.append('tenant_id', String(tenantId))
    if (dryRun) body.append('dry_run', 'true')
    return http.post('/database/excel/import/', body, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  restore: (file: File, confirmation: string) => {
    const body = new FormData()
    body.append('backup', file)
    body.append('confirmation', confirmation)
    return http.post('/database/backups/restore/', body, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  downloadUrl: (name: string) => `/database/backups/${encodeURIComponent(name)}/download/`,
}
