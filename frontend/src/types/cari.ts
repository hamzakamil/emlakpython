export interface Cari {
  id: number
  ad: string
  tip: string
  tur: string
  vergi_no?: string
  vergi_dairesi?: string
  tc_kimlik_no?: string
  ticaret_sicil_no?: string
  mersis_no?: string
  vergi_mukellefiyeti?: 'kdv_mukellefi' | 'kdv_istisna' | 'basit_usul' | 'vergi_mukellefi_degil'
  telefon_maskeli?: string | null
  iban_maskeli?: string | null
  telefon?: string
  telefonlar?: string[]
  iban?: string
  adres?: string
  fatura_adresi?: string
  sevk_adresi?: string
  il?: string
  ilce?: string
  posta_kodu?: string
  yetkili_kisi?: string
  yetkili_telefon?: string
  yetkili_kisiler?: Array<{ ad: string; telefon: string }>
  cep_telefonu?: string
  cep_telefonlari?: string[]
  eposta?: string
  epostalar?: string[]
  ulke?: string
  eski_adres?: string
  web_sitesi?: string
  banka_adi?: string
  sube_adi?: string
  odeme_sekli?: 'nakit' | 'havale' | 'cek' | 'senet' | 'kredi_karti' | 'takas'
  vade_gunu?: number
  iskonto_orani?: string
  risk_limiti?: string
  para_birimi?: 'TRY' | 'USD' | 'EUR' | 'GBP'
  muhasebe_hesap_kodu?: string
  e_fatura_profili?: 'e_fatura' | 'e_arsiv' | 'kagit'
  grup?: string
  proje?: number | null
  notlar?: string
  is_active: boolean
  tenant: number
}

export interface CariHareket {
  id: number
  cari: number
  cari_ad?: string | null
  yon: 'borc' | 'alacak'
  tutar: string
  aciklama: string
  islem_tarihi: string
  is_cancelled: boolean
  iptal_nedeni?: string
  muhasebe_fisi?: number | null
  muhasebelesti?: boolean
}

export interface CariOzet {
  borc: string
  alacak: string
  bakiye: string
}

export const CARI_TIPLERI: Record<string, string> = {
  kiraci: 'Kiracı',
  malik: 'Malik',
  tedarikci: 'Tedarikçi',
  taseron: 'Taşeron',
  diger: 'Diğer',
}

export const CARI_TURLERI: Record<string, string> = {
  bireysel: 'Bireysel',
  kurumsal: 'Kurumsal',
}
