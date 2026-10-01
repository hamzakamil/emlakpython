<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import type { Proje, ProjeNakitAkisi } from '@/types/insaat'

const projeler = ref<Proje[]>([])
const seciliProje = ref<number | null>(null)
const yil = ref(new Date().getFullYear())
const rapor = ref<ProjeNakitAkisi | null>(null)
const yukleniyor = ref(false)
const hata = ref('')
const para = (v: string): string => Number(v).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 2 })
const ayAdi = (donem: string): string => new Intl.DateTimeFormat('tr-TR', { month: 'long' }).format(new Date(`${donem}-01T00:00:00`))
async function yukle(): Promise<void> {
  try { projeler.value = await tumunuGetir(insaatApi.projeler.liste); if (!seciliProje.value) seciliProje.value = projeler.value[0]?.id || null; if (seciliProje.value) await getir() } catch (e) { hata.value = hataMesaji(e) }
}
async function getir(): Promise<void> {
  if (!seciliProje.value) { hata.value = 'Nakit akışı için proje seçin.'; return }
  yukleniyor.value = true; hata.value = ''
  try { rapor.value = await insaatApi.nakitAkisi(seciliProje.value, yil.value) } catch (e) { hata.value = hataMesaji(e); rapor.value = null } finally { yukleniyor.value = false }
}
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p class="text-sm font-medium text-primary-700">İnşaat / Finans</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Proje Nakit Akışı</h1><p class="mt-1 text-sm text-surface-500">Planlanan maliyet ile onaylanmış hakediş giderlerini dönem bazında karşılaştırın.</p></div></div>
    <div class="mb-5 flex flex-wrap gap-2 rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><select v-model.number="seciliProje" class="alan min-w-64"><option :value="null">Proje seçin</option><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} — {{ x.ad }}</option></select><input v-model.number="yil" class="alan w-28" type="number" min="2000" max="2100" /><button class="birincil-dugme" type="button" :disabled="yukleniyor" @click="getir">{{ yukleniyor ? 'Hesaplanıyor...' : 'Raporu Getir' }}</button></div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <template v-if="rapor">
      <div class="mb-5 grid gap-3 sm:grid-cols-3"><div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Planlanan Gider</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ para(rapor.planlanan_gider) }}</p></div><div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Gerçekleşen Hakediş</p><p class="mt-1 text-2xl font-bold text-amber-700">{{ para(rapor.gerceklesen_gider) }}</p></div><div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Net Nakit</p><p class="mt-1 text-2xl font-bold text-danger-700">{{ para(rapor.net) }}</p></div></div>
      <p class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">{{ rapor.veri_notu }}</p>
      <div class="overflow-x-auto rounded-xl border border-surface-200 bg-surface-50 shadow-card"><table class="min-w-full divide-y divide-surface-200 text-sm"><thead class="bg-surface-100"><tr><th class="px-4 py-3 text-left">Dönem</th><th class="px-4 py-3 text-right">Gerçekleşen Gider</th><th class="px-4 py-3 text-right">Gelir</th><th class="px-4 py-3 text-right">Net</th><th class="px-4 py-3 text-right">Kümülatif Net</th></tr></thead><tbody class="divide-y divide-surface-100"><tr v-for="x in rapor.aylar" :key="x.donem" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-semibold">{{ ayAdi(x.donem) }}</td><td class="px-4 py-3 text-right">{{ para(x.gerceklesen_gider) }}</td><td class="px-4 py-3 text-right">{{ para(x.gelir) }}</td><td class="px-4 py-3 text-right text-danger-700">{{ para(x.net) }}</td><td class="px-4 py-3 text-right font-semibold">{{ para(x.kümülatif_net) }}</td></tr></tbody></table></div>
    </template>
    <div v-else-if="!yukleniyor" class="rounded-xl border border-dashed border-surface-300 bg-surface-50 p-10 text-center text-surface-500">Proje seçip raporu getirin.</div>
  </div>
</template>
