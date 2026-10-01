export interface FinansHesabi {
  id: number
  kod: string
  ad: string
  tip: string
  iban_maskeli?: string | null
  para_birimi: string
  is_active: boolean
  tenant: number
}

export interface FinansalIslem {
  id: number
  hesap: number
  hesap_kodu?: string | null
  cari: number | null
  yon: 'gelir' | 'gider' | 'transfer'
  tutar: string
  islem_tarihi: string
  aciklama: string
  is_cancelled: boolean
}

export type CekSenetTuru = 'cek' | 'senet'
export type CekSenetDurumu = 'bekliyor' | 'tahsil_edildi' | 'odendi' | 'karsiliksiz' | 'iptal'

export interface CekSenet {
  id: number
  tur: CekSenetTuru
  numara: string
  cari: number | null
  hesap: number | null
  proje: number | null
  tutar: string
  vade_tarihi: string
  durum: CekSenetDurumu
  aciklama: string
  created_at: string
  updated_at: string
}

export const CEK_SENET_TURLERI: Record<CekSenetTuru, string> = { cek: 'Çek', senet: 'Senet' }
export const CEK_SENET_DURUMLARI: Record<CekSenetDurumu, string> = {
  bekliyor: 'Bekliyor',
  tahsil_edildi: 'Tahsil Edildi',
  odendi: 'Ödendi',
  karsiliksiz: 'Karşılıksız',
  iptal: 'İptal',
}

export const FINANS_HESAP_TIPLERI: Record<string, string> = {
  kasa: 'Kasa',
  banka: 'Banka',
  kredi_karti: 'Kredi Kartı',
  cek: 'Çek',
}

export const FINANS_ISLEM_YONLERI: Record<string, string> = {
  gelir: 'Gelir',
  gider: 'Gider',
  transfer: 'Transfer',
}
