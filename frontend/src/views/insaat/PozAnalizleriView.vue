<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useInsaatStore } from '@/stores/insaat'
import { useToast } from '@/composables/useToast'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

const insaatStore = useInsaatStore()
const toast = useToast()

const loading = ref(false)
const analizList = ref<any[]>([])
const availableYears = ref<number[]>([])
const selectedAnaliz = ref<any>(null)

const searchQuery = ref('')
const filterYil = ref<string | number>('')
const filterTip = ref('')
const filterActive = ref('')

const pagination = ref({ page: 1, pageSize: 20, total: 0 })

const tipClass = (tip: string) => {
  const map: Record<string, string> = {
    MALZEME: 'bg-blue-100 text-blue-800',
    ISCILIK: 'bg-green-100 text-green-800',
    NAKLIYE: 'bg-yellow-100 text-yellow-800',
    MAKINE: 'bg-purple-100 text-purple-800',
    DIGER: 'bg-gray-100 text-gray-800'
  }
  return map[tip] || 'bg-gray-100 text-gray-800'
}

const formatNumber = (val: string | number) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toLocaleString('tr-TR', { minimumFractionDigits: 4, maximumFractionDigits: 4 })
}

const formatCurrency = (val: string | number) => {
  if (val === null || val === undefined) return '-'
  return Number(val).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 2 })
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('tr-TR')
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('tr-TR')
}

