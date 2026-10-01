export type FaturaDurumu = 'taslak' | 'aktif' | 'odendi' | 'iptal'
export type FaturaTuru = 'satis' | 'kira' | 'hakedis' | 'iade' | 'aidat' | 'hizmet' | 'proforma' | 'alis'
export type ParaBirimi = 'TRY' | 'USD' | 'EUR' | 'GBP'
export type EFaturaDurum = 'gonderilmedi' | 'gonderildi' | 'kabul' | 'red'
export type Senaryo = 'e_fatura' | 'e_arsiv' | 'kagit'

export interface Fatura {
  id: number
  No: string
  cari: number | null
  cari_ad?: string | null
  kasa_banka_hesabi: number | null
  hesap_ad?: string | null
  durum: FaturaDurumu
  tarih: string
  vade_tarihi: string | null
  tutar: string
  alacakli: boolean
  aciklama: string
  fatura_turu?: FaturaTuru
  senaryo?: Senaryo
  para_birimi?: ParaBirimi
  kur?: string
  kdv_dahil_mi?: boolean
  iskonto_tutari?: string
  odenen_tutar?: string
  iade_faturasi?: number | null
  e_fatura_uuid?: string
  e_fatura_durum?: EFaturaDurum
  matrah?: string
  kdv?: string
  tevkifat?: string
  stopaj?: string
  odenecek?: string
  tl_karsiligi?: string
  kalemler: FaturaKalemi[]
  ara_toplam?: string
  kdv_tutari?: string
  tevkifat_tutari?: string
  stopaj_tutari?: string
  created_at?: string
  updated_at?: string
}

export interface FaturaKalemi {
  id?: number
  aciklama: string
  miktar: string
  birim: string
  birim_fiyat: string
  kdv_orani: string
  tevkifat_orani: string
  stopaj_orani: string
  poz_no?: string
  iskonto_orani?: string
  ara_toplam?: string
  satir_toplami?: string
}

export interface VergiProfili {
  id: number
  kod: string
  ad: string
  kdv_orani: string
  tevkifat_orani: string
  stopaj_orani: string
  is_active: boolean
}

export const FATURA_DURUMLARI: Record<FaturaDurumu, string> = {
  taslak: 'Taslak',
  aktif: 'Aktif',
  odendi: 'Ödendi',
  iptal: 'İptal',
}

export const FATURA_TURLERI: Record<FaturaTuru, string> = {
  satis: 'Satış', kira: 'Kira', hakedis: 'Hakediş', iade: 'İade',
  aidat: 'Aidat', hizmet: 'Hizmet', proforma: 'Proforma', alis: 'Alış',
}

export const PARA_BIRIMLERI: ParaBirimi[] = ['TRY', 'USD', 'EUR', 'GBP']