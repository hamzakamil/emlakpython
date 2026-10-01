/**
 * Liste durumu composable'ı — CRUD listeleri için ortak yükleme/arama/sayfalama.
 * Backend: DRF sayfalama (PAGE_SIZE=25) + search/filter (ViewSet search_fields).
 */
import { ref, type Ref } from 'vue'
import { get, hataMesaji } from '@/services/apiClient'
import type { Sayfali } from '@/types/api'

export function useKayitListesi<T>(
  kaynak: string,
  baslangicFiltreleri: Record<string, unknown> = {},
) {
  const kayitlar = ref<T[]>([]) as Ref<T[]>
  const yukleniyor = ref(false)
  const hata = ref('')
  const toplam = ref(0)
  const sayfa = ref(1)
  const arama = ref('')
  const filtreler = ref<Record<string, unknown>>({ ...baslangicFiltreleri })

  async function yukle(): Promise<void> {
    yukleniyor.value = true
    hata.value = ''
    try {
      const params: Record<string, unknown> = { ...filtreler.value }
      const aranan = arama.value.trim()
      if (aranan) params.search = aranan
      if (sayfa.value > 1) params.page = sayfa.value
      const veri = await get<Sayfali<T>>(kaynak, params)
      kayitlar.value = veri.results
      toplam.value = veri.count
    } catch (bilinmeyen) {
      hata.value = hataMesaji(bilinmeyen)
    } finally {
      yukleniyor.value = false
    }
  }

  function aramaYap(): Promise<void> {
    sayfa.value = 1
    return yukle()
  }

  function filtreleriSifirla(): Promise<void> {
    filtreler.value = { ...baslangicFiltreleri }
    arama.value = ''
    sayfa.value = 1
    return yukle()
  }

  return { kayitlar, yukleniyor, hata, toplam, sayfa, arama, filtreler, yukle, aramaYap, filtreleriSifirla }
}
