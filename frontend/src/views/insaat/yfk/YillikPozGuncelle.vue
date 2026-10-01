<template>
  <div class="p-4">
    <div class="mb-6">
      <h2 class="text-xl font-bold mb-2">Yıllık Poz Güncelleme</h2>
      <p class="text-gray-600">YFK yıllık poz verilerini içe aktar veya güncelleyin.</p>
    </div>

    <div class="card mb-6">
      <div class="card-header">
        <h3 class="card-title">Yıllık Poz Verisi Yükle</h3>
      </div>
      <div class="card-body">
        <form @submit.prevent="handleImport">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div><label class="block text-sm font-medium mb-1">Yıl *</label><input v-model.number="importForm.yil" type="number" min="2020" max="2030" class="input w-full" required /></div>
            <div><label class="block text-sm font-medium mb-1">Kaynak</label><input v-model="importForm.kaynak" type="text" placeholder="Örn. YFK 2026 Tebliği" class="input w-full" /></div>
            <div><label class="block text-sm font-medium mb-1">Kaynak URL</label><input v-model="importForm.kaynak_url" type="url" placeholder="https://..." class="input w-full" /></div>
            <div><label class="block text-sm font-medium mb-1">Yayın Tarihi</label><input v-model="importForm.yayin_tarihi" type="date" class="input w-full" /></div>
          </div>

          <div class="mb-4">
            <label class="block text-sm font-medium mb-1">CSV Dosyası *</label>
            <input ref="fileInput" type="file" accept=".csv" @change="onFileSelect" class="input w-full" required />
            <p class="text-sm text-gray-500 mt-1">CSV sütunları: poz_no, ad, birim, grup_kodu, grup_adi, aciklama, birim_fiyat, kaynak, kaynak_url, yayin_tarihi, gecerlilik_baslangic, gecerlilik_bitis</p>
          </div>

          <div class="flex gap-2">
            <button type="submit" :disabled="loading" class="btn btn-primary"><LoadingSpinner v-if="loading" class="mr-2 h-4 w-4" />{{ loading ? 'İçe Aktarılıyor...' : 'CSV İçe Aktar' }}</button>
            <button type="button" @click="downloadTemplate" class="btn btn-secondary">Şablon İndir</button>
          </div>
        </form>

        <div v-if="importResult" class="mt-4 p-4 rounded" :class="importResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
          <h4 class="font-medium" :class="importResult.success ? 'text-green-800' : 'text-red-800'">{{ importResult.success ? '✓ İçe Aktarma Başarılı' : '✗ İçe Aktarma Başarısız' }}</h4>
          <ul class="mt-2 text-sm space-y-1">
            <li v-for="(value, key) in importResult.stats" :key="key"><strong>{{ formatStatKey(key) }}:</strong> {{ value }}</li>
            <li v-if="importResult.errors && importResult.errors.length"><strong>Hatalar:</strong><ul class="ml-4 list-disc"><li v-for="(err, idx) in importResult.errors" :key="idx" class="text-red-600">{{ err }}</li></ul></li>
          </ul>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="card-header flex justify-between items-center">
        <h3 class="card-title">YFK Poz Versiyonları ({{ pozList.length }})</h3>
        <div class="flex gap-2"><input v-model="searchQuery" type="text" placeholder="Poz no, ad veya grup kodu ile ara..." class="input w-64" /><select v-model="filterYil" class="input w-32"><option value="">Tüm Yıllar</option><option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option></select></div>
      </div>
      <div class="card-body p-0">
        <div class="overflow-x-auto"><table class="table w-full"><thead><tr><th>Poz No</th><th>Ad</th><th>Birim</th><th>Grup</th><th>Versiyon</th><th>Değişiklik</th><th>Yıl</th><th>Fiyat (₺)</th><th>Kaynak</th><th>Durum</th><th>İşlemler</th></tr></thead><tbody>
          <tr v-for="poz in filteredPozList" :key="poz.id"><td class="font-mono">{{ poz.poz_no }}</td><td>{{ poz.ad }}</td><td>{{ poz.birim }}</td><td>{{ poz.grup_kodu }} - {{ poz.grup_adi }}</td><td>v{{ poz.versiyon }}</td><td><span class="badge" :class="degisiklikTuruClass(poz.degisiklik_turu)">{{ poz.degisiklik_turu }}</span></td><td>{{ poz.yil || '-' }}</td><td class="font-mono">{{ poz.birim_fiyat ? formatCurrency(poz.birim_fiyat) : '-' }}</td><td>{{ poz.kaynak }}</td><td><span class="badge" :class="poz.is_active ? 'badge-success' : 'badge-secondary'">{{ poz.is_active ? 'Aktif' : 'Arşiv' }}</span></td><td><button @click="showPozDetail(poz)" class="btn btn-sm btn-ghost">Detay</button></td></tr>
          <tr v-if="filteredPozList.length === 0"><td colspan="11" class="text-center py-8 text-gray-500">Kayıt bulunamadı</td></tr>
        </tbody></table></div>
        <div class="p-4 border-t flex justify-between items-center" v-if="pagination.total > 0"><p class="text-sm text-gray-600"> {{ (pagination.page - 1) * pagination.pageSize + 1 }} - {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} / {{ pagination.total }} kayıt</p><div class="flex gap-2"><button @click="pagination.page > 1 && (pagination.page--, loadPozList())" :disabled="pagination.page <= 1" class="btn btn-sm btn-ghost">Önceki</button><button @click="pagination.page * pagination.pageSize < pagination.total && (pagination.page++, loadPozList())" :disabled="pagination.page * pagination.pageSize >= pagination.total" class="btn btn-sm btn-ghost">Sonraki</button></div></div>
      </div>
    </div>

    <div v-if="selectedPoz" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div class="p-4 border-b flex justify-between items-center"><h3 class="text-lg font-bold">{{ selectedPoz.poz_no }} - {{ selectedPoz.ad }} (v{{ selectedPoz.versiyon }})</h3><button @click="selectedPoz = null" class="text-gray-500 hover:text-gray-700">✕</button></div>
        <div class="p-4 overflow-y-auto max-h-[70vh]">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4"><div><strong>Poz No:</strong> {{ selectedPoz.poz_no }}</div><div><strong>Ad:</strong> {{ selectedPoz.ad }}</div><div><strong>Birim:</strong> {{ selectedPoz.birim }}</div><div><strong>Grup:</strong> {{ selectedPoz.grup_kodu }} - {{ selectedPoz.grup_adi }}</div><div><strong>Versiyon:</strong> {{ selectedPoz.versiyon }}</div><div><strong>Değişiklik Türü:</strong> {{ selectedPoz.degisiklik_turu }}</div><div><strong>Yayın Tarihi:</strong> {{ selectedPoz.yayin_tarihi || '-' }}</div><div><strong>Geçerlilik:</strong> {{ selectedPoz.gecerlilik_baslangic || '-' }} - {{ selectedPoz.gecerlilik_bitis || '-' }}</div></div>
          <div v-if="selectedPoz.fiyatlar && selectedPoz.fiyatlar.length" class="mb-4"><h4 class="font-medium mb-2">Fiyat Geçmişi</h4><table class="table w-full text-sm"><thead><tr><th>Yıl</th><th>Dönem</th><th>Birim Fiyat</th><th>Kaynak</th><th>Yayın Tarihi</th><th>Geçerlilik</th></tr></thead><tbody><tr v-for="f in selectedPoz.fiyatlar" :key="f.id"><td>{{ f.yil }}</td><td>{{ f.donem || 'Yıllık' }}</td><td class="font-mono">{{ formatCurrency(f.birim_fiyat) }}</td><td>{{ f.kaynak }}</td><td>{{ f.yayin_tarihi || '-' }}</td><td>{{ f.gecerlilik_tarihi || '-' }}</td></tr></tbody></table></div>
          <div v-if="selectedPoz.rayiclar && selectedPoz.rayiclar.length" class="mb-4"><h4 class="font-medium mb-2">Rayıçlar</h4><table class="table w-full text-sm"><thead><tr><th>Tip</th><th>Malzeme Kodu</th><th>Malzeme Adı</th><th>Birim</th><th>Katsayı</th></tr></thead><tbody><tr v-for="r in selectedPoz.rayiclar" :key="r.id"><td>{{ r.malzeme_tipi }}</td><td>{{ r.malzeme_kodu }}</td><td>{{ r.malzeme_adi }}</td><td>{{ r.birim }}</td><td class="font-mono">{{ r.katsayi }}</td></tr></tbody></table></div>
          <div v-if="selectedPoz.analizler && selectedPoz.analizler.length" class="mb-4"><h4 class="font-medium mb-2">Analiz Detayları</h4><table class="table w-full text-sm"><thead><tr><th>Tip</th><th>Sıra</th><th>Malzeme Kodu</th><th>Malzeme Adı</th><th>Birim</th><th>Miktar</th><th>Birim Fiyat</th><th>Toplam</th></tr></thead><tbody><tr v-for="a in selectedPoz.analizler" :key="a.id"><td>{{ a.malzeme_tipi }}</td><td>{{ a.sira_no }}</td><td>{{ a.malzeme_kodu }}</td><td>{{ a.malzeme_adi }}</td><td>{{ a.birim }}</td><td class="font-mono">{{ a.miktar }}</td><td class="font-mono">{{ formatCurrency(a.birim_fiyat) }}</td><td class="font-mono">{{ formatCurrency(a.toplam_tutar) }}</td></tr></tbody></table></div>
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
  kaynak: '',
  kaynak_url: '',
  yayin_tarihi: '',
})
const selectedFile = ref(null)
const importResult = ref(null)

