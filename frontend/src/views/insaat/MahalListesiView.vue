<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import ExcelAktarim, { type ExcelSutun } from '@/components/ExcelAktarim.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { MAHAL_ELEMANI_TIPLERI, MAHAL_TIPLERI, type Mahal, type MahalElemani, type Proje } from '@/types/insaat'
import { MAHAL_SABLONLARI } from '@/data/mahalSablonlari'

const mahaller = ref<Mahal[]>([])
const projeler = ref<Proje[]>([])
const proje = ref<number | null>(null)
const secili = ref<Mahal | null>(null)
const elemanlar = ref<MahalElemani[]>([])
const modalAcik = ref(false)
const sablonAcik = ref(false)
const hata = ref('')
const yukleniyor = ref(false)
const form = ref({
  proje: null as number | null, blok: '', kat: '', mahal_no: '', mahal_adi: '',
  mahal_tipi: 'oda', alan_m2: '', cevre_m: '', yukseklik_m: '', aciklama: '',
})
const excelSutunlari: ExcelSutun[] = [
  { key: 'proje', label: 'Proje', required: true }, { key: 'mahal_no', label: 'Mahal No', required: true },
  { key: 'mahal_adi', label: 'Mahal Adı', required: true }, { key: 'mahal_tipi', label: 'Tip', templateValue: 'oda' },
  { key: 'blok', label: 'Blok' }, { key: 'kat', label: 'Kat' }, { key: 'alan_m2', label: 'Alan (m²)' },
  { key: 'cevre_m', label: 'Çevre (m)' }, { key: 'yukseklik_m', label: 'Yükseklik (m)' }, { key: 'aciklama', label: 'Açıklama' },
]
async function excelAl(rows: Record<string, unknown>[]): Promise<void> {
  try {
    for (const row of rows) await insaatApi.mahaller.olustur(row)
    await yukle()
    hata.value = ''
  } catch (error) {
    hata.value = `Excel içe aktarma kısmi olarak tamamlandı: ${error instanceof Error ? error.message : 'geçersiz veri.'}`
    await yukle()
  }
}

const filtreliMahaller = computed(() => proje.value ? mahaller.value.filter((x) => x.proje === proje.value) : mahaller.value)
const projeAdi = (id: number): string => projeler.value.find((x) => x.id === id)?.ad || `#${id}`

