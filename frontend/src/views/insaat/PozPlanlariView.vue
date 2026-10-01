<script setup lang="ts">
/**
 * Poz Planları (metraj) — proje/poz/yıl bazlı planlanan vs gerçekleşen metraj
 * ve S-eğrisi (planlanan/gerçekleşen maliyet karşılaştırma) raporu.
 * Backend: /api/v1/construction/poz-planlari/ (+ /s-egrisi/).
 */
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type {
  FiyatAnomaliRaporu,
  GanttRaporu,
  Metraj,
  MetrajHesaplamaSonucu,
  MetrajKontrolRaporu,
  Poz,
  PozPlan,
  Proje,
  SEkgrisiRaporu,
} from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))

const L = useKayitListesi<PozPlan>('/construction/poz-planlari/')
const projeler = ref<Proje[]>([])
const pozlar = ref<Poz[]>([])
const activeTab = ref<'planlar' | 'metrajlar'>('planlar')
const metrajlar = ref<Metraj[]>([])
const metrajYukleniyor = ref(false)
const metrajHata = ref('')
const metrajFormHata = ref('')
const metrajKaydediliyor = ref(false)
const metrajDuzenlenen = ref<Metraj | null>(null)
const metrajOnizleme = ref<MetrajHesaplamaSonucu | null>(null)
const metrajOnizlemeYukleniyor = ref(false)
const metrajForm = ref({
  ad: '',
  metraj_tipi: 'genel',
  ifade: '',
  birim: 'miktar',
  aciklama: '',
})

function metrajFormuSifirla(): void {
  metrajDuzenlenen.value = null
  metrajForm.value = { ad: '', metraj_tipi: 'genel', ifade: '', birim: 'miktar', aciklama: '' }
  metrajOnizleme.value = null
  metrajFormHata.value = ''
}

async function metrajListesiniGetir(): Promise<void> {
  metrajYukleniyor.value = true
  metrajHata.value = ''
  try {
    const sayfa = await insaatApi.metrajlar.liste({ is_active: true })
    metrajlar.value = sayfa.results
  } catch (bilinmeyen) {
    metrajHata.value = hataMesaji(bilinmeyen)
  } finally {
    metrajYukleniyor.value = false
  }
}

function metrajPayload(): Record<string, unknown> {
  const form = metrajForm.value
  return {
    ad: form.ad.trim(),
    metraj_tipi: form.metraj_tipi,
    ifade: form.ifade.trim(),
    sonuc: metrajOnizleme.value?.sonuc || '0',
    birim: form.birim.trim() || 'miktar',
    aciklama: form.aciklama.trim(),
    is_active: true,
  }
}

async function metrajOnizle(): Promise<void> {
  const form = metrajForm.value
  if (!form.ifade.trim()) {
    metrajFormHata.value = 'Hesap ifadesi zorunludur.'
    return
  }
  metrajOnizlemeYukleniyor.value = true
  metrajFormHata.value = ''
  try {
    metrajOnizleme.value = await insaatApi.metrajlar.hesapla({
      metraj_tipi: form.metraj_tipi,
      ifade: form.ifade.trim(),
      birim: form.birim.trim() || 'miktar',
    })
  } catch (bilinmeyen) {
    metrajOnizleme.value = null
    metrajFormHata.value = hataMesaji(bilinmeyen)
  } finally {
    metrajOnizlemeYukleniyor.value = false
  }
}

function metrajDuzenle(kayit: Metraj): void {
  metrajDuzenlenen.value = kayit
  metrajForm.value = {
    ad: kayit.ad,
    metraj_tipi: kayit.metraj_tipi,
    ifade: kayit.ifade,
    birim: kayit.birim,
    aciklama: kayit.aciklama || '',
  }
  metrajOnizleme.value = {
    sonuc: kayit.sonuc,
    birim: kayit.birim,
    metraj_tipi: kayit.metraj_tipi,
    ifade: kayit.ifade,
  }
}

async function metrajKaydet(): Promise<void> {
  const form = metrajForm.value
  if (!form.ad.trim() || !form.ifade.trim()) {
    metrajFormHata.value = 'Ad ve hesap ifadesi zorunludur.'
    return
  }
  if (!metrajOnizleme.value) {
    await metrajOnizle()
    if (!metrajOnizleme.value) return
  }
  metrajKaydediliyor.value = true
  metrajFormHata.value = ''
  try {
    const payload = metrajPayload()
    if (metrajDuzenlenen.value) {
      await insaatApi.metrajlar.guncelle(metrajDuzenlenen.value.id, payload)
    } else {
      await insaatApi.metrajlar.olustur(payload)
    }
    metrajFormuSifirla()
    await metrajListesiniGetir()
  } catch (bilinmeyen) {
    metrajFormHata.value = hataMesaji(bilinmeyen)
  } finally {
    metrajKaydediliyor.value = false
  }
}

