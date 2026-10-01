import { del, get, patch, post } from './apiClient'
import type { Sayfali } from '@/types/api'
import type { Hakedis } from '@/types/insaat'
import type { IFCImportJob } from '@/types/insaat'

/** Santiye günlüğü tipi */
export interface SantiyeGunlugu {
  id: number
  gunluk_no: string
  santiye_id: number
  santiye_adi: string
  tarih: string // YYYY-MM-DD
  hava_durumu: string
  sicaklik_min: number | null
  sicaklik_max: number | null
  isci_sayisi: number
  isci_tipi: string
  calisma_saati: number
  yapilan_isler: string
  malzeme_giris: string | null
  malzeme_cikis: string | null
  ekipmanlar: string | null
  sorunlar: string | null
  aciklama: string
  is_active: boolean
  created_at: string
  updated_at: string
}
export interface SantiyeCheckIn { id: number; proje: number; proje_kodu?: string; kullanici_adi?: string; giris_zamani: string; cikis_zamani: string | null; notlar: string }
export interface MalzemeHareketi { id: number; proje: number; proje_kodu?: string; malzeme: number; malzeme_adi?: string; yon: 'giris' | 'cikis'; miktar: number; birim: string; qr_kodu: string; gerceklesme_zamani: string; kaydeden_adi?: string; notlar: string }

/** Kalite kontrol tipi */
export interface KaliteKontrol {
  id: number
  kontrol_no: string
  santiye_id: number
  santiye_adi: string
  poz_id: number | null
  poz_adi: string | null
  poz_kod: string | null
  kontrol_tipi: string
  beklenen_deger: string
  olculen_deger: string
  tolerek_aralik: string
  durum: string
  kontrol_eden_adi: string | null
  onaylayan_adi: string | null
  onay_tarihi: string | null
  aciklama: string
  is_active: boolean
  created_at: string
  updated_at: string
}

/** CRUD factory for a resource */
function crudFactory<T>(kaynak: string) {
  return {
    liste: (params?: Record<string, unknown>) => get<Sayfali<T>>(kaynak, params),
    tek: (id: number) => get<T>(`${kaynak}${id}/`),
    olustur: (veri: Record<string, unknown>) => post<T>(kaynak, veri),
    guncelle: (id: number, veri: Record<string, unknown>) => patch<T>(`${kaynak}${id}/`, veri),
    sil: (id: number) => del<T>(`${kaynak}${id}/`),
  }
}

// API instances for each entity
const santiyeGunlukleriApi = crudFactory<SantiyeGunlugu>('/construction/santiye-gunlukleri/')
const hakedislerApi = crudFactory<Hakedis>('/construction/hakedisler/')
const kaliteKontrolleriApi = crudFactory<KaliteKontrol>('/construction/kalite-kontrolleri/')
const checkinApi = crudFactory<SantiyeCheckIn>('/construction/santiye-checkinleri/')
const malzemeHareketleriApi = crudFactory<MalzemeHareketi>('/construction/malzeme-hareketleri/')

/** İnşaat modülü API servisi — /api/v1/construction/ kaynakları. */
export const constructionApi = {
  // Santiye günlükleri
  listDailyLogs: santiyeGunlukleriApi.liste,
  deleteDailyLog: santiyeGunlukleriApi.sil,
  createDailyLog: santiyeGunlukleriApi.olustur,
  updateDailyLog: santiyeGunlukleriApi.guncelle,

  // Hakedisler (taşeron hakedişleri)
  listSubcontractorProgressBillings: hakedislerApi.liste,
  deleteSubcontractorProgressBilling: hakedislerApi.sil,
  createSubcontractorProgressBilling: hakedislerApi.olustur,
  updateSubcontractorProgressBilling: hakedislerApi.guncelle,

  // Kalite kontrolleri
  listQualityControls: kaliteKontrolleriApi.liste,
  deleteQualityControl: kaliteKontrolleriApi.sil,
  createQualityControl: kaliteKontrolleriApi.olustur,
  updateQualityControl: kaliteKontrolleriApi.guncelle,

  // Filter dropdowns
  listSites: () => get<Sayfali<{ id: number; ad: string }>>('/construction/santiyeler/'),
  listSubcontractors: () => get<Sayfali<{ id: number; ad: string }>>('/construction/taseronlar/'),
  listItems: () => get<Sayfali<{ id: number; ad: string; kod: string }>>('/construction/pozlar/'),
  checkinler: checkinApi,
  malzemeHareketleri: malzemeHareketleriApi,
  ifcImportlari: {
    liste: (params?: Record<string, unknown>) => get<Sayfali<IFCImportJob>>('/construction/ifc-importlari/', params),
    yukle: (form: FormData) => post<IFCImportJob>('/construction/ifc-importlari/', form),
    isle: (id: number) => post<IFCImportJob>(`/construction/ifc-importlari/${id}/process/`),
  },
}