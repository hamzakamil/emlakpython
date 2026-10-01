<template>
  <div class="p-4">
    <div class="mb-6">
      <h2 class="text-xl font-bold mb-2">Analiz (Islem) Guncelleme</h2>
      <p class="text-gray-600">YFK analiz/islem verilerini ice aktar veya guncelleyin.</p>
    </div>
    <div class="card mb-6">
      <div class="card-header"><h3 class="card-title">Analiz Verisi Yukle</h3></div>
      <div class="card-body">
        <form @submit.prevent="handleImport">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div><label class="block text-sm font-medium mb-1">Yil *</label><input v-model.number="importForm.yil" type="number" min="2020" max="2030" class="input w-full" required /></div>
            <div><label class="block text-sm font-medium mb-1">Donem (Ay)</label><select v-model.number="importForm.donem" class="input w-full"><option value="">Yillik</option><option v-for="n in 12" :key="n" :value="n">{{ n }}</option></select></div>
            <div><label class="block text-sm font-medium mb-1">Kaynak</label><input v-model="importForm.kaynak" type="text" placeholder="Orn. YFK 2026 Analiz Tebligi" class="input w-full" /></div>
            <div><label class="block text-sm font-medium mb-1">Kaynak URL</label><input v-model="importForm.kaynak_url" type="url" placeholder="https://..." class="input w-full" /></div>
          </div>
          <div class="mb-4">
            <label class="block text-sm font-medium mb-1">CSV Dosyasi *</label>
            <input ref="fileInput" type="file" accept=".csv" @change="onFileSelect" class="input w-full" required />
            <p class="text-sm text-gray-500 mt-1">CSV sutunlari: poz_no, malzeme_tipi, malzeme_kodu, malzeme_adi, birim, miktar, birim_fiyat, kaynak, kaynak_url, yayin_tarihi, gecerlilik_tarihi</p>
          </div>
          <div class="flex gap-2">
            <button type="submit" :disabled="loading" class="btn btn-primary"><LoadingSpinner v-if="loading" class="mr-2 h-4 w-4" />{{ loading ? 'Ice Aktariliyor...' : 'CSV Ice Aktar' }}</button>
            <button type="button" @click="downloadTemplate" class="btn btn-secondary">Sablon Indir</button>
          </div>
        </form>
        <div v-if="importResult" class="mt-4 p-4 rounded" :class="importResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
          <h4 class="font-medium" :class="importResult.success ? 'text-green-800' : 'text-red-800'">{{ importResult.success ? 'OK Ice Aktarma Basarili' : 'ERR Ice Aktarma Basarisiz' }}</h4>
          <ul class="mt-2 text-sm space-y-1">
            <li v-for="(value, key) in importResult.stats" :key="key"><strong>{{ formatStatKey(key) }}:</strong> {{ value }}</li>
            <li v-if="importResult.errors && importResult.errors.length"><strong>Hatalar:</strong><ul class="ml-4 list-disc"><li v-for="(err, idx) in importResult.errors" :key="idx" class="text-red-600">{{ err }}</li></ul></li>
          </ul>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="card-header flex justify-between items-center">
        <h3 class="card-title">YFK Analizler ({{ analizList.length }})</h3>
        <div class="flex gap-2"><input v-model="searchQuery" type="text" placeholder="Poz no, malzeme kodu veya adi ile ara..." class="input w-64" /><select v-model="filterYil" class="input w-32"><option value="">Tum Yillar</option><option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option></select><select v-model="filterTip" class="input w-40"><option value="">Tum Tipler</option><option value="MALZEME">Malzeme</option><option value="ISCILIK">Iscilik</option><option value="NAKLIYE">Nakliye</option><option value="MAKINE">Makine</option></select></div>
      </div>
      <div class="card-body p-0">
        <div class="overflow-x-auto"><table class="table w-full"><thead><tr><th>Poz No</th><th>Tip</th><th>Malzeme Kodu</th><th>Malzeme Adi</th><th>Birim</th><th>Miktar</th><th>Birim Fiyat</th><th>Toplam</th><th>Yil</th><th>Donem</th><th>Kaynak</th><th>Gecerlilik</th><th>Islemler</th></tr></thead><tbody>
          <tr v-for="a in filteredAnalizList" :key="a.id"><td class="font-mono">{{ a.poz_no }}</td><td><span class="badge" :class="tipClass(a.malzeme_tipi)">{{ a.malzeme_tipi }}</span></td><td>{{ a.malzeme_kodu }}</td><td>{{ a.malzeme_adi }}</td><td>{{ a.birim }}</td><td class="font-mono">{{ a.miktar }}</td><td class="font-mono">{{ formatCurrency(a.birim_fiyat) }}</td><td class="font-mono">{{ formatCurrency(a.miktar * a.birim_fiyat) }}</td><td>{{ a.yil || '-' }}</td><td>{{ a.donem || 'Yillik' }}</td><td>{{ a.kaynak }}</td><td>{{ a.gecerlilik_tarihi || '-' }}</td><td><button @click="showAnalizDetail(a)" class="btn btn-sm btn-ghost">Detay</button></td></tr>
          <tr v-if="filteredAnalizList.length === 0"><td colspan="13" class="text-center py-8 text-gray-500">Kayit bulunamadi</td></tr>
        </tbody></table></div>
        <div class="p-4 border-t flex justify-between items-center" v-if="pagination.total > 0"><p class="text-sm text-gray-600"> {{ (pagination.page - 1) * pagination.pageSize + 1 }} - {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} / {{ pagination.total }} kayit</p><div class="flex gap-2"><button @click="pagination.page > 1 && (pagination.page--, loadAnalizList())" :disabled="pagination.page <= 1" class="btn btn-sm btn-ghost">Onceki</button><button @click="pagination.page * pagination.pageSize < pagination.total && (pagination.page++, loadAnalizList())" :disabled="pagination.page * pagination.pageSize >= pagination.total" class="btn btn-sm btn-ghost">Sonraki</button></div></div>
      </div>
    </div>
    <div v-if="selectedAnaliz" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden">
        <div class="p-4 border-b flex justify-between items-center"><h3 class="text-lg font-bold">{{ selectedAnaliz.poz_no }} - {{ selectedAnaliz.malzeme_adi }} ({{ selectedAnaliz.malzeme_tipi }})</h3><button @click="selectedAnaliz = null" class="text-gray-500 hover:text-gray-700">X</button></div>
        <div class="p-4 overflow-y-auto max-h-[70vh]">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4"><div><strong>Poz No:</strong> {{ selectedAnaliz.poz_no }}</div><div><strong>Malzeme Tipi:</strong> {{ selectedAnaliz.malzeme_tipi }}</div><div><strong>Malzeme Kodu:</strong> {{ selectedAnaliz.malzeme_kodu }}</div><div><strong>Malzeme Adi:</strong> {{ selectedAnaliz.malzeme_adi }}</div><div><strong>Birim:</strong> {{ selectedAnaliz.birim }}</div><div><strong>Miktar:</strong> {{ selectedAnaliz.miktar }}</div><div><strong>Birim Fiyat:</strong> {{ formatCurrency(selectedAnaliz.birim_fiyat) }}</div><div><strong>Toplam:</strong> {{ formatCurrency(selectedAnaliz.miktar * selectedAnaliz.birim_fiyat) }}</div><div><strong>Yil:</strong> {{ selectedAnaliz.yil || '-' }}</div><div><strong>Donem:</strong> {{ selectedAnaliz.donem || 'Yillik' }}</div><div><strong>Kaynak:</strong> {{ selectedAnaliz.kaynak }}</div><div><strong>Yayin Tarihi:</strong> {{ selectedAnaliz.yayin_tarihi || '-' }}</div><div><strong>Gecerlilik:</strong> {{ selectedAnaliz.gecerlilik_tarihi || '-' }}</div></div>
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
const importForm = reactive({
  yil: new Date().getFullYear(),
  donem: null,
  kaynak: '',
  kaynak_url: '',
})
const selectedFile = ref(null)
const importResult = ref(null)

