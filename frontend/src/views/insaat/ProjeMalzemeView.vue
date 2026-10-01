<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Check, ClipboardList, Pencil, Plus, Search, X } from 'lucide-vue-next'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { cariApi } from '@/services/cariApi'
import type { Malzeme, Proje, ProjeMalzeme, Tedarikci, TedarikciTeklifi } from '@/types/insaat'
import type { Cari } from '@/types/cari'

const malzemeler = ref<ProjeMalzeme[]>([])
const projeler = ref<Proje[]>([])
const malzemeListesi = ref<Malzeme[]>([])
const tedarikciler = ref<Tedarikci[]>([])
const cariListesi = ref<Cari[]>([])
const yukleniyor = ref(true)
const modalAcik = ref(false)
const duzenlenen = ref<number | null>(null)
const arama = ref('')
const projeFiltresi = ref('')
const hata = ref('')
const secimKayit = ref<ProjeMalzeme | null>(null)
const teklifModalAcik = ref(false)
const tedarikciModalAcik = ref(false)
const teklifListesi = ref<TedarikciTeklifi[]>([])
const seciliTeklif = ref('')
const tedarikciSecim = ref('')
const islemHata = ref('')
const islemBasari = ref('')
const islemYukleniyor = ref(false)

const form = reactive({
  proje: '',
  malzeme: '',
  tedarikci: '',
  cari: '',
  kaynak: '',
  kaynak_url: '',
  aciklama: '',
  is_active: true,
})

const filtrelenmis = computed(() => malzemeler.value.filter((m) => {
  const metin = `${m.proje_kodu} ${m.malzeme_adi} ${m.tedarikci_adi || ''}`.toLocaleLowerCase('tr-TR')
  return (!arama.value || metin.includes(arama.value.toLocaleLowerCase('tr-TR')))
    && (!projeFiltresi.value || String(m.proje) === projeFiltresi.value)
}))

async function yukle() {
  yukleniyor.value = true
  try {
    const [liste, p, m, t, cariListe] = await Promise.all([
      tumunuGetir(insaatApi.projeMalzemeler.liste),
      tumunuGetir(insaatApi.projeler.liste, { is_active: true }),
      tumunuGetir(insaatApi.malzemeler.liste, { is_active: true }),
      tumunuGetir(insaatApi.tedarikciler.liste, { is_active: true }),
      cariApi.cariler.liste({ is_active: true })
    ])
    malzemeler.value = liste
    projeler.value = p
    malzemeListesi.value = m
    tedarikciler.value = t
    cariListesi.value = cariListe.results || []
  } catch { hata.value = 'Kayıtlar yüklenemedi. Lütfen tekrar deneyin.' } finally { yukleniyor.value = false }
}

function formuAc(kayit?: ProjeMalzeme) {
  duzenlenen.value = kayit?.id ?? null
  Object.assign(form, kayit ? {
    proje: String(kayit.proje),
    malzeme: String(kayit.malzeme),
    tedarikci: String(kayit.tedarikci || ''),
    cari: String(kayit.cari || ''),
    kaynak: kayit.kaynak || '',
    kaynak_url: kayit.kaynak_url || '',
    aciklama: kayit.aciklama || '',
    is_active: kayit.is_active,
  } : { proje: '', malzeme: '', tedarikci: '', cari: '', kaynak: '', kaynak_url: '', aciklama: '', is_active: true })
  hata.value = ''; modalAcik.value = true
}

async function kaydet() {
  hata.value = ''
  try {
    const veri = {
      ...form,
      proje: Number(form.proje),
      malzeme: Number(form.malzeme),
      tedarikci: form.tedarikci ? Number(form.tedarikci) : null,
      cari: form.cari ? Number(form.cari) : null,
    }
    if (duzenlenen.value) await insaatApi.projeMalzemeler.guncelle(duzenlenen.value, veri)
    else await insaatApi.projeMalzemeler.olustur(veri)
    modalAcik.value = false; await yukle()
  } catch { hata.value = 'Kayıt kaydedilemedi. Zorunlu alanları kontrol edin.' }
}

