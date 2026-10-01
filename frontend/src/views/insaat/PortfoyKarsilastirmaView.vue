<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { AlertTriangle, BarChart3, CheckCircle2, RefreshCw, Search, SlidersHorizontal } from 'lucide-vue-next'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi } from '@/services/insaatApi'
import { PROJE_DURUMLARI, type PortfoyKarsilastirma } from '@/types/insaat'

const yil = ref(new Date().getFullYear())
const arama = ref('')
const durum = ref('')
const sinif = ref('')
const yukleniyor = ref(false)
const hata = ref('')
const rapor = ref<PortfoyKarsilastirma | null>(null)

const para = (deger: string): string =>
  new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(Number(deger || 0))
const yuzde = (deger: string): string => deger || '0%'
const sapmaClass = (deger: string): string => Number(deger || 0) > 0 ? 'text-rose-700' : 'text-emerald-700'
const durumSecenekleri = computed(() => Object.entries(PROJE_DURUMLARI))

async function yukle(): Promise<void> {
  yukleniyor.value = true
  hata.value = ''
  try {
    rapor.value = await insaatApi.portfoyOzeti({
      yil: yil.value,
      ...(arama.value.trim() ? { arama: arama.value.trim() } : {}),
      ...(durum.value ? { durum: durum.value } : {}),
      ...(sinif.value.trim() ? { sinif: sinif.value.trim().toUpperCase() } : {}),
    })
  } catch (e) {
    hata.value = hataMesaji(e)
    rapor.value = null
  } finally {
    yukleniyor.value = false
  }
}

function filtreleriTemizle(): void {
  arama.value = ''
  durum.value = ''
  sinif.value = ''
}

