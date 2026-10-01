export type HatirlatmaSeviyesi = 'kritik' | 'uyari' | 'bilgi'
export type HatirlatmaDurumu = 'bekliyor' | 'tamamlandi' | 'iptal'
export type HatirlatmaTekrarlama = 'yok' | 'gunluk' | 'haftalik' | 'aylik' | 'yillik'

export interface Hatirlatma {
  id: number
  baslik: string
  aciklama: string
  ilgili_app: string
  ilgili_model: string
  ilgili_kayit_id: number | null
  hatirlatma_tarihi: string
  seviye: HatirlatmaSeviyesi
  durum: HatirlatmaDurumu
  sorumlu_kullanici: number | null
  tekrarlama: HatirlatmaTekrarlama
}

export interface HatirlatmaPayload {
  baslik: string
  aciklama?: string
  ilgili_app?: string
  ilgili_model?: string
  ilgili_kayit_id?: number | null
  hatirlatma_tarihi: string
  seviye?: HatirlatmaSeviyesi
  durum?: HatirlatmaDurumu
  sorumlu_kullanici?: number | null
  tekrarlama?: HatirlatmaTekrarlama
}