const analizList = ref([])
const searchQuery = ref('')
const filterYil = ref('')
const filterTip = ref('')
const selectedAnaliz = ref(null)
const availableYears = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const filteredAnalizList = computed(() => {
  let result = analizList.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(a => a.poz_no.toLowerCase().includes(q) || a.malzeme_kodu.toLowerCase().includes(q) || a.malzeme_adi.toLowerCase().includes(q))
  }
  if (filterYil.value) result = result.filter(a => a.yil == filterYil.value)
  if (filterTip.value) result = result.filter(a => a.malzeme_tipi == filterTip.value)
  return result
})

const tipClass = (tip) => {
  const map = { MALZEME: 'badge-primary', ISCILIK: 'badge-success', NAKLIYE: 'badge-warning', MAKINE: 'badge-info' }
  return map[tip] || 'badge-secondary'
}
const formatCurrency = (val) => {
  if (!val) return '-'
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 2 }).format(val)
}
const formatStatKey = (key) => {
  const map = { created: 'Olusturulan', updated: 'Guncellenen', skipped: 'Atlanan', errors: 'Hatali' }
  return map[key] || key
}

onMounted(async () => {
  await loadAnalizList()
  await loadAvailableYears()
})

async function loadAnalizList() {
  loading.value = true
  try {
    const res = await insaatStore.fetchYfkAnalizler({ page: pagination.page, page_size: pagination.pageSize, yil: filterYil.value || undefined, malzeme_tipi: filterTip.value || undefined, search: searchQuery.value || undefined })
    analizList.value = res.results || res
    pagination.total = res.count || res.length
  } catch (e) {
    toast.error('Analiz listesi yuklenemedi')
  } finally {
    loading.value = false
  }
}