watch([durum, sinif], () => void yukle())
onMounted(() => void yukle())
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <header class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-sm font-medium uppercase tracking-[0.18em] text-primary-700">Yönetici paneli · Portföy</p>
        <h1 class="font-heading text-3xl font-bold tracking-tight text-surface-900">Proje karşılaştırma merkezi</h1>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-surface-500">Projelerin bütçe, onaylı hakediş ve maliyet sapmasını aynı dönem içinde karşılaştırın.</p>
      </div>
      <button type="button" class="ikincil-dugme" :disabled="yukleniyor" @click="yukle">
        <RefreshCw class="mr-2 inline h-4 w-4" :class="{ 'animate-spin': yukleniyor }" /> Yenile
      </button>
    </header>

    <section class="rounded-2xl border border-surface-200 bg-white p-4 shadow-sm">
      <div class="mb-3 flex items-center gap-2 text-sm font-semibold text-surface-800"><SlidersHorizontal class="h-4 w-4 text-primary-700" /> Filtreler</div>
      <form class="grid gap-3 md:grid-cols-[1.5fr_0.7fr_1fr_0.8fr_auto]" @submit.prevent="yukle">
        <label class="relative">
          <span class="sr-only">Proje ara</span>
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-400" />
          <input v-model="arama" class="alan pl-9" type="search" placeholder="Kod veya proje adı…" />
        </label>
        <label><span class="sr-only">Yıl</span><input v-model.number="yil" class="alan" type="number" min="2000" max="2100" /></label>
        <label><span class="sr-only">Durum</span><select v-model="durum" class="alan"><option value="">Tüm durumlar</option><option v-for="[kod, etiket] in durumSecenekleri" :key="kod" :value="kod">{{ etiket }}</option></select></label>
        <label><span class="sr-only">Yapı sınıfı</span><input v-model="sinif" class="alan" type="text" placeholder="Yapı sınıfı (IV-A)" /></label>
        <div class="flex gap-2">
          <button class="birincil-dugme" type="submit">Uygula</button>
          <button class="ikincil-dugme" type="button" title="Filtreleri temizle" @click="filtreleriTemizle">Temizle</button>
        </div>
      </form>
    </section>

    <p v-if="hata" class="hata-kutusu mt-4" role="alert"><AlertTriangle class="mr-2 inline h-4 w-4" />{{ hata }}</p>

    <template v-if="rapor">
      <section class="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article class="rounded-2xl border border-surface-200 bg-white p-5 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-wider text-surface-500">İncelenen proje</p>
          <strong class="mt-2 block text-3xl font-bold text-surface-900">{{ rapor.proje_sayisi }}</strong>
          <span class="text-xs text-surface-500">{{ rapor.yil }} dönemi</span>
        </article>
        <article class="rounded-2xl border border-surface-200 bg-white p-5 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-wider text-surface-500">Toplam bütçe</p>
          <strong class="mt-2 block text-2xl font-bold text-surface-900">{{ para(rapor.toplam_butce) }}</strong>
          <span class="text-xs text-surface-500">Aktif poz planları</span>
        </article>
        <article class="rounded-2xl border border-surface-200 bg-white p-5 shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-wider text-surface-500">Gerçekleşen maliyet</p>
          <strong class="mt-2 block text-2xl font-bold text-surface-900">{{ para(rapor.toplam_gerceklesen) }}</strong>
          <span class="text-xs text-surface-500">Onaylı hakedişler</span>
        </article>
        <article class="rounded-2xl border border-surface-200 bg-surface-900 p-5 text-white shadow-sm">
          <p class="text-xs font-semibold uppercase tracking-wider text-surface-300">Portföy sapması</p>
          <strong class="mt-2 block text-2xl font-bold" :class="Number(rapor.toplam_sapma) > 0 ? 'text-rose-300' : 'text-emerald-300'">{{ para(rapor.toplam_sapma) }}</strong>
          <span class="text-xs text-surface-300">Gerçekleşen − bütçe</span>
        </article>
      </section>

      <section class="mt-6 overflow-hidden rounded-2xl border border-surface-200 bg-white shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-surface-100 px-5 py-4">
          <div><h2 class="font-heading text-lg font-bold text-surface-900">Proje bazında görünüm</h2><p class="mt-1 text-xs text-surface-500">Rapor: {{ rapor.yil }} · {{ rapor.proje_sayisi }} proje</p></div>
          <BarChart3 class="h-5 w-5 text-primary-700" />
        </div>
        <div v-if="!rapor.projeler.length" class="p-10 text-center text-sm text-surface-500">Seçilen filtrelerle eşleşen proje bulunamadı.</div>
        <div v-else class="overflow-x-auto">
          <table class="w-full min-w-[850px] text-left text-sm">
            <thead class="bg-surface-50 text-xs uppercase tracking-wider text-surface-500"><tr><th class="px-5 py-3">Proje</th><th class="px-4 py-3">Durum</th><th class="px-4 py-3">Yapı sınıfı</th><th class="px-4 py-3 text-right">Bütçe</th><th class="px-4 py-3 text-right">Gerçekleşen</th><th class="px-4 py-3 text-right">Sapma</th><th class="px-5 py-3 text-right">Durum</th></tr></thead>
            <tbody class="divide-y divide-surface-100">
              <tr v-for="proje in rapor.projeler" :key="proje.id" class="transition-colors hover:bg-surface-50">
                <td class="px-5 py-4"><strong class="block text-surface-900">{{ proje.proje_kodu }}</strong><span class="text-xs text-surface-500">{{ proje.proje_adi }}</span></td>
                <td class="px-4 py-4 text-surface-600">{{ proje.durum }}</td>
                <td class="px-4 py-4 font-mono text-xs text-surface-600">{{ proje.yapisinif_kodu || '—' }}</td>
                <td class="px-4 py-4 text-right tabular-nums">{{ para(proje.butce) }}</td>
                <td class="px-4 py-4 text-right tabular-nums">{{ para(proje.gerceklesen) }}</td>
                <td class="px-4 py-4 text-right tabular-nums" :class="sapmaClass(proje.sapma)"><strong>{{ para(proje.sapma) }}</strong><span class="ml-1 text-xs">({{ yuzde(proje.sapma_yuzde) }})</span></td>
                <td class="px-5 py-4 text-right"><span v-if="Number(proje.sapma) <= 0" class="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700"><CheckCircle2 class="h-4 w-4" /> Kontrolde</span><span v-else class="inline-flex items-center gap-1 text-xs font-semibold text-rose-700"><AlertTriangle class="h-4 w-4" /> İncele</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <p class="border-t border-surface-100 px-5 py-3 text-xs text-surface-500">{{ rapor.veri_notu }}</p>
      </section>
    </template>
    <div v-else-if="yukleniyor" class="mt-8 rounded-2xl border border-surface-200 bg-white p-12 text-center text-sm text-surface-500">Portföy verileri hazırlanıyor…</div>
  </div>
</template>
