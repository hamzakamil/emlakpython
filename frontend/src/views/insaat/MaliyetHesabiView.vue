<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import type { PozPlan, Proje, SEkgrisiRaporu, YaklasikMaliyet } from '@/types/insaat'

const projeler = ref<Proje[]>([])
const seciliProje = ref<number | null>(null)
const yil = ref(new Date().getFullYear())
const yaklasiklar = ref<YaklasikMaliyet[]>([])
const pozPlanlari = ref<PozPlan[]>([])
const sEgrisi = ref<SEkgrisiRaporu | null>(null)
const yaklasikToplam = ref('0.00')
const yukleniyor = ref(false)
const hata = ref('')
const para = (v: string): string => Number(v).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 2 })

async function yukle(): Promise<void> {
  try {
    projeler.value = await tumunuGetir(insaatApi.projeler.liste)
    if (!seciliProje.value) seciliProje.value = projeler.value[0]?.id || null
    await getir()
  } catch (e) { hata.value = hataMesaji(e) }
}
async function getir(): Promise<void> {
  if (!seciliProje.value) { hata.value = 'Maliyet özeti için proje seçin.'; return }
  yukleniyor.value = true; hata.value = ''
  try {
    const [ymTumu, ppTumu] = await Promise.all([
      tumunuGetir(insaatApi.yaklasikMaliyetler.liste, { proje: seciliProje.value, yil: yil.value }),
      tumunuGetir(insaatApi.pozPlanlari.liste, { proje: seciliProje.value, yil: yil.value }),
    ])
    yaklasiklar.value = ymTumu.slice(0, 5)
    pozPlanlari.value = ppTumu.slice(0, 5)
    yaklasikToplam.value = ymTumu.reduce((t, x) => t + Number(x.toplam_tutar || 0), 0).toFixed(2)
    try { sEgrisi.value = await insaatApi.sEgrisi(seciliProje.value, yil.value) }
    catch { sEgrisi.value = null }
  } catch (e) { hata.value = hataMesaji(e) } finally { yukleniyor.value = false }
}
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat / Maliyet</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Maliyet Hesabı</h1>
        <p class="mt-1 text-sm text-surface-500">Yaklaşık maliyet, poz planı ve S-eğrisi akışlarını tek ekranda toplayın; üretim mevcut ekranlarda yapılır.</p>
      </div>
    </div>
    <div class="mb-5 flex flex-wrap gap-2 rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card">
      <select v-model.number="seciliProje" class="alan min-w-64">
        <option :value="null">Proje seçin</option>
        <option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} — {{ x.ad }}</option>
      </select>
      <input v-model.number="yil" class="alan w-28" type="number" min="2000" max="2100" />
      <button class="birincil-dugme" type="button" :disabled="yukleniyor" @click="getir">{{ yukleniyor ? 'Hesaplanıyor…' : 'Getir' }}</button>
    </div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">1. Maliyet Özeti</h2>
    <div class="mb-6 grid gap-3 sm:grid-cols-3">
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Yaklaşık Maliyet Toplamı</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ para(yaklasikToplam) }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Planlanan Değer</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ para(sEgrisi?.toplam_plan_deger || '0') }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Sapma</p><p class="mt-1 text-2xl font-bold text-amber-700">%{{ sEgrisi?.toplam_sapma_yuzde || '0' }}</p></div>
    </div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">2. Yaklaşık Maliyet</h2>
    <div class="mb-6 overflow-x-auto rounded-xl border border-surface-200 bg-surface-50 shadow-card">
      <table class="min-w-full divide-y divide-surface-200 text-sm">
        <thead class="bg-surface-100"><tr><th class="px-4 py-3 text-left">Ad</th><th class="px-4 py-3 text-left">Versiyon</th><th class="px-4 py-3 text-right">Toplam</th></tr></thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="x in yaklasiklar" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-medium">{{ x.ad }}</td><td class="px-4 py-3">v{{ x.versiyon }}</td><td class="px-4 py-3 text-right">{{ para(x.toplam_tutar) }}</td></tr>
          <tr v-if="!yaklasiklar.length"><td colspan="3" class="px-4 py-8 text-center text-surface-500">Seçili proje/yılda yaklaşık maliyet yok.</td></tr>
        </tbody>
      </table>
    </div>
    <div class="mb-6"><RouterLink to="/insaat/yaklasik-maliyet" class="ikincil-dugme">Yaklaşık Maliyet ekranını aç →</RouterLink></div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">3. Poz Planları</h2>
    <div class="mb-6 overflow-x-auto rounded-xl border border-surface-200 bg-surface-50 shadow-card">
      <table class="min-w-full divide-y divide-surface-200 text-sm">
        <thead class="bg-surface-100"><tr><th class="px-4 py-3 text-left">Poz</th><th class="px-4 py-3 text-right">Planlanan</th><th class="px-4 py-3 text-right">Gerçekleşen</th></tr></thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="x in pozPlanlari" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-medium">{{ x.poz_no }}</td><td class="px-4 py-3 text-right">{{ x.planlanan_miktar }}</td><td class="px-4 py-3 text-right">{{ x.gercek_miktar }}</td></tr>
          <tr v-if="!pozPlanlari.length"><td colspan="3" class="px-4 py-8 text-center text-surface-500">Seçili proje/yılda poz planı yok.</td></tr>
        </tbody>
      </table>
    </div>
    <div class="mb-6"><RouterLink to="/insaat/poz-planlari" class="ikincil-dugme">Poz Planları ekranını aç →</RouterLink></div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">4. S-Eğrisi / Maliyet Dağılımı</h2>
    <div class="mb-6 overflow-x-auto rounded-xl border border-surface-200 bg-surface-50 shadow-card">
      <table class="min-w-full divide-y divide-surface-200 text-sm">
        <thead class="bg-surface-100"><tr><th class="px-4 py-3 text-left">Poz</th><th class="px-4 py-3 text-right">Plan Değer</th><th class="px-4 py-3 text-right">Gerçek Değer</th><th class="px-4 py-3 text-right">Sapma %</th></tr></thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="x in (sEgrisi?.pozlar || []).slice(0, 8)" :key="x.poz_no" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-medium">{{ x.poz_no }}</td><td class="px-4 py-3 text-right">{{ para(x.plan_deger) }}</td><td class="px-4 py-3 text-right">{{ para(x.gercek_deger) }}</td><td class="px-4 py-3 text-right">%{{ x.sapma_yuzde }}</td></tr>
          <tr v-if="!(sEgrisi?.pozlar || []).length"><td colspan="4" class="px-4 py-8 text-center text-surface-500">S-eğrisi verisi yok — poz planlarına gerçekleşen metraj girin.</td></tr>
        </tbody>
      </table>
    </div>
    <div class="mb-6 flex flex-wrap gap-2">
      <RouterLink to="/insaat/poz-planlari" class="ikincil-dugme">S-eğrisi panelini aç →</RouterLink>
      <RouterLink to="/insaat/analiz-kitabi" class="ikincil-dugme">Analiz Kitabı ekranını aç →</RouterLink>
    </div>
  </div>
</template>