async function teklifSec(kayit: ProjeMalzeme) {
  secimKayit.value = kayit
  seciliTeklif.value = kayit.selected_teklif_id ? String(kayit.selected_teklif_id) : ''
  teklifListesi.value = []
  islemHata.value = ''; islemBasari.value = ''
  teklifModalAcik.value = true
  try {
    teklifListesi.value = await tumunuGetir(insaatApi.tedarikciTeklifleri.liste, { proje: kayit.proje, malzeme: kayit.malzeme, is_active: true })
  } catch { islemHata.value = 'Teklifler yüklenemedi. Lütfen tekrar deneyin.' }
}

async function teklifKaydet() {
  if (!secimKayit.value || !seciliTeklif.value) { islemHata.value = 'Teklif seçimi zorunludur.'; return }
  islemYukleniyor.value = true; islemHata.value = ''; islemBasari.value = ''
  try {
    await insaatApi.projeMalzemeler.teklifSec(secimKayit.value.id, Number(seciliTeklif.value))
    islemBasari.value = 'Teklif seçildi.'
    await yukle()
  } catch { islemHata.value = 'Teklif seçilemedi. Teklifin aynı proje/malzemeye ait olduğunu kontrol edin.' } finally { islemYukleniyor.value = false }
}

async function tedarikciAta(kayit: ProjeMalzeme) {
  secimKayit.value = kayit
  tedarikciSecim.value = kayit.tedarikci ? String(kayit.tedarikci) : ''
  islemHata.value = ''; islemBasari.value = ''
  tedarikciModalAcik.value = true
}

async function tedarikciKaydet() {
  if (!secimKayit.value || !tedarikciSecim.value) { islemHata.value = 'Tedarikçi seçimi zorunludur.'; return }
  islemYukleniyor.value = true; islemHata.value = ''; islemBasari.value = ''
  try {
    await insaatApi.projeMalzemeler.tedarikciAta(secimKayit.value.id, Number(tedarikciSecim.value))
    islemBasari.value = 'Tedarikçi atandı.'
    await yukle()
  } catch { islemHata.value = 'Tedarikçi atanamadı. Kaydın aktif olduğunu kontrol edin.' } finally { islemYukleniyor.value = false }
}

onMounted(yukle)
</script>