async function metrajSil(kayit: Metraj): Promise<void> {
  if (!window.confirm(`“${kayit.ad}” metrajı silinsin mi?`)) return
  try {
    await insaatApi.metrajlar.sil(kayit.id)
    await metrajListesiniGetir()
    if (metrajDuzenlenen.value?.id === kayit.id) metrajFormuSifirla()
  } catch (bilinmeyen) {
    metrajHata.value = hataMesaji(bilinmeyen)
  }
}

const raporYil = ref<number>(new Date().getFullYear())
const rapor = ref<SEkgrisiRaporu | null>(null)
const raporYukleniyor = ref(false)
const raporHata = ref('')
const kontrol = ref<MetrajKontrolRaporu | null>(null)
const kontrolYukleniyor = ref(false)
const kontrolHata = ref('')
const fiyatAnomalileri = ref<FiyatAnomaliRaporu | null>(null)
const fiyatYukleniyor = ref(false)
const fiyatHata = ref('')

const para = (v: string): string => Number(v).toLocaleString('tr-TR', { minimumFractionDigits: 2 })
const metraj = (v: string): string => Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 4 })
const projeGoster = (id: number): string => projeler.value.find((p) => p.id === id)?.proje_kodu || `#${id}`
const sapmaSinifi = (v: string): string => (Number(v) > 0 ? 'text-danger-600' : 'text-success-700')

interface F {
  proje: number | null
  poz: number | null
  yil: number
  planlanan_miktar: string
  gercek_miktar: string
  planlanan_baslangic: string
  planlanan_bitis: string
  aciklama: string
}
const Fm = useKayitFormu<PozPlan, F>(
  insaatApi.pozPlanlari,
  () => ({ proje: null, poz: null, yil: new Date().getFullYear(), planlanan_miktar: '', gercek_miktar: '0', planlanan_baslangic: '', planlanan_bitis: '', aciklama: '' }),
  (k) => ({ proje: k.proje, poz: k.poz, yil: k.yil, planlanan_miktar: k.planlanan_miktar, gercek_miktar: k.gercek_miktar, planlanan_baslangic: k.planlanan_baslangic || '', planlanan_bitis: k.planlanan_bitis || '', aciklama: k.aciklama || '' }),
  (f) => ({
    proje: f.proje,
    poz: f.poz,
    yil: f.yil,
    planlanan_miktar: f.planlanan_miktar,
    gercek_miktar: f.gercek_miktar || '0',
    planlanan_baslangic: f.planlanan_baslangic || null,
    planlanan_bitis: f.planlanan_bitis || null,
    aciklama: f.aciklama.trim(),
  }),
  (f) => {
    if (!f.proje || !f.poz) return 'Proje ve poz seçimi zorunludur.'
    if (!f.yil) return 'Fiyat yılı zorunludur.'
    if (!(Number(f.planlanan_miktar) > 0)) return 'Planlanan metraj 0’dan büyük olmalıdır.'
    if (Number(f.gercek_miktar) < 0) return 'Gerçekleşen metraj negatif olamaz.'
    if (f.planlanan_baslangic && f.planlanan_bitis && f.planlanan_bitis < f.planlanan_baslangic)
      return 'Planlanan bitiş, başlangıçtan önce olamaz.'
    return ''
  },
)

async function raporGetir(): Promise<void> {
  const projeId = L.filtreler.value.proje as number | undefined
  if (!projeId) {
    raporHata.value = 'S-eğrisi için önce proje filtresi seçin.'
    rapor.value = null
    return
  }

  raporYukleniyor.value = true
  raporHata.value = ''
  try {
    rapor.value = await insaatApi.sEgrisi(projeId, raporYil.value)
  } catch (bilinmeyen) {
    raporHata.value = hataMesaji(bilinmeyen)
    rapor.value = null
  } finally {
    raporYukleniyor.value = false
  }
}

async function metrajKontroluGetir(): Promise<void> {
  const projeId = L.filtreler.value.proje as number | undefined
  if (!projeId) {
    kontrolHata.value = 'Akıllı kontrol için önce proje filtresi seçin.'
    kontrol.value = null
    return
  }
  kontrolYukleniyor.value = true
  kontrolHata.value = ''
  try {
    kontrol.value = await insaatApi.metrajKontrolu(projeId, raporYil.value)
  } catch (bilinmeyen) {
    kontrolHata.value = hataMesaji(bilinmeyen)
    kontrol.value = null
  } finally {
    kontrolYukleniyor.value = false
  }
}

const kontrolSinifi = (seviye: string): string => ({
  kritik: 'border-danger-200 bg-danger-50 text-danger-800',
  uyari: 'border-amber-200 bg-amber-50 text-amber-800',
  bilgi: 'border-primary-200 bg-primary-50 text-primary-800',
}[seviye] || 'border-surface-200 bg-surface-50 text-surface-700')

