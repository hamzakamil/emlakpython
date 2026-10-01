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
import { PROJE_DURUMLARI, type Proje, type YapiSinifi, type ProjePozFiyat, type Poz } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const L = useKayitListesi<Proje>('/construction/projeler/')
const excelSutunlari: ExcelSutun[] = [
  { key: 'proje_kodu', label: 'Kod', required: true }, { key: 'ad', label: 'Ad', required: true },
  { key: 'durum', label: 'Durum', templateValue: 'teklif' }, { key: 'baslangic', label: 'Başlangıç' },
  { key: 'bitis', label: 'Bitiş' },
]

// Poz Fiyatları Modal
const pozFiyatlarModalAcik = ref(false)
const seciliProje = ref<Proje | null>(null)
const pozFiyatlar = ref<ProjePozFiyat[]>([])
const pozFiyatlarYukleniyor = ref(false)
const pozFiyatlarHata = ref('')
const pozlar = ref<Poz[]>([])

async function pozFiyatlariAc(proje: Proje): Promise<void> {
  seciliProje.value = proje
  pozFiyatlarModalAcik.value = true
  pozFiyatlarHata.value = ''
  pozFiyatlarYukleniyor.value = true
  try {
    const [fiyatlar, pozlarListesi] = await Promise.all([
      tumunuGetir(insaatApi.projePozFiyatlari.liste, { proje: proje.id }),
      tumunuGetir(insaatApi.pozlar.liste),
    ])
    pozFiyatlar.value = fiyatlar
    pozlar.value = pozlarListesi
  } catch (error) {
    pozFiyatlarHata.value = hataMesaji(error)
  } finally {
    pozFiyatlarYukleniyor.value = false
  }
}

