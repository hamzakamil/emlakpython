/**
 * KaliteKontrol.vue - Kalite Kontrol Vue 3 Component
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
const yazabilir = computed(() => auth.kullanici?.role === 'admin' || auth.kullanici?.role === 'manager' || auth.kullanici?.role === 'engineer')

// State
const kaliteKontrolleri = ref([])
const loadingKontroller = ref(true)
const errorKontrol = ref(null)

// Pagination and filter state
const sayfa = ref(1)
const limit = ref(20)
const arama = ref('')
const filtreSantiye = ref('')
const filtrePoz = ref('')
const filtreDurum = ref('tum')
const filtreTarihBaslangic = ref('')
const filtreTarihBitis = ref('')
const santiyeler = ref([])
const pozlar = ref([])

// Computed for filtered records
const filteredKontroller = computed(() => {
  let result = kaliteKontrolleri.value

  if (arama.value) {
    result = result.filter(
      (k) =>
        k.kontrol_no?.includes(arama.value) ||
        k.aciklama?.includes(arama.value) ||
        k.santiye_adi?.includes(arama.value) ||
        k.poz_adi?.includes(arama.value)
    )
  }

  if (filtreSantiye.value) {
    result = result.filter((k) => k.santiye_id === Number(filtreSantiye.value))
  }

  if (filtrePoz.value) {
    result = result.filter((k) => k.poz_id === Number(filtrePoz.value))
  }

  if (filtreDurum.value !== 'tum') {
    result = result.filter((k) => k.durum === filtreDurum.value)
  }

  if (filtreTarihBaslangic.value) {
    result = result.filter((k) => k.tarih >= filtreTarihBaslangic.value)
  }

  if (filtreTarihBitis.value) {
    result = result.filter((k) => k.tarih <= filtreTarihBitis.value)
  }

  return result
})

// Load kalite kontrolleri from API
async function yukleKaliteKontrolleri() {
  loadingKontroller.value = true
  errorKontrol.value = null
  try {
    const response = await constructionApi.listQualityControls({
      page: sayfa.value,
      limit: limit.value,
      search: arama.value,
      santiye_id: filtreSantiye.value || undefined,
      poz_id: filtrePoz.value || undefined,
      durum: filtreDurum.value !== 'tum' ? filtreDurum.value : undefined,
      tarih_baslangic: filtreTarihBaslangic.value || undefined,
      tarih_bitis: filtreTarihBitis.value || undefined,
    })
    kaliteKontrolleri.value = response.data || []
  } catch (error: any) {
    hataMesaji(error, 'Kalite kontrolleri yüklenirken hata oluştu')
    errorKontrol.value = error.message
  } finally {
    loadingKontroller.value = false
  }
}

// Load construction sites and items for filter dropdown
async function yukleFiltreVerileri() {
  try {
    const [santiyeRes, pozRes] = await Promise.all([
      constructionApi.listSites(),
      constructionApi.listItems(),
    ])
    santiyeler.value = santiyeRes.data || []
    pozlar.value = pozRes.data || []
  } catch (error: any) {
    hataMesaji(error, 'Filtre verileri yüklenirken hata oluştu')
  }
}

// Delete a quality control
async function silKaliteKontrol(id: number) {
  if (!confirm('Bu kalite kontrol kaydını silmek istediğinizden emin misiniz?')) return
  try {
    await constructionApi.deleteQualityControl(id)
    yukleKaliteKontrolleri()
  } catch (error: any) {
    hataMesaji(error, 'Kalite kontrol silinirken hata oluştu')
  }
}

// Format date
function tarihFormatla(tarih: string) {
  return new Date(tarih).toLocaleDateString('tr-TR')
}

// Format status
function durumFormatla(durum?: string) {
  if (!durum) return '—'
  const labels: Record<string, { label: string; class: string }> = {
    beklemede: { label: 'Beklemede', class: 'bg-amber-100 text-amber-800' },
    gecti: { label: 'Geçti', class: 'bg-emerald-100 text-emerald-800' },
    kaldi: { label: 'Kaldı', class: 'bg-red-100 text-red-800' },
    onaylandi: { label: 'Onaylandı', class: 'bg-blue-100 text-blue-800' },
    reddedildi: { label: 'Reddedildi', class: 'bg-rose-100 text-rose-800' },
  }
  const d = labels[durum] || { label: durum, class: 'bg-surface-200 text-surface-600' }
  return { label: d.label, class: `px-2 py-1 text-xs font-medium rounded-full ${d.class}` }
}

// Format control type
function kontrolTipiFormatla(tip?: string) {
  if (!tip) return '—'
  return {
    malzeme: 'Malzeme Kontrolü',
    iscilik: 'İşçilik Kontrolü',
    boyut: 'Boyut Ölçümü',
    test: 'Test/Analiz',
    goruntuleme: 'Görsel İnceleme',
    diger: 'Diğer',
  }[tip] || tip
}

onMounted(() => {
  yukleFiltreVerileri()
  yukleKaliteKontrolleri()
})

// Watch for filter changes
watch(
  [arama, filtreSantiye, filtrePoz, filtreDurum, filtreTarihBaslangic, filtreTarihBitis],
  () => {
    sayfa.value = 1
    yukleKaliteKontrolleri()
  }
)

// Modal form for adding/editing quality control
import { useKayitFormu } from '@/hooks/useKayitFormu'

type KaliteKontrolForm = {
  santiye_id: number
  poz_id: number
  tarih: string
  kontrol_tipi: string
  durum: string
  olculen_deger: string
  beklenen_deger: string
  tolerek_aralik: string
  kontrol_eden_id: number
  onaylayan_id: number | null
  onay_tarihi: string | null
  aciklama: string
  ek_gorseller: string[]
}

const Fm = useKayitFormu(
  {
    olustur: (veri) => constructionApi.createQualityControl(veri),
    guncelle: (id, veri) => constructionApi.updateQualityControl(id, veri),
  },
  () => ({
    santiye_id: 0,
    poz_id: 0,
    tarih: new Date().toISOString().split('T')[0],
    kontrol_tipi: 'malzeme',
    durum: 'beklemede',
    olculen_deger: '',
    beklenen_deger: '',
    tolerek_aralik: '',
    kontrol_eden_id: auth.kullanici?.id || 0,
    onaylayan_id: null,
    onay_tarihi: null,
    aciklama: '',
    ek_gorseller: [],
  }),
  (k) => ({
    santiye_id: k.santiye_id,
    poz_id: k.poz_id,
    tarih: k.tarih,
    kontrol_tipi: k.kontrol_tipi || 'malzeme',
    durum: k.durum || 'beklemede',
    olculen_deger: k.olculen_deger || '',
    beklenen_deger: k.beklenen_deger || '',
    tolerek_aralik: k.tolerek_aralik || '',
    kontrol_eden_id: k.kontrol_eden_id,
    onaylayan_id: k.onaylayan_id,
    onay_tarihi: k.onay_tarihi,
    aciklama: k.aciklama || '',
    ek_gorseller: k.ek_gorseller || [],
  }),
  (form) => ({
    ...form,
    santiye_id: Number(form.santiye_id),
    poz_id: Number(form.poz_id),
    tarih: form.tarih,
    kontrol_tipi: form.kontrol_tipi,
    durum: form.durum,
    olculen_deger: form.olculen_deger?.trim(),
    beklenen_deger: form.beklenen_deger?.trim(),
    tolerek_aralik: form.tolerek_aralik?.trim(),
    kontrol_eden_id: Number(form.kontrol_eden_id),
    onaylayan_id: form.onaylayan_id ? Number(form.onaylayan_id) : null,
    onay_tarihi: form.onay_tarihi,
    aciklama: form.aciklama?.trim(),
    ek_gorseller: form.ek_gorseller,
  }),
  (form) => {
    if (!form.santiye_id) return 'Şantiye seçimi zorunlu'
    if (!form.poz_id) return 'Poz seçimi zorunlu'
    if (!form.tarih) return 'Tarih zorunlu'
    if (!form.kontrol_tipi) return 'Kontrol tipi zorunlu'
    if (!form.kontrol_eden_id) return 'Kontrol eden kişi zorunlu'
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
          Kalite Kontrol
        </h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">
        + Yeni Kontrol
      </button>
    </div>

    <!-- Arama ve Filtre -->
    <div class="mb-6 flex flex-wrap items-center gap-3">
      <div class="flex-1 min-w-[250px]">
        <input
          v-model="arama"
          type="search"
          placeholder="Kontrol no, açıklama, şantiye veya poz ile ara..."
          class="alan w-full"
        />
      </div>
      <select v-model="filtreSantiye" class="alan" @change="sayfa = 1; yukleKaliteKontrolleri()">
        <option value="">Tüm Şantiyeler</option>
        <option v-for="s in santiyeler" :key="s.id" :value="s.id">
          {{ s.adi }}
        </option>
      </select>
      <select v-model="filtrePoz" class="alan" @change="sayfa = 1; yukleKaliteKontrolleri()">
        <option value="">Tüm Pozlar</option>
        <option v-for="p in pozlar" :key="p.id" :value="p.id">
          {{ p.kod }} - {{ p.adi }}
        </option>
      </select>
      <select v-model="filtreDurum" class="alan" @change="sayfa = 1; yukleKaliteKontrolleri()">
        <option value="tum">Tüm Durumlar</option>
        <option value="beklemede">Beklemede</option>
        <option value="gecti">Geçti</option>
        <option value="kaldi">Kaldı</option>
        <option value="onaylandi">Onaylandı</option>
        <option value="reddedildi">Reddedildi</option>
      </select>
      <input
        v-model="filtreTarihBaslangic"
        type="date"
        class="alan"
        @change="sayfa = 1; yukleKaliteKontrolleri()"
      />
      <input
        v-model="filtreTarihBitis"
        type="date"
        class="alan"
        @change="sayfa = 1; yukleKaliteKontrolleri()"
      />
      <button type="button" class="ikincil-dugme" @click="yukleKaliteKontrolleri">
        Yenile
      </button>
    </div>

    <!-- Hata Mesajı -->
    <p v-if="errorKontrol" class="hata-kutusu mb-4" role="alert">{{ errorKontrol }}</p>

    <!-- Kalite Kontrol Tablosu -->
    <VeriTablosu
      :basliklar="[
        'Tarih',
        'Şantiye',
        'Poz',
        'Kontrol Tipi',
        'Durum',
        'Beklenen Değer',
        'Ölçülen Değer',
        'Tolerans Aralığı',
        'Kontrol Eden',
        'Onaylayan',
        'Onay Tarihi',
        'Açıklama',
        'İşlem'
      ]"
      :bos-mu="!loadingKontroller && filteredKontroller.length === 0"
    >
      <template v-if="filteredKontroller.length">
        <tr
          v-for="k in paginatedKontroller"
          :key="k.id"
          class="transition-colors hover:bg-surface-100/60"
        >
          <td class="px-4 py-3 whitespace-nowrap text-surface-700">
            {{ tarihFormatla(k.tarih) }}
          </td>
          <td class="px-4 py-3 font-medium text-surface-900">
            {{ k.santiye_adi || '—' }}
          </td>
          <td class="px-4 py-3 text-surface-600">
            {{ k.poz_kod || '—' }} - {{ k.poz_adi || '—' }}
          </td>
          <td class="px-4 py-3">
            {{ kontrolTipiFormatla(k.kontrol_tipi) }}
          </td>
          <td class="px-4 py-3">
            <span :class="durumFormatla(k.durum).class">
              {{ durumFormatla(k.durum).label }}
            </span>
          </td>
          <td class="px-4 py-3 font-mono text-surface-700">
            {{ k.beklenen_deger || '—' }}
          </td>
          <td class="px-4 py-3 font-mono text-surface-700">
            {{ k.olculen_deger || '—' }}
          </td>
          <td class="px-4 py-3 font-mono text-surface-700">
            {{ k.tolerek_aralik || '—' }}
          </td>
          <td class="px-4 py-3 text-surface-600">
            {{ k.kontrol_eden_adi || '—' }}
          </td>
          <td class="px-4 py-3 text-surface-600">
            {{ k.onaylayan_adi || '—' }}
          </td>
          <td class="px-4 py-3 whitespace-nowrap text-surface-600">
            {{ k.onay_tarihi ? tarihFormatla(k.onay_tarihi) : '—' }}
          </td>
          <td class="px-4 py-3 max-w-md truncate text-surface-600">
            {{ k.aciklama || '—' }}
          </td>
          <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
            <div class="flex items-center gap-2">
              <button
                type="button"
                class="text-sm font-medium text-primary-700 hover:underline"
                @click="Fm.duzenleAc(k)"
              >
                Düzenle
              </button>
              <button
                type="button"
                class="text-sm font-medium text-red-700 hover:underline"
                @click="silKaliteKontrol(k.id)"
              >
                Sil
              </button>
            </div>
          </td>
        </tr>
      </template>
      <tr v-else>
        <td colspan="13" class="px-4 py-8 text-center text-sm text-surface-400">
          Kalite kontrol kaydı bulunmuyor.
        </td>
      </tr>
    </VeriTablosu>

    <!-- Sayfalama -->
    <Sayfalama
      :sayfa="sayfa"
      :toplam="toplamSayfa"
      :yukleniyor="loadingKontroller"
      @sayfa-degistir="(s) => (sayfa = s)"
    />
  </div>
</template>

<script setup lang="ts">
// Ek computed özellikler
const paginatedKontroller = computed(() => {
  const start = (sayfa.value - 1) * limit.value
  const end = start + limit.value
  return filteredKontroller.value.slice(start, end)
})

const toplamSayfa = computed(() => Math.ceil(filteredKontroller.value.length / limit.value))
</script>