const pozList = ref([])
const searchQuery = ref('')
const filterYil = ref('')
const selectedPoz = ref(null)
const availableYears = ref([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const filteredPozList = computed(() => {
  let result = pozList.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(p => p.poz_no.toLowerCase().includes(q) || p.ad.toLowerCase().includes(q) || p.grup_kodu.toLowerCase().includes(q))
  }
  if (filterYil.value) {
    result = result.filter(p => p.yil == filterYil.value)
  }
  return result
})

const degisiklikTuruClass = (tur) => {
  const map = { YENI: 'badge-primary', GUNCELLENDI: 'badge-warning', SILINDI: 'badge-danger', DEGISIKLIK_YOK: 'badge-secondary' }
  return map[tur] || 'badge-secondary'
}

const formatCurrency = (val) => {
  if (!val) return '-'
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 2 }).format(val)
}

const formatStatKey = (key) => {
  const map = { created: 'Oluşturulan', updated: 'Güncellenen', skipped: 'Atlanan', errors: 'Hatalı' }
  return map[key] || key
}

onMounted(async () => {
  await loadPozList()
  await loadAvailableYears()
})

async function loadPozList() {
  loading.value = true
  try {
    const res = await insaatStore.fetchYfkYillikPozlar({ page: pagination.page, page_size: pagination.pageSize, yil: filterYil.value || undefined, search: searchQuery.value || undefined })
    pozList.value = res.results || res
    pagination.total = res.count || res.length
  } catch (e) {
    toast.error('Poz listesi yüklenemedi')
  } finally {
    loading.value = false
  }
}

