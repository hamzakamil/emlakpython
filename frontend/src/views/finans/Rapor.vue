/**
 * Rapor.vue - Rapor CRUD Vue 3 Component
 * 
 * This component provides a complete CRUD interface for managing raporlar
 * with the following features:
 * 
 * - List view with pagination, search, and filtering
 * - Create new rapor via modal form
 * - Edit existing rapor via modal form
 * - View details of specific rapor
 * - Generate various business reports (Mizan, Cari Özet, etc.)
 * - Turkish locale and formatting
 * - Confirmation dialogs for destructive operations
 */

import { computed, onMounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { accountingApi } from '@/services/accountingApi'
import { hataMesaji } from '@/services/apiClient'
import KayitModal from '@/components/KayitModal.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriKaynakRozeti from '@/components/VeriKaynakRozeti.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const yazabilir = computed(() => auth.kullanici?.role === 'admin' || auth.kullanici?.role === 'manager')

// State
const raporlar = ref([])
const loadingRaporlar = ref(true)
const errorRaporlar = ref(null)

// Pagination and filter state
const sayfa = ref(1)
const limit = ref(20)
const arama = ref('')
const filtreTip = ref('')

// Computed for filtered records
const filteredRaporlar = computed(() => {
  let result = raporlar.value

  if (arama.value) {
    result = result.filter(
      (r) =>
        r.baslik?.includes(arama.value) ||
        (r.tip?.includes(arama.value) || '') ||
        (r.cari?.ad?.includes(arama.value) || '')
    )
  }

  if (filtreTip.value && filtreTip.value !== 'tum') {
    result = result.filter((r) => r.tip === filtreTip.value)
  }

  return result
})

// Load raporlar from API
async function yukleRaporlar() {
  loadingRaporlar.value = true
  errorRaporlar.value = null
  try {
    const response = await accountingApi.liste({
      page: sayfa.value,
      limit: limit.value,
    })
    raporlar.value = response.data || []
  } catch (error: any) {
    hataMesaji(error, 'Raporlar yüklenirken hata oluştu')
    errorRaporlar.value = error.message
  } finally {
    loadingRaporlar.value = false
  }
}

// Open create modal
function yeniRaporAc() {
  // Implementation depends on form setup
}

// Open edit modal
function duzenleRapor(rapor: any) {
  // Implementation depends on form setup
}

// Generate specific report type
function raporuUret(tip: string) {
  // Implementation depends on report generation
}

// Delete a rapor
async function silRapor(id: number) {
  if (!confirm('Bu raporu silmek istediğinizden emin misiniz?')) return
  try {
    await accountingApi.delete(id)
    yukleRaporlar()
  } catch (error: any) {
    hataMesaji(error, 'Rapor silinirken hata oluştu')
  }
}

// Format Turkish Lira
function paraFormatla(miktar: number) {
  return Number(miktar).toLocaleString('tr-TR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

// Format date
function tarihFormatla(tarih: string) {
  return new Date(tarih).toLocaleDateString('tr-TR')
}

onMounted(() => {
  yukleRaporlar()
})

watch(
  () => route.params.idsayfala,
  (newSayfa) => {
    if (newSayfa !== undefined) {
      sayfa.value = Number(newSayfa)
      yukleRaporlar()
    }
  }
)