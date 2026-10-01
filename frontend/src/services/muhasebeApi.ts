import { get, patch, post } from './apiClient'
import type { Sayfali } from '@/types/api'
import type { HesapPlani, MizanSatiri, MuhasebeFisi } from '@/types/muhasebe'

const kaynak = '/accounting/hesap-plani/'
const fisKaynagi = '/accounting/fisler/'

export const muhasebeApi = {
  hesapPlani: {
    liste: (params?: Record<string, unknown>) => get<Sayfali<HesapPlani>>(kaynak, params),
    olustur: (veri: Record<string, unknown>) => post<HesapPlani>(kaynak, veri),
    guncelle: (id: number, veri: Record<string, unknown>) => patch<HesapPlani>(`${kaynak}${id}/`, veri),
  },
  fisler: {
    liste: (params?: Record<string, unknown>) => get<Sayfali<MuhasebeFisi>>(fisKaynagi, params),
    olustur: (veri: Record<string, unknown>) => post<MuhasebeFisi>(fisKaynagi, veri),
    mizan: () => get<MizanSatiri[]>(`${fisKaynagi}mizan/`),
  },
}
