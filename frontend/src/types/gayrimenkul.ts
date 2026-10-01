/**
 * Gayrimenkul modülü tipleri — backend RealEstateSerializer ile senkron
 * (real_estate/serializers.py, fields=__all__).
 */

/** RealEstate.Durum choices. */
export type GayrimenkulDurumu = 'available' | 'rented' | 'sold' | 'reserved' | 'maintenance'

export interface Gayrimenkul {
  id: number
  ad: string
  proje: number | null
  /** read-only gösterim alanı (proje.proje_kodu) */
  proje_kodu: string | null
  blok: string
  kat: string
  daire_no: string
  /** JSON'da string olarak gelir (Decimal); boşsa null */
  brut_m2: string | null
  durum: GayrimenkulDurumu
  tapu_adi: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export const GAYRIMENKUL_DURUMLARI: Record<GayrimenkulDurumu, string> = {
  available: 'Müsait',
  rented: 'Kirada',
  sold: 'Satıldı',
  reserved: 'Rezerve',
  maintenance: 'Bakımda',
}

export interface Ada {
  id: number
  ada_no: string
  mahalle: string
  ilce: string
  il: string
  is_active: boolean
}

export interface Parsel {
  id: number
  ada: number
  ada_no?: string
  ilce?: string
  parsel_no: string
  pafta: string
  alan_m2: string | null
  imar_durumu: string
  kat_karsiligi_orani: string
  malik_sayisi: number
  is_active: boolean
}

export const IMAR_DURUMLARI: Record<string, string> = {
  belirsiz: 'Belirsiz',
  imara_uygun: 'İmara Uygun',
  imarli: 'İmarlı',
  imar_hakki_verilmis: 'İmar Hakkı Verilmiş',
  plan_degisikligi: 'Plan Değişikliği',
}

export interface KatKarsiligiSenaryo {
  id: number
  parsel: number
  parsel_no?: string
  senaryo_adi: string
  arsa_pay_orani: string
  kat_karsiligi_orani: string
  bagimsiz_bolum_m2: string
  toplam_birim_sayisi: number
  is_active: boolean
}

export type MalikOyDurumu = 'bekliyor' | 'kabul' | 'red' | 'bilinmiyor'

export interface MalikMutabakati {
  id: number
  senaryo: number
  senaryo_adi?: string
  malik_adi: string
  pay_orani: string
  oy_durumu: MalikOyDurumu
  notlar: string
  created_at: string
  updated_at: string
}

export const MALIK_OY_DURUMLARI: Record<MalikOyDurumu, string> = {
  bekliyor: 'Bekliyor',
  kabul: 'Kabul',
  red: 'Red',
  bilinmiyor: 'Bilinmiyor',
}
