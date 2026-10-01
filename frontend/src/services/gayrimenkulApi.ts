/**
 * Gayrimenkul modülü API servisi — /api/v1/real-estate/gayrimenkuller/.
 */
import { del, get, patch, post } from './apiClient'
import type { Sayfali } from '@/types/api'
import type { Ada, Gayrimenkul, KatKarsiligiSenaryo, MalikMutabakati, Parsel } from '@/types/gayrimenkul'
import type { Proje } from '@/types/insaat'
import { insaatApi, tumunuGetir } from './insaatApi'

export { tumunuGetir }

function crudFactory<T>(kaynak: string) {
  return {
    liste: (params?: Record<string, unknown>) => get<Sayfali<T>>(kaynak, params),
    tek: (id: number) => get<T>(`${kaynak}${id}/`),
    olustur: (veri: Record<string, unknown>) => post<T>(kaynak, veri),
    guncelle: (id: number, veri: Record<string, unknown>) => patch<T>(`${kaynak}${id}/`, veri),
    sil: (id: number) => del<T>(`${kaynak}${id}/`),
  }
}

export const gayrimenkulApi = {
  gayrimenkuller: crudFactory<Gayrimenkul>('/real-estate/gayrimenkuller/'),
  adalar: crudFactory<Ada>('/real-estate/adalar/'),
  parseller: crudFactory<Parsel>('/real-estate/parseller/'),
  senaryolar: crudFactory<KatKarsiligiSenaryo>('/real-estate/kat-karsiligi-senaryolari/'),
  malikMutabakatlari: crudFactory<MalikMutabakati>('/real-estate/malik-mutabakatlari/'),
}

/** Form seçicileri için: aktif projeler (sayfalı kaynağın tamamı). */
export function tumProjeleriGetir(): Promise<Proje[]> {
  return tumunuGetir<Proje>(insaatApi.projeler.liste)
}
