import { del, get, patch, post } from './apiClient'
import type { Sayfali } from '@/types/api'
import type { CekSenet, FinansalIslem, FinansHesabi } from '@/types/finans'
import type { VergiProfili } from '@/types/fatura'

const kaynak = '/finance/kasa-banka-hesaplari/'
const islemKaynagi = '/finance/finansal-islemler/'
const cekSenetKaynagi = '/finance/cek-senetler/'
const vergiProfiliKaynagi = '/finance/vergi-profilleri/'

export const finansApi = {
  hesaplar: {
    liste: (params?: Record<string, unknown>) => get<Sayfali<FinansHesabi>>(kaynak, params),
    olustur: (veri: Record<string, unknown>) => post<FinansHesabi>(kaynak, veri),
    guncelle: (id: number, veri: Record<string, unknown>) => patch<FinansHesabi>(`${kaynak}${id}/`, veri),
  },
  islemler: {
    liste: (params?: Record<string, unknown>) => get<Sayfali<FinansalIslem>>(islemKaynagi, params),
    olustur: (veri: Record<string, unknown>) => post<FinansalIslem>(islemKaynagi, veri),
    iptal: (id: number) => post<FinansalIslem>(`${islemKaynagi}${id}/iptal/`),
    sil: (id: number) => del<FinansalIslem>(`${islemKaynagi}${id}/`),
  },
  cekSenetler: {
    liste: (params?: Record<string, unknown>) => get<Sayfali<CekSenet>>(cekSenetKaynagi, params),
    olustur: (veri: Record<string, unknown>) => post<CekSenet>(cekSenetKaynagi, veri),
    guncelle: (id: number, veri: Record<string, unknown>) => patch<CekSenet>(`${cekSenetKaynagi}${id}/`, veri),
    sil: (id: number) => del<CekSenet>(`${cekSenetKaynagi}${id}/`),
  },
  vergiProfilleri: {
    liste: (params?: Record<string, unknown>) => get<Sayfali<VergiProfili>>(vergiProfiliKaynagi, params),
    olustur: (veri: Record<string, unknown>) => post<VergiProfili>(vergiProfiliKaynagi, veri),
    guncelle: (id: number, veri: Record<string, unknown>) => patch<VergiProfili>(`${vergiProfiliKaynagi}${id}/`, veri),
  },
}
