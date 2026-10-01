import { get, patch, post } from './apiClient'
import type { Sayfali } from '@/types/api'
import type { Cari, CariHareket, CariOzet } from '@/types/cari'

const kaynak = '/cari/cariler/'

export const cariApi = {
  cariler: {
    liste: (params?: Record<string, unknown>) => get<Sayfali<Cari>>(kaynak, params),
    olustur: (veri: Record<string, unknown>) => post<Cari>(kaynak, veri),
    guncelle: (id: number, veri: Record<string, unknown>) => patch<Cari>(`${kaynak}${id}/`, veri),
    getir: (id: number) => get<Cari>(`${kaynak}${id}/`),
    hareketlerListe: (params?: Record<string, unknown>) => get<Sayfali<CariHareket>>('/cari/cari-hareketler/', params),
    ozet: (id: number) => get<CariOzet>(`${kaynak}${id}/ozet/`),
    hareketEkle: (veri: Record<string, unknown>) => post<CariHareket>('/cari/cari-hareketler/', veri),
    hareketGuncelle: (id: number, veri: Record<string, unknown>) => patch<CariHareket>(`/cari/cari-hareketler/${id}/`, veri),
  },
}