const pozAdi = (k: ProjePozFiyat): string => pozlar.value.find((p) => p.id === k.poz)?.ad || '—'
const pozNo = (k: ProjePozFiyat): string => pozlar.value.find((p) => p.id === k.poz)?.poz_no || '#' + k.poz
async function excelAl(rows: Record<string, unknown>[]): Promise<void> {
  try {
    for (const row of rows) await insaatApi.projeler.olustur(row)
    await L.yukle()
    L.hata.value = ''
  } catch (error) {
    L.hata.value = `Excel içe aktarma kısmi olarak tamamlandı: ${error instanceof Error ? error.message : 'geçersiz veri.'}`
    await L.yukle()
  }
}
const siniflar = ref<YapiSinifi[]>([])
const sinifSecimi = (k: Proje): string => k.yapisinif_kodu || '—'
interface F { proje_kodu: string; ad: string; durum: string; yapisinif_maliyet: number | null; baslangic: string; bitis: string }
const Fm = useKayitFormu<Proje, F>(
  insaatApi.projeler,
  () => ({ proje_kodu: '', ad: '', durum: 'teklif', yapisinif_maliyet: null, baslangic: '', bitis: '' }),
  (k) => ({ proje_kodu: k.proje_kodu, ad: k.ad, durum: k.durum, yapisinif_maliyet: k.yapisinif_maliyet, baslangic: k.baslangic || '', bitis: k.bitis || '' }),
  (f) => ({ proje_kodu: f.proje_kodu.trim(), ad: f.ad.trim(), durum: f.durum, yapisinif_maliyet: f.yapisinif_maliyet, baslangic: f.baslangic || null, bitis: f.bitis || null }),
  (f) => (!f.proje_kodu.trim() || !f.ad.trim() ? 'Proje kodu ve adı zorunludur.' : ''),
)
onMounted(async () => {
  try { siniflar.value = await tumunuGetir(insaatApi.yapiSinifi.liste) }
  catch (b) { L.hata.value = hataMesaji(b) }
  await L.yukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Projeler</h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Proje</button>
    </div>
    <div class="mb-4"><ExcelAktarim :rows="L.kayitlar.value as unknown as Record<string, unknown>[]" :columns="excelSutunlari" filename="projeler" @imported="excelAl" /></div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Proje kodu veya adı ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.durum" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm durumlar</option>
        <option v-for="(e, k) in PROJE_DURUMLARI" :key="k" :value="k">{{ e }}</option>
      </select>
    </div>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <VeriTablosu :basliklar="['Kod', 'Ad', 'Durum', 'Yapı Sınıfı', 'Başlangıç', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="p in L.kayitlar.value" :key="p.id" class="transition-colors hover:bg-surface-100/60">
        <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium">{{ p.proje_kodu }}</td>
        <td class="max-w-xs truncate px-4 py-3">{{ p.ad }}</td>
        <td class="px-4 py-3">{{ PROJE_DURUMLARI[p.durum] }}</td>
        <td class="px-4 py-3">{{ sinifSecimi(p) }}</td>
        <td class="whitespace-nowrap px-4 py-3">{{ p.baslangic || '—' }}</td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
          <div class="flex items-center gap-3">
            <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(p)">Düzenle</button>
            <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="pozFiyatlariAc(p)">Poz Fiyatları</button>
          </div>
        </td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Projeyi Düzenle' : 'Yeni Proje'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <label class="etiket">Proje Kodu<input v-model="Fm.form.value.proje_kodu" type="text" class="alan" /></label>
        <label class="etiket">Proje Adı<input v-model="Fm.form.value.ad" type="text" class="alan" /></label>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Durum<select v-model="Fm.form.value.durum" class="alan"><option v-for="(e, k) in PROJE_DURUMLARI" :key="k" :value="k">{{ e }}</option></select></label>
          <label class="etiket">Yapı Sınıfı<select v-model.number="Fm.form.value.yapisinif_maliyet" class="alan"><option :value="null">—</option><option v-for="s in siniflar" :key="s.id" :value="s.id">{{ s.sinif_kodu }} / {{ s.yil }}</option></select></label>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Başlangıç<input v-model="Fm.form.value.baslangic" type="date" class="alan" /></label>
          <label class="etiket">Bitiş<input v-model="Fm.form.value.bitis" type="date" class="alan" /></label>
        </div>
        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">{{ Fm.kaydediliyor.value ? 'Kaydediliyor…' : 'Kaydet' }}</button>
        </div>
      </form>
    </KayitModal>

    <!-- Poz Fiyatları Modal -->
    <KayitModal v-if="pozFiyatlarModalAcik" :baslik="'Poz Fiyatları: ' + (seciliProje?.proje_kodu || '') + ' — ' + (seciliProje?.ad || '')" :genis-icerik="true" @kapat="pozFiyatlarModalAcik = false">
      <div v-if="pozFiyatlarHata" class="hata-kutusu mb-4" role="alert">{{ pozFiyatlarHata }}</div>
      <p v-if="pozFiyatlarYukleniyor" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
      <div v-else class="overflow-x-auto">
        <table class="min-w-full divide-y divide-surface-200 text-sm">
          <thead class="bg-surface-100">
            <tr>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">Poz No</th>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">Poz Adı</th>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">Yıl</th>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">Kaynak</th>
              <th class="px-3 py-2 text-right text-xs font-semibold uppercase text-surface-500">Birim Fiyat (₺)</th>
              <th class="px-3 py-2 text-left text-xs font-semibold uppercase text-surface-500">Durum</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-surface-100">
            <tr v-for="f in pozFiyatlar" :key="f.id" class="hover:bg-surface-50">
              <td class="px-3 py-2 font-mono text-xs font-medium">{{ pozNo(f) }}</td>
              <td class="px-3 py-2">{{ pozAdi(f) }}</td>
              <td class="px-3 py-2">{{ f.yil }}</td>
              <td class="px-3 py-2">{{ f.kaynak || '—' }}</td>
              <td class="px-3 py-2 text-right font-mono">{{ Number(f.birim_fiyat).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td>
              <td class="px-3 py-2">
                <span class="durum-rozot" :class="f.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">
                  {{ f.is_active ? 'Aktif' : 'Pasif' }}
                </span>
              </td>
            </tr>
            <tr v-if="pozFiyatlar.length === 0">
              <td colspan="6" class="px-3 py-8 text-center text-sm text-surface-400">Bu proje için poz özel fiyatı bulunmuyor.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </KayitModal>
  </div>
</template>
