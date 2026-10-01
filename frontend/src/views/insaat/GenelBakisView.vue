<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import type { GanttRaporu, PortfoyKarsilastirma, Proje, ProjeKarZarar, ProjeNakitAkisi, SEkgrisiRaporu } from '@/types/insaat'

const projeler = ref<Proje[]>([])
const seciliProje = ref<number | null>(null)
const yil = ref(new Date().getFullYear())
const portfoy = ref<PortfoyKarsilastirma | null>(null)
const nakit = ref<ProjeNakitAkisi | null>(null)
const karZarar = ref<ProjeKarZarar | null>(null)
const sEgrisi = ref<SEkgrisiRaporu | null>(null)
const gantt = ref<GanttRaporu | null>(null)
const yukleniyor = ref(false)
const hata = ref('')
const para = (v: string): string => Number(v).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 2 })
const ganttIlerleme = (): string => {
  const cubuklar = gantt.value?.cubuklar || []
  if (!cubuklar.length) return '0'
  return (cubuklar.reduce((t, x) => t + Number(x.ilerleme_yuzde || 0), 0) / cubuklar.length).toFixed(1)
}
const ganttTarihli = (): number => (gantt.value?.cubuklar || []).filter((x) => x.tarih_atandi).length

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
    portfoy.value = await insaatApi.portfoyOzeti({ yil: yil.value })
  } catch { portfoy.value = null }
  if (!seciliProje.value) { yukleniyor.value = false; return }
  const pid = seciliProje.value
  try { nakit.value = await insaatApi.nakitAkisi(pid, yil.value) } catch { nakit.value = null }
  try { karZarar.value = await insaatApi.karZarar(pid, yil.value) } catch { karZarar.value = null }
  try { sEgrisi.value = await insaatApi.sEgrisi(pid, yil.value) } catch { sEgrisi.value = null }
  try { gantt.value = await insaatApi.gantt(pid, yil.value) } catch { gantt.value = null }
  yukleniyor.value = false
}
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat / Maliyet</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Genel Bakış</h1>
        <p class="mt-1 text-sm text-surface-500">Portföy, nakit, kâr/zarar, ilerleme ve zaman çizelgesini tek ekranda izleyin; detay mevcut ekranlardadır.</p>
      </div>
    </div>
    <div class="mb-5 flex flex-wrap gap-2 rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card">
      <select v-model.number="seciliProje" class="alan min-w-64">
        <option :value="null">Proje seçin</option>
        <option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} — {{ x.ad }}</option>
      </select>
      <input v-model.number="yil" class="alan w-28" type="number" min="2000" max="2100" />
      <button class="birincil-dugme" type="button" :disabled="yukleniyor" @click="getir">{{ yukleniyor ? 'Yükleniyor…' : 'Getir' }}</button>
    </div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">1. Genel Maliyet Özeti</h2>
    <div class="mb-6 grid gap-3 sm:grid-cols-4">
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Proje Sayısı</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ portfoy?.proje_sayisi || 0 }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Toplam Bütçe</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ para(portfoy?.toplam_butce || '0') }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Gerçekleşen</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ para(portfoy?.toplam_gerceklesen || '0') }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Net Sonuç</p><p class="mt-1 text-2xl font-bold text-amber-700">{{ para(portfoy?.toplam_net_sonuc || '0') }}</p></div>
    </div>
    <div class="mb-6"><RouterLink to="/insaat/portfoy-karsilastirma" class="ikincil-dugme">Portföy Karşılaştırma ekranını aç →</RouterLink></div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">2. Nakit Akışı Özeti</h2>
    <div class="mb-6 grid gap-3 sm:grid-cols-3">
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Planlanan Gider</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ para(nakit?.planlanan_gider || '0') }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Gerçekleşen Gider</p><p class="mt-1 text-2xl font-bold text-amber-700">{{ para(nakit?.gerceklesen_gider || '0') }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Net</p><p class="mt-1 text-2xl font-bold text-danger-700">{{ para(nakit?.net || '0') }}</p></div>
    </div>
    <div class="mb-6"><RouterLink to="/insaat/nakit-akisi" class="ikincil-dugme">Nakit Akışı ekranını aç →</RouterLink></div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">3. Kâr / Zarar Özeti</h2>
    <div class="mb-6 grid gap-3 sm:grid-cols-3">
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Bütçelenen Maliyet</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ para(karZarar?.butcelenen_maliyet || '0') }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Maliyet Sapması</p><p class="mt-1 text-2xl font-bold text-amber-700">%{{ karZarar?.maliyet_sapmasi_yuzde || '0' }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Net Sonuç</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ para(karZarar?.net_sonuc || '0') }}</p></div>
    </div>
    <div class="mb-6"><RouterLink to="/insaat/kar-zarar" class="ikincil-dugme">Kâr/Zarar ekranını aç →</RouterLink></div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">4. Mini S-Eğrisi</h2>
    <div class="mb-6 grid gap-3 sm:grid-cols-3">
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Plan Değer</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ para(sEgrisi?.toplam_plan_deger || '0') }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Gerçek Değer</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ para(sEgrisi?.toplam_gercek_deger || '0') }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Sapma</p><p class="mt-1 text-2xl font-bold text-amber-700">%{{ sEgrisi?.toplam_sapma_yuzde || '0' }}</p></div>
    </div>

    <h2 class="mb-3 font-heading text-lg font-bold text-surface-900">5. Gantt Durum Özeti</h2>
    <div class="mb-6 grid gap-3 sm:grid-cols-3">
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">İş Kalemi</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ gantt?.cubuklar?.length || 0 }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Tarihli / Tarihsiz</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ ganttTarihli() }} / {{ (gantt?.cubuklar?.length || 0) - ganttTarihli() }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Ortalama İlerleme</p><p class="mt-1 text-2xl font-bold text-primary-800">%{{ ganttIlerleme() }}</p></div>
    </div>
    <div class="mb-6 flex flex-wrap gap-2">
      <RouterLink to="/insaat/poz-planlari" class="ikincil-dugme">Poz Planları ekranını aç →</RouterLink>
      <RouterLink to="/insaat/gantt" class="ikincil-dugme">Gantt ekranını aç →</RouterLink>
    </div>
  </div>
</template>
