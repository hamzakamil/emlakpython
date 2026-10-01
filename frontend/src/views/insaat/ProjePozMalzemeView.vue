<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ClipboardList, Pencil, Plus, Search, X } from 'lucide-vue-next'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import type { Malzeme, Poz, Proje, ProjePozMalzeme } from '@/types/insaat'

const pozMalzemeler = ref<ProjePozMalzeme[]>([])
const projeler = ref<Proje[]>([])
const pozlar = ref<Poz[]>([])
const malzemeler = ref<Malzeme[]>([])
const yukleniyor = ref(true)
const modalAcik = ref(false)
const duzenlenen = ref<number | null>(null)
const arama = ref('')
const projeFiltresi = ref('')
const pozFiltresi = ref('')
const hata = ref('')

const form = reactive({
  proje: '',
  poz: '',
  kaynak_malzeme: '',
  etkin_malzeme: '',
  miktar_override: '',
  aciklama: '',
  is_active: true,
})

const filtrelenmis = computed(() => pozMalzemeler.value.filter((p) => {
  const metin = `${p.proje_kodu} ${p.poz_no} ${p.kaynak_malzeme_kodu} ${p.etkin_malzeme_kodu}`.toLocaleLowerCase('tr-TR')
  return (!arama.value || metin.includes(arama.value.toLocaleLowerCase('tr-TR')))
    && (!projeFiltresi.value || String(p.proje) === projeFiltresi.value)
    && (!pozFiltresi.value || String(p.poz) === pozFiltresi.value)
}))

async function yukle() {
  yukleniyor.value = true
  try {
    const [liste, p, po, m] = await Promise.all([
      tumunuGetir(insaatApi.projePozMalzemeler.liste),
      tumunuGetir(insaatApi.projeler.liste, { is_active: true }),
      tumunuGetir(insaatApi.pozlar.liste, { is_active: true }),
      tumunuGetir(insaatApi.malzemeler.liste, { is_active: true }),
    ])
    pozMalzemeler.value = liste
    projeler.value = p
    pozlar.value = po
    malzemeler.value = m
  } catch { hata.value = 'Kayıtlar yüklenemedi. Lütfen tekrar deneyin.' } finally { yukleniyor.value = false }
}

function formuAc(kayit?: ProjePozMalzeme) {
  duzenlenen.value = kayit?.id ?? null
  Object.assign(form, kayit ? {
    proje: String(kayit.proje),
    poz: String(kayit.poz),
    kaynak_malzeme: String(kayit.kaynak_malzeme),
    etkin_malzeme: String(kayit.etkin_malzeme),
    miktar_override: kayit.miktar_override || '',
    aciklama: kayit.aciklama || '',
    is_active: kayit.is_active,
  } : { proje: '', poz: '', kaynak_malzeme: '', etkin_malzeme: '', miktar_override: '', aciklama: '', is_active: true })
  hata.value = ''; modalAcik.value = true
}

async function kaydet() {
  hata.value = ''
  try {
    const veri = {
      ...form,
      proje: Number(form.proje),
      poz: Number(form.poz),
      kaynak_malzeme: Number(form.kaynak_malzeme),
      etkin_malzeme: Number(form.etkin_malzeme),
      miktar_override: form.miktar_override ? Number(form.miktar_override) : null,
    }
    if (duzenlenen.value) await insaatApi.projePozMalzemeler.guncelle(duzenlenen.value, veri)
    else await insaatApi.projePozMalzemeler.olustur(veri)
    modalAcik.value = false; await yukle()
  } catch { hata.value = 'Kayıt kaydedilemedi. Zorunlu alanları kontrol edin.' }
}

onMounted(yukle)
</script>

