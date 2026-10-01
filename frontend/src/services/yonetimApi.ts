/**
 * Süper admin yönetim servisi — firma (tenant) ve kullanıcı CRUD.
 * Uçlar yalnızca süper admin'e açıktır (backend IsSuperUser).
 */
import { del, get, patch, post } from './apiClient'
import type { KullaniciYonetim, Sayfali, Tenant } from '@/types/api'

function crudFactory<T>(kaynak: string) {
  return {
    liste: (params?: Record<string, unknown>) => get<Sayfali<T>>(kaynak, params),
    tek: (id: number) => get<T>(`${kaynak}${id}/`),
    olustur: (veri: Record<string, unknown>) => post<T>(kaynak, veri),
    guncelle: (id: number, veri: Record<string, unknown>) => patch<T>(`${kaynak}${id}/`, veri),
    sil: (id: number) => del<T>(`${kaynak}${id}/`),
  }
}

export const yonetimApi = {
  firmalar: crudFactory<Tenant>('/tenants-yonetim/'),
  kullanicilar: crudFactory<KullaniciYonetim>('/kullanicilar/'),
}