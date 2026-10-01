export interface HesapPlani {
  id: number
  kod: string
  ad: string
  tip: string
  is_active: boolean
  tenant: number
}

export interface FisSatiri {
  id?: number
  hesap: number
  hesap_kodu?: string | null
  borc: string
  alacak: string
  aciklama: string
}

export interface MuhasebeFisi {
  id: number
  fis_no: string
  fis_tarihi: string
  aciklama: string
  durum: 'taslak' | 'kayitli' | 'iptal'
  satirlar: FisSatiri[]
}

export interface MizanSatiri {
  hesap_kodu: string
  hesap_adi: string
  borc: string
  alacak: string
  bakiye: string
}

export const MUHASEBE_HESAP_TIPLERI: Record<string, string> = {
  aktif: 'Aktif',
  pasif: 'Pasif',
  gelir: 'Gelir',
  gider: 'Gider',
  nazim: 'Nazım',
}
