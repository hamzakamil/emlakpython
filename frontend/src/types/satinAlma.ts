/** FAZ 3A — Satın alma tipleri (backend: purchasing). */

export type TalepDurumu =
  | 'taslak'
  | 'onaya_gonderildi'
  | 'onaylandi'
  | 'reddedildi'
  | 'siparise_donustu'
  | 'iptal'

export type SiparisDurumu =
  | 'taslak'
  | 'onay_bekliyor'
  | 'onaylandi'
  | 'kismi_teslim'
  | 'tamamlandi'
  | 'iptal'

export const TALEP_DURUMLARI: { deger: TalepDurumu; etiket: string }[] = [
  { deger: 'taslak', etiket: 'Taslak' },
  { deger: 'onaya_gonderildi', etiket: 'Onaya Gönderildi' },
  { deger: 'onaylandi', etiket: 'Onaylandı' },
  { deger: 'reddedildi', etiket: 'Reddedildi' },
  { deger: 'siparise_donustu', etiket: 'Siparişe Dönüştü' },
  { deger: 'iptal', etiket: 'İptal' },
]

export const SIPARIS_DURUMLARI: { deger: SiparisDurumu; etiket: string }[] = [
  { deger: 'taslak', etiket: 'Taslak' },
  { deger: 'onay_bekliyor', etiket: 'Onay Bekliyor' },
  { deger: 'onaylandi', etiket: 'Onaylandı' },
  { deger: 'kismi_teslim', etiket: 'Kısmi Teslim' },
  { deger: 'tamamlandi', etiket: 'Tamamlandı' },
  { deger: 'iptal', etiket: 'İptal' },
]

export interface TalepKalemi {
  id: number
  talep: number
  malzeme: number
  malzeme_adi?: string
  malzeme_kodu?: string
  poz: number | null
  poz_no?: string | null
  mahal: number | null
  mahal_kodu?: string | null
  miktar: string
  birim: string
  ihtiyac_tarihi: string | null
  tahmini_birim_fiyat: string | null
  secili_teklif: number | null
  aciklama: string
  is_active: boolean
}

export interface SatinAlmaTalebi {
  id: number
  proje: number
  proje_kodu?: string
  proje_adi?: string
  talep_no: string
  tarih: string
  talep_sahibi: number
  talep_sahibi_adi?: string
  durum: TalepDurumu
  aciklama: string
  is_active: boolean
  kalemler: TalepKalemi[]
}

export interface SiparisKalemi {
  id: number
  siparis: number
  malzeme: number
  malzeme_adi?: string
  malzeme_kodu?: string
  poz: number | null
  poz_no?: string | null
  mahal: number | null
  mahal_kodu?: string | null
  miktar: string
  birim: string
  birim_fiyat: string
  toplam_tutar?: string | null
  kaynak_teklif: number | null
  aciklama: string
  is_active: boolean
}

export type MalKabulDurumu = 'taslak' | 'onaylandi' | 'kismi_teslim' | 'tamamlandi' | 'iptal'

export const MAL_KABUL_DURUMLARI: { deger: MalKabulDurumu; etiket: string }[] = [
  { deger: 'taslak', etiket: 'Taslak' },
  { deger: 'onaylandi', etiket: 'Onaylandı' },
  { deger: 'kismi_teslim', etiket: 'Kısmi Teslim' },
  { deger: 'tamamlandi', etiket: 'Tamamlandı' },
  { deger: 'iptal', etiket: 'İptal' },
]

export interface Depo {
  id: number
  kod: string
  ad: string
  aciklama: string
  is_active: boolean
}

export interface MalKabulKalemi {
  id: number
  mal_kabul: number
  siparis_kalemi: number
  malzeme: number
  malzeme_adi?: string
  malzeme_kodu?: string
  siparis_miktari?: string | null
  kabul_miktari: string
  red_miktari: string
  birim: string
  birim_fiyat_snapshot?: string | null
  aciklama: string
  is_active: boolean
}

export interface MalKabulMuhasebe {
  fatura_no: string | null
  cari_hareket_id: number | null
  fis_no: string | null
}

export interface MalKabul {
  id: number
  siparis: number
  proje: number
  proje_kodu?: string
  depo: number
  depo_kodu?: string
  belge_no: string
  kabul_tarihi: string
  durum: MalKabulDurumu
  aciklama: string
  is_active: boolean
  kalemler: MalKabulKalemi[]
  muhasebe?: MalKabulMuhasebe | null
}

export interface StokHareketi {
  id: number
  depo: number
  depo_kodu?: string
  malzeme: number
  malzeme_adi?: string
  hareket_tipi: string
  miktar: string
  birim: string
  maliyet: string
  tarih: string
  aciklama: string
  is_active: boolean
}

export interface StokHesapEsleme {
  id: number
  malzeme: number | null
  malzeme_kodu?: string | null
  malzeme_adi?: string | null
  hesap_turu: 'stok' | 'kdv'
  hesap: number
  hesap_kodu?: string
  hesap_adi?: string
  is_active: boolean
}

export interface SatinAlmaSiparisi {
  id: number
  siparis_no: string
  tedarikci: number
  tedarikci_adi?: string
  proje: number
  proje_kodu?: string
  proje_adi?: string
  kaynak_talep: number | null
  tarih: string
  teslim_tarihi: string | null
  para_birimi: string
  kur: string
  durum: SiparisDurumu
  aciklama: string
  is_active: boolean
  kalemler: SiparisKalemi[]
}