<template>
  <main class="mx-auto max-w-7xl space-y-6 p-6">
    <header class="flex flex-col justify-between gap-4 md:flex-row md:items-end">
      <div>
        <p class="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-primary-700"><ClipboardList :size="15" /> Satın alma</p>
        <h1 class="font-heading text-3xl font-bold text-surface-950">Proje Malzemeleri</h1>
        <p class="mt-1 text-sm text-surface-500">Proje bazlı malzeme tedarikçi, cari ve teklif yönetimi.</p>
      </div>
      <button class="inline-flex items-center justify-center gap-2 rounded-lg bg-primary-800 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700" @click="formuAc()"><Plus :size="17" /> Yeni kayıt</button>
    </header>
    <div v-if="hata" class="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ hata }}</div>
    <section class="grid gap-3 rounded-xl border border-surface-200 bg-white p-4 shadow-sm md:grid-cols-[1fr_200px_180px]">
      <label class="relative"><Search class="absolute left-3 top-2.5 text-surface-400" :size="17" /><input v-model="arama" class="w-full rounded-lg border border-surface-200 py-2 pl-10 pr-3 text-sm outline-none focus:border-primary-500" placeholder="Proje, malzeme veya tedarikçi ara" /></label>
      <select v-model="projeFiltresi" class="rounded-lg border border-surface-200 px-3 py-2 text-sm"><option value="">Tüm projeler</option><option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option></select>
    </section>
    <div v-if="yukleniyor" class="rounded-xl border border-surface-200 bg-white p-12 text-center text-sm text-surface-500">Kayıtlar yükleniyor…</div>
    <div v-else-if="!filtrelenmis.length" class="rounded-xl border border-dashed border-surface-300 bg-white p-14 text-center"><ClipboardList class="mx-auto mb-3 text-surface-300" :size="34" /><p class="font-semibold text-surface-700">Henüz kayıt yok</p><p class="mt-1 text-sm text-surface-500">İlk proje malzemesini ekleyerek başlayın.</p></div>
    <section class="overflow-hidden rounded-xl border border-surface-200 bg-white shadow-sm">
      <div class="overflow-x-auto"><table class="w-full min-w-[900px] text-left text-sm"><thead class="text-xs uppercase tracking-wide text-surface-500"><tr><th class="px-5 py-3">Proje</th><th class="px-5 py-3">Malzeme</th><th class="px-5 py-3">Tedarikçi</th><th class="px-5 py-3">Cari</th><th class="px-5 py-3">Seçili Teklif</th><th class="px-5 py-3">Etkin Fiyat</th><th class="px-5 py-3">Kaynak</th><th class="px-5 py-3">Aktif</th><th class="px-5 py-3 text-right">İşlem</th></tr></thead><tbody><tr v-for="m in filtrelenmis" :key="m.id" class="border-t border-surface-100"><td class="px-5 py-4 font-medium text-surface-800">{{ m.proje_kodu }}</td><td class="px-5 py-4">{{ m.malzeme_kodu }} — {{ m.malzeme_adi }}</td><td class="px-5 py-4">{{ m.tedarikci_adi || '—' }}</td><td class="px-5 py-4">{{ m.cari_adi || '—' }}</td><td class="px-5 py-4"><span v-if="m.selected_teklif_id" class="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700"><Check :size="12" /> Seçili</span><span v-else class="text-surface-400">—</span></td><td class="px-5 py-4 font-medium">{{ m.etkin_fiyat ? m.etkin_fiyat + ' ₺' : '—' }}<small v-if="m.etkin_fiyat_kaynak" class="block text-xs text-surface-500">{{ m.etkin_fiyat_kaynak }}</small></td><td class="px-5 py-4 max-w-[180px] truncate">{{ m.kaynak || '—' }}</td><td class="px-5 py-4"><span class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium" :class="m.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-surface-100 text-surface-500'"><span :class="m.is_active ? 'bg-emerald-500' : 'bg-surface-400'" class="w-2 h-2 rounded-full" />{{ m.is_active ? 'Aktif' : 'Pasif' }}</span></td><td class="px-5 py-4 text-right"><button class="mr-2 inline-flex rounded-md border border-primary-200 px-2.5 py-1.5 text-xs font-semibold text-primary-700 hover:bg-primary-50" @click="teklifSec(m)">Teklif Seç</button><button class="mr-2 inline-flex rounded-md border border-blue-200 px-2.5 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-50" @click="tedarikciAta(m)">Tedarikçi Ata</button><button class="inline-flex rounded-md border border-surface-200 p-1.5 text-surface-500 hover:bg-surface-50" title="Düzenle" @click="formuAc(m)"><Pencil :size="15" /></button></td></tr></tbody></table></div>
    </section>
    <div v-if="modalAcik" class="fixed inset-0 z-50 flex items-center justify-center bg-surface-950/40 p-4" @click.self="modalAcik = false"><form class="w-full max-w-2xl space-y-4 rounded-2xl bg-white p-6 shadow-xl" @submit.prevent="kaydet"><div class="flex items-center justify-between"><h2 class="font-heading text-xl font-bold">{{ duzenlenen ? 'Kayıt düzenle' : 'Yeni proje malzemesi' }}</h2><button type="button" @click="modalAcik = false"><X :size="20" /></button></div><div class="grid gap-3 md:grid-cols-2"><label class="text-sm font-medium">Proje *<select v-model="form.proje" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option></select></label><label class="text-sm font-medium">Malzeme *<select v-model="form.malzeme" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="m in malzemeListesi" :key="m.id" :value="m.id">{{ m.malzeme_kodu }} — {{ m.ad }}</option></select></label><label class="text-sm font-medium">Tedarikçi<select v-model="form.tedarikci" class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="">Seçin (opsiyonel)</option><option v-for="t in tedarikciler" :key="t.id" :value="t.id">{{ t.firma_adi }}</option></select></label><label class="text-sm font-medium">Cari<select v-model="form.cari" class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="">Seçin (opsiyonel)</option><option v-for="c in cariListesi" :key="c.id" :value="c.id">{{ c.ad }}</option></select></label><label class="text-sm font-medium md:col-span-2">Kaynak<input v-model="form.kaynak" class="mt-1 w-full rounded-lg border border-surface-200 p-2" placeholder="Örn. Tedarikçi listesi, piyasa araştırması" /></label><label class="text-sm font-medium md:col-span-2">Kaynak URL<input v-model="form.kaynak_url" type="url" class="mt-1 w-full rounded-lg border border-surface-200 p-2" placeholder="https://..." /></label><label class="text-sm font-medium md:col-span-2">Açıklama<textarea v-model="form.aciklama" class="mt-1 w-full rounded-lg border border-surface-200 p-2" rows="3" /></label><label class="flex items-center gap-2"><input v-model="form.is_active" type="checkbox" class="rounded border-surface-300 text-primary-600" /><span class="text-sm">Aktif</span></label></div><div class="flex justify-end gap-3 pt-4 border-t border-surface-100"><button type="button" class="rounded-lg border border-surface-200 px-4 py-2 text-sm font-medium text-surface-700 hover:bg-surface-50" @click="modalAcik = false">İptal</button><button class="inline-flex items-center justify-center gap-2 rounded-lg bg-primary-800 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-700" type="submit">Kaydet</button></div></form></div>
    <div v-if="teklifModalAcik" class="fixed inset-0 z-50 flex items-center justify-center bg-surface-950/40 p-4" @click.self="teklifModalAcik = false"><div class="w-full max-w-lg space-y-4 rounded-2xl bg-white p-6 shadow-xl"><div class="flex items-center justify-between"><h2 class="font-heading text-xl font-bold">Teklif Seç</h2><button type="button" @click="teklifModalAcik = false"><X :size="20" /></button></div><p class="text-sm text-surface-500">Kayıt: {{ secimKayit?.malzeme_kodu }} — {{ secimKayit?.malzeme_adi }} (yalnızca aynı proje/malzeme teklifleri listelenir)</p><label class="block text-sm font-medium">Teklif *<select v-model="seciliTeklif" class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="t in teklifListesi" :key="t.id" :value="t.id">{{ t.tedarikci_adi || ('#' + t.tedarikci) }} — {{ t.miktar }} × {{ t.birim_fiyat }} ₺</option></select></label><p v-if="!teklifListesi.length" class="text-sm text-surface-500">Uygun teklif yok — önce Tedarikçi Teklifleri ekranından teklif girin.</p><p v-if="islemHata" class="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">{{ islemHata }}</p><p v-if="islemBasari" class="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700" role="status">{{ islemBasari }}</p><div class="flex justify-end gap-2"><button type="button" class="rounded-lg border border-surface-200 px-4 py-2 text-sm" @click="teklifModalAcik = false">Vazgeç</button><button type="button" :disabled="islemYukleniyor" class="rounded-lg bg-primary-800 px-4 py-2 text-sm font-semibold text-white" @click="teklifKaydet">{{ islemYukleniyor ? 'Kaydediliyor…' : 'Kaydet' }}</button></div></div></div>
    <div v-if="tedarikciModalAcik" class="fixed inset-0 z-50 flex items-center justify-center bg-surface-950/40 p-4" @click.self="tedarikciModalAcik = false"><div class="w-full max-w-lg space-y-4 rounded-2xl bg-white p-6 shadow-xl"><div class="flex items-center justify-between"><h2 class="font-heading text-xl font-bold">Tedarikçi Ata</h2><button type="button" @click="tedarikciModalAcik = false"><X :size="20" /></button></div><p class="text-sm text-surface-500">Kayıt: {{ secimKayit?.malzeme_kodu }} — {{ secimKayit?.malzeme_adi }}</p><label class="block text-sm font-medium">Tedarikçi *<select v-model="tedarikciSecim" class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="t in tedarikciler" :key="t.id" :value="t.id">{{ t.firma_adi }}</option></select></label><p v-if="islemHata" class="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700" role="alert">{{ islemHata }}</p><p v-if="islemBasari" class="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700" role="status">{{ islemBasari }}</p><div class="flex justify-end gap-2"><button type="button" class="rounded-lg border border-surface-200 px-4 py-2 text-sm" @click="tedarikciModalAcik = false">Vazgeç</button><button type="button" :disabled="islemYukleniyor" class="rounded-lg bg-primary-800 px-4 py-2 text-sm font-semibold text-white" @click="tedarikciKaydet">{{ islemYukleniyor ? 'Kaydediliyor…' : 'Kaydet' }}</button></div></div></div>
  </main>
</template>

<style scoped>
/* Stillere gerek yok, Tailwind kullanılıyor */
</style>