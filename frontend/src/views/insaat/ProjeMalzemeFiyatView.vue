<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ClipboardList, Pencil, Plus, Search, X } from 'lucide-vue-next'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import type { Malzeme, Proje, ProjeMalzemeFiyat } from '@/types/insaat'

const fiyatlar = ref<ProjeMalzemeFiyat[]>([])
const projeler = ref<Proje[]>([])
const malzemeler = ref<Malzeme[]>([])
const yukleniyor = ref(true)
const modalAcik = ref(false)
const duzenlenen = ref<number | null>(null)
const arama = ref('')
const projeFiltresi = ref('')
const yilFiltresi = ref('')
const hata = ref('')

const form = reactive({
  proje: '',
  malzeme: '',
  yil: new Date().getFullYear(),
  birim_fiyat: '',
  para_birimi: 'TRY',
  kaynak: '',
  kaynak_url: '',
  is_active: true,
})

const filtrelenmis = computed(() => fiyatlar.value.filter((f) => {
  const metin = `${f.proje_kodu} ${f.malzeme_kodu} ${f.malzeme_adi}`.toLocaleLowerCase('tr-TR')
  return (!arama.value || metin.includes(arama.value.toLocaleLowerCase('tr-TR')))
    && (!projeFiltresi.value || String(f.proje) === projeFiltresi.value)
    && (!yilFiltresi.value || String(f.yil) === yilFiltresi.value)
}))

const paraBirimleri = ['TRY', 'USD', 'EUR'] as const

async function yukle() {
  yukleniyor.value = true
  try {
    const [liste, p, m] = await Promise.all([
      tumunuGetir(insaatApi.projeMalzemeFiyatlari.liste),
      tumunuGetir(insaatApi.projeler.liste, { is_active: true }),
      tumunuGetir(insaatApi.malzemeler.liste, { is_active: true }),
    ])
    fiyatlar.value = liste
    projeler.value = p
    malzemeler.value = m
  } catch { hata.value = 'Kayıtlar yüklenemedi. Lütfen tekrar deneyin.' } finally { yukleniyor.value = false }
}

function formuAc(kayit?: ProjeMalzemeFiyat) {
  duzenlenen.value = kayit?.id ?? null
  Object.assign(form, kayit ? {
    proje: String(kayit.proje),
    malzeme: String(kayit.malzeme),
    yil: kayit.yil,
    birim_fiyat: kayit.birim_fiyat,
    para_birimi: kayit.para_birimi,
    kaynak: kayit.kaynak || '',
    kaynak_url: kayit.kaynak_url || '',
    is_active: kayit.is_active,
  } : { proje: '', malzeme: '', yil: new Date().getFullYear(), birim_fiyat: '', para_birimi: 'TRY', kaynak: '', kaynak_url: '', is_active: true })
  hata.value = ''; modalAcik.value = true
}

