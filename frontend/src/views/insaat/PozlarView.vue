<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import ExcelAktarim, { type ExcelSutun } from '@/components/ExcelAktarim.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import { POZ_TIPLERI, type Poz, type PozGrubu, type ProjePozFiyat, type Proje } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const globalGorunum = computed(() => auth.kullanici?.role === 'super_admin' && auth.seciliTenantId === null)
const pozYazabilir = computed(() => yazabilir.value && !globalGorunum.value)
const L = useKayitListesi<Poz>('/construction/pozlar/')
const gruplar = ref<PozGrubu[]>([])
const excelSutunlari: ExcelSutun[] = [
  { key: 'poz_no', label: 'Poz No', required: true }, { key: 'ad', label: 'Ad', required: true },
  { key: 'birim', label: 'Birim', required: true }, { key: 'tip', label: 'Tip', templateValue: 'yapim' },
  { key: 'grup', label: 'Grup', required: true },
]

// Proje Fiyatları Modal
const projeFiyatlarModalAcik = ref(false)
const seciliPoz = ref<Poz | null>(null)
const projeFiyatlar = ref<ProjePozFiyat[]>([])
const projeFiyatlarYukleniyor = ref(false)
const projeFiyatlarHata = ref('')
const projeler = ref<Proje[]>([])

async function projeFiyatlariAc(poz: Poz): Promise<void> {
  seciliPoz.value = poz
  projeFiyatlarModalAcik.value = true
  projeFiyatlarHata.value = ''
  projeFiyatlarYukleniyor.value = true
  try {
    const [fiyatlar, projelerListesi] = await Promise.all([
      tumunuGetir(insaatApi.projePozFiyatlari.liste, { poz: poz.id }),
      tumunuGetir(insaatApi.projeler.liste),
    ])
    projeFiyatlar.value = fiyatlar
    projeler.value = projelerListesi
  } catch (error) {
    projeFiyatlarHata.value = hataMesaji(error)
  } finally {
    projeFiyatlarYukleniyor.value = false
  }
}

const projeAdi = (k: ProjePozFiyat): string => k.proje_kodu || projeler.value.find((p) => p.id === k.proje)?.ad || '#' + k.proje
async function excelAl(rows: Record<string, unknown>[]): Promise<void> {
  try {
    for (const row of rows) await insaatApi.pozlar.olustur(row)
    await L.yukle()
    L.hata.value = ''
  } catch (error) {
    L.hata.value = `Excel içe aktarma kısmi olarak tamamlandı: ${error instanceof Error ? error.message : 'geçersiz veri.'}`
    await L.yukle()
  }
}
const grupAdi = (k: Poz): string => k.grup_bilgisi
  || gruplar.value.find((g) => g.id === k.grup)?.ad || `#${k.grup}`
