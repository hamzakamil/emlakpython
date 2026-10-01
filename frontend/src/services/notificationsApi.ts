import { del, get, patch, post } from './apiClient'
import type { Sayfali } from '@/types/api'
import type { Hatirlatma, HatirlatmaPayload } from '@/types/notifications'

const kaynak = '/notifications/hatirlatmalar/'

export const notificationsApi = {
  liste: (params?: Record<string, unknown>) => get<Sayfali<Hatirlatma>>(kaynak, params),
  gunluk: () => get<Hatirlatma[]>(`${kaynak}gunluk/`),
  olustur: (veri: HatirlatmaPayload) => post<Hatirlatma>(kaynak, veri),
  guncelle: (id: number, veri: Partial<HatirlatmaPayload>) => patch<Hatirlatma>(`${kaynak}${id}/`, veri),
  sil: (id: number) => del<Hatirlatma>(`${kaynak}${id}/`),
  tamamla: (id: number) => post<Hatirlatma>(`${kaynak}${id}/tamamla/`),
  uret: () => post<{ uretilen: number }>(`${kaynak}uret/`),
}
