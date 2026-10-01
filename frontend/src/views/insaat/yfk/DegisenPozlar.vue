<template>
  <div class="p-4">
    <div class="mb-6">
      <h2 class="text-xl font-bold mb-2">Degisen Pozlar</h2>
      <p class="text-gray-600">YFK donemler arasi degisen pozlari goruntuleyin.</p>
    </div>
    <div class="card">
      <div class="card-header flex justify-between items-center">
        <h3 class="card-title">YFK Degisen Pozlar ({{ pozList.length }})</h3>
        <div class="flex gap-2"><input v-model="searchQuery" type="text" placeholder="Poz no, ad veya degisim turu ile ara..." class="input w-64" /><select v-model="filterYil" class="input w-32"><option value="">Tum Yillar</option><option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option></select><select v-model="filterTip" class="input w-40"><option value="">Tum Turler</option><option value="YENI">Yeni Poz</option><option value="SILINEN">Silinen Poz</option><option value="FIYAT_DEGISIKLIGI">Fiyat Degisikligi</option><option value="DIGER">Diger</option></select></div>
      </div>
      <div class="card-body p-0">
        <div class="overflow-x-auto"><table class="table w-full"><thead><tr><th>Poz No</th><th>Ad</th><th>Grup</th><th>Birim</th><th>Eski Fiyat</th><th>Yeni Fiyat</th><th>Fark</th><th>Fark %</th><th>Degisim Turu</th><th>Yil</th><th>Kaynak</th><th>Islemler</th></tr></thead><tbody>
          <tr v-for="p in filteredPozList" :key="p.id"><td class="font-mono">{{ p.poz_no }}</td><td>{{ p.ad }}</td><td>{{ p.grup_kodu }} - {{ p.grup_adi }}</td><td>{{ p.birim }}</td><td class="font-mono">{{ formatCurrency(p.eski_birim_fiyat) }}</td><td class="font-mono">{{ formatCurrency(p.yeni_birim_fiyat) }}</td><td class="font-mono" :class="p.fark > 0 ? 'text-red-600' : p.fark < 0 ? 'text-green-600' : ''">{{ formatCurrency(p.fark) }}</td><td :class="p.fark_yuzde > 0 ? 'text-red-600' : p.fark_yuzde < 0 ? 'text-green-600' : ''">{{ p.fark_yuzde }}%</td><td><span class="badge" :class="degisimClass(p.degisim_turu)">{{ p.degisim_turu }}</span></td><td>{{ p.yil }}</td><td>{{ p.kaynak }}</td><td><button @click="showPozDetail(p)" class="btn btn-sm btn-ghost">Detay</button></td></tr>
          <tr v-if="filteredPozList.length === 0"><td colspan="12" class="text-center py-8 text-gray-500">Kayit bulunamadi</td></tr>
        </tbody></table></div>
        <div class="p-4 border-t flex justify-between items-center" v-if="pagination.total > 0"><p class="text-sm text-gray-600"> {{ (pagination.page - 1) * pagination.pageSize + 1 }} - {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} / {{ pagination.total }} kayit</p><div class="flex gap-2"><button @click="pagination.page > 1 && (pagination.page--, loadPozList())" :disabled="pagination.page <= 1" class="btn btn-sm btn-ghost">Onceki</button><button @click="pagination.page * pagination.pageSize < pagination.total && (pagination.page++, loadPozList())" :disabled="pagination.page * pagination.pageSize >= pagination.total" class="btn btn-sm btn-ghost">Sonraki</button></div></div>
      </div>
    </div>
    <div v-if="selectedPoz" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden">
        <div class="p-4 border-b flex justify-between items-center"><h3 class="text-lg font-bold">{{ selectedPoz.poz_no }} - {{ selectedPoz.ad }}</h3><button @click="selectedPoz = null" class="text-gray-500 hover:text-gray-700">X</button></div>
        <div class="p-4 overflow-y-auto max-h-[70vh]">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4"><div><strong>Poz No:</strong> {{ selectedPoz.poz_no }}</div><div><strong>Ad:</strong> {{ selectedPoz.ad }}</div><div><strong>Grup Kodu:</strong> {{ selectedPoz.grup_kodu }}</div><div><strong>Grup Adi:</strong> {{ selectedPoz.grup_adi }}</div><div><strong>Birim:</strong> {{ selectedPoz.birim }}</div><div><strong>Degisim Turu:</strong> <span class="badge" :class="degisimClass(selectedPoz.degisim_turu)">{{ selectedPoz.degisim_turu }}</span></div><div><strong>Eski Birim Fiyat:</strong> {{ formatCurrency(selectedPoz.eski_birim_fiyat) }}</div><div><strong>Yeni Birim Fiyat:</strong> {{ formatCurrency(selectedPoz.yeni_birim_fiyat) }}</div><div><strong>Fark:</strong> <span :class="selectedPoz.fark > 0 ? 'text-red-600' : selectedPoz.fark < 0 ? 'text-green-600' : ''">{{ formatCurrency(selectedPoz.fark) }}</span></div><div><strong>Fark %:</strong> <span :class="selectedPoz.fark_yuzde > 0 ? 'text-red-600' : selectedPoz.fark_yuzde < 0 ? 'text-green-600' : ''">{{ selectedPoz.fark_yuzde }}%</span></div><div><strong>Yil:</strong> {{ selectedPoz.yil }}</div><div><strong>Kaynak:</strong> {{ selectedPoz.kaynak }}</div></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useInsaatStore } from '@/stores/insaat'