async function pozuSil(poz: Poz): Promise<void> {
  if (globalGorunum.value) {
    L.hata.value = 'Silme işlemi için üst menüden bir firma seçin.'
    return
  }
  if (!window.confirm(`"${poz.poz_no} — ${poz.ad}" pozunu silmek istediğinize emin misiniz?`)) return
  try {
    await insaatApi.pozlar.sil(poz.id)
    await L.yukle()
  } catch (error) {
    L.hata.value = hataMesaji(error)
  }
}
interface F { poz_no: string; ad: string; birim: string; grup: number; tip: string }
const Fm = useKayitFormu<Poz, F>(
  insaatApi.pozlar,
  () => ({ poz_no: '', ad: '', birim: '', grup: gruplar.value[0]?.id || 0, tip: 'yapim' }),
  (k) => ({ poz_no: k.poz_no, ad: k.ad, birim: k.birim, grup: k.grup, tip: k.tip }),
  (f) => ({ poz_no: f.poz_no.trim(), ad: f.ad.trim(), birim: f.birim.trim(), grup: f.grup, tip: f.tip }),
  (f) => (!f.poz_no.trim() || !f.ad.trim() || !f.birim.trim() || !f.grup ? 'Poz no, ad, birim ve grup zorunludur.' : ''),
)
onMounted(async () => {
  if (globalGorunum.value) return
  try { gruplar.value = await tumunuGetir(insaatApi.pozGruplari.liste) }
  catch (b) { L.hata.value = hataMesaji(b) }
  await L.yukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Pozlar</h1>
      </div>
      <button v-if="pozYazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Poz</button>
    </div>
    <div v-if="globalGorunum" class="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <strong>Global firma görünümü açık.</strong>
      Aynı poz kütüphanesi birden fazla firmada bulunabildiği için kayıtlar burada tekrarlı görünebilir.
      Doğru firmayı üst menüden seçerek yalnızca o firmanın kayıtlarını görüntüleyin ve düzenleyin.
    </div>
    <template v-if="!globalGorunum">
      <div class="mb-4"><ExcelAktarim :rows="L.kayitlar.value as unknown as Record<string, unknown>[]" :columns="excelSutunlari" filename="pozlar" @imported="excelAl" /></div>
      <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Poz no veya ad ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.tip" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm tipler</option>
        <option v-for="(e, k) in POZ_TIPLERI" :key="k" :value="k">{{ e }}</option>
      </select>
      <select v-model="L.filtreler.value.grup" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm gruplar</option>
        <option v-for="g in gruplar" :key="g.id" :value="g.id">{{ g.kod }} — {{ g.ad }}</option>
      </select>
      <select v-model="L.filtreler.value.is_active" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm durumlar</option>
        <option :value="true">Aktif</option>
        <option :value="false">Pasif</option>
      </select>
      </div>
    </template>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <p v-if="globalGorunum" class="rounded-xl border border-surface-200 bg-surface-50 px-4 py-6 text-center text-sm text-surface-600">
      Pozları görüntülemek için üst menüden işlem yapılacak firmayı seçin.
    </p>
    <VeriTablosu v-else :basliklar="['Poz No', 'Ad', 'Birim', 'Tip', 'Grup', 'Durum', pozYazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="p in L.kayitlar.value" :key="p.id" class="transition-colors hover:bg-surface-100/60">
        <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium text-surface-900">{{ p.poz_no }}</td>
        <td class="max-w-xs truncate px-4 py-3">{{ p.ad }}</td>
        <td class="px-4 py-3">{{ p.birim }}</td>
        <td class="px-4 py-3">{{ POZ_TIPLERI[p.tip] }}</td>
        <td class="px-4 py-3">{{ grupAdi(p) }}</td>
        <td class="px-4 py-3"><span class="durum-rozot" :class="p.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">{{ p.is_active ? 'Aktif' : 'Pasif' }}</span></td>
        <td v-if="pozYazabilir" class="whitespace-nowrap px-4 py-3">
          <div class="flex items-center gap-3">
            <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(p)">Düzenle</button>
            <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="projeFiyatlariAc(p)">Proje Fiyatları</button>
            <button type="button" class="text-sm font-medium text-danger-700 hover:underline" @click="pozuSil(p)">Sil</button>
          </div>
        </td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Pozu Düzenle' : 'Yeni Poz'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <label class="etiket">Poz No (KK.GGG.SSSS)<input v-model="Fm.form.value.poz_no" type="text" placeholder="örn. 15.110.1001" class="alan" /></label>
        <label class="etiket">Poz Adı<input v-model="Fm.form.value.ad" type="text" class="alan" /></label>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Birim<input v-model="Fm.form.value.birim" type="text" placeholder="m², m³, adet…" class="alan" /></label>
          <label class="etiket">Tip<select v-model="Fm.form.value.tip" class="alan"><option v-for="(e, k) in POZ_TIPLERI" :key="k" :value="k">{{ e }}</option></select></label>
        </div>
        <label class="etiket">Poz Grubu<select v-model.number="Fm.form.value.grup" class="alan"><option v-for="g in gruplar" :key="g.id" :value="g.id">{{ g.kod }} — {{ g.ad }}</option></select></label>
        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">{{ Fm.kaydediliyor.value ? 'Kaydediliyor…' : 'Kaydet' }}</button>
        </div>
      </form>
    </KayitModal>

    <!-- Proje Fiyatları Modal -->
    <KayitModal v-if="projeFiyatlarModalAcik" :baslik="'Proje Fiyatları: ' + (seciliPoz?.poz_no || '') + ' — ' + (seciliPoz?.ad || '')" :genis-icerik="true" @kapat="projeFiyatlarModalAcik = false">
      <div v-if="projeFiyatlarHata" class="hata-kutusu mb-4" role="alert">{{ projeFiyatlarHata }}</div>
      <p v-if="projeFiyatlarYukleniyor" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-surface-200 text-sm">
          <thead class="bg-surface-100">
            <tr>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">Proje</th>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">Yıl</th>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">Kaynak</th>
              <th class="px-3 py-2 text-right text-xs font-semibold uppercase text-surface-500">Birim Fiyat (₺)</th>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">Durum</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-surface-100">
            <tr v-for="f in projeFiyatlar" :key="f.id" class="hover:bg-surface-50">
              <td class="px-3 py-2 font-medium">{{ projeAdi(f) }}</td>
              <td class="px-3 py-2">{{ f.yil }}</td>
              <td class="px-3 py-2">{{ f.kaynak || '—' }}</td>
              <td class="px-3 py-2 text-right font-mono">{{ Number(f.birim_fiyat).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td>
              <td class="px-3 py-2">
                <span class="durum-rozot" :class="f.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">
                  {{ f.is_active ? 'Aktif' : 'Pasif' }}
                </span>
              </td>
            </tr>
            <tr v-if="projeFiyatlar.length === 0">
              <td colspan="5" class="px-3 py-8 text-center text-sm text-surface-400">Bu poz için proje özel fiyatı bulunmuyor.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </KayitModal>
  </div>
</template>