async function fiyatAnomalileriniGetir(): Promise<void> {
  const projeId = L.filtreler.value.proje as number | undefined
  if (!projeId) {
    fiyatHata.value = 'Fiyat kontrolü için önce proje filtresi seçin.'
    fiyatAnomalileri.value = null
    return
  }
  fiyatYukleniyor.value = true
  fiyatHata.value = ''
  try {
    fiyatAnomalileri.value = await insaatApi.fiyatAnomalileri(projeId, raporYil.value)
  } catch (bilinmeyen) {
    fiyatHata.value = hataMesaji(bilinmeyen)
    fiyatAnomalileri.value = null
  } finally {
    fiyatYukleniyor.value = false
  }
}

// ── Gantt şeması — iş kalemi bazlı zaman çizelgesi (roadmap Faz 2) ─────────
const ganttYil = ref<number | undefined>(undefined)
const gantt = ref<GanttRaporu | null>(null)
const ganttYukleniyor = ref(false)
const ganttHata = ref('')

async function ganttGetir(): Promise<void> {
  const projeId = L.filtreler.value.proje as number | undefined
  if (!projeId) {
    ganttHata.value = 'Gantt için önce proje filtresi seçin.'
    gantt.value = null
    return
  }
  ganttYukleniyor.value = true
  ganttHata.value = ''
  try {
    gantt.value = await insaatApi.gantt(projeId, ganttYil.value)
  } catch (bilinmeyen) {
    ganttHata.value = hataMesaji(bilinmeyen)
    gantt.value = null
  } finally {
    ganttYukleniyor.value = false
  }
}

const GUN_MS = 86_400_000
const tarihMs = (iso: string): number => new Date(`${iso}T00:00:00`).getTime()
const tarihKisa = (iso: string | null): string => (iso ? iso.slice(2) : '—')

/** Eksen aralığı (en erken → en geç + 1 gün) — çubuk konumları buna göre ölçeklenir. */
const ganttAralik = computed(() => {
  if (!gantt.value?.en_erken || !gantt.value?.en_gec) return null
  const ilk = tarihMs(gantt.value.en_erken)
  const son = tarihMs(gantt.value.en_gec) + GUN_MS
  return { ilk, gun: Math.max(1, Math.round((son - ilk) / GUN_MS)) }
})

/** Çubuk stili — sol konum ve genişlik yüzde; tarihsiz çubuk çizilmez. */
function cubukStili(baslangic: string | null, bitis: string | null): Record<string, string> | null {
  const a = ganttAralik.value
  if (!a || !baslangic) return null
  const bas = tarihMs(baslangic)
  const son = bitis ? tarihMs(bitis) + GUN_MS : bas + GUN_MS
  const sol = Math.max(0, ((bas - a.ilk) / (a.gun * GUN_MS)) * 100)
  const genislik = Math.min(100 - sol, Math.max(1.5, ((son - bas) / (a.gun * GUN_MS)) * 100))
  return { left: `${sol}%`, width: `${genislik}%` }
}

