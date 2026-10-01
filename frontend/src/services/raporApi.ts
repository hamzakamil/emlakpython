import { get, post } from './apiClient'

export interface CariRaporSatiri {
  cari: number
  cari_ad: string
  borc: string
  alacak: string
  bakiye: string
}

export interface FinansRaporu {
  gelir: string
  gider: string
  transfer: string
}

export interface MizanRaporSatiri {
  hesap_kodu: string
  hesap_adi: string
  borc: string
  alacak: string
  bakiye: string
}

export interface DogalDilRaporu {
  soru: string
  rapor_tipi: 'finans_ozeti' | 'cari_ozeti' | 'mizan'
  ozet: string
  veri_notu: string
  metrikler?: { gelir: string; gider: string; net: string }
  satirlar?: Array<Record<string, string | number>>
}

const kaynak = '/finance/raporlar/'

export const raporApi = {
  finansOzeti: () => get<FinansRaporu>(`${kaynak}finans-ozeti/`),
  cariOzeti: () => get<CariRaporSatiri[]>(`${kaynak}cari-ozeti/`),
  mizan: () => get<MizanRaporSatiri[]>(`${kaynak}mizan/`),
  dogalDil: (soru: string) => post<DogalDilRaporu>(`${kaynak}dogal-dil/`, { soru }),
}