async function kaydet() {
  hata.value = ''
  try {
    const veri = {
      ...form,
      proje: Number(form.proje),
      malzeme: Number(form.malzeme),
      yil: Number(form.yil),
      birim_fiyat: form.birim_fiyat,
    }
    if (duzenlenen.value) await insaatApi.projeMalzemeFiyatlari.guncelle(duzenlenen.value, veri)
    else await insaatApi.projeMalzemeFiyatlari.olustur(veri)
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
        <h1 class="font-heading text-3xl font-bold text-surface-950">Proje Malzeme Fiyatları</h1>
        <p class="mt-1 text-sm text-surface-500">Proje bazlı malzeme yıl bazlı fiyat tanımları (FAZ 2: sadece TRY maliyet hesabına girer).</p>
      </div>
      <button class="inline-flex items-center justify-center gap-2 rounded-lg bg-primary-800 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700" @click="formuAc()"><Plus :size="17" /> Yeni fiyat</button>
    </header>
    <div v-if="hata" class="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ hata }}</div>
    <section class="grid gap-3 rounded-xl border border-surface-200 bg-white p-4 shadow-sm md:grid-cols-[1fr_200px_180px_120px]">
      <label class="relative"><Search class="absolute left-3 top-2.5 text-surface-400" :size="17" /><input v-model="arama" class="w-full rounded-lg border border-surface-200 py-2 pl-10 pr-3 text-sm outline-none focus:border-primary-500" placeholder="Proje, malzeme kodu veya adı ara" /></label>
      <select v-model="projeFiltresi" class="rounded-lg border border-surface-200 px-3 py-2 text-sm"><option value="">Tüm projeler</option><option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option></select>
      <select v-model="yilFiltresi" class="rounded-lg border border-surface-200 px-3 py-2 text-sm"><option value="">Tüm yıllar</option><option v-for="y in [2026, 2025, 2024, 2023, 2022]" :key="y" :value="y">{{ y }}</option></select>
    </section>
    <div v-if="yukleniyor" class="rounded-xl border border-surface-200 bg-white p-12 text-center text-sm text-surface-500">Kayıtlar yükleniyor…</div>
    <div v-else-if="!filtrelenmis.length" class="rounded-xl border border-dashed border-surface-300 bg-white p-14 text-center"><ClipboardList class="mx-auto mb-3 text-surface-300" :size="34" /><p class="font-semibold text-surface-700">Henüz fiyat tanımı yok</p><p class="mt-1 text-sm text-surface-500">İlk fiyatı ekleyerek başlayın.</p></div>
    <section class="overflow-hidden rounded-xl border border-surface-200 bg-white shadow-sm">
      <div class="overflow-x-auto"><table class="w-full min-w-[800px] text-left text-sm"><thead class="text-xs uppercase tracking-wide text-surface-500"><tr><th class="px-5 py-3">Proje</th><th class="px-5 py-3">Malzeme</th><th class="px-5 py-3">Yıl</th><th class="px-5 py-3">Birim Fiyat</th><th class="px-5 py-3">Para Birimi</th><th class="px-5 py-3">Kaynak</th><th class="px-5 py-3">Aktif</th><th class="px-5 py-3 text-right">İşlem</th></tr></thead><tbody><tr v-for="f in filtrelenmis" :key="f.id" class="border-t border-surface-100"><td class="px-5 py-4 font-medium text-surface-800">{{ f.proje_kodu }}</td><td class="px-5 py-4">{{ f.malzeme_kodu }} — {{ f.malzeme_adi }}</td><td class="px-5 py-4">{{ f.yil }}</td><td class="px-5 py-4 font-medium tabular-nums">{{ Number(f.birim_fiyat).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td><td class="px-5 py-4"><span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium" :class="f.para_birimi === 'TRY' ? 'bg-emerald-50 text-emerald-700' : f.para_birimi === 'USD' ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700'">{{ f.para_birimi }}</span></td><td class="px-5 py-4 max-w-[180px] truncate">{{ f.kaynak || '—' }}</td><td class="px-5 py-4"><span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium" :class="f.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-surface-100 text-surface-500'"><span :class="f.is_active ? 'bg-emerald-500' : 'bg-surface-400'" class="w-2 h-2 rounded-full" />{{ f.is_active ? 'Aktif' : 'Pasif' }}</span></td><td class="px-5 py-4 text-right"><button class="inline-flex rounded-md border border-surface-200 p-1.5 text-surface-500 hover:bg-surface-50" title="Düzenle" @click="formuAc(f)"><Pencil :size="15" /></button></td></tr></tbody></table></div>
    </section>
    <div v-if="modalAcik" class="fixed inset-0 z-50 flex items-center justify-center bg-surface-950/40 p-4" @click.self="modalAcik = false"><form class="w-full max-w-lg space-y-4 rounded-2xl bg-white p-6 shadow-xl" @submit.prevent="kaydet"><div class="flex items-center justify-between"><h2 class="font-heading text-xl font-bold">{{ duzenlenen ? 'Fiyat düzenle' : 'Yeni fiyat' }}</h2><button type="button" @click="modalAcik = false"><X :size="20" /></button></div><div class="grid gap-3 md:grid-cols-2"><label class="text-sm font-medium">Proje *<select v-model="form.proje" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option></select></label><label class="text-sm font-medium">Malzeme *<select v-model="form.malzeme" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="m in malzemeler" :key="m.id" :value="m.id">{{ m.malzeme_kodu }} — {{ m.ad }}</option></select></label><label class="text-sm font-medium">Yıl *<input v-model.number="form.yil" type="number" min="2000" max="2100" required class="mt-1 w-full rounded-lg border border-surface-200 p-2" /></label><label class="text-sm font-medium">Para Birimi *<select v-model="form.para_birimi" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option v-for="p in paraBirimleri" :key="p" :value="p">{{ p }}</option></select></label><label class="text-sm font-medium">Birim Fiyat *<input v-model="form.birim_fiyat" type="number" min="0.01" step="0.01" required class="mt-1 w-full rounded-lg border border-surface-200 p-2" placeholder="Örn. 1250.00" /></label><label class="text-sm font-medium md:col-span-2">Kaynak<input v-model="form.kaynak" class="mt-1 w-full rounded-lg border border-surface-200 p-2" placeholder="Örn. Tedarikçi teklifi, piyasa fiyatı" /></label><label class="text-sm font-medium md:col-span-2">Kaynak URL<input v-model="form.kaynak_url" type="url" class="mt-1 w-full rounded-lg border border-surface-200 p-2" placeholder="https://..." /></label><label class="flex items-center gap-2"><input v-model="form.is_active" type="checkbox" class="rounded border-surface-300 text-primary-600" /><span class="text-sm">Aktif</span></label></div><div class="flex justify-end gap-3 pt-4 border-t border-surface-100"><button type="button" class="rounded-lg border border-surface-200 px-4 py-2 text-sm font-medium text-surface-700 hover:bg-surface-50" @click="modalAcik = false">İptal</button><button class="inline-flex items-center justify-center gap-2 rounded-lg bg-primary-800 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-700" type="submit">Kaydet</button></div></form></div>
  </main>
</template>

<style scoped>
/* Stillere gerek yok, Tailwind kullanılıyor */
</style>