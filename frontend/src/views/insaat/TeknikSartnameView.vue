<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { AlertTriangle, FileText, Printer, RefreshCw } from 'lucide-vue-next'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import type { Proje, TeknikSartnameTaslagi } from '@/types/insaat'

const projeler = ref<Proje[]>([])
const projeId = ref<number | null>(null)
const yil = ref(new Date().getFullYear())
const rapor = ref<TeknikSartnameTaslagi | null>(null)
const yukleniyor = ref(false)
const listeYukleniyor = ref(true)
const hata = ref('')

async function projeleriYukle(): Promise<void> {
  try {
    projeler.value = await tumunuGetir(insaatApi.projeler.liste, { is_active: true })
    if (!projeId.value && projeler.value.length) projeId.value = projeler.value[0].id
  } catch (e) {
    hata.value = hataMesaji(e)
  } finally {
    listeYukleniyor.value = false
  }
}

async function taslakUret(): Promise<void> {
  if (!projeId.value) {
    hata.value = 'Önce bir proje seçmelisiniz.'
    return
  }
  yukleniyor.value = true
  hata.value = ''
  try {
    rapor.value = await insaatApi.teknikSartname(projeId.value, yil.value)
  } catch (e) {
    hata.value = hataMesaji(e)
    rapor.value = null
  } finally {
    yukleniyor.value = false
  }
}

function yazdir(): void {
  window.print()
}

onMounted(async () => {
  await projeleriYukle()
  if (projeId.value) await taslakUret()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <header class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-sm font-medium uppercase tracking-[0.18em] text-primary-700">İnşaat · Doküman üretimi</p>
        <h1 class="font-heading text-3xl font-bold tracking-tight text-surface-900">Teknik şartname taslağı</h1>
        <p class="mt-2 max-w-2xl text-sm leading-6 text-surface-500">Poz planları ve malzeme kartlarındaki TS/TS EN referanslarından denetlenebilir bir başlangıç dokümanı üretin.</p>
      </div>
      <button v-if="rapor" type="button" class="ikincil-dugme print:hidden" @click="yazdir"><Printer class="mr-2 inline h-4 w-4" /> Yazdır / PDF</button>
    </header>

    <section class="rounded-2xl border border-surface-200 bg-white p-5 shadow-sm print:hidden">
      <div class="grid gap-4 md:grid-cols-[1fr_180px_auto] md:items-end">
        <label class="etiket">Proje
          <select v-model="projeId" class="alan" :disabled="listeYukleniyor">
            <option :value="null">Proje seçin</option>
            <option v-for="proje in projeler" :key="proje.id" :value="proje.id">{{ proje.proje_kodu }} — {{ proje.ad }}</option>
          </select>
        </label>
        <label class="etiket">Yıl<input v-model.number="yil" class="alan" type="number" min="2000" max="2100" /></label>
        <button type="button" class="birincil-dugme" :disabled="yukleniyor || !projeId" @click="taslakUret"><RefreshCw class="mr-2 inline h-4 w-4" :class="{ 'animate-spin': yukleniyor }" /> {{ yukleniyor ? 'Üretiliyor…' : 'Taslak üret' }}</button>
      </div>
    </section>

    <p v-if="hata" class="hata-kutusu mt-4 print:hidden" role="alert"><AlertTriangle class="mr-2 inline h-4 w-4" />{{ hata }}</p>

    <section v-if="rapor" class="sartname-paper mt-6 rounded-2xl border border-surface-200 bg-white p-6 shadow-sm md:p-10">
      <div class="border-b-2 border-surface-900 pb-5">
        <div class="flex items-start justify-between gap-4">
          <div><p class="text-xs font-semibold uppercase tracking-[0.2em] text-surface-500">Teknik doküman · {{ rapor.yil }}</p><h2 class="mt-2 font-heading text-2xl font-bold text-surface-900">{{ rapor.baslik }}</h2><p class="mt-1 text-sm text-surface-500">{{ rapor.proje_kodu }} · {{ rapor.proje_adi }}</p></div>
          <FileText class="h-8 w-8 text-primary-700" />
        </div>
      </div>
      <div class="my-5 grid gap-3 sm:grid-cols-2">
        <div class="rounded-xl bg-surface-50 p-4"><strong class="block text-2xl text-surface-900">{{ rapor.kalem_sayisi }}</strong><span class="text-xs text-surface-500">Poz kalemi</span></div>
        <div class="rounded-xl bg-surface-50 p-4"><strong class="block text-2xl text-surface-900">{{ rapor.malzeme_sayisi }}</strong><span class="text-xs text-surface-500">Malzeme / standart referansı</span></div>
      </div>
      <div class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900"><strong>Kontrol notu:</strong> {{ rapor.uretim_notu }}</div>
      <div v-if="!rapor.kalemler.length" class="py-12 text-center text-sm text-surface-500">Bu proje ve yıl için aktif poz planı bulunamadı.</div>
      <article v-for="(kalem, index) in rapor.kalemler" :key="kalem.poz_no" class="mt-8 break-inside-avoid">
        <h3 class="font-heading text-lg font-bold text-surface-900">{{ index + 1 }}. {{ kalem.poz_no }} — {{ kalem.poz_ad }}</h3>
        <dl class="mt-2 grid gap-2 text-sm sm:grid-cols-2"><div><dt class="text-xs text-surface-500">Poz grubu</dt><dd class="font-medium">{{ kalem.grup }}</dd></div><div><dt class="text-xs text-surface-500">Ölçü birimi</dt><dd class="font-medium">{{ kalem.birim }}</dd></div></dl>
        <div class="mt-3 overflow-x-auto rounded-xl border border-surface-200">
          <table class="w-full min-w-[650px] text-left text-sm"><thead class="bg-surface-50 text-xs uppercase tracking-wider text-surface-500"><tr><th class="px-4 py-3">Kod</th><th class="px-4 py-3">Malzeme</th><th class="px-4 py-3">Birim / poz</th><th class="px-4 py-3">TS / TS EN</th></tr></thead><tbody class="divide-y divide-surface-100"><tr v-for="malzeme in kalem.malzemeler" :key="malzeme.kod"><td class="px-4 py-3 font-mono text-xs">{{ malzeme.kod }}</td><td class="px-4 py-3">{{ malzeme.ad }}</td><td class="px-4 py-3">{{ malzeme.miktar }} {{ malzeme.birim }}</td><td class="px-4 py-3 font-medium">{{ malzeme.ts_no }}</td></tr><tr v-if="!kalem.malzemeler.length"><td colspan="4" class="px-4 py-4 text-sm text-surface-500">Aktif malzeme referansı bulunamadı.</td></tr></tbody></table>
        </div>
      </article>
    </section>
    <div v-else-if="yukleniyor" class="mt-8 rounded-2xl border border-surface-200 bg-white p-12 text-center text-sm text-surface-500">Taslak hazırlanıyor…</div>
    <p v-else-if="!listeYukleniyor && !projeler.length" class="mt-8 rounded-2xl border border-surface-200 bg-white p-12 text-center text-sm text-surface-500">Aktif proje bulunamadı.</p>
  </div>
</template>

<style scoped>
@media print {
  .sartname-paper { border: 0; box-shadow: none; margin: 0; max-width: none; }
  @page { margin: 1.5cm; }
}
</style>