async function yukle(): Promise<void> {
  yukleniyor.value = true
  hata.value = ''
  try { mahaller.value = await tumunuGetir(insaatApi.mahaller.liste, proje.value ? { proje: proje.value } : {}) }
  catch (e) { hata.value = hataMesaji(e) }
  finally { yukleniyor.value = false }
}
async function detayAc(x: Mahal): Promise<void> {
  secili.value = x
  try { elemanlar.value = await insaatApi.mahaller.elemanlar(x.id) }
  catch (e) { hata.value = hataMesaji(e) }
}
function yeniAc(): void {
  form.value = { proje: proje.value, blok: '', kat: '', mahal_no: '', mahal_adi: '', mahal_tipi: 'oda', alan_m2: '', cevre_m: '', yukseklik_m: '', aciklama: '' }
  modalAcik.value = true
}
async function kaydet(): Promise<void> {
  hata.value = ''
  if (!form.value.proje || !form.value.mahal_no.trim() || !form.value.mahal_adi.trim()) { hata.value = 'Proje, mahal numarası ve mahal adı zorunludur.'; return }
  try {
    await insaatApi.mahaller.olustur({ ...form.value, mahal_no: form.value.mahal_no.trim(), mahal_adi: form.value.mahal_adi.trim() })
    modalAcik.value = false; await yukle()
  } catch (e) { hata.value = hataMesaji(e) }
}
async function sablondanOlustur(sablon: typeof MAHAL_SABLONLARI[number]): Promise<void> {
  if (!proje.value) { hata.value = 'Önce proje seçmelisiniz.'; return }
  try {
    await insaatApi.mahalSablondanOlustur(proje.value, { sablon: sablon.mahal_tipi, mahal_adi: sablon.ad })
    sablonAcik.value = false; await yukle()
  } catch (e) { hata.value = hataMesaji(e) }
}
async function elemanSil(x: MahalElemani): Promise<void> {
  if (!secili.value) return
  try { await insaatApi.mahaller.elemanSil(secili.value.id, x.id); elemanlar.value = elemanlar.value.filter((e) => e.id !== x.id) }
  catch (e) { hata.value = hataMesaji(e) }
}
onMounted(async () => {
  try { projeler.value = await tumunuGetir(insaatApi.projeler.liste) } catch (e) { hata.value = hataMesaji(e) }
  await yukle()
})
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div><p class="text-sm font-medium text-primary-700">İnşaat</p><h1 class="font-heading text-2xl font-bold text-surface-900">Mahal Listesi</h1><p class="mt-1 text-sm text-surface-500">Proje mahallerini, ölçülerini ve imalat elemanlarını yönetin.</p></div>
      <div class="flex flex-wrap gap-2"><button class="ikincil-dugme" type="button" @click="sablonAcik = true">Şablondan oluştur</button><button class="birincil-dugme" type="button" @click="yeniAc">+ Yeni Mahal</button></div>
    </div>
    <div class="mb-4"><ExcelAktarim :rows="filtreliMahaller as unknown as Record<string, unknown>[]" :columns="excelSutunlari" filename="mahal-listesi" @imported="excelAl" /></div>
    <div class="mb-4 flex flex-wrap gap-2">
      <select v-model="proje" class="alan max-w-sm" @change="yukle"><option :value="null">Tüm projeler</option><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} / {{ x.ad }}</option></select>
    </div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <div class="grid min-h-[28rem] gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
      <div class="overflow-hidden rounded-2xl border border-surface-200 bg-white">
        <div class="overflow-x-auto"><table class="w-full min-w-[760px] text-left text-sm"><thead class="bg-surface-50 text-xs uppercase tracking-wide text-surface-500"><tr><th class="px-4 py-3">Proje</th><th class="px-4 py-3">No</th><th class="px-4 py-3">Mahal</th><th class="px-4 py-3">Tip</th><th class="px-4 py-3">Alan</th><th class="px-4 py-3">Kat / Blok</th></tr></thead><tbody><tr v-for="x in filtreliMahaller" :key="x.id" class="cursor-pointer border-t border-surface-100 hover:bg-primary-50/50" :class="{ 'bg-primary-50': secili?.id === x.id }" @click="detayAc(x)"><td class="px-4 py-3">{{ projeAdi(x.proje) }}</td><td class="px-4 py-3 font-mono">{{ x.mahal_no }}</td><td class="px-4 py-3 font-medium">{{ x.mahal_adi }}</td><td class="px-4 py-3">{{ MAHAL_TIPLERI[x.mahal_tipi] }}</td><td class="px-4 py-3">{{ x.alan_m2 || '—' }} m²</td><td class="px-4 py-3">{{ x.kat || '—' }} / {{ x.blok || '—' }}</td></tr><tr v-if="!filtreliMahaller.length && !yukleniyor"><td colspan="6" class="px-4 py-12 text-center text-sm text-surface-500">Henüz mahal kaydı yok.</td></tr></tbody></table></div>
      </div>
      <aside class="rounded-2xl border border-surface-200 bg-surface-50 p-4"><template v-if="secili"><p class="text-xs font-semibold uppercase tracking-wide text-primary-700">Mahal detayı</p><h2 class="mt-1 text-lg font-semibold text-surface-900">{{ secili.mahal_no }} — {{ secili.mahal_adi }}</h2><p class="mt-1 text-xs text-surface-500">{{ projeAdi(secili.proje) }} · {{ MAHAL_TIPLERI[secili.mahal_tipi] }}</p><dl class="mt-4 grid grid-cols-2 gap-3 text-sm"><div><dt class="text-xs text-surface-500">Alan</dt><dd class="font-medium">{{ secili.alan_m2 || '—' }} m²</dd></div><div><dt class="text-xs text-surface-500">Çevre</dt><dd class="font-medium">{{ secili.cevre_m || '—' }} m</dd></div><div><dt class="text-xs text-surface-500">Yükseklik</dt><dd class="font-medium">{{ secili.yukseklik_m || '—' }} m</dd></div></dl><h3 class="mt-6 text-sm font-semibold">Elemanlar</h3><ul class="mt-2 space-y-2"><li v-for="x in elemanlar" :key="x.id" class="flex items-center justify-between rounded-lg bg-white px-3 py-2 text-xs"><span>{{ MAHAL_ELEMANI_TIPLERI[x.eleman_tipi] }} · {{ x.malzeme_aciklama || 'Malzeme belirtilmedi' }}</span><button class="text-red-700" type="button" title="Elemanı kaldır" @click="elemanSil(x)">×</button></li><li v-if="!elemanlar.length" class="text-xs text-surface-500">Eleman bulunmuyor.</li></ul></template><p v-else class="py-16 text-center text-sm text-surface-500">Detay için bir mahal seçin.</p></aside>
    </div>
    <KayitModal v-if="modalAcik" baslik="Yeni Mahal" :genis-icerik="true" @kapat="modalAcik = false"><form class="grid grid-cols-2 gap-3" @submit.prevent="kaydet"><label class="etiket">Proje *<select v-model="form.proje" class="alan"><option :value="null">Seçiniz</option><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} / {{ x.ad }}</option></select></label><label class="etiket">Mahal No *<input v-model="form.mahal_no" class="alan" required /></label><label class="etiket">Mahal Adı *<input v-model="form.mahal_adi" class="alan" required /></label><label class="etiket">Tip<select v-model="form.mahal_tipi" class="alan"><option v-for="(e, k) in MAHAL_TIPLERI" :key="k" :value="k">{{ e }}</option></select></label><label class="etiket">Blok<input v-model="form.blok" class="alan" /></label><label class="etiket">Kat<input v-model="form.kat" class="alan" /></label><label class="etiket">Alan (m²)<input v-model="form.alan_m2" class="alan" type="number" min="0" step="0.01" /></label><label class="etiket">Çevre (m)<input v-model="form.cevre_m" class="alan" type="number" min="0" step="0.01" /></label><label class="etiket">Yükseklik (m)<input v-model="form.yukseklik_m" class="alan" type="number" min="0" step="0.01" /></label><label class="etiket col-span-2">Açıklama<textarea v-model="form.aciklama" class="alan" rows="3" /></label><div class="col-span-2 flex justify-end gap-2"><button class="ikincil-dugme" type="button" @click="modalAcik = false">Vazgeç</button><button class="birincil-dugme" type="submit">Kaydet</button></div></form></KayitModal>
    <KayitModal v-if="sablonAcik" baslik="Mahal Şablonundan Oluştur" @kapat="sablonAcik = false"><div class="grid gap-3"><p class="text-sm text-surface-500">Seçili projeye standart mahal ve elemanlarını ekleyin.</p><button v-for="x in MAHAL_SABLONLARI" :key="x.ad" class="rounded-xl border border-surface-200 bg-white p-3 text-left hover:border-primary-400" type="button" @click="sablondanOlustur(x)"><strong class="block text-sm">{{ x.ad }}</strong><span class="text-xs text-surface-500">{{ x.elemanlar.length }} standart eleman</span></button></div></KayitModal>
  </div>
</template>