async function loadAnalizList() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize
    }
    if (searchQuery.value) params.search = searchQuery.value
    if (filterYil.value) params.yil = filterYil.value
    if (filterTip.value) params.malzeme_tipi = filterTip.value
    if (filterActive.value !== '') params.is_active = filterActive.value === 'true'

    const res = await insaatStore.fetchYfkAnalizler(params)
    analizList.value = res.results || res
    pagination.value.total = res.count || res.length
  } catch (e: any) {
    toast.error('Analiz listesi yüklenemedi: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

async function loadAvailableYears() {
  try {
    const res = await insaatStore.fetchYfkAnalizler({ page_size: 1000 })
    const years = [...new Set((res.results || res).map((r: any) => r.yil).filter(Boolean))] as number[]
    years.sort((a, b) => b - a)
    availableYears.value = years
  } catch (e) {
    // sessiz
  }
}

function prevPage() {
  if (pagination.value.page > 1) {
    pagination.value.page--
    loadAnalizList()
  }
}

function nextPage() {
  if (pagination.value.page * pagination.value.pageSize < pagination.value.total) {
    pagination.value.page++
    loadAnalizList()
  }
}

async function showDetail(analiz: any) {
  loading.value = true
  try {
    const detail = await insaatStore.fetchYfkAnalizDetail(analiz.id)
    selectedAnaliz.value = detail
  } catch (e: any) {
    toast.error('Detay yüklenemedi: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

function closeDetail() {
  selectedAnaliz.value = null
}

onMounted(async () => {
  await loadAnalizList()
  await loadAvailableYears()
})

const Math = window.Math
</script>
<template>
  <div class="p-4">
    <div class="mb-6">
      <h2 class="text-xl font-bold mb-2">YFK Poz Analizleri</h2>
      <p class="text-gray-600">Yapı Fiyatları Kılavuzu poz analiz (malzeme/işçilik/nakliye/makine detayları) verilerini görüntüleyin ve filtreleyin.</p>
    </div>

    <div class="card mb-6">
      <div class="card-header"><h3 class="card-title">Filtreler</h3></div>
      <div class="card-body">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <label class="etiket">
            Arama
            <input v-model="searchQuery" type="text" placeholder="Poz no, malzeme kodu veya adı..." class="alan w-full" @keyup.enter="loadAnalizList" />
          </label>
          <label class="etiket">
            Yıl
            <select v-model="filterYil" class="alan w-full" @change="loadAnalizList">
              <option value="">Tüm Yıllar</option>
              <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
            </select>
          </label>
          <label class="etiket">
            Malzeme Tipi
            <select v-model="filterTip" class="alan w-full" @change="loadAnalizList">
              <option value="">Tüm Tipler</option>
              <option value="MALZEME">Malzeme</option>
              <option value="ISCILIK">İşçilik</option>
              <option value="NAKLIYE">Nakliye</option>
              <option value="MAKINE">Makine</option>
              <option value="DIGER">Diğer</option>
            </select>
          </label>
          <label class="etiket">
            Aktiflik
            <select v-model="filterActive" class="alan w-full" @change="loadAnalizList">
              <option value="">Tümü</option>
              <option value="true">Aktif</option>
              <option value="false">Pasif</option>
            </select>
          </label>
          <div class="flex items-end">
            <button @click="loadAnalizList" class="birincil-dugme w-full"><LoadingSpinner v-if="loading" class="mr-2 h-4 w-4" />Filtrele</button>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header flex justify-between items-center">
        <h3 class="card-title">Analiz Kayıtları ({{ analizList.length }})</h3>
        <div class="flex gap-2">
          <router-link to="/insaat/yfk/analiz-guncelle" class="birincil-dugme">İçe Aktar / Güncelle</router-link>
        </div>
      </div>
      <div class="card-body p-0">
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Poz No</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Poz Adı</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Malzeme Tipi</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sıra No</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Malzeme Kodu</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Malzeme Adı</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Birim</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Miktar</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Birim Fiyat</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Toplam Tutar</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Yıl</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Yayın Tarihi</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Durum</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">İşlem</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
<tr v-for="analiz in analizList" :key="analiz.id" class="hover:bg-gray-50 transition-colors">
                <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ analiz.poz_no }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ analiz.poz_adi || '' }}</td>
                <td class="px-4 py-3 text-sm">
                  <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full" :class="tipClass(analiz.malzeme_tipi)">
                    {{ analiz.malzeme_tipi }}
                  </span>
                </td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ analiz.sira_no }}</td>
                <td class="px-4 py-3 text-sm font-mono text-gray-700">{{ analiz.malzeme_kodu }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ analiz.malzeme_adi }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ analiz.birim }}</td>
                <td class="px-4 py-3 text-sm text-right font-mono tabular-nums text-gray-900">{{ formatNumber(analiz.miktar) }}</td>
                <td class="px-4 py-3 text-sm text-right font-mono tabular-nums text-gray-900">{{ formatCurrency(analiz.birim_fiyat) }}</td>
                <td class="px-4 py-3 text-sm text-right font-mono tabular-nums text-gray-900 font-semibold">{{ formatCurrency(analiz.toplam_tutar) }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ analiz.yil }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ analiz.yayin_tarihi ? formatDate(analiz.yayin_tarihi) : '-' }}</td>
                <td class="px-4 py-3 text-sm">
                  <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full" :class="analiz.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'">
                    {{ analiz.is_active ? 'Aktif' : 'Pasif' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-sm">
                  <button @click="showDetail(analiz)" class="text-primary hover:underline">Detay</button>
                </td>
              </tr>
              <tr v-if="analizList.length === 0">
                <td colspan="14" class="px-4 py-8 text-center text-gray-500">Kayıt bulunamadı</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="pagination.total > pagination.pageSize" class="px-4 py-4 border-t border-gray-200 flex justify-between items-center">
          <p class="text-sm text-gray-700">
            {{ (pagination.page - 1) * pagination.pageSize + 1 }} - {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} / {{ pagination.total }} kayıt
          </p>
          <div class="flex gap-2">
            <button @click="prevPage" :disabled="pagination.page === 1" class="ikincil-dugme px-3 py-1.5 text-xs">Önceki</button>
            <button @click="nextPage" :disabled="pagination.page * pagination.pageSize >= pagination.total" class="ikincil-dugme px-3 py-1.5 text-xs">Sonraki</button>
          </div>
        </div>
      </div>
    </div>
<!-- Detay Modal -->
    <div v-if="selectedAnaliz" class="fixed inset-0 z-50 overflow-y-auto" @click.self="closeDetail">
      <div class="flex min-h-full items-center justify-center p-4">
        <div class="fixed inset-0 bg-black/50 transition-opacity" />
        <div class="relative w-full max-w-3xl bg-white rounded-lg shadow-xl max-h-[90vh] overflow-hidden">
          <div class="flex items-center justify-between px-6 py-4 border-b">
            <h3 class="text-lg font-semibold">Analiz Detayı</h3>
            <button @click="closeDetail" class="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
          </div>
          <div class="p-6 overflow-y-auto max-h-[70vh]">
            <dl class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div><dt class="font-medium text-gray-500">ID</dt><dd class="font-mono">{{ selectedAnaliz.id }}</dd></div>
                <div><dt class="font-medium text-gray-500">Poz No</dt><dd>{{ selectedAnaliz.poz_no }}</dd></div>
                <div><dt class="font-medium text-gray-500">Poz Adı</dt><dd>{{ selectedAnaliz.poz_adi || '-' }}</dd></div>
                <div><dt class="font-medium text-gray-500">Malzeme Tipi</dt><dd><span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full" :class="tipClass(selectedAnaliz.malzeme_tipi)">{{ selectedAnaliz.malzeme_tipi }}</span></dd></div>
                <div><dt class="font-medium text-gray-500">Sıra No</dt><dd>{{ selectedAnaliz.sira_no }}</dd></div>
                <div><dt class="font-medium text-gray-500">Malzeme Kodu</dt><dd class="font-mono">{{ selectedAnaliz.malzeme_kodu }}</dd></div>
                <div><dt class="font-medium text-gray-500">Malzeme Adı</dt><dd>{{ selectedAnaliz.malzeme_adi }}</dd></div>
                <div><dt class="font-medium text-gray-500">Birim</dt><dd>{{ selectedAnaliz.birim }}</dd></div>
                <div><dt class="font-medium text-gray-500">Miktar</dt><dd class="font-mono tabular-nums">{{ formatNumber(selectedAnaliz.miktar) }}</dd></div>
                <div><dt class="font-medium text-gray-500">Birim Fiyat</dt><dd class="font-mono tabular-nums">{{ formatCurrency(selectedAnaliz.birim_fiyat) }}</dd></div>
                <div><dt class="font-medium text-gray-500">Toplam Tutar</dt><dd class="font-mono tabular-nums font-semibold">{{ formatCurrency(selectedAnaliz.toplam_tutar) }}</dd></div>
                <div><dt class="font-medium text-gray-500">Yıl</dt><dd>{{ selectedAnaliz.yil }}</dd></div>
                <div><dt class="font-medium text-gray-500">Kaynak</dt><dd>{{ selectedAnaliz.kaynak || '-' }}</dd></div>
                <div><dt class="font-medium text-gray-500">Yayın Tarihi</dt><dd>{{ selectedAnaliz.yayin_tarihi ? formatDate(selectedAnaliz.yayin_tarihi) : '-' }}</dd></div>
                <div><dt class="font-medium text-gray-500">Durum</dt><dd><span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full" :class="selectedAnaliz.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'">{{ selectedAnaliz.is_active ? 'Aktif' : 'Pasif' }}</span></dd></div>
                <div><dt class="font-medium text-gray-500">Oluşturulma</dt><dd>{{ selectedAnaliz.created_at ? formatDateTime(selectedAnaliz.created_at) : '-' }}</dd></div>
                <div><dt class="font-medium text-gray-500">Güncellenme</dt><dd>{{ selectedAnaliz.updated_at ? formatDateTime(selectedAnaliz.updated_at) : '-' }}</dd></div>
              </dl>
            </div>
            <div class="border-t border-gray-200 px-6 py-4 flex justify-end">
              <button @click="closeDetail" class="ikincil-dugme">Kapat</button>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>
