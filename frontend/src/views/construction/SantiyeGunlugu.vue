/**
 * SantiyeGunlugu.vue - Construction Site Daily Log Vue 3 Component
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
const logs = ref([])
const loadingLogs = ref(true)
const errorLogs = ref(null)

// Pagination and filter state
const sayfa = ref(1)
const limit = ref(20)
const arama = ref('')
const filtreSantiye = ref('')
const filtreTarihBaslangic = ref('')
const filtreTarihBitis = ref('')
const santiyeler = ref([])

// Computed for filtered logs
const filteredLogs = computed(() => {
  let result = logs.value

  if (arama.value) {
    result = result.filter(
      (log) =>
        log.gunluk_no?.includes(arama.value) ||
        log.aciklama?.includes(arama.value) ||
        log.santiye_adi?.includes(arama.value)
    )
  }

  if (filtreSantiye.value) {
    result = result.filter((log) => log.santiye_id === Number(filtreSantiye.value))
  }

  if (filtreTarihBaslangic.value) {
    result = result.filter((log) => log.tarih >= filtreTarihBaslangic.value)
  }

  if (filtreTarihBitis.value) {
    result = result.filter((log) => log.tarih <= filtreTarihBitis.value)
  }

  return result
})

// Load daily logs from API
async function yukleGunlukler() {
  loadingLogs.value = true
  errorLogs.value = null
  try {
    const response = await constructionApi.listDailyLogs({
      page: sayfa.value,
      limit: limit.value,
      search: arama.value,
      santiye_id: filtreSantiye.value || undefined,
      tarih_baslangic: filtreTarihBaslangic.value || undefined,
      tarih_bitis: filtreTarihBitis.value || undefined,
    })
    logs.value = response.data || []
  } catch (error: any) {
    hataMesaji(error, 'Günlükler yüklenirken hata oluştu')
    errorLogs.value = error.message
  } finally {
    loadingLogs.value = false
  }
}

// Load construction sites for filter dropdown
async function yukleSantiyeler() {
  try {
    const response = await constructionApi.listSites()
    santiyeler.value = response.data || []
  } catch (error: any) {
    hataMesaji(error, 'Şantiyeler yüklenirken hata oluştu')
  }
}

// Delete a daily log
async function silGunluk(id: number) {
  if (!confirm('Bu günlük kaydını silmek istediğinizden emin misiniz?')) return
  try {
    await constructionApi.deleteDailyLog(id)
    yukleGunlukler()
  } catch (error: any) {
    hataMesaji(error, 'Günlük silinirken hata oluştu')
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

// Format weather
function havaDurumuFormatla(durum?: string) {
  if (!durum) return '—'
  const icons: Record<string, string> = {
    gunesli: '☀️',
    parcali_bulutlu: '⛅',
    bulutlu: '☁️',
    yagmurlu: '🌧️',
    saganak: '⛈️',
    karli: '❄️',
    sisli: '🌫️',
  }
  return `${icons[durum] || ''} ${durum}`.trim()
}

// Format labor type
function isciTipiFormatla(tip?: string) {
  if (!tip) return '—'
  return {
    usta: 'Usta',
    cirak: 'Çırak',
    genel: 'Genel İşçi',
    makine_operatoru: 'Makine Operatörü',
    muhendis: 'Mühendis',
    tekniker: 'Teknisyen',
    guvenlik: 'Güvenlik',
  }[tip] || tip
}

onMounted(() => {
  yukleSantiyeler()
  yukleGunlukler()
})

// Watch for filter changes
watch(
  [arama, filtreSantiye, filtreTarihBaslangic, filtreTarihBitis],
  () => {
    sayfa.value = 1
    yukleGunlukler()
  }
)

// Modal form for adding/editing daily log
import { useKayitFormu } from '@/hooks/useKayitFormu'

type GunlukForm = {
  santiye_id: number
  tarih: string
  hava_durumu: string
  sicaklik_min: number | null
  sicaklik_max: number | null
  isci_sayisi: number
  isci_tipi: string
  calisma_saati: number
  yapilan_isler: string
  malzeme_giris: string
  malzeme_cikis: string
  ekipmanlar: string
  sorunlar: string
  aciklama: string
}

const Fm = useKayitFormu(
  {
    olustur: (veri) => constructionApi.createDailyLog(veri),
    guncelle: (id, veri) => constructionApi.updateDailyLog(id, veri),
  },
  () => ({
    santiye_id: 0,
    tarih: new Date().toISOString().split('T')[0],
    hava_durumu: 'gunesli',
    sicaklik_min: null,
    sicaklik_max: null,
    isci_sayisi: 0,
    isci_tipi: 'genel',
    calisma_saati: 8,
    yapilan_isler: '',
    malzeme_giris: '',
    malzeme_cikis: '',
    ekipmanlar: '',
    sorunlar: '',
    aciklama: '',
  }),
  (log) => ({
    santiye_id: log.santiye_id,
    tarih: log.tarih,
    hava_durumu: log.hava_durumu || 'gunesli',
    sicaklik_min: log.sicaklik_min,
    sicaklik_max: log.sicaklik_max,
    isci_sayisi: log.isci_sayisi || 0,
    isci_tipi: log.isci_tipi || 'genel',
    calisma_saati: log.calisma_saati || 8,
    yapilan_isler: log.yapilan_isler || '',
    malzeme_giris: log.malzeme_giris || '',
    malzeme_cikis: log.malzeme_cikis || '',
    ekipmanlar: log.ekipmanlar || '',
    sorunlar: log.sorunlar || '',
    aciklama: log.aciklama || '',
  }),
  (form) => ({
    ...form,
    santiye_id: Number(form.santiye_id),
    tarih: form.tarih,
    hava_durumu: form.hava_durumu,
    sicaklik_min: form.sicaklik_min,
    sicaklik_max: form.sicaklik_max,
    isci_sayisi: Number(form.isci_sayisi),
    isci_tipi: form.isci_tipi,
    calisma_saati: Number(form.calisma_saati),
    yapilan_isler: form.yapilan_isler?.trim(),
    malzeme_giris: form.malzeme_giris?.trim(),
    malzeme_cikis: form.malzeme_cikis?.trim(),
    ekipmanlar: form.ekipmanlar?.trim(),
    sorunlar: form.sorunlar?.trim(),
    aciklama: form.aciklama?.trim(),
  }),
  (form) => {
    if (!form.santiye_id) return 'Şantiye seçimi zorunlu'
    if (!form.tarih) return 'Tarih zorunlu'
    if (!form.hava_durumu) return 'Hava durumu zorunlu'
    if (form.isci_sayisi < 0) return 'İşçi sayısı negatif olamaz'
    return null
  }
)
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">
          Şantiye Günlüğü
        </h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">
        + Yeni Günlük
      </button>
    </div>

    <!-- Search and Filter -->
    <div class="mb-6 flex flex-wrap items-center gap-3">
      <div class="flex-1 min-w-[250px]">
        <input
          v-model="arama"
          type="search"
          placeholder="Günlük no, açıklama veya şantiye ile ara..."
          class="alan w-full"
        />
      </div>
      <select v-model="filtreSantiye" class="alan" @change="sayfa = 1; yukleGunlukler()">
        <option value="">Tüm Şantiyeler</option>
        <option v-for="s in santiyeler" :key="s.id" :value="s.id">
          {{ s.adi }}
        </option>
      </select>
      <input
        v-model="filtreTarihBaslangic"
        type="date"
        class="alan"
        @change="sayfa = 1; yukleGunlukler()"
      />
      <input
        v-model="filtreTarihBitis"
        type="date"
        class="alan"
        @change="sayfa = 1; yukleGunlukler()"
      />
      <button type="button" class="ikincil-dugme" @click="yukleGunlukler">
        Yenile
      </button>
    </div>

    <!-- Error Message -->
    <p v-if="errorLogs" class="hata-kutusu mb-4" role="alert">{{ errorLogs }}</p>

    <!-- Daily Logs Table -->
    <VeriTablosu
      :basliklar="[
        'Tarih',
        'Şantiye',
        'Hava',
        'Sıcaklık (Min/Max)',
        'İşçi Sayısı',
        'İşçi Tipi',
        'Çalışma Saati',
        'Yapılan İşler',
        'Malzeme Giriş/Çıkış',
        'Ekipmanlar',
        'Sorunlar',
        'İşlem'
      ]"
      :bos-mu="!loadingLogs && filteredLogs.length === 0"
    >
      <template v-if="filteredLogs.length">
        <tr
          v-for="log in paginatedLogs"
          :key="log.id"
          class="transition-colors hover:bg-surface-100/60"
        >
          <td class="px-4 py-3 whitespace-nowrap text-surface-700">
            {{ tarihFormatla(log.tarih) }}
          </td>
          <td class="px-4 py-3 font-medium text-surface-900">
            {{ log.santiye_adi || '—' }}
          </td>
          <td class="px-4 py-3 text-center">
            {{ havaDurumuFormatla(log.hava_durumu) }}
          </td>
          <td class="px-4 py-3 text-center font-mono">
            {{ log.sicaklik_min !== null ? log.sicaklik_min + '°C' : '—' }} / {{ log.sicaklik_max !== null ? log.sicaklik_max + '°C' : '—' }}
          </td>
          <td class="px-4 py-3 text-center font-mono">
            {{ log.isci_sayisi }}
          </td>
          <td class="px-4 py-3">
            {{ isciTipiFormatla(log.isci_tipi) }}
          </td>
          <td class="px-4 py-3 text-center font-mono">
            {{ log.calisma_saati }} saat
          </td>
          <td class="px-4 py-3 max-w-md truncate text-surface-600">
            {{ log.yapilan_isler || '—' }}
          </td>
          <td class="px-4 py-3 max-w-md truncate text-surface-600">
            <div v-if="log.malzeme_giris">Giriş: {{ log.malzeme_giris }}</div>
            <div v-if="log.malzeme_cikis">Çıkış: {{ log.malzeme_cikis }}</div>
            <span v-if="!log.malzeme_giris && !log.malzeme_cikis" class="text-surface-400">—</span>
          </td>
          <td class="px-4 py-3 max-w-md truncate text-surface-600">
            {{ log.ekipmanlar || '—' }}
          </td>
          <td class="px-4 py-3 max-w-md truncate" :class="log.sorunlar ? 'text-red-600' : 'text-surface-400'">
            {{ log.sorunlar || '—' }}
          </td>
          <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
            <div class="flex items-center gap-2">
              <button
                type="button"
                class="text-sm font-medium text-primary-700 hover:underline"
                @click="Fm.duzenleAc(log)"
              >
                Düzenle
              </button>
              <button
                type="button"
                class="text-sm font-medium text-red-700 hover:underline"
                @click="silGunluk(log.id)"
              >
                Sil
              </button>
            </div>
          </td>
        </tr>
      </template>
      <tr v-else>
        <td colspan="12" class="px-4 py-8 text-center text-sm text-surface-400">
          Günlük kayıt bulunmuyor.
        </td>
      </tr>
    </VeriTablosu>

    <!-- Sayfalama -->
    <Sayfalama
      :sayfa="sayfa"
      :toplam="toplamSayfa"
      :yukleniyor="loadingLogs"
      @sayfa-degistir="(s) => (sayfa = s)"
    />
  </div>
</template>

<script setup lang="ts">
// Ek computed özellikler
const paginatedLogs = computed(() => {
  const start = (sayfa.value - 1) * limit.value
  const end = start + limit.value
  return filteredLogs.value.slice(start, end)
})

const toplamSayfa = computed(() => Math.ceil(filteredLogs.value.length / limit.value))
</script>