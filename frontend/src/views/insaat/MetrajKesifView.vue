<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { constructionApi } from '@/services/constructionApi'
import type { IFCImportJob, Mahal, Metraj, Proje } from '@/types/insaat'

const projeler = ref<Proje[]>([])
const seciliProje = ref<number | null>(null)
const mahaller = ref<Mahal[]>([])
const metrajlar = ref<Metraj[]>([])
const ifcIsleri = ref<IFCImportJob[]>([])
const yukleniyor = ref(false)
const hata = ref('')

async function yukle(): Promise<void> {
  try {
    projeler.value = await tumunuGetir(insaatApi.projeler.liste)
    if (!seciliProje.value) seciliProje.value = projeler.value[0]?.id || null
    await getir()
  } catch (e) { hata.value = hataMesaji(e) }
}
async function getir(): Promise<void> {
  yukleniyor.value = true; hata.value = ''
  try {
    const projeFiltre = seciliProje.value ? { proje: seciliProje.value } : {}
    const [mahalListe, metrajListe, ifcListe] = await Promise.all([
      tumunuGetir(insaatApi.mahaller.liste, projeFiltre),
      insaatApi.metrajlar.liste({ page: 1 }),
      constructionApi.ifcImportlari.liste(seciliProje.value ? { project: seciliProje.value, page: 1 } : { page: 1 }),
    ])
    mahaller.value = mahalListe.slice(0, 5)
    metrajlar.value = metrajListe.results.slice(0, 5)
    ifcIsleri.value = (ifcListe.results || []).slice(0, 5)
  } catch (e) { hata.value = hataMesaji(e) } finally { yukleniyor.value = false }
}
const mahalSayisi = ref(0)
async function ozetSayilari(): Promise<void> {
  try {
    const projeFiltre = seciliProje.value ? { proje: seciliProje.value } : {}
    const [mahalTumu, metrajTumu] = await Promise.all([
      tumunuGetir(insaatApi.mahaller.liste, projeFiltre),
      tumunuGetir(insaatApi.metrajlar.liste),
    ])
    mahalSayisi.value = mahalTumu.length
    metrajSayisi.value = metrajTumu.length
  } catch { /* özet sayaçları sessiz geçilir */ }
}
const metrajSayisi = ref(0)
async function yenile(): Promise<void> { await Promise.all([getir(), ozetSayilari()]) }
onMounted(async () => { await yukle(); await ozetSayilari() })
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat / Maliyet</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Metraj &amp; Keşif</h1>
        <p class="mt-1 text-sm text-surface-500">Mahal, metraj, model ve analiz akışlarını tek ekranda toplayın; üretim mevcut ekranlarda yapılır.</p>
      </div>
    </div>
    <div class="mb-5 flex flex-wrap gap-2 rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card">
      <select v-model.number="seciliProje" class="alan min-w-64">
        <option :value="null">Proje seçin</option>
        <option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} — {{ x.ad }}</option>
      </select>
      <button class="birincil-dugme" type="button" :disabled="yukleniyor" @click="yenile">{{ yukleniyor ? 'Yükleniyor…' : 'Yenile' }}</button>
    </div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">1. Metraj Özeti</h2>
    <div class="mb-6 grid gap-3 sm:grid-cols-3">
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Mahal</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ mahalSayisi }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Metraj Kaydı</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ metrajSayisi }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">IFC İşi</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ ifcIsleri.length }}</p></div>
    </div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">2. Mahaller</h2>
    <div class="mb-6 overflow-x-auto rounded-xl border border-surface-200 bg-surface-50 shadow-card">
      <table class="min-w-full divide-y divide-surface-200 text-sm">
        <thead class="bg-surface-100"><tr><th class="px-4 py-3 text-left">Mahal</th><th class="px-4 py-3 text-left">Tip</th><th class="px-4 py-3 text-right">Alan (m²)</th></tr></thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="x in mahaller" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-medium">{{ x.mahal_no }} — {{ x.mahal_adi }}</td><td class="px-4 py-3">{{ x.mahal_tipi }}</td><td class="px-4 py-3 text-right">{{ x.alan_m2 }}</td></tr>
          <tr v-if="!mahaller.length"><td colspan="3" class="px-4 py-8 text-center text-surface-500">Seçili projede mahal yok.</td></tr>
        </tbody>
      </table>
    </div>
    <div class="mb-6"><RouterLink to="/insaat/mahaller" class="ikincil-dugme">Mahal Listesi ekranını aç →</RouterLink></div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">3. Metrajlar</h2>
    <div class="mb-6 overflow-x-auto rounded-xl border border-surface-200 bg-surface-50 shadow-card">
      <table class="min-w-full divide-y divide-surface-200 text-sm">
        <thead class="bg-surface-100"><tr><th class="px-4 py-3 text-left">Ad</th><th class="px-4 py-3 text-left">İfade</th><th class="px-4 py-3 text-right">Sonuç</th></tr></thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="x in metrajlar" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-medium">{{ x.ad }}</td><td class="px-4 py-3 font-mono text-xs">{{ x.ifade }}</td><td class="px-4 py-3 text-right">{{ x.sonuc }} {{ x.birim }}</td></tr>
          <tr v-if="!metrajlar.length"><td colspan="3" class="px-4 py-8 text-center text-surface-500">Metraj kaydı yok — Mahal ekranından üretin.</td></tr>
        </tbody>
      </table>
    </div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">4. IFC / Modelden Metraj</h2>
    <div class="mb-6 overflow-x-auto rounded-xl border border-surface-200 bg-surface-50 shadow-card">
      <table class="min-w-full divide-y divide-surface-200 text-sm">
        <thead class="bg-surface-100"><tr><th class="px-4 py-3 text-left">Dosya</th><th class="px-4 py-3 text-left">Durum</th><th class="px-4 py-3 text-left">Yıl</th></tr></thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="x in ifcIsleri" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-medium">{{ x.file_name }}</td><td class="px-4 py-3">{{ x.status }}</td><td class="px-4 py-3">{{ x.year }}</td></tr>
          <tr v-if="!ifcIsleri.length"><td colspan="3" class="px-4 py-8 text-center text-surface-500">IFC işi yok.</td></tr>
        </tbody>
      </table>
    </div>
    <div class="mb-6"><RouterLink to="/insaat/ifc-import" class="ikincil-dugme">IFC içe aktarma ekranını aç →</RouterLink></div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">5. Analiz Kitabı</h2>
    <div class="mb-6 rounded-xl border border-surface-200 bg-surface-50 p-5 shadow-card">
      <p class="text-sm text-surface-600">Poz bileşen, nakliye ve birim fiyat analizleri mevcut Analiz Kitabı ekranında yönetilir.</p>
      <div class="mt-3"><RouterLink to="/insaat/analiz-kitabi" class="ikincil-dugme">Analiz Kitabı ekranını aç →</RouterLink></div>
    </div>
  </div>
</template>
