/**
 * Ortak API tipleri — backend yanıt zarfı:
 *   başarı: { success, data, message }
 *   hata:   { success: false, message, errors }
 * Kaynak: config/renderers.py + config/exceptions.py (DRF tarafı).
 */

export interface Zarf<T = unknown> {
  success: boolean
  data: T
  message: string
  errors?: AlanHatalari | null
}

export type AlanHatalari = Record<string, string[] | string>

/** DRF sayfalama zarf içi gövdesi (PageNumberPagination benzeri). */
export interface Sayfali<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/** users.models.UserRole ile senkron (backend tek doğruluk kaynağıdır). */
export type Rol =
  | 'super_admin'
  | 'tenant_admin'
  | 'firma_admin'
  | 'muhasebe'
  | 'finans'
  | 'proje_yoneticisi'
  | 'satis'
  | 'santiye_sefi'
  | 'maliyet_muhendisi'
  | 'kullanici'

export interface Kullanici {
  id: number
  username: string
  email: string
  role: Rol
  tenant: number | null
  /** /auth/me'den gelen gerçek firma adı (topbar'da gösterilir). */
  tenant_ad?: string | null
  first_name?: string
  last_name?: string
}

/** POST /api/v1/auth/token/ zarf içi gövdesi (simplejwt). */
export interface TokenCevap {
  access: string
  refresh: string
}

/** GET /api/v1/tenants/ kaydı — yalnızca süper admin (seçici listesi). */
export interface TenantSecim {
  id: number
  name: string
  slug: string
  is_active: boolean
}

/** Süper admin firma (tenant) yönetimi kaydı — tam CRUD. */
export interface Tenant {
  id: number
  name: string
  slug: string
  is_active: boolean
  max_users: number
  max_projects: number
  max_storage_gb: number
  created_at?: string
  updated_at?: string
}

/** Süper admin kullanıcı yönetimi kaydı — parola yalnızca yazılabilir. */
export interface KullaniciYonetim {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: Rol
  tenant: number | null
  is_active: boolean
  password?: string
}

