/**
 * TaseronHakedisleri.vue - Taşeron Hakedişleri Vue 3 Component
 */

import { computed, onMounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { constructionApi } from '@/services/constructionApi'
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
const hakedisler = ref([])
const loadingHakedisler = ref(true)
const errorHakedis = ref(null)

// Pagination and filter state
const sayfa = ref(1)
const limit = ref(20)
const arama = ref('')
const filtreSantiye = ref('')
const filtreTaseron = ref('')
const filtreDurum = ref('tum')
const filtreMuhasebeDurum = ref('tum')
const filtreDonemBaslangic = ref('')
const filtreDonemBitis = ref('')
const santiyeler = ref([])
const taseronlar = ref([])

// Computed for filtered records
const filteredHakedisler = computed(() => {
  let result = hakedisler.value

  if (arama.value) {
    result = result.filter(
      (h) =>
        h.hakedis_no?.includes(arama.value) ||
        h.aciklama?.includes(arama.value) ||
        h.santiye_adi?.includes(arama.value) ||
        h.taseron_adi?.includes(arama.value)
    )
  }

  if (filtreSantiye.value) {
    result = result.filter((h) => h.santiye_id === Number(filtreSantiye.value))
  }

  if (filtreTaseron.value) {
    result = result.filter((h) => h.taseron_id === Number(filtreTaseron.value))
  }

  if (filtreDurum.value !== 'tum') {
    result = result.filter((h) => h.durum === filtreDurum.value)
  }

  if (filtreMuhasebeDurum.value !== 'tum') {
    result = result.filter((h) => h.muhasebe_durumu === filtreMuhasebeDurum.value)
  }

  if (filtreDonemBaslangic.value) {
    result = result.filter((h) => h.donem_baslangic >= filtreDonemBaslangic.value)
  }

  if (filtreDonemBitis.value) {
    result = result.filter((h) => h.donem_bitis <= filtreDonemBitis.value)
  }

  return result
})

// Load hakedisler from API
async function yukleHakedisler() {
  loadingHakedisler.value = true
  errorHakedis.value = null
  try {
    const response = await constructionApi.listSubcontractorProgressBillings({
      page: sayfa.value,
      limit: limit.value,
      search: arama.value,
      santiye_id: filtreSantiye.value || undefined,
      taseron_id: filtreTaseron.value || undefined,
      durum: filtreDurum.value !== 'tum' ? filtreDurum.value : undefined,
      muhasebe_durumu: filtreMuhasebeDurum.value !== 'tum' ? filtreMuhasebeDurum.value : undefined,
      donem_baslangic: filtreDonemBaslangic.value || undefined,
      donem_bitis: filtreDonemBitis.value || undefined,
    })
    hakedisler.value = response.data || []
  } catch (error: any) {
    hataMesaji(error, 'Hakedişler yüklenirken hata oluştu')
    errorHakedis.value = error.message
  } finally {
    loadingHakedisler.value = false
  }
}

// Load construction sites and subcontractors for filter dropdown
async function yukleFiltreVerileri() {
  try {
    const [santiyeRes, taseronRes] = await Promise.all([
      constructionApi.listSites(),
      constructionApi.listSubcontractors(),
    ])
    santiyeler.value = santiyeRes.data || []
    taseronlar.value = taseronRes.data || []
  } catch (error: any) {
    hataMesaji(error, 'Filtre verileri yüklenirken hata oluştu')
  }
}

// Delete a hakedis
async function silHakedis(id: number) {
  if (!confirm('Bu hakedişi silmek istediğinizden emin misiniz?')) return
  try {
    await constructionApi.deleteSubcontractorProgressBilling(id)
    yukleHakedisler()
  } catch (error: any) {
    hataMesaji(error, 'Hakediş silinirken hata oluştu')
  }
}

// Post to accounting (muhasebeye naklet)
async function nakletMuhasebe(id: number) {
  if (!confirm('Bu hakedişi muhasebeye nakletmek istediğinizden emin misiniz?')) return
  try {
    await accountingApi.postSubcontractorProgressBilling(id)
    yukleHakedisler()
  } catch (error: any) {
    hataMesaji(error, 'Muhasebeye nakletme sırasında hata oluştu')
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

// Format status
function durumFormatla(durum?: string) {
  if (!durum) return '—'
  const labels: Record<string, { label: string; class: string }> = {
    taslak: { label: 'Taslak', class: 'bg-amber-100 text-amber-800' },
    onaylandi: { label: 'Onaylandı', class: 'bg-emerald-100 text-emerald-800' },
    reddedildi: { label: 'Reddedildi', class: 'bg-red-100 text-red-800' },
    odendi: { label: 'Ödendi', class: 'bg-blue-100 text-blue-800' },
  }
  const d = labels[durum] || { label: durum, class: 'bg-surface-200 text-surface-600' }
  return { label: d.label, class: `px-2 py-1 text-xs font-medium rounded-full ${d.class}` }
}

// Format accounting status
function muhasebeDurumuFormatla(durum?: string) {
  if (!durum) return '—'
  const labels: Record<string, { label: string; class: string }> = {
    bekliyor: { label: 'Bekliyor', class: 'bg-amber-100 text-amber-800' },
    nakledildi: { label: 'Nakledildi', class: 'bg-emerald-100 text-emerald-800' },
    hata: { label: 'Hata', class: 'bg-red-100 text-red-800' },
    iptal: { label: 'İptal', class: 'bg-surface-200 text-surface-600' },
  }
  const d = labels[durum] || { label: durum, class: 'bg-surface-200 text-surface-600' }
  return { label: d.label, class: `px-2 py-1 text-xs font-medium rounded-full ${d.class}` }
}

onMounted(() => {
  yukleFiltreVerileri()
  yukleHakedisler()
})

// Watch for filter changes
watch(
  [arama, filtreSantiye, filtreTaseron, filtreDurum, filtreMuhasebeDurum, filtreDonemBaslangic, filtreDonemBitis],
  () => {
    sayfa.value = 1
    yukleHakedisler()
  }
)

// Modal form for adding/editing hakedis
import { useKayitFormu } from '@/hooks/useKayitFormu'

type HakedisForm = {
  santiye_id: number
  taseron_id: number
  hakedis_no: string
  donem_baslangic: string
  donem_bitis: string
  toplam_tutar: number
  kesinti_toplam: number
  net_tutar: number
  durum: string
  muhasebe_durumu: string
  muhasebe_fis_id: number | null
  aciklama: string
  kalemler: Array<{
    poz_id: number
    miktar: number
    birim_fiyat: number
    tutar: number
    onceki_miktar: number
    bu_donem_miktar: number
    kumulatif_miktar: number
  }>
}

const Fm = useKayitFormu(
  {
    olustur: (veri) => constructionApi.createSubcontractorProgressBilling(veri),
    guncelle: (id, veri) => constructionApi.updateSubcontractorProgressBilling(id, veri),
  },
  () => ({
    santiye_id: 0,
    taseron_id: 0,
    hakedis_no: '',
    donem_baslangic: new Date().toISOString().split('T')[0],
    donem_bitis: new Date().toISOString().split('T')[0],
    toplam_tutar: 0,
    kesinti_toplam: 0,
    net_tutar: 0,
    durum: 'taslak',
    muhasebe_durumu: 'bekliyor',
    muhasebe_fis_id: null,
    aciklama: '',
    kalemler: [],
  }),
  (h) => ({
    santiye_id: h.santiye_id,
    taseron_id: h.taseron_id,
    hakedis_no: h.hakedis_no || '',
    donem_baslangic: h.donem_baslangic,
    donem_bitis: h.donem_bitis,
    toplam_tutar: h.toplam_tutar || 0,
    kesinti_toplam: h.kesinti_toplam || 0,
    net_tutar: h.net_tutar || 0,
    durum: h.durum || 'taslak',
    muhasebe_durumu: h.muhasebe_durumu || 'bekliyor',
    muhasebe_fis_id: h.muhasebe_fis_id,
    aciklama: h.aciklama || '',
    kalemler: h.kalemler || [],
  }),
  (form) => ({
    ...form,
    santiye_id: Number(form.santiye_id),
    taseron_id: Number(form.taseron_id),
    hakedis_no: form.hakedis_no?.trim(),
    donem_baslangic: form.donem_baslangic,
    donem_bitis: form.donem_bitis,
    toplam_tutar: Number(form.toplam_tutar),
    kesinti_toplam: Number(form.kesinti_toplam),
    net_tutar: Number(form.net_tutar),
    durum: form.durum,
    muhasebe_durumu: form.muhasebe_durumu,
    muhasebe_fis_id: form.muhasebe_fis_id ? Number(form.muhasebe_fis_id) : null,
    aciklama: form.aciklama?.trim(),
    kalemler: form.kalemler,
  }),
  (form) => {
    if (!form.santiye_id) return 'Şantiye seçimi zorunlu'
    if (!form.taseron_id) return 'Taşeron seçimi zorunlu'
    if (!form.hakedis_no) return 'Hakediş numarası zorunlu'
    if (!form.donem_baslangic) return 'Dönem başlangıç tarihi zorunlu'
    if (!form.donem_bitis) return 'Dönem bitiş tarihi zorunlu'
    if (new Date(form.donem_bitis) < new Date(form.donem_baslangic)) return 'Dönem bitiş tarihi başlangıç tarihinden önce olamaz'
    if (form.toplam_tutar < 0) return 'Toplam tutar negatif olamaz'
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
          Taşeron Hakedişleri
        </h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">
        + Yeni Hakediş
      </button>
    </div>

    <!-- Arama ve Filtre -->
    <div class="mb-6 flex flex-wrap items-center gap-3">
      <div class="flex-1 min-w-[250px]">
        <input
          v-model="arama"
          type="search"
          placeholder="Hakediş no, açıklama, şantiye veya taşeron ile ara..."
          class="alan w-full"
        />
      </div>
      <select v-model="filtreSantiye" class="alan" @change="sayfa = 1; yukleHakedisler()">
        <option value="">Tüm Şantiyeler</option>
        <option v-for="s in santiyeler" :key="s.id" :value="s.id">
          {{ s.adi }}
        </option>
      </select>
      <select v-model="filtreTaseron" class="alan" @change="sayfa = 1; yukleHakedisler()">
        <option value="">Tüm Taşeronlar</option>
        <option v-for="t in taseronlar" :key="t.id" :value="t.id">
          {{ t.adi }}
        </option>
      </select>
      <select v-model="filtreDurum" class="alan" @change="sayfa = 1; yukleHakedisler()">
        <option value="tum">Tüm Durumlar</option>
        <option value="taslak">Taslak</option>
        <option value="onaylandi">Onaylandı</option>
        <option value="reddedildi">Reddedildi</option>
        <option value="odendi">Ödendi</option>
      </select>
      <select v-model="filtreMuhasebeDurum" class="alan" @change="sayfa = 1; yukleHakedisler()">
        <option value="tum">Tüm Muhasebe Durumları</option>
        <option value="bekliyor">Bekliyor</option>
        <option value="nakledildi">Nakledildi</option>
        <option value="hata">Hata</option>
        <option value="iptal">İptal</option>
      </select>
      <input
        v-model="filtreDonemBaslangic"
        type="date"
        class="alan"
        @change="sayfa = 1; yukleHakedisler()"
      />
      <input
        v-model="filtreDonemBitis"
        type="date"
        class="alan"
        @change="sayfa = 1; yukleHakedisler()"
      />
      <button type="button" class="ikincil-dugme" @click="yukleHakedisler">
        Yenile
      </button>
    </div>

    <!-- Hata Mesajı -->
    <p v-if="errorHakedis" class="hata-kutusu mb-4" role="alert">{{ errorHakedis }}</p>

    <!-- Hakediş Tablosu -->
    <VeriTablosu
      :basliklar="[
        'Hakediş No',
        'Şantiye',
        'Taşeron',
        'Dönem',
        'Toplam Tutar (TL)',
        'Kesinti Toplamı (TL)',
        'Net Tutar (TL)',
        'Durum',
        'Muhasebe Durumu',
        'Muhasebe Fişi',
        'İşlem'
      ]"
      :bos-mu="!loadingHakedisler && filteredHakedisler.length === 0"
    >
      <template v-if="filteredHakedisler.length">
        <tr
          v-for="h in paginatedHakedisler"
          :key="h.id"
          class="transition-colors hover:bg-surface-100/60"
        >
          <td class="px-4 py-3 whitespace-nowrap text-surface-700 font-mono">
            <VeriKaynakRozeti
              :aktif="auth.gelistiriciModu"
              tablo="insaat_taseron_hakedis"
              sutun="hakedis_no"
              alan="TaseronHakedis.hakedis_no"
              tip="varchar(50)"
              api="GET /api/v1/construction/subcontractor-billings/"
              :iliski="`id=${h.id}`"
            >
              {{ h.hakedis_no || '—' }}
            </VeriKaynakRozeti>
          </td>
          <td class="px-4 py-3 font-medium text-surface-900">
            {{ h.santiye_adi || '—' }}
          </td>
          <td class="px-4 py-3 text-surface-600">
            {{ h.taseron_adi || '—' }}
          </td>
          <td class="px-4 py-3 whitespace-nowrap text-surface-600">
            {{ tarihFormatla(h.donem_baslangic) }} - {{ tarihFormatla(h.donem_bitis) }}
          </td>
          <td class="px-4 py-3 font-mono tabular-nums text-right">
            {{ paraFormatla(h.toplam_tutar) }} ₺
          </td>
          <td class="px-4 py-3 font-mono tabular-nums text-right">
            {{ paraFormatla(h.kesinti_toplam) }} ₺
          </td>
          <td class="px-4 py-3 font-mono tabular-nums text-right font-bold" :class="h.net_tutar >= 0 ? 'text-emerald-600' : 'text-red-600'">
            {{ paraFormatla(h.net_tutar) }} ₺
          </td>
          <td class="px-4 py-3">
            <span :class="durumFormatla(h.durum).class">
              {{ durumFormatla(h.durum).label }}
            </span>
          </td>
          <td class="px-4 py-3">
            <span :class="muhasebeDurumuFormatla(h.muhasebe_durumu).class">
              {{ muhasebeDurumuFormatla(h.muhasebe_durumu).label }}
            </span>
          </td>
          <td class="px-4 py-3 text-surface-600">
            {{ h.muhasebe_fis_id ? 'Fiş #' + h.muhasebe_fis_id : '—' }}
          </td>
          <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
            <div class="flex items-center gap-2">
              <button
                type="button"
                class="text-sm font-medium text-primary-700 hover:underline"
                @click="Fm.duzenleAc(h)"
              >
                Düzenle
              </button>
              <button
                v-if="h.muhasebe_durumu === 'bekliyor' && h.durum === 'onaylandi'"
                type="button"
                class="text-sm font-medium text-blue-700 hover:underline"
                @click="nakletMuhasebe(h.id)"
              >
                Naklet
              </button>
              <button
                type="button"
                class="text-sm font-medium text-red-700 hover:underline"
                @click="silHakedis(h.id)"
              >
                Sil
              </button>
            </div>
          </td>
        </tr>
      </template>
      <tr v-else>
        <td colspan="11" class="px-4 py-8 text-center text-sm text-surface-400">
          Hakediş kaydı bulunmuyor.
        </td>
      </tr>
    </VeriTablosu>

    <!-- Sayfalama -->
    <Sayfalama
      :sayfa="sayfa"
      :toplam="toplamSayfa"
      :yukleniyor="loadingHakedisler"
      @sayfa-degistir="(s) => (sayfa = s)"
    />
  </div>
</template>

<script setup lang="ts">
// Ek computed özellikler
const paginatedHakedisler = computed(() => {
  const start = (sayfa.value - 1) * limit.value
  const end = start + limit.value
  return filteredHakedisler.value.slice(start, end)
})

const toplamSayfa = computed(() => Math.ceil(filteredHakedisler.value.length / limit.value))
</script>