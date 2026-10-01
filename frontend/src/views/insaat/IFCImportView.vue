<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { constructionApi } from '@/services/constructionApi'
import { hataMesaji } from '@/services/apiClient'
import type { IFCImportJob, Proje } from '@/types/insaat'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'

const jobs = ref<IFCImportJob[]>([])
const projects = ref<Proje[]>([])
const project = ref<number | null>(null)
const year = ref(new Date().getFullYear())
const file = ref<File | null>(null)
const filter = ref('')
const loading = ref(false)
const error = ref('')
const statusLabel: Record<string, string> = { queued: 'Kuyrukta', processing: 'İşleniyor', completed: 'Tamamlandı', failed: 'Başarısız' }

async function load() {
  jobs.value = (await constructionApi.ifcImportlari.liste({ status: filter.value || undefined })).results
}
async function upload() {
  if (!file.value || !project.value) { error.value = 'Proje ve .ifc dosyası seçin.'; return }
  loading.value = true; error.value = ''
  try {
    const form = new FormData()
    form.append('project', String(project.value)); form.append('year', String(year.value)); form.append('file', file.value)
    const job = await constructionApi.ifcImportlari.yukle(form)
    await constructionApi.ifcImportlari.isle(job.id)
    file.value = null
    await load()
  } catch (e) { error.value = hataMesaji(e) } finally { loading.value = false }
}
onMounted(async () => {
  try { projects.value = await tumunuGetir(insaatApi.projeler.liste); await load() } catch (e) { error.value = hataMesaji(e) }
})
</script>

<template>
  <main class="mx-auto max-w-6xl space-y-6">
    <header>
      <p class="text-sm font-medium text-primary-700">İnşaat · Metraj</p>
      <h1 class="font-heading text-2xl font-bold text-surface-900">IFC miktar taslakları</h1>
      <p class="mt-1 text-sm text-surface-500">İçe aktarılan miktarlar yalnızca inceleme taslağıdır; aktif Poz Planı değiştirilmez.</p>
    </header>
    <section class="rounded-xl border border-surface-200 bg-white p-5 shadow-sm">
      <div class="grid gap-3 md:grid-cols-[1fr_120px_1fr_auto]">
        <select v-model="project" class="rounded-lg border p-2"><option :value="null">Proje seçin</option><option v-for="p in projects" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option></select>
        <input v-model.number="year" type="number" min="2000" max="2100" class="rounded-lg border p-2">
        <input type="file" accept=".ifc,.ifczip" class="rounded-lg border p-2" @change="file = ($event.target as HTMLInputElement).files?.[0] || null">
        <button class="rounded-lg bg-primary-700 px-4 py-2 font-semibold text-white disabled:opacity-50" :disabled="loading" @click="upload">{{ loading ? 'İşleniyor…' : 'Yükle ve taslak oluştur' }}</button>
      </div>
      <p v-if="error" class="mt-3 rounded-lg bg-danger-50 p-3 text-sm text-danger-700">{{ error }}</p>
    </section>
    <section class="rounded-xl border border-surface-200 bg-white p-5 shadow-sm">
      <div class="mb-4 flex items-center justify-between"><h2 class="font-semibold">İçe aktarma geçmişi</h2><select v-model="filter" class="rounded border p-2 text-sm" @change="load"><option value="">Tümü</option><option value="completed">Tamamlandı</option><option value="failed">Başarısız</option></select></div>
      <div v-for="job in jobs" :key="job.id" class="mb-4 rounded-lg border border-surface-200 p-4">
        <div class="flex flex-wrap justify-between gap-2"><strong>{{ job.file_name }}</strong><span class="rounded-full bg-surface-100 px-2 py-1 text-xs">{{ statusLabel[job.status] }}</span></div>
        <p class="mt-1 text-sm text-surface-500">{{ job.processing_message }} <span v-if="job.parser_mode">({{ job.parser_mode }})</span></p>
        <div v-if="job.draft_rows?.length" class="mt-3 overflow-auto"><table class="w-full text-left text-sm"><thead><tr class="border-b"><th class="p-2">Kaynak</th><th class="p-2">Miktar</th><th class="p-2">Eşleşme</th></tr></thead><tbody><tr v-for="row in job.draft_rows" :key="row.id" class="border-b last:border-0"><td class="p-2">{{ row.source_name }}</td><td class="p-2">{{ row.quantity }} {{ row.unit }}</td><td class="p-2">{{ row.poz_no || row.mapping_status }}<small v-if="row.validation_message" class="ml-2 text-amber-700">{{ row.validation_message }}</small></td></tr></tbody></table></div>
      </div>
      <p v-if="!jobs.length" class="py-8 text-center text-sm text-surface-500">Henüz IFC içe aktarımı yok.</p>
    </section>
  </main>
</template>
