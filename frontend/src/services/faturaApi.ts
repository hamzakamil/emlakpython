import { del, get, patch, post } from './apiClient'
import type { Sayfali } from '@/types/api'
import type { Fatura } from '@/types/fatura'

const kaynak = '/finance/faturalar/'

export const faturaApi = {
  liste: (params?: Record<string, unknown>) => get<Sayfali<Fatura>>(kaynak, params),
  olustur: (veri: Record<string, unknown>) => post<Fatura>(kaynak, veri),
  guncelle: (id: number, veri: Record<string, unknown>) => patch<Fatura>(`${kaynak}${id}/`, veri),
  sil: (id: number) => del<Fatura>(`${kaynak}${id}/`),
  hesapOzeti: (id: number) => get<Fatura>(`${kaynak}${id}/hesap-ozeti/`),
  eFaturaGonder: (id: number) => post<Fatura>(`${kaynak}${id}/e-fatura-gonder/`),
  iadeOlustur: (id: number) => post<Fatura>(`${kaynak}${id}/iade-olustur/`),
}