async function loadAvailableYears() {
  try {
    const res = await insaatStore.fetchYfkAnalizler({ page_size: 1000 })
    const years = [...new Set((res.results || res).map(a => a.yil).filter(Boolean))].sort((a, b) => b - a)
    availableYears.value = years
  } catch (e) {}
}

async function onFileSelect(e) {
  selectedFile.value = e.target.files[0]
}

async function handleImport() {
  if (!selectedFile.value) { toast.error('CSV dosyasi secin'); return }
  loading.value = true
  importResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('yil', importForm.yil)
    if (importForm.donem) formData.append('donem', importForm.donem)
    formData.append('kaynak', importForm.kaynak)
    formData.append('kaynak_url', importForm.kaynak_url)
    const res = await insaatStore.importYfkAnaliz(formData)
    importResult.value = { success: true, stats: res, errors: [] }
    toast.success('Ice aktarma tamamlandi')
    await loadAnalizList()
    await loadAvailableYears()
    selectedFile.value = null
    importForm.kaynak = ''
    importForm.kaynak_url = ''
    importForm.donem = null
  } catch (e) {
    importResult.value = { success: false, stats: {}, errors: [e.response?.data?.detail || e.message || 'Bilinmeyen hata'] }
    toast.error('Ice aktarma basarisiz')
  } finally {
    loading.value = false
  }
}

async function downloadTemplate() {
  try {
    const blob = await insaatStore.downloadYfkAnalizTemplate()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'yfk_analiz_template.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) { toast.error('Sablon indirilemedi') }
}

async function showAnalizDetail(analiz) {
  loading.value = true
  try {
    const detail = await insaatStore.fetchYfkAnalizDetail(analiz.id)
    selectedAnaliz.value = detail
  } catch (e) { toast.error('Detay yuklenemedi') }
  finally { loading.value = false }
}

const Math = window.Math
</script>
