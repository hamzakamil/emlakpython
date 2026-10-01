<script setup lang="ts">
import { onMounted, ref } from 'vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import type { Proje, ProjeKarZarar } from '@/types/insaat'

const projeler = ref<Proje[]>([])
const seciliProje = ref<number | null>(null)
const yil = ref(new Date().getFullYear())
const rapor = ref<ProjeKarZarar | null>(null)
const hata = ref('')
const yukleniyor = ref(false)
const para = (v: string): string => Number(v).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 2 })
async function yukle(): Promise<void> {
  try { projeler.value = await tumunuGetir(insaatApi.projeler.liste); seciliProje.value = projeler.value[0]?.id || null } catch (e) { hata.value = hataMesaji(e) }
}
async function getir(): Promise<void> {
  if (!seciliProje.value) { hata.value = 'Rapor için proje seçin.'; return }
  yukleniyor.value = true; hata.value = ''
  try { rapor.value = await insaatApi.karZarar(seciliProje.value, yil.value) } catch (e) { hata.value = hataMesaji(e); rapor.value = null } finally { yukleniyor.value = false }
}
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6"><p class="text-sm font-medium text-primary-700">İnşaat / Finans</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Proje Kâr / Zarar ve Bütçe Sapması</h1><p class="mt-1 text-sm text-surface-500">Bütçelenen poz maliyetini onaylı hakediş gerçekleşmeleriyle karşılaştırın.</p></div>
    <div class="mb-5 flex flex-wrap gap-2 rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><select v-model.number="seciliProje" class="alan min-w-64"><option :value="null">Proje seçin</option><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} — {{ x.ad }}</option></select><input v-model.number="yil" class="alan w-28" type="number" min="2000" max="2100" /><button class="birincil-dugme" type="button" :disabled="yukleniyor" @click="getir">{{ yukleniyor ? 'Hesaplanıyor...' : 'Raporu Getir' }}</button></div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <template v-if="rapor"><div class="mb-5 grid gap-3 sm:grid-cols-4"><div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Bütçe</p><p class="mt-1 text-xl font-bold text-primary-800">{{ para(rapor.butcelenen_maliyet) }}</p></div><div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Gerçekleşen</p><p class="mt-1 text-xl font-bold text-amber-700">{{ para(rapor.gerceklesen_maliyet) }}</p></div><div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Maliyet Sapması</p><p class="mt-1 text-xl font-bold" :class="Number(rapor.maliyet_sapmasi) > 0 ? 'text-danger-700' : 'text-success-700'">{{ para(rapor.maliyet_sapmasi) }} ({{ rapor.maliyet_sapmasi_yuzde }})</p></div><div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Net Sonuç</p><p class="mt-1 text-xl font-bold text-danger-700">{{ para(rapor.net_sonuc) }}</p></div></div><p class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">{{ rapor.veri_notu }}</p><VeriTablosu :basliklar="['Poz','Bütçe','Gerçekleşen Metraj Değeri','Sapma']" :bos-mu="!rapor.pozlar.length"><tr v-for="x in rapor.pozlar" :key="x.poz_no" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-semibold">{{ x.poz_no }} — {{ x.poz_ad }}</td><td class="px-4 py-3 text-right">{{ para(x.butce) }}</td><td class="px-4 py-3 text-right">{{ para(x.gerceklesen_metraj_degeri) }}</td><td class="px-4 py-3 text-right">{{ para(x.sapma) }}</td></tr></VeriTablosu></template><div v-else-if="!yukleniyor" class="rounded-xl border border-dashed border-surface-300 bg-surface-50 p-10 text-center text-surface-500">Proje ve yıl seçip raporu getirin.</div>
  </div>
</template>