async function loadAvailableYears() {
  try {
    const res = await insaatStore.fetchYfkYillikPozlar({ page_size: 1000 })
    const years = [...new Set((res.results || res).map(p => p.yil).filter(Boolean))].sort((a, b) => b - a)
    availableYears.value = years
  } catch (e) {}
}

async function onFileSelect(e) {
  selectedFile.value = e.target.files[0]
}

async function handleImport() {
  if (!selectedFile.value) { toast.error('CSV dosyası seçin'); return }
  loading.value = true
  importResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('yil', importForm.yil)
    formData.append('kaynak', importForm.kaynak)
    formData.append('kaynak_url', importForm.kaynak_url)
    formData.append('yayin_tarihi', importForm.yayin_tarihi)
    const res = await insaatStore.importYfkYillikPoz(formData)
    importResult.value = { success: true, stats: res, errors: [] }
    toast.success('İçe aktarma tamamlandı')
    await loadPozList()
    await loadAvailableYears()
    selectedFile.value = null
    importForm.kaynak = ''
    importForm.kaynak_url = ''
    importForm.yayin_tarihi = ''
  } catch (e) {
    importResult.value = { success: false, stats: {}, errors: [e.response?.data?.detail || e.message || 'Bilinmeyen hata'] }
    toast.error('İçe aktarma başarısız')
  } finally {
    loading.value = false
  }
}

async function downloadTemplate() {
  try {
    const blob = await insaatStore.downloadYfkYillikTemplate()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'yfk_yillik_poz_template.csv'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) { toast.error('Şablon indirilemedi') }
}

async function showPozDetail(poz) {
  loading.value = true
  try {
    const detail = await insaatStore.fetchYfkYillikPozDetail(poz.id)
    selectedPoz.value = detail
  } catch (e) { toast.error('Detay yüklenemedi') }
  finally { loading.value = false }
}

const Math = window.Math
</script>
