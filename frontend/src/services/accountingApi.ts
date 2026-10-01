import { get, post, patch, del } from './apiClient'
import type { Sayfali } from '@/types/api'
import type { MuhasebeFisi, MizanSatiri } from '@/types/muhasebe'

/** Genel muhasebe defteri API servisi — /api/v1/accounting/ */
export const accountingApi = {
  /** Accounting entries (fişler) list with pagination/filtering */
  liste: (params?: Record<string, unknown>) => get<Sayfali<MuhasebeFisi>>('/accounting/', params),

  /** Get single accounting entry by ID */
  getById: (id: number) => get<MuhasebeFisi>(`/accounting/${id}/`),

  /** Create new accounting entry */
  create: (veri: Record<string, unknown>) => post<MuhasebeFisi>('/accounting/', veri),

  /** Update existing accounting entry */
  update: (id: number, veri: Record<string, unknown>) => patch<MuhasebeFisi>(`/accounting/${id}/`, veri),

  /** Delete accounting entry (with reversal) */
  delete: (id: number) => del<MuhasebeFisi>(`/accounting/${id}/`),

  /** Get accounting entry lines */
  getLines: (id: number) => get<any>(`/accounting/${id}/lines/`),

  /** Trial balance report */
  mizan: () => get<MizanSatiri[]>('/accounting/mizan/'),

  /** Post subcontractor progress billing to accounting */
  postSubcontractorProgressBilling: (id: number) => post<{ success: boolean }>(`/construction/hakedisler/${id}/naklet/`),
}