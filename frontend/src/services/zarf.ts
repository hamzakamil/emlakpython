/**
 * Yanıt zarfı çözücü — backend her yanıtı {success, data, message, errors}
 * zarfıyla döner; burada açılır, success=false ise ApiHatasi fırlatılır.
 */
import type { AlanHatalari, Zarf } from '@/types/api'

export class ApiHatasi extends Error {
  readonly durum: number
  readonly hatalar: AlanHatalari | null

  constructor(durum: number, mesaj: string, hatalar: AlanHatalari | null = null) {
    super(mesaj)
    this.name = 'ApiHatasi'
    this.durum = durum
    this.hatalar = hatalar
  }
}

function zarfMi<T>(deger: unknown): deger is Zarf<T> {
  return (
    typeof deger === 'object' &&
    deger !== null &&
    'success' in deger &&
    typeof (deger as Zarf).success === 'boolean'
  )
}

/** Zarflı gövdeyi açar; success=false veya zarf dışı yanıtta ApiHatasi fırlatır. */
export function zarfAc<T>(govde: unknown, durum: number): T {
  if (!zarfMi<T>(govde)) {
    throw new ApiHatasi(durum, 'Beklenmeyen yanıt biçimi (zarf yok).', null)
  }
  if (!govde.success) {
    throw new ApiHatasi(durum, govde.message || 'Bilinmeyen bir hata oluştu.', govde.errors ?? null)
  }
  return govde.data
}
