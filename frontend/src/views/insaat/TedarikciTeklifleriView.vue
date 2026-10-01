<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Check, ClipboardList, Pencil, Plus, Search, Trophy, X } from 'lucide-vue-next'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import type { Malzeme, Proje, Tedarikci, TedarikciTeklifi } from '@/types/insaat'

const teklifler = ref<TedarikciTeklifi[]>([])
const projeler = ref<Proje[]>([])
const malzemeler = ref<Malzeme[]>([])
const tedarikciler = ref<Tedarikci[]>([])
const yukleniyor = ref(true)
const modalAcik = ref(false)
const duzenlenen = ref<number | null>(null)
const arama = ref('')
const projeFiltresi = ref('')
const durumFiltresi = ref('')
const hata = ref('')

const form = reactive({
  proje: '', malzeme: '', tedarikci: '', miktar: '', birim_fiyat: '',
  durum: 'taslak', gecerlilik_tarihi: '', notlar: '',
})

const durumEtiketleri: Record<string, string> = {
  taslak: 'Taslak', istendi: 'İstendi', geldi: 'Teklif alındı',
  degerlendiriliyor: 'Değerlendiriliyor', kabul: 'Kabul edildi', red: 'Reddedildi', iptal: 'İptal',
}
const filtrelenmis = computed(() => teklifler.value.filter((t) => {
  const metin = `${t.proje_kodu} ${t.malzeme_adi} ${t.tedarikci_adi}`.toLocaleLowerCase('tr-TR')
  return (!arama.value || metin.includes(arama.value.toLocaleLowerCase('tr-TR')))
    && (!projeFiltresi.value || String(t.proje) === projeFiltresi.value)
    && (!durumFiltresi.value || t.durum === durumFiltresi.value)
}))
const gruplar = computed(() => {
  const map = new Map<string, TedarikciTeklifi[]>()
  filtrelenmis.value.forEach((t) => {
    const key = `${t.proje}-${t.malzeme}`
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(t)
  })
  return [...map.values()]
})
const para = (deger: string) => new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(Number(deger))
const durumRengi = (durum: string) => ({ kabul: 'bg-emerald-50 text-emerald-700', red: 'bg-rose-50 text-rose-700', istendi: 'bg-amber-50 text-amber-700', geldi: 'bg-blue-50 text-blue-700' }[durum] || 'bg-surface-100 text-surface-600')

async function yukle() {
  yukleniyor.value = true
  try {
    const [liste, p, m, t] = await Promise.all([
      tumunuGetir(insaatApi.tedarikciTeklifleri.liste),
      tumunuGetir(insaatApi.projeler.liste, { is_active: true }),
      tumunuGetir(insaatApi.malzemeler.liste, { is_active: true }),
      tumunuGetir(insaatApi.tedarikciler.liste, { is_active: true }),
    ])
    teklifler.value = liste
    projeler.value = p
    malzemeler.value = m
    tedarikciler.value = t
  } catch { hata.value = 'Teklifler yüklenemedi. Lütfen tekrar deneyin.' } finally { yukleniyor.value = false }
}
function formuAc(teklif?: TedarikciTeklifi) {
  duzenlenen.value = teklif?.id ?? null
  Object.assign(form, teklif ? {
    proje: String(teklif.proje), malzeme: String(teklif.malzeme), tedarikci: String(teklif.tedarikci),
    miktar: teklif.miktar, birim_fiyat: teklif.birim_fiyat, durum: teklif.durum,
    gecerlilik_tarihi: teklif.gecerlilik_tarihi || '', notlar: teklif.notlar,
  } : { proje: '', malzeme: '', tedarikci: '', miktar: '', birim_fiyat: '', durum: 'taslak', gecerlilik_tarihi: '', notlar: '' })
  hata.value = ''; modalAcik.value = true
}
async function kaydet() {
  hata.value = ''
  try {
    const veri = { ...form, proje: Number(form.proje), malzeme: Number(form.malzeme), tedarikci: Number(form.tedarikci) }
    if (duzenlenen.value) await insaatApi.tedarikciTeklifleri.guncelle(duzenlenen.value, veri)
    else await insaatApi.tedarikciTeklifleri.olustur(veri)
    modalAcik.value = false; await yukle()
  } catch { hata.value = 'Kayıt kaydedilemedi. Zorunlu alanları kontrol edin.' }
}
async function kazananSec(teklif: TedarikciTeklifi) {
  if (!confirm(`${teklif.tedarikci_adi} teklifini kazanan olarak seçmek istiyor musunuz?`)) return
  try { await insaatApi.tedarikciTeklifleri.kazananSec(teklif.id); await yukle() }
  catch { hata.value = 'Kazanan seçilemedi.' }
}
onMounted(yukle)
</script>

