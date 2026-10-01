export interface SantiyeGunlugu {
  id: number
  proje: number
  proje_kodu?: string
  tarih: string
  hava_durumu: string
  sicaklik_min: number | null
  sicaklik_max: number | null
  isci_sayisi: number
  isci_tipi: string
  calisma_saati: number
  yapilan_isler: string
  malzeme_giris: string
  malzeme_cikis: string
  ekipmanlar: string
  sorunlar: string
  notlar: string
  created_at?: string
  updated_at?: string
}

export interface KaliteKontrol {
  id: number
  proje: number
  proje_kodu?: string
  poz: number | null
  poz_no?: string | null
  tarih: string
  kontrol_tipi: string
  kriter: string
  durum: 'beklemede' | 'gecti' | 'kaldi' | 'onaylandi' | 'reddedildi'
  olculen_deger: string
  beklenen_deger: string
  tolerek_aralik: string
  aciklama: string
  duzeltici_faaliyet: string
}

export const KALITE_SONUCLARI: Record<string, string> = {
  beklemede: 'Beklemede',
  gecti: 'Geçti',
  kaldi: 'Kaldı',
  onaylandi: 'Onaylandı',
  reddedildi: 'Reddedildi',
}
