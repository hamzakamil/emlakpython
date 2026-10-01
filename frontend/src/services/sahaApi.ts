import { get, patch, post } from './apiClient'
import type { Sayfali } from '@/types/api'
import type { KaliteKontrol, SantiyeGunlugu } from '@/types/saha'

function crud<T>(kaynak: string) {
  return {
    liste: (params?: Record<string, unknown>) => get<Sayfali<T>>(kaynak, params),
    olustur: (veri: Record<string, unknown>) => post<T>(kaynak, veri),
    guncelle: (id: number, veri: Record<string, unknown>) => patch<T>(`${kaynak}${id}/`, veri),
    sil: (id: number) => post<T>(`${kaynak}${id}/sil/`, {}), // soft delete / iptal endpoint
  }
}

export const sahaApi = {
  gunlukler: crud<SantiyeGunlugu>('/construction/santiye-gunlukleri/'),
  kalite: crud<KaliteKontrol>('/construction/kalite-kontrolleri/'),
}