<template>
  <main class="mx-auto max-w-7xl space-y-6 p-6">
    <header class="flex flex-col justify-between gap-4 md:flex-row md:items-end">
      <div>
        <p class="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-primary-700"><ClipboardList :size="15" /> Satın alma</p>
        <h1 class="font-heading text-3xl font-bold text-surface-950">Proje Poz Malzemeleri</h1>
        <p class="mt-1 text-sm text-surface-500">Proje-poz seviyesinde malzeme alternatifi ve miktar override (FAZ 2). Aynı malzeme farklı pozlarda farklı alternatiflere bağlanabilir.</p>
      </div>
      <button class="inline-flex items-center justify-center gap-2 rounded-lg bg-primary-800 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700" @click="formuAc()"><Plus :size="17" /> Yeni eşleşme</button>
    </header>
    <div v-if="hata" class="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ hata }}</div>
    <section class="grid gap-3 rounded-xl border border-surface-200 bg-white p-4 shadow-sm md:grid-cols-[1fr_200px_200px]">
      <label class="relative"><Search class="absolute left-3 top-2.5 text-surface-400" :size="17" /><input v-model="arama" class="w-full rounded-lg border border-surface-200 py-2 pl-10 pr-3 text-sm outline-none focus:border-primary-500" placeholder="Proje, poz, kaynak/etkin malzeme ara" /></label>
      <select v-model="projeFiltresi" class="rounded-lg border border-surface-200 px-3 py-2 text-sm"><option value="">Tüm projeler</option><option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option></select>
      <select v-model="pozFiltresi" class="rounded-lg border border-surface-200 px-3 py-2 text-sm"><option value="">Tüm pozlar</option><option v-for="p in pozlar" :key="p.id" :value="p.id">{{ p.poz_no }} — {{ p.ad }}</option></select>
    </section>
    <div v-if="yukleniyor" class="rounded-xl border border-surface-200 bg-white p-12 text-center text-sm text-surface-500">Kayıtlar yükleniyor…</div>
    <div v-else-if="!filtrelenmis.length" class="rounded-xl border border-dashed border-surface-300 bg-white p-14 text-center"><ClipboardList class="mx-auto mb-3 text-surface-300" :size="34" /><p class="font-semibold text-surface-700">Henüz eşleşme yok</p><p class="mt-1 text-sm text-surface-500">İlk poz-malzemeyi ekleyerek başlayın.</p></div>
    <section class="overflow-hidden rounded-xl border border-surface-200 bg-white shadow-sm">
      <div class="overflow-x-auto"><table class="w-full min-w-[1000px] text-left text-sm"><thead class="text-xs uppercase tracking-wide text-surface-500"><tr><th class="px-5 py-3">Proje</th><th class="px-5 py-3">Poz</th><th class="px-5 py-3">Kaynak Malzeme</th><th class="px-5 py-3">Etkin Malzeme</th><th class="px-5 py-3">Miktar Override</th><th class="px-5 py-3">Etkin Fiyat</th><th class="px-5 py-3">Aktif</th><th class="px-5 py-3 text-right">İşlem</th></tr></thead><tbody><tr v-for="p in filtrelenmis" :key="p.id" class="border-t border-surface-100"><td class="px-5 py-4 font-medium text-surface-800">{{ p.proje_kodu }}</td><td class="px-5 py-4">{{ p.poz_no }} — {{ p.poz_adi }}</td><td class="px-5 py-4">{{ p.kaynak_malzeme_kodu }} — {{ p.kaynak_malzeme_adi }}</td><td class="px-5 py-4 font-medium">{{ p.etkin_malzeme_kodu }} — {{ p.etkin_malzeme_adi }}</td><td class="px-5 py-4">{{ p.miktar_override ? p.miktar_override + ' ' + p.etkin_malzeme_birim : '— (varsayılan)' }}</td><td class="px-5 py-4 font-medium">{{ p.etkin_fiyat ? p.etkin_fiyat + ' ₺' : '—' }}<small v-if="p.etkin_fiyat_kaynak" class="block text-xs text-surface-500">{{ p.etkin_fiyat_kaynak }}</small></td><td class="px-5 py-4"><span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium" :class="p.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-surface-100 text-surface-500'"><span :class="p.is_active ? 'bg-emerald-500' : 'bg-surface-400'" class="w-2 h-2 rounded-full" />{{ p.is_active ? 'Aktif' : 'Pasif' }}</span></td><td class="px-5 py-4 text-right"><button class="inline-flex rounded-md border border-surface-200 p-1.5 text-surface-500 hover:bg-surface-50" title="Düzenle" @click="formuAc(p)"><Pencil :size="15" /></button></td></tr></tbody></table></div>
    </section>
    <div v-if="modalAcik" class="fixed inset-0 z-50 flex items-center justify-center bg-surface-950/40 p-4" @click.self="modalAcik = false"><form class="w-full max-w-2xl space-y-4 rounded-2xl bg-white p-6 shadow-xl" @submit.prevent="kaydet"><div class="flex items-center justify-between"><h2 class="font-heading text-xl font-bold">{{ duzenlenen ? 'Eşleşme düzenle' : 'Yeni poz-malzemesi' }}</h2><button type="button" @click="modalAcik = false"><X :size="20" /></button></div><div class="grid gap-3 md:grid-cols-2"><label class="text-sm font-medium">Proje *<select v-model="form.proje" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option></select></label><label class="text-sm font-medium">Poz *<select v-model="form.poz" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="p in pozlar" :key="p.id" :value="p.id">{{ p.poz_no }} — {{ p.ad }}</option></select></label><label class="text-sm font-medium">Kaynak Malzeme *<select v-model="form.kaynak_malzeme" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="m in malzemeler" :key="m.id" :value="m.id">{{ m.malzeme_kodu }} — {{ m.ad }}</option></select></label><label class="text-sm font-medium">Etkin Malzeme *<select v-model="form.etkin_malzeme" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="m in malzemeler" :key="m.id" :value="m.id">{{ m.malzeme_kodu }} — {{ m.ad }}</option></select></label><label class="text-sm font-medium">Miktar Override<input v-model="form.miktar_override" type="number" min="0.0001" step="0.0001" class="mt-1 w-full rounded-lg border border-surface-200 p-2" placeholder="Boş = PozMalzemeIliskisi miktarı kullanılır" /></label><label class="text-sm font-medium md:col-span-2">Açıklama<textarea v-model="form.aciklama" class="mt-1 w-full rounded-lg border border-surface-200 p-2" rows="3" /></label><label class="flex items-center gap-2"><input v-model="form.is_active" type="checkbox" class="rounded border-surface-300 text-primary-600" /><span class="text-sm">Aktif</span></label></div><div class="flex justify-end gap-3 pt-4 border-t border-surface-100"><button type="button" class="rounded-lg border border-surface-200 px-4 py-2 text-sm font-medium text-surface-700 hover:bg-surface-50" @click="modalAcik = false">İptal</button><button class="inline-flex items-center justify-center gap-2 rounded-lg bg-primary-800 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-700" type="submit">Kaydet</button></div></form></div>
  </main>
</template>

<style scoped>
/* Stillere gerek yok, Tailwind kullanılıyor */
</style>