<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import type { Poz, PozAnaliz, AnalizTipi } from '@/types/insaat'

const pozlar = ref<Poz[]>([])
const seciliPoz = ref<number | null>(null)
const satirlar = ref<PozAnaliz[]>([])
const modalAcik = ref(false)
const hata = ref('')
const form = ref({ poz: null as number | null, satir_no: 1, malzeme: '', birim: 'm³', miktar: '1', birim_fiyat: '0', analiz_tipi: 'malzeme' as AnalizTipi })
const toplam = computed(() => satirlar.value.reduce((t, x) => t + Number(x.tutar), 0))
const pozAdi = (id: number): string => pozlar.value.find((x) => x.id === id)?.poz_no || `#${id}`
async function yukle(): Promise<void> {
  if (!seciliPoz.value) { satirlar.value = []; return }
  try { satirlar.value = await tumunuGetir(insaatApi.pozAnalizleri.liste, { poz: seciliPoz.value }) } catch (e) { hata.value = hataMesaji(e) }
}
function yeniAc(): void { form.value = { poz: seciliPoz.value, satir_no: satirlar.value.length + 1, malzeme: '', birim: 'm³', miktar: '1', birim_fiyat: '0', analiz_tipi: 'malzeme' }; modalAcik.value = true }
async function kaydet(): Promise<void> {
  if (!form.value.poz || !form.value.malzeme.trim() || Number(form.value.miktar) <= 0) { hata.value = 'Poz, kalem adı ve pozitif miktar zorunludur.'; return }
  try { await insaatApi.pozAnalizleri.olustur({ ...form.value, malzeme: form.value.malzeme.trim() }); modalAcik.value = false; await yukle() } catch (e) { hata.value = hataMesaji(e) }
}
onMounted(async () => { try { pozlar.value = await tumunuGetir(insaatApi.pozlar.liste) } catch (e) { hata.value = hataMesaji(e) } })
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-3"><div><p class="text-sm font-medium text-primary-700">İnşaat</p><h1 class="font-heading text-2xl font-bold text-surface-900">Analiz Kitabı</h1><p class="mt-1 text-sm text-surface-500">Poz bileşenlerini, nakliye ve birim fiyat analizlerini yönetin.</p></div><button class="birincil-dugme" type="button" @click="yeniAc">+ Analiz Satırı</button></div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <div class="mb-4 flex flex-wrap gap-2"><select v-model="seciliPoz" class="alan max-w-sm" @change="yukle"><option :value="null">Poz seçiniz</option><option v-for="x in pozlar" :key="x.id" :value="x.id">{{ x.poz_no }} / {{ x.ad }}</option></select></div>
    <div class="grid gap-4 xl:grid-cols-[minmax(0,1fr)_18rem]"><div class="overflow-x-auto rounded-2xl border border-surface-200 bg-white"><table class="w-full min-w-[720px] text-left text-sm"><thead class="bg-surface-50 text-xs uppercase text-surface-500"><tr><th class="px-4 py-3">Satır</th><th class="px-4 py-3">Kalem</th><th class="px-4 py-3">Tip</th><th class="px-4 py-3">Miktar</th><th class="px-4 py-3">Birim Fiyat</th><th class="px-4 py-3">Tutar</th></tr></thead><tbody><tr v-for="x in satirlar" :key="x.id" class="border-t border-surface-100"><td class="px-4 py-3">{{ x.satir_no }}</td><td class="px-4 py-3 font-medium">{{ x.malzeme }}</td><td class="px-4 py-3">{{ x.analiz_tipi }}</td><td class="px-4 py-3">{{ x.miktar }} {{ x.birim }}</td><td class="px-4 py-3">{{ x.birim_fiyat }}</td><td class="px-4 py-3 font-semibold">{{ x.tutar }}</td></tr><tr v-if="!satirlar.length"><td colspan="6" class="px-4 py-12 text-center text-surface-500">Seçili poz için analiz satırı yok.</td></tr></tbody></table></div><aside class="h-fit rounded-2xl border border-primary-100 bg-primary-50 p-5"><p class="text-xs uppercase tracking-wide text-primary-700">Poz Analizi</p><p class="mt-2 font-semibold">{{ seciliPoz ? pozAdi(seciliPoz) : 'Poz seçilmedi' }}</p><p class="mt-6 text-sm text-surface-600">Analiz toplamı</p><p class="mt-1 text-2xl font-bold text-primary-800">{{ toplam.toLocaleString('tr-TR', { minimumFractionDigits: 2 }) }}</p></aside></div>
    <KayitModal v-if="modalAcik" baslik="Yeni Poz Analiz Satırı" :genis-icerik="true" @kapat="modalAcik = false"><form class="grid grid-cols-2 gap-3" @submit.prevent="kaydet"><label class="etiket">Poz *<select v-model="form.poz" class="alan"><option :value="null">Seçiniz</option><option v-for="x in pozlar" :key="x.id" :value="x.id">{{ x.poz_no }} / {{ x.ad }}</option></select></label><label class="etiket">Analiz Tipi<select v-model="form.analiz_tipi" class="alan"><option value="malzeme">Malzeme</option><option value="iscilik">İşçilik</option><option value="makine">Makine</option><option value="nakliye">Nakliye</option><option value="diger">Diğer</option></select></label><label class="etiket col-span-2">Kalem *<input v-model="form.malzeme" class="alan" required /></label><label class="etiket">Miktar<input v-model="form.miktar" class="alan" type="number" min="0.0001" step="0.0001" /></label><label class="etiket">Birim<input v-model="form.birim" class="alan" /></label><label class="etiket">Birim Fiyat<input v-model="form.birim_fiyat" class="alan" type="number" min="0" step="0.01" /></label><div class="col-span-2 flex justify-end gap-2"><button class="ikincil-dugme" type="button" @click="modalAcik = false">Vazgeç</button><button class="birincil-dugme" type="submit">Kaydet</button></div></form></KayitModal>
  </div>
</template>