<template>
  <main class="mx-auto max-w-7xl space-y-6 p-6">
    <header class="flex flex-col justify-between gap-4 md:flex-row md:items-end">
      <div>
        <p class="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-primary-700"><ClipboardList :size="15" /> Satın alma</p>
        <h1 class="font-heading text-3xl font-bold text-surface-950">Tedarikçi teklifleri</h1>
        <p class="mt-1 text-sm text-surface-500">Aynı malzeme için gelen teklifleri yan yana değerlendirin, kazananı seçin.</p>
      </div>
      <button class="inline-flex items-center justify-center gap-2 rounded-lg bg-primary-800 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-700" @click="formuAc()"><Plus :size="17" /> Yeni teklif</button>
    </header>
    <div v-if="hata" class="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{{ hata }}</div>
    <section class="grid gap-3 rounded-xl border border-surface-200 bg-white p-4 shadow-sm md:grid-cols-[1fr_200px_180px]">
      <label class="relative"><Search class="absolute left-3 top-2.5 text-surface-400" :size="17" /><input v-model="arama" class="w-full rounded-lg border border-surface-200 py-2 pl-10 pr-3 text-sm outline-none focus:border-primary-500" placeholder="Proje, malzeme veya tedarikçi ara" /></label>
      <select v-model="projeFiltresi" class="rounded-lg border border-surface-200 px-3 py-2 text-sm"><option value="">Tüm projeler</option><option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option></select>
      <select v-model="durumFiltresi" class="rounded-lg border border-surface-200 px-3 py-2 text-sm"><option value="">Tüm durumlar</option><option v-for="(etiket, kod) in durumEtiketleri" :key="kod" :value="kod">{{ etiket }}</option></select>
    </section>
    <div v-if="yukleniyor" class="rounded-xl border border-surface-200 bg-white p-12 text-center text-sm text-surface-500">Teklifler yükleniyor…</div>
    <div v-else-if="!gruplar.length" class="rounded-xl border border-dashed border-surface-300 bg-white p-14 text-center"><ClipboardList class="mx-auto mb-3 text-surface-300" :size="34" /><p class="font-semibold text-surface-700">Henüz teklif yok</p><p class="mt-1 text-sm text-surface-500">İlk teklifi ekleyerek karşılaştırmaya başlayın.</p></div>
    <section v-for="grup in gruplar" :key="`${grup[0].proje}-${grup[0].malzeme}`" class="overflow-hidden rounded-xl border border-surface-200 bg-white shadow-sm">
      <div class="flex flex-wrap items-center justify-between gap-2 border-b border-surface-100 bg-surface-50 px-5 py-4"><div><h2 class="font-semibold text-surface-900">{{ grup[0].malzeme_adi }}</h2><p class="text-xs text-surface-500">{{ grup[0].proje_kodu }} · {{ grup[0].malzeme_birimi }}</p></div><span class="rounded-full bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700">{{ grup.length }} teklif</span></div>
      <div class="overflow-x-auto"><table class="w-full min-w-[760px] text-left text-sm"><thead class="text-xs uppercase tracking-wide text-surface-500"><tr><th class="px-5 py-3">Tedarikçi</th><th class="px-5 py-3">Miktar</th><th class="px-5 py-3">Birim fiyat</th><th class="px-5 py-3">Toplam</th><th class="px-5 py-3">Durum</th><th class="px-5 py-3 text-right">İşlem</th></tr></thead><tbody><tr v-for="t in grup" :key="t.id" class="border-t border-surface-100" :class="{ 'bg-emerald-50/50': t.secildi }"><td class="px-5 py-4 font-medium text-surface-800"><span class="flex items-center gap-2">{{ t.tedarikci_adi }} <Trophy v-if="t.secildi" class="text-amber-500" :size="16" /></span><small v-if="t.notlar" class="mt-1 block max-w-[230px] truncate text-xs font-normal text-surface-500">{{ t.notlar }}</small></td><td class="px-5 py-4">{{ t.miktar }} {{ t.malzeme_birimi }}</td><td class="px-5 py-4 font-medium">{{ para(t.birim_fiyat) }}</td><td class="px-5 py-4 font-semibold">{{ para(t.toplam_tutar) }}</td><td class="px-5 py-4"><span class="rounded-full px-2.5 py-1 text-xs font-medium" :class="durumRengi(t.durum)">{{ durumEtiketleri[t.durum] }}</span></td><td class="px-5 py-4 text-right"><button v-if="!t.secildi" class="mr-2 inline-flex items-center gap-1 rounded-md border border-emerald-200 px-2.5 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-50" @click="kazananSec(t)"><Check :size="14" /> Kazanan seç</button><button class="inline-flex rounded-md border border-surface-200 p-1.5 text-surface-500 hover:bg-surface-50" title="Düzenle" @click="formuAc(t)"><Pencil :size="15" /></button></td></tr></tbody></table></div>
    </section>
    <div v-if="modalAcik" class="fixed inset-0 z-50 flex items-center justify-center bg-surface-950/40 p-4" @click.self="modalAcik = false"><form class="w-full max-w-lg space-y-4 rounded-2xl bg-white p-6 shadow-xl" @submit.prevent="kaydet"><div class="flex items-center justify-between"><h2 class="font-heading text-xl font-bold">{{ duzenlenen ? 'Teklifi düzenle' : 'Yeni teklif' }}</h2><button type="button" @click="modalAcik = false"><X :size="20" /></button></div><div class="grid gap-3 md:grid-cols-2"><label class="text-sm font-medium">Proje<select v-model="form.proje" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }}</option></select></label><label class="text-sm font-medium">Malzeme<select v-model="form.malzeme" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="m in malzemeler" :key="m.id" :value="m.id">{{ m.ad }}</option></select></label><label class="text-sm font-medium">Tedarikçi<select v-model="form.tedarikci" required class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option value="" disabled>Seçin</option><option v-for="t in tedarikciler" :key="t.id" :value="t.id">{{ t.firma_adi }}</option></select></label><label class="text-sm font-medium">Durum<select v-model="form.durum" class="mt-1 w-full rounded-lg border border-surface-200 p-2"><option v-for="(etiket, kod) in durumEtiketleri" :key="kod" :value="kod">{{ etiket }}</option></select></label><label class="text-sm font-medium">Miktar<input v-model="form.miktar" required type="number" min="0.0001" step="0.0001" class="mt-1 w-full rounded-lg border border-surface-200 p-2" /></label><label class="text-sm font-medium">Birim fiyat (₺)<input v-model="form.birim_fiyat" required type="number" min="0.01" step="0.01" class="mt-1 w-full rounded-lg border border-surface-200 p-2" /></label><label class="text-sm font-medium">Geçerlilik tarihi<input v-model="form.gecerlilik_tarihi" type="date" class="mt-1 w-full rounded-lg border border-surface-200 p-2" /></label></div><label class="text-sm font-medium">Notlar<textarea v-model="form.notlar" rows="3" class="mt-1 w-full rounded-lg border border-surface-200 p-2"></textarea></label><button class="w-full rounded-lg bg-primary-800 py-2.5 font-semibold text-white hover:bg-primary-700">{{ duzenlenen ? 'Güncelle' : 'Teklifi kaydet' }}</button></form></div>
  </main>
</template>
