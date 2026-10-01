<template>
  <div class="p-4">
    <div class="mb-6">
      <h2 class="text-xl font-bold mb-2">Guncelleme Gecmisi</h2>
      <p class="text-gray-600">YFK guncelleme islemlerinin gecmisini goruntuleyin.</p>
    </div>
    <div class="card">
      <div class="card-header flex justify-between items-center">
        <h3 class="card-title">YFK Guncelleme Gecmisi ({{ gecmisList.length }})</h3>
        <div class="flex gap-2"><input v-model="searchQuery" type="text" placeholder="Poz no, islem turu veya aciklama ile ara..." class="input w-64" /><select v-model="filterYil" class="input w-32"><option value="">Tum Yillar</option><option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option></select><select v-model="filterIslem" class="input w-40"><option value="">Tum Islemler</option><option value="IMPORT">Import</option><option value="MANUEL">Manuel</option><option value="IPTAL">Iptal</option></select></div>
      </div>
      <div class="card-body p-0">
        <div class="overflow-x-auto"><table class="table w-full"><thead><tr><th>Tarih</th><th>Islem Turu</th><th>Veri Turu</th><th>Poz No</th><th>Ad</th><th>Eski Deger</th><th>Yeni Deger</th><th>Yil</th><th>Donem</th><th>Kaynak</th><th>Kullanici</th><th>Aciklama</th></tr></thead><tbody>
          <tr v-for="g in filteredGecmisList" :key="g.id"><td>{{ formatDateTime(g.tarih) }}</td><td><span class="badge" :class="islemClass(g.islem_turu)">{{ g.islem_turu }}</span></td><td>{{ g.veri_turu }}</td><td class="font-mono">{{ g.poz_no }}</td><td>{{ g.ad }}</td><td>{{ g.eski_deger }}</td><td>{{ g.yeni_deger }}</td><td>{{ g.yil }}</td><td>{{ g.donem || '-' }}</td><td>{{ g.kaynak }}</td><td>{{ g.kullanici }}</td><td>{{ g.aciklama }}</td></tr>
          <tr v-if="filteredGecmisList.length === 0"><td colspan="12" class="text-center py-8 text-gray-500">Kayit bulunamadi</td></tr>
        </tbody></table></div>
        <div class="p-4 border-t flex justify-between items-center" v-if="pagination.total > 0"><p class="text-sm text-gray-600"> {{ (pagination.page - 1) * pagination.pageSize + 1 }} - {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} / {{ pagination.total }} kayit</p><div class="flex gap-2"><button @click="pagination.page > 1 && (pagination.page--, loadGecmisList())" :disabled="pagination.page <= 1" class="btn btn-sm btn-ghost">Onceki</button><button @click="pagination.page * pagination.pageSize < pagination.total && (pagination.page++, loadGecmisList())" :disabled="pagination.page * pagination.pageSize >= pagination.total" class="btn btn-sm btn-ghost">Sonraki</button></div></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useInsaatStore } from '@/stores/insaat'
import { useToast } from '@/composables/useToast'

const insaatStore = useInsaatStore()
const toast = useToast()

const loading = ref(false)
const gecmisList = ref([])
const searchQuery = ref('')
const filterYil = ref('')
const filterIslem = ref('')
const availableYears = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const filteredGecmisList = computed(() => {
  let result = gecmisList.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(g => g.poz_no.toLowerCase().includes(q) || g.ad.toLowerCase().includes(q) || g.aciklama.toLowerCase().includes(q) || g.islem_turu.toLowerCase().includes(q))
  }
  if (filterYil.value) result = result.filter(g => g.yil == filterYil.value)
  if (filterIslem.value) result = result.filter(g => g.islem_turu == filterIslem.value)
  return result
})

const islemClass = (tur) => {
  const map = { IMPORT: 'badge-primary', MANUEL: 'badge-success', IPTAL: 'badge-error' }
  return map[tur] || 'badge-secondary'
}
const formatDateTime = (val) => {
  if (!val) return '-'
  return new Date(val).toLocaleString('tr-TR')
}

onMounted(async () => {
  await loadGecmisList()
  await loadAvailableYears()
})

async function loadGecmisList() {
  loading.value = true
  try {
    const res = await insaatStore.fetchYfkGuncellemeGecmisi({ page: pagination.page, page_size: pagination.pageSize, yil: filterYil.value || undefined, islem_turu: filterIslem.value || undefined, search: searchQuery.value || undefined })
    gecmisList.value = res.results || res
    pagination.total = res.count || res.length
  } catch (e) {
    toast.error('Guncelleme gecmisi yuklenemedi')
  } finally {
    loading.value = false
  }
}

async function loadAvailableYears() {
  try {
    const res = await insaatStore.fetchYfkGuncellemeGecmisi({ page_size: 1000 })
    const years = [...new Set((res.results || res).map(g => g.yil).filter(Boolean))].sort((a, b) => b - a)
    availableYears.value = years
  } catch (e) {}
}

const Math = window.Math
</script>