onMounted(async () => {
  try {
    projeler.value = await tumunuGetir(insaatApi.projeler.liste)
    pozlar.value = await tumunuGetir(insaatApi.pozlar.liste)
  } catch (bilinmeyen) {
    L.hata.value = hataMesaji(bilinmeyen)
  }
  await L.yukle()
  await metrajListesiniGetir()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Poz Planları (Metraj)</h1>
        <p class="mt-1 text-sm text-surface-500">
          Planlanan/gerçekleşen metraj — birim fiyat kayıt anında snapshot olarak saklanır.
        </p>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Plan</button>
    </div>

    <div class="mb-5 flex gap-1 border-b border-surface-200" role="tablist" aria-label="Poz planı çalışma alanı">
      <button
        type="button"
        role="tab"
        :aria-selected="activeTab === 'planlar'"
        class="border-b-2 px-3 py-2 text-sm font-medium transition-colors"
        :class="activeTab === 'planlar' ? 'border-primary-600 text-primary-700' : 'border-transparent text-surface-500 hover:text-surface-800'"
        @click="activeTab = 'planlar'"
      >
        Poz Planları
      </button>
      <button
        type="button"
        role="tab"
        :aria-selected="activeTab === 'metrajlar'"
        class="border-b-2 px-3 py-2 text-sm font-medium transition-colors"
        :class="activeTab === 'metrajlar' ? 'border-primary-600 text-primary-700' : 'border-transparent text-surface-500 hover:text-surface-800'"
        @click="activeTab = 'metrajlar'"
      >
        Metraj Hesapları
      </button>
    </div>

    <section v-if="activeTab === 'metrajlar'" class="rounded-2xl border border-surface-200 bg-surface-50 p-5 shadow-card" role="tabpanel" aria-label="Metraj hesapları">
      <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 class="font-heading text-base font-semibold text-surface-900">Metraj hesapları</h2>
          <p class="mt-1 text-xs text-surface-500">
            Seçili proje: <strong class="text-surface-700">{{ L.filtreler.value.proje ? projeGoster(L.filtreler.value.proje as number) : 'Tüm projeler' }}</strong>
            · Güvenli önizleme yalnızca dört işlem ve parantez kabul eder.
          </p>
        </div>
        <select v-model.number="L.filtreler.value.proje" class="alan w-full sm:w-auto" aria-label="Metraj proje bağlamı">
          <option :value="undefined">Tüm projeler</option>
          <option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option>
        </select>
      </div>

      <form v-if="yazabilir" class="mb-5 rounded-xl border border-primary-100 bg-white p-4" @submit.prevent="metrajKaydet">
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-[1.4fr_0.9fr_1fr_0.7fr]">
          <label class="etiket">Ad<input v-model="metrajForm.ad" class="alan" maxlength="200" required /></label>
          <label class="etiket">Hesap türü
            <select v-model="metrajForm.metraj_tipi" class="alan">
              <option value="genel">Genel ifade</option>
            </select>
          </label>
          <label class="etiket sm:col-span-2 lg:col-span-1">İfade<input v-model="metrajForm.ifade" class="alan font-mono" placeholder="12.5 * 3" required /></label>
          <label class="etiket">Birim<input v-model="metrajForm.birim" class="alan" maxlength="20" /></label>
        </div>
        <label class="etiket mt-3">Açıklama<textarea v-model="metrajForm.aciklama" class="alan" rows="1"></textarea></label>
        <div class="mt-3 flex flex-wrap items-center justify-between gap-3">
          <p v-if="metrajOnizleme" class="rounded-lg bg-success-50 px-3 py-2 text-sm text-success-800" aria-live="polite">
            Önizleme: <strong>{{ metraj(metrajOnizleme.sonuc) }} {{ metrajOnizleme.birim }}</strong>
          </p>
          <p v-else class="text-xs text-surface-500">Kaydetmeden önce önizleme yapın.</p>
          <div class="flex gap-2">
            <button type="button" class="ikincil-dugme" :disabled="metrajOnizlemeYukleniyor" @click="metrajOnizle">
              {{ metrajOnizlemeYukleniyor ? 'Hesaplanıyor…' : 'Önizle' }}
            </button>
            <button v-if="metrajDuzenlenen" type="button" class="ikincil-dugme" @click="metrajFormuSifirla">Yeni</button>
            <button type="submit" class="birincil-dugme" :disabled="metrajKaydediliyor">
              {{ metrajKaydediliyor ? 'Kaydediliyor…' : metrajDuzenlenen ? 'Güncelle' : 'Kaydet' }}
            </button>
          </div>
        </div>
        <p v-if="metrajFormHata" class="hata-kutusu mt-3" role="alert">{{ metrajFormHata }}</p>
      </form>

      <p v-if="metrajHata" class="hata-kutusu mb-3" role="alert">{{ metrajHata }}</p>
      <p v-if="metrajYukleniyor" class="text-sm text-surface-500">Metrajlar yükleniyor…</p>
      <div v-else class="overflow-x-auto rounded-xl border border-surface-200 bg-white">
        <table class="min-w-full divide-y divide-surface-200 text-sm">
          <thead class="bg-surface-100">
            <tr>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">Ad</th>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">İfade</th>
              <th class="px-3 py-2 text-right text-xs font-semibold uppercase text-surface-500">Sonuç</th>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">Birim</th>
              <th v-if="yazabilir" class="px-3 py-2 text-right text-xs font-semibold uppercase text-surface-500">İşlem</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-surface-100">
            <tr v-for="kayit in metrajlar" :key="kayit.id" class="hover:bg-surface-50">
              <td class="px-3 py-2 font-medium">{{ kayit.ad }}</td>
              <td class="px-3 py-2 font-mono text-xs text-surface-600">{{ kayit.ifade }}</td>
              <td class="px-3 py-2 text-right">{{ metraj(kayit.sonuc) }}</td>
              <td class="px-3 py-2">{{ kayit.birim }}</td>
              <td v-if="yazabilir" class="whitespace-nowrap px-3 py-2 text-right">
                <button type="button" class="mr-3 text-sm font-medium text-primary-700 hover:underline" @click="metrajDuzenle(kayit)">Düzenle</button>
                <button type="button" class="text-sm font-medium text-danger-700 hover:underline" @click="metrajSil(kayit)">Sil</button>
              </td>
            </tr>
            <tr v-if="metrajlar.length === 0">
              <td :colspan="yazabilir ? 5 : 4" class="px-3 py-8 text-center text-sm text-surface-400">Henüz metraj hesabı yok.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="activeTab === 'planlar'">
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Poz no / adı veya proje kodu ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model.number="L.filtreler.value.proje" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm projeler</option>
        <option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option>
      </select>
      <select v-model.number="L.filtreler.value.yil" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm yıllar</option>
        <option v-for="y in [raporYil - 1, raporYil, raporYil + 1]" :key="y" :value="y">{{ y }}</option>
      </select>
    </div>

    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>

    <VeriTablosu
      :basliklar="['Proje', 'Poz No', 'Poz Adı', 'Yıl', 'Planlanan', 'Gerçekleşen', 'Birim Fiyat', 'Plan Değer', 'Gerçek Değer', yazabilir ? 'İşlem' : '']"
      :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0"
    >
      <tr v-for="k in L.kayitlar.value" :key="k.id" class="transition-colors hover:bg-surface-100/60">
        <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium">{{ projeGoster(k.proje) }}</td>
        <td class="whitespace-nowrap px-4 py-3 font-mono text-xs">{{ k.poz_no }}</td>
        <td class="max-w-xs truncate px-4 py-3">{{ pozlar.find((p) => p.id === k.poz)?.ad || '—' }}</td>
        <td class="px-4 py-3">{{ k.yil }}</td>
        <td class="whitespace-nowrap px-4 py-3 text-right">{{ metraj(k.planlanan_miktar) }}</td>
        <td class="whitespace-nowrap px-4 py-3 text-right">{{ metraj(k.gercek_miktar) }}</td>
        <td class="whitespace-nowrap px-4 py-3 text-right">{{ para(k.birim_fiyat_snapshot) }} ₺</td>
        <td class="whitespace-nowrap px-4 py-3 text-right">{{ para(k.plan_deger) }} ₺</td>
        <td class="whitespace-nowrap px-4 py-3 text-right">{{ para(k.gercek_deger) }} ₺</td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
          <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(k)">Düzenle</button>
        </td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />

    <section class="mt-8 rounded-2xl border border-surface-200 bg-surface-50 p-5 shadow-card">
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 class="font-heading text-base font-semibold text-surface-900">
            S-Eğrisi — Planlanan / Gerçekleşen Karşılaştırma
          </h2>
          <p class="mt-1 text-xs text-surface-500">
            PV = planlanan metraj × birim fiyat · AV = gerçekleşen metraj × birim fiyat
          </p>
        </div>
        <div class="flex items-end gap-2">
          <label class="etiket">Yıl<input v-model.number="raporYil" type="number" class="alan w-28" /></label>
          <button type="button" class="ikincil-dugme" :disabled="raporYukleniyor" @click="raporGetir()">
            {{ raporYukleniyor ? 'Hesaplanıyor…' : 'Raporu Getir' }}
          </button>
        </div>
      </div>

      <p v-if="raporHata" class="hata-kutusu mt-4" role="alert">{{ raporHata }}</p>

      <template v-if="rapor">
        <div class="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <div class="rounded-xl border border-surface-200 bg-surface-100 p-4">
            <p class="text-xs font-medium uppercase tracking-wide text-surface-500">Toplam Plan (PV)</p>
            <p class="mt-1 font-heading text-lg font-semibold text-surface-900">{{ para(rapor.toplam_plan_deger) }} ₺</p>
          </div>
          <div class="rounded-xl border border-surface-200 bg-surface-100 p-4">
            <p class="text-xs font-medium uppercase tracking-wide text-surface-500">Toplam Gerçekleşen (AV)</p>
            <p class="mt-1 font-heading text-lg font-semibold text-surface-900">{{ para(rapor.toplam_gercek_deger) }} ₺</p>
          </div>
          <div class="rounded-xl border border-surface-200 bg-surface-100 p-4">
            <p class="text-xs font-medium uppercase tracking-wide text-surface-500">Sapma</p>
            <p class="mt-1 font-heading text-lg font-semibold" :class="sapmaSinifi(rapor.toplam_sapma_tutar)">
              {{ para(rapor.toplam_sapma_tutar) }} ₺
            </p>
          </div>
          <div class="rounded-xl border border-surface-200 bg-surface-100 p-4">
            <p class="text-xs font-medium uppercase tracking-wide text-surface-500">Sapma %</p>
            <p class="mt-1 font-heading text-lg font-semibold" :class="sapmaSinifi(rapor.toplam_sapma_tutar)">
              {{ rapor.toplam_sapma_yuzde }}
            </p>
          </div>
        </div>

        <div class="mt-4 overflow-x-auto rounded-xl border border-surface-200 bg-surface-50">
          <table class="min-w-full divide-y divide-surface-200 text-sm">
            <thead class="bg-surface-100">
              <tr>
                <th class="px-4 py-3 text-left font-heading text-xs font-semibold uppercase tracking-wider text-surface-500">Poz No</th>
                <th class="px-4 py-3 text-left font-heading text-xs font-semibold uppercase tracking-wider text-surface-500">Poz Adı</th>
                <th class="px-4 py-3 text-right font-heading text-xs font-semibold uppercase tracking-wider text-surface-500">Plan Metraj</th>
                <th class="px-4 py-3 text-right font-heading text-xs font-semibold uppercase tracking-wider text-surface-500">Gerçekleşen</th>
                <th class="px-4 py-3 text-right font-heading text-xs font-semibold uppercase tracking-wider text-surface-500">Plan Değer</th>
                <th class="px-4 py-3 text-right font-heading text-xs font-semibold uppercase tracking-wider text-surface-500">Gerçek Değer</th>
                <th class="px-4 py-3 text-right font-heading text-xs font-semibold uppercase tracking-wider text-surface-500">Sapma</th>
                <th class="px-4 py-3 text-right font-heading text-xs font-semibold uppercase tracking-wider text-surface-500">Sapma %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-100">
              <tr v-for="s in rapor.pozlar" :key="s.poz_no">
                <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium">{{ s.poz_no }}</td>
                <td class="max-w-xs truncate px-4 py-3">{{ s.poz_ad }}</td>
                <td class="whitespace-nowrap px-4 py-3 text-right">{{ metraj(s.planlanan_miktar) }} {{ s.birim }}</td>
                <td class="whitespace-nowrap px-4 py-3 text-right">{{ metraj(s.gercek_miktar) }} {{ s.birim }}</td>
                <td class="whitespace-nowrap px-4 py-3 text-right">{{ para(s.plan_deger) }} ₺</td>
                <td class="whitespace-nowrap px-4 py-3 text-right">{{ para(s.gercek_deger) }} ₺</td>
                <td class="whitespace-nowrap px-4 py-3 text-right" :class="sapmaSinifi(s.sapma_tutar)">{{ para(s.sapma_tutar) }} ₺</td>
                <td class="whitespace-nowrap px-4 py-3 text-right" :class="sapmaSinifi(s.sapma_tutar)">{{ s.sapma_yuzde }}</td>
              </tr>
              <tr v-if="rapor.pozlar.length === 0">
                <td colspan="8" class="px-4 py-8 text-center text-sm text-surface-400">
                  Seçilen proje/yıl için plan bulunamadı.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </section>

    <section class="mt-8 rounded-2xl border border-primary-100 bg-gradient-to-br from-primary-50 via-white to-surface-50 p-5 shadow-card">
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.16em] text-primary-700">Akıllı metraj kontrolü</p>
          <h2 class="mt-1 font-heading text-base font-semibold text-surface-900">Sahadaki sapmaları erken yakalayın</h2>
          <p class="mt-1 max-w-2xl text-xs text-surface-500">Açıklanabilir eşiklerle fazla metraj, gerçekleşmeyen plan ve düşük ilerleme sinyallerini tarar. Öneriler karar desteğidir; kayıtları otomatik değiştirmez.</p>
        </div>
        <button type="button" class="birincil-dugme" :disabled="kontrolYukleniyor" @click="metrajKontroluGetir">
          {{ kontrolYukleniyor ? 'Kontrol ediliyor…' : 'Kontrolü Çalıştır' }}
        </button>
      </div>
      <p v-if="kontrolHata" class="hata-kutusu mt-4" role="alert">{{ kontrolHata }}</p>
      <template v-if="kontrol">
        <div class="mt-4 grid gap-3 sm:grid-cols-4">
          <div class="rounded-xl border border-surface-200 bg-white p-4"><p class="text-xs text-surface-500">Kontrol edilen poz</p><p class="mt-1 text-xl font-bold text-surface-900">{{ kontrol.kontrol_edilen_poz }}</p></div>
          <div class="rounded-xl border border-danger-200 bg-danger-50 p-4"><p class="text-xs text-danger-700">Kritik</p><p class="mt-1 text-xl font-bold text-danger-800">{{ kontrol.kritik }}</p></div>
          <div class="rounded-xl border border-amber-200 bg-amber-50 p-4"><p class="text-xs text-amber-700">Uyarı</p><p class="mt-1 text-xl font-bold text-amber-800">{{ kontrol.uyari }}</p></div>
          <div class="rounded-xl border border-primary-200 bg-primary-50 p-4"><p class="text-xs text-primary-700">Bilgi</p><p class="mt-1 text-xl font-bold text-primary-800">{{ kontrol.bilgi }}</p></div>
        </div>
        <div v-if="kontrol.oneriler.length" class="mt-4 space-y-2">
          <article v-for="oner in kontrol.oneriler" :key="`${oner.poz_no}-${oner.kod}`" class="rounded-xl border p-4" :class="kontrolSinifi(oner.seviye)">
            <div class="flex flex-wrap items-start justify-between gap-2"><div><p class="font-mono text-xs font-semibold">{{ oner.poz_no }} · {{ oner.poz_ad }}</p><p class="mt-1 text-sm font-medium">{{ oner.mesaj }}</p></div><span class="rounded-full bg-white/70 px-2 py-1 text-[11px] font-semibold uppercase">{{ oner.seviye }}</span></div>
            <p class="mt-2 text-xs opacity-80">Önerilen aksiyon: {{ oner.onerilen_aksiyon }}</p>
          </article>
        </div>
        <p v-else class="mt-4 rounded-xl border border-success-200 bg-success-50 p-4 text-sm text-success-800">Seçilen dönem için kritik sapma veya eksik gerçekleşme sinyali bulunmadı.</p>
      </template>
    </section>

    <section class="mt-8 rounded-2xl border border-amber-100 bg-gradient-to-br from-amber-50 via-white to-surface-50 p-5 shadow-card">
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.16em] text-amber-700">Fiyat riski</p>
          <h2 class="mt-1 font-heading text-base font-semibold text-surface-900">Birim fiyat anomalilerini inceleyin</h2>
          <p class="mt-1 max-w-2xl text-xs text-surface-500">Seçilen yılın snapshot fiyatını önceki yılın aktif fiyatıyla karşılaştırır. Sonuçlar açıklanabilir uyarıdır; kayıtlar otomatik değiştirilmez.</p>
        </div>
        <button type="button" class="ikincil-dugme" :disabled="fiyatYukleniyor" @click="fiyatAnomalileriniGetir">
          {{ fiyatYukleniyor ? 'Taranıyor…' : 'Fiyatları Tara' }}
        </button>
      </div>
      <p v-if="fiyatHata" class="hata-kutusu mt-4" role="alert">{{ fiyatHata }}</p>
      <template v-if="fiyatAnomalileri">
        <div class="mt-4 grid gap-3 sm:grid-cols-3">
          <div class="rounded-xl border border-surface-200 bg-white p-4"><p class="text-xs text-surface-500">Kontrol edilen poz</p><p class="mt-1 text-xl font-bold">{{ fiyatAnomalileri.kontrol_edilen_poz }}</p></div>
          <div class="rounded-xl border border-danger-200 bg-danger-50 p-4"><p class="text-xs text-danger-700">Kritik fiyat farkı</p><p class="mt-1 text-xl font-bold text-danger-800">{{ fiyatAnomalileri.kritik }}</p></div>
          <div class="rounded-xl border border-amber-200 bg-amber-50 p-4"><p class="text-xs text-amber-700">İncelenecek uyarı</p><p class="mt-1 text-xl font-bold text-amber-800">{{ fiyatAnomalileri.uyari }}</p></div>
        </div>
        <div v-if="fiyatAnomalileri.anomaliler.length" class="mt-4 space-y-2">
          <article v-for="anomali in fiyatAnomalileri.anomaliler" :key="`${anomali.poz_no}-${anomali.yil}`" class="rounded-xl border p-4" :class="kontrolSinifi(anomali.seviye)">
            <div class="flex flex-wrap items-start justify-between gap-2"><div><p class="font-mono text-xs font-semibold">{{ anomali.poz_no }} · {{ anomali.poz_ad }}</p><p class="mt-1 text-sm font-medium">{{ anomali.mesaj }}</p></div><span class="rounded-full bg-white/70 px-2 py-1 text-[11px] font-semibold uppercase">{{ anomali.seviye }}</span></div>
            <div class="mt-3 flex flex-wrap gap-4 text-xs opacity-80"><span>Mevcut: <strong>{{ para(anomali.mevcut_fiyat) }} ₺</strong></span><span>Referans: <strong>{{ para(anomali.referans_fiyat) }} ₺</strong></span><span>Değişim: <strong>{{ anomali.degisim_yuzde }}</strong></span></div>
            <p class="mt-2 text-xs opacity-80">Önerilen aksiyon: {{ anomali.onerilen_aksiyon }}</p>
          </article>
        </div>
        <p v-else class="mt-4 rounded-xl border border-success-200 bg-success-50 p-4 text-sm text-success-800">Seçilen proje ve yıl için önceki yıla göre olağandışı fiyat farkı bulunmadı.</p>
      </template>
    </section>

    <!-- Gantt şeması — iş kalemi bazlı zaman çizelgesi -->
    <section class="mt-8 rounded-2xl border border-surface-200 bg-surface-50 shadow-card">
      <div class="flex flex-wrap items-center justify-between gap-3 border-b border-surface-100 px-6 py-4">
        <div>
          <h2 class="font-heading text-sm font-semibold text-surface-900">Gantt Şeması</h2>
          <p class="mt-0.5 text-xs text-surface-500">
            Poz planlarındaki planlanan tarihler; çubuk üstündeki koyu bant gerçekleşen metraj oranını gösterir.
          </p>
        </div>
        <div class="flex items-center gap-2">
          <select v-model.number="ganttYil" class="alan" title="Yıl filtresi (boş = tüm yıllar)">
            <option :value="undefined">Tüm yıllar</option>
            <option v-for="y in [new Date().getFullYear() - 1, new Date().getFullYear(), new Date().getFullYear() + 1]" :key="y" :value="y">{{ y }}</option>
          </select>
          <button type="button" class="ikincil-dugme" :disabled="ganttYukleniyor" @click="ganttGetir">
            {{ ganttYukleniyor ? 'Yükleniyor…' : 'Çiz' }}
          </button>
        </div>
      </div>
      <div class="px-6 py-4">
        <p v-if="ganttHata" class="hata-kutusu mb-4" role="alert">{{ ganttHata }}</p>
        <template v-if="gantt">
          <p class="mb-3 text-xs text-surface-500">
            Aralık: <span class="font-medium text-surface-700">{{ tarihKisa(gantt.en_erken) }} → {{ tarihKisa(gantt.en_gec) }}</span>
            <span
              v-if="gantt.tarihsiz_sayi > 0"
              class="ml-2 rounded bg-warning-50 px-1.5 py-0.5 text-warning-700"
            >{{ gantt.tarihsiz_sayi }} poz tarihsiz</span>
          </p>
          <div class="overflow-hidden rounded-xl border border-surface-100">
            <div
              v-for="c in gantt.cubuklar"
              :key="c.id"
              class="grid grid-cols-[220px_1fr_70px] items-center gap-3 border-b border-surface-100 px-4 py-2 last:border-b-0"
            >
              <div class="min-w-0">
                <p class="truncate font-mono text-xs font-medium text-surface-800">{{ c.poz_no }}</p>
                <p class="truncate text-xs text-surface-500">{{ c.poz_ad }}</p>
              </div>
              <div class="relative h-6 rounded bg-surface-100">
                <div
                  v-if="cubukStili(c.baslangic, c.bitis)"
                  class="absolute top-0.5 h-5 rounded bg-primary-200/70"
                  :style="cubukStili(c.baslangic, c.bitis)!"
                >
                  <div
                    class="h-full rounded bg-primary-700"
                    :style="{ width: `${Math.min(100, Number(c.ilerleme_yuzde))}%` }"
                  ></div>
                </div>
                <span v-else class="absolute inset-y-0 left-2 flex items-center text-xs text-surface-400">
                  Tarih girilmedi
                </span>
              </div>
              <p class="text-right text-xs font-medium" :class="Number(c.ilerleme_yuzde) >= 100 ? 'text-success-700' : 'text-surface-700'">
                {{ c.ilerleme_yuzde }}%
              </p>
            </div>
            <p v-if="gantt.cubuklar.length === 0" class="px-4 py-8 text-center text-sm text-surface-400">
              Seçilen proje için plan bulunamadı.
            </p>
          </div>
        </template>
        <p v-else-if="!ganttHata" class="text-center text-sm text-surface-400">
          Gantt için proje filtresi seçip “Çiz”e basın.
        </p>
      </div>
    </section>

    <KayitModal
      v-if="Fm.modalAcik.value"
      :baslik="Fm.duzenlenen.value ? 'Planı Düzenle' : 'Yeni Poz Planı'"
      @kapat="Fm.modalAcik.value = false"
    >
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <label class="etiket">
          Proje
          <select v-model.number="Fm.form.value.proje" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option>
          </select>
        </label>
        <label class="etiket">
          Poz
          <select v-model.number="Fm.form.value.poz" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="p in pozlar" :key="p.id" :value="p.id">{{ p.poz_no }} — {{ p.ad }}</option>
          </select>
        </label>
        <div class="grid grid-cols-3 gap-4">
          <label class="etiket">Yıl<input v-model.number="Fm.form.value.yil" type="number" class="alan" /></label>
          <label class="etiket">Planlanan Metraj<input v-model="Fm.form.value.planlanan_miktar" type="text" inputmode="decimal" class="alan" /></label>
          <label class="etiket">Gerçekleşen<input v-model="Fm.form.value.gercek_miktar" type="text" inputmode="decimal" class="alan" /></label>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">
            Planlanan Başlangıç
            <input v-model="Fm.form.value.planlanan_baslangic" type="date" class="alan" />
          </label>
          <label class="etiket">
            Planlanan Bitiş
            <input v-model="Fm.form.value.planlanan_bitis" type="date" class="alan" />
          </label>
        </div>
        <p class="text-xs text-surface-500">
          Birim fiyat, seçilen pozun ilgili yıldaki aktif fiyatından otomatik alınır (snapshot — değişmez).
          Planlanan tarihler Gantt şemasında çubuk olarak görünür (opsiyonel).
        </p>
        <label class="etiket">Açıklama<textarea v-model="Fm.form.value.aciklama" rows="2" class="alan"></textarea></label>
        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">
            {{ Fm.kaydediliyor.value ? 'Kaydediliyor…' : 'Kaydet' }}
          </button>
        </div>
      </form>
    </KayitModal>
    </div>
  </div>
</template>