import { useToast } from '@/composables/useToast'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

const insaatStore = useInsaatStore()
const toast = useToast()

const loading = ref(false)
const pozList = ref([])
const searchQuery = ref('')
const filterYil = ref('')
const filterTip = ref('')
const selectedPoz = ref(null)
const availableYears = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const filteredPozList = computed(() => {
  let result = pozList.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(p => p.poz_no.toLowerCase().includes(q) || p.ad.toLowerCase().includes(q) || p.degisim_turu.toLowerCase().includes(q))
  }
  if (filterYil.value) result = result.filter(p => p.yil == filterYil.value)
  if (filterTip.value) result = result.filter(p => p.degisim_turu == filterTip.value)
  return result
})

const degisimClass = (tur) => {
  const map = { YENI: 'badge-success', SILINEN: 'badge-error', FIYAT_DEGISIKLIGI: 'badge-warning', DIGER: 'badge-info' }
  return map[tur] || 'badge-secondary'
}
const formatCurrency = (val) => {
  if (!val) return '-'
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 2 }).format(val)
}

onMounted(async () => {
  await loadPozList()
  await loadAvailableYears()
})

async function loadPozList() {
  loading.value = true
  try {
    const res = await insaatStore.fetchYfkDegisenPozlar({ page: pagination.page, page_size: pagination.pageSize, yil: filterYil.value || undefined, degisim_turu: filterTip.value || undefined, search: searchQuery.value || undefined })
    pozList.value = res.results || res
    pagination.total = res.count || res.length
  } catch (e) {
    toast.error('Degisen pozlar yuklenemedi')
  } finally {
    loading.value = false
  }
}

async function loadAvailableYears() {
  try {
    const res = await insaatStore.fetchYfkDegisenPozlar({ page_size: 1000 })
    const years = [...new Set((res.results || res).map(p => p.yil).filter(Boolean))].sort((a, b) => b - a)
    availableYears.value = years
  } catch (e) {}
}

async function showPozDetail(poz) {
  loading.value = true
  try {
    const detail = await insaatStore.fetchYfkDegisenPozDetail(poz.id)
    selectedPoz.value = detail
  } catch (e) { toast.error('Detay yuklenemedi') }
  finally { loading.value = false }
}

const Math = window.Math
</script>
