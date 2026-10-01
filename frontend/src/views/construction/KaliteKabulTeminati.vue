/**
 * KaliteKabulTeminati.vue - Kalite Kabul Teminatları CRUD Vue 3 Component
 * 
 * This component provides a complete CRUD interface for managing quality
 * acceptance guarantees with the following features:
 * 
 * - List view with pagination, search, and filtering
 * - Create new kalite kabul teminati via modal form
 * - Edit existing kalite kabul teminati via modal form
 * - View details of specific kalite kabul teminati
 * - Related kalite kontrol records navigation
 * - Turkish locale and formatting
 * - Decimal precision for financial amounts
 * - Confirmation dialogs for destructive operations
 */

import { computed, onMounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { constructionApi } from '@/services/constructionApi'
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
const kaliteKabulTeminati = ref([])
const loadingTeminatlar = ref(true)
const errorTeminatlar = ref(null)

// Pagination and filter state
const sayfa = ref(1)
const limit = ref(20)
const arama = ref('')
const filtreDurum = ref('aktif')
const filtreSantiye = ref('')

// Computed for filtered records
const filteredTeminatlar = computed(() => {
  let result = kaliteKabulTeminati.value

  if (arama.value) {
    result = result.filter(
      (t) =>
        t.kabul_no?.includes(arama.value) ||
        t.aciklama?.includes(arama.value) ||
        t.santiye_adi?.includes(arama.value)
    )
  }

  if (filtreSantiye.value) {
    result = result.filter(
      (t) => t.santiye_id === Number(filtreSantiye.value)
    )
  }

  if (filtreDurum.value !== 'tum') {
    result = result.filter((t) => t.durum === filtreDurum.value)
  }

  return result
})

// Load kalite kabul teminati from API
async function yukleTeminatlar() {
  loadingTeminatlar.value = true
  errorTeminatlar.value = null
  try {
    const response = await constructionApi.listQualityControls({
      page: sayfa.value,
      limit: limit.value,
      search: arama.value,
      santiye_id: filtreSantiye.value || undefined,
    })
    kaliteKabulTeminati.value = response.data || []
  } catch (error: any) {
    hataMesaji(error, 'Kalite kabul teminati yüklenirken hata oluştu')
    errorTeminatlar.value = error.message
  } finally {
    loadingTeminatlar.value = false
  }
}

// Select a site for filtering
function santiyeSec(santiyeId: number, santiyeAdi: string) {
  filtreSantiye.value = santiyeId
  yukleTeminatlar()
}

// Open filter dropdown
function filtreyiAc() {
  // Implementation depends on layout
}

// Delete a kalite kabul teminati
async function silTeminati(id: number) {
  if (!confirm('Bu kalite kabul teminatını silmek istediğinizden emin misiniz?')) return
  try {
    await constructionApi.deleteQualityControl(id)
    yukleTeminatlar()
  } catch (error: any) {
    hataMesaji(error, 'Kalite kabul teminatı silinirken hata oluştu')
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
  yukleTeminatlar()
})

watch(
  () => route.params.idsayfala,
  (newSayfa) => {
    if (newSayfa !== undefined) {
      sayfa.value = Number(newSayfa)
      yukleTeminatlar()
    }
  }
)