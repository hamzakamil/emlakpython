<template>
  <div class="p-4">
    <div class="mb-6">
      <h2 class="text-xl font-bold mb-2">YFK Rayıç (Katsayı) Listesi</h2>
      <p class="text-gray-600">Yapı Fiyatları Kılavuzu rayıç/katsayı verilerini görüntüleyin ve filtreleyin.</p>
    </div>

    <div class="card mb-6">
      <div class="card-header"><h3 class="card-title">Filtreler</h3></div>
      <div class="card-body">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <label class="etiket">
            Arama
            <input v-model="searchQuery" type="text" placeholder="Poz no, malzeme kodu veya adı..." class="alan w-full" @keyup.enter="loadRayicList" />
          </label>
          <label class="etiket">
            Yıl
            <select v-model="filterYil" class="alan w-full" @change="loadRayicList">
              <option value="">Tüm Yıllar</option>
              <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
            </select>
          </label>
          <label class="etiket">
            Malzeme Tipi
            <select v-model="filterTip" class="alan w-full" @change="loadRayicList">
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
            <select v-model="filterActive" class="alan w-full" @change="loadRayicList">
              <option value="">Tümü</option>
              <option value="true">Aktif</option>
              <option value="false">Pasif</option>
            </select>
          </label>
          <div class="flex items-end">
            <button @click="loadRayicList" class="birincil-dugme w-full"><LoadingSpinner v-if="loading" class="mr-2 h-4 w-4" />Filtrele</button>
          </div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header flex justify-between items-center">
        <h3 class="card-title">Rayıç Kayıtları ({{ rayicList.length }})</h3>
        <div class="flex gap-2">
          <router-link to="/insaat/yfk/rayic-guncelle" class="birincil-dugme">İçe Aktar / Güncelle</router-link>
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
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Malzeme Kodu</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Malzeme Adı</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Birim</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Katsayı</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Yıl</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dönem</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Yayın Tarihi</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Durum</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">İşlemler</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="rayic in rayicList" :key="rayic.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 text-sm font-mono text-gray-900">{{ rayic.poz_no }}</td>
                <td class="px-4 py-3 text-sm text-gray-900">{{ rayic.poz_adi }}</td>
                <td class="px-4 py-3 text-sm">
                  <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full" :class="tipClass(rayic.malzeme_tipi)">
                    {{ rayic.malzeme_tipi }}
                  </span>
                </td>
                <td class="px-4 py-3 text-sm font-mono text-gray-700">{{ rayic.malzeme_kodu }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ rayic.malzeme_adi }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ rayic.birim }}</td>
                <td class="px-4 py-3 text-sm text-right font-mono tabular-nums text-gray-900">{{ formatNumber(rayic.katsayi) }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ rayic.yil }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ rayic.donem || 'Yıllık' }}</td>
                <td class="px-4 py-3 text-sm text-gray-700">{{ rayic.yayin_tarihi ? formatDate(rayic.yayin_tarihi) : '-' }}</td>
                <td class="px-4 py-3 text-sm">
                  <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full" :class="rayic.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'">
                    {{ rayic.is_active ? 'Aktif' : 'Pasif' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-sm">
                  <button @click="showDetail(rayic)" class="text-primary hover:underline">Detay</button>
                </td>
              </tr>
              <tr v-if="rayicList.length === 0">
                <td colspan="12" class="px-4 py-8 text-center text-gray-500">Kayıt bulunamadı</td>
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

    <div v-if="selectedRayic" class="fixed inset-0 z-50 overflow-y-auto" @click.self="closeDetail">
      <div class="flex min-h-full items-center justify-center p-4">
        <div class="fixed inset-0 bg-black/50 transition-opacity" />
        <div class="relative w-full max-w-3xl bg-white rounded-lg shadow-xl max-h-[90vh] overflow-hidden">
          <div class="flex items-center justify-between px-6 py-4 border-b">
            <h3 class="text-lg font-semibold">Rayıç Detayı</h3>
            <button @click="closeDetail" class="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
          </div>
          <div class="p-6 overflow-y-auto max-h-[70vh]">
            <dl class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div><dt class="font-medium text-gray-500">ID</dt><dd class="font-mono">{{ selectedRayic.id }}</dd></div>
              <div><dt class="font-medium text-gray-500">Poz No</dt><dd>{{ selectedRayic.poz_no }}</dd></div>
              <div><dt class="font-medium text-gray-500">Poz Adı</dt><dd>{{ selectedRayic.poz_adi }}</dd></div>
              <div><dt class="font-medium text-gray-500">Malzeme Tipi</dt><dd><span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full" :class="tipClass(selectedRayic.malzeme_tipi)">{{ selectedRayic.malzeme_tipi }}</span></dd></div>
              <div><dt class="font-medium text-gray-500">Malzeme Kodu</dt><dd class="font-mono">{{ selectedRayic.malzeme_kodu }}</dd></div>
              <div><dt class="font-medium text-gray-500">Malzeme Adı</dt><dd>{{ selectedRayic.malzeme_adi }}</dd></div>
              <div><dt class="font-medium text-gray-500">Birim</dt><dd>{{ selectedRayic.birim }}</dd></div>
              <div><dt class="font-medium text-gray-500">Katsayı</dt><dd class="font-mono tabular-nums">{{ formatNumber(selectedRayic.katsayi) }}</dd></div>
              <div><dt class="font-medium text-gray-500">Yıl</dt><dd>{{ selectedRayic.yil }}</dd></div>
              <div><dt class="font-medium text-gray-500">Dönem</dt><dd>{{ selectedRayic.donem || 'Yıllık' }}</dd></div>
              <div><dt class="font-medium text-gray-500">Kaynak</dt><dd>{{ selectedRayic.kaynak || '-' }}</dd></div>
              <div><dt class="font-medium text-gray-500">Kaynak URL</dt><dd><a v-if="selectedRayic.kaynak_url" :href="selectedRayic.kaynak_url" target="_blank" class="text-primary hover:underline">{{ selectedRayic.kaynak_url }}</a><span v-else class="text-gray-400">-</span></dd></div>
              <div><dt class="font-medium text-gray-500">Yayın Tarihi</dt><dd>{{ selectedRayic.yayin_tarihi ? formatDate(selectedRayic.yayin_tarihi) : '-' }}</dd></div>
              <div><dt class="font-medium text-gray-500">Geçerlilik Tarihi</dt><dd>{{ selectedRayic.gecerlilik_tarihi ? formatDate(selectedRayic.gecerlilik_tarihi) : '-' }}</dd></div>
              <div><dt class="font-medium text-gray-500">Durum</dt><dd><span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full" :class="selectedRayic.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'">{{ selectedRayic.is_active ? 'Aktif' : 'Pasif' }}</span></dd></div>
              <div class="md:col-span-2"><dt class="font-medium text-gray-500">Açıklama</dt><dd class="whitespace-pre-wrap">{{ selectedRayic.aciklama || '-' }}</dd></div>
              <div><dt class="font-medium text-gray-500">Oluşturulma</dt><dd>{{ selectedRayic.created_at ? formatDateTime(selectedRayic.created_at) : '-' }}</dd></div>
              <div><dt class="font-medium text-gray-500">Güncellenme</dt><dd>{{ selectedRayic.updated_at ? formatDateTime(selectedRayic.updated_at) : '-' }}</dd></div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

import { useInsaatStore } from '@/stores/insaat'
import { useToast } from '@/composables/useToast'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

const insaatStore = useInsaatStore()
const toast = useToast()

const loading = ref(false)
const rayicList = ref<any[]>([])
const availableYears = ref<number[]>([])
const selectedRayic = ref<any>(null)

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

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('tr-TR')
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('tr-TR')
}

async function loadRayicList() {
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

    const res = await insaatStore.fetchYfkRayiclar(params)
    rayicList.value = res.results || res
    pagination.value.total = res.count || res.length
  } catch (e: any) {
    toast.error('Rayıç listesi yüklenemedi: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

async function loadAvailableYears() {
  try {
    const res = await insaatStore.fetchYfkRayiclar({ page_size: 1000 })
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
    loadRayicList()
  }
}

function nextPage() {
  if (pagination.value.page * pagination.value.pageSize < pagination.value.total) {
    pagination.value.page++
    loadRayicList()
  }
}

async function showDetail(rayic: any) {
  loading.value = true
  try {
    const detail = await insaatStore.fetchYfkRayicDetail(rayic.id)
    selectedRayic.value = detail
  } catch (e: any) {
    toast.error('Detay yüklenemedi: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

function closeDetail() {
  selectedRayic.value = null
}

onMounted(async () => {
  await loadRayicList()
  await loadAvailableYears()
})

const Math = window.Math
</script>





