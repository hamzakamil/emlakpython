import { get, patch, post } from './apiClient'
import type { Sayfali } from '@/types/api'

export interface Ayar {
  id: number
  anahtar: string
  deger: string
  aciklama: string
  created_at?: string
  updated_at?: string
}

const kaynak = '/finance/ayarlar/'

export const ayarApi = {
  liste: (params?: Record<string, unknown>) => get<Sayfali<Ayar>>(kaynak, params),
  olustur: (veri: Record<string, unknown>) => post<Ayar>(kaynak, veri),
  guncelle: (id: number, veri: Record<string, unknown>) => patch<Ayar>(`${kaynak}${id}/`, veri),
}