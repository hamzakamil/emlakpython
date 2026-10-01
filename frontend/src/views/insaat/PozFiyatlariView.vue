<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import { type Poz, type PozGrubu, type PozFiyat, type ProjePozFiyat, type Proje } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const globalGorunum = computed(() => auth.kullanici?.role === 'super_admin' && auth.seciliTenantId === null)
const pozFiyatYazabilir = computed(() => yazabilir.value && !globalGorunum.value)

const activeTab = ref<'genel' | 'proje'>('genel')

// Genel Poz Fiyatları
const L = useKayitListesi<PozFiyat>('/construction/poz-fiyatlari/')
const pozlar = ref<Poz[]>([])
const gruplar = ref<PozGrubu[]>([])

const pozAdi = (k: PozFiyat): string => k.poz_bilgisi || pozlar.value.find((p) => p.id === k.poz)?.ad || '#' + k.poz
const pozNo = (k: PozFiyat): string => pozlar.value.find((p) => p.id === k.poz)?.poz_no || '#' + k.poz

async function pozFiyatiSil(kayit: PozFiyat): Promise<void> {
  if (globalGorunum.value) {
    L.hata.value = 'Silme işlemi için üst menüden bir firma seçin.'
    return
  }
  const mesaj = '"' + pozNo(kayit) + ' — ' + pozAdi(kayit) + ' (' + kayit.yil + (kayit.donem ? ' ' + kayit.donem : '') + ')" fiyatını silmek istediğinize emin misiniz?'
  if (!window.confirm(mesaj)) return
  try {
    await insaatApi.pozFiyatlari.sil(kayit.id)
    await L.yukle()
  } catch (error) {
    L.hata.value = hataMesaji(error)
  }
}

interface F {
  poz: number
  yil: number
  donem: string
  kaynak: string
  birim_fiyat: string
  kaynak_url: string
  yayin_tarihi: string
  gecerlilik_tarihi: string
  is_active: boolean
}

const Fm = useKayitFormu<PozFiyat, F>(
  insaatApi.pozFiyatlari,
  () => ({
    poz: pozlar.value[0]?.id || 0,
    yil: new Date().getFullYear(),
    donem: '',
    kaynak: '',
    birim_fiyat: '',
    kaynak_url: '',
    yayin_tarihi: '',
    gecerlilik_tarihi: '',
    is_active: true,
  }),
  (k) => ({
    poz: k.poz,
    yil: k.yil,
    donem: k.donem,
    kaynak: k.kaynak,
    birim_fiyat: k.birim_fiyat,
    kaynak_url: k.kaynak_url,
    yayin_tarihi: k.yayin_tarihi || '',
    gecerlilik_tarihi: k.gecerlilik_tarihi || '',
    is_active: k.is_active,
  }),
  (f) => ({
    poz: f.poz,
    yil: f.yil,
    donem: f.donem.trim(),
    kaynak: f.kaynak.trim(),
    birim_fiyat: f.birim_fiyat.trim(),
    kaynak_url: f.kaynak_url.trim(),
    yayin_tarihi: f.yayin_tarihi || '',
    gecerlilik_tarihi: f.gecerlilik_tarihi || '',
    is_active: f.is_active,
  }),
  (f) => (!f.poz || !f.yil || !f.kaynak.trim() || !f.birim_fiyat.trim() ? 'Poz, yıl, kaynak ve birim fiyat zorunludur.' : ''),
)

// Proje Poz Fiyatları
const LProje = useKayitListesi<ProjePozFiyat>('/construction/proje-poz-fiyatlari/')
const projeler = ref<Proje[]>([])

const projeAdi = (k: ProjePozFiyat): string => k.proje_kodu || projeler.value.find((p) => p.id === k.proje)?.ad || '#' + k.proje
const projePozNo = (k: ProjePozFiyat): string => k.poz_no || pozlar.value.find((p) => p.id === k.poz)?.poz_no || '#' + k.poz
const projePozAdi = (k: ProjePozFiyat): string => pozlar.value.find((p) => p.id === k.poz)?.ad || '—'

async function projePozFiyatiSil(kayit: ProjePozFiyat): Promise<void> {
  if (globalGorunum.value) {
    LProje.hata.value = 'Silme işlemi için üst menüden bir firma seçin.'
    return
  }
  const mesaj = '"' + projeAdi(kayit) + ' / ' + projePozNo(kayit) + ' — ' + projePozAdi(kayit) + ' (' + kayit.yil + ')" fiyatını silmek istediğinize emin misiniz?'
  if (!window.confirm(mesaj)) return
  try {
    await insaatApi.projePozFiyatlari.sil(kayit.id)
    await LProje.yukle()
  } catch (error) {
    LProje.hata.value = hataMesaji(error)
  }
}

interface FProje {
  proje: number
  poz: number
  yil: number
  birim_fiyat: string
  kaynak: string
  kaynak_url: string
  is_active: boolean
}

const FmProje = useKayitFormu<ProjePozFiyat, FProje>(
  insaatApi.projePozFiyatlari,
  () => ({
    proje: projeler.value[0]?.id || 0,
    poz: pozlar.value[0]?.id || 0,
    yil: new Date().getFullYear(),
    birim_fiyat: '',
    kaynak: '',
    kaynak_url: '',
    is_active: true,
  }),
  (k) => ({
    proje: k.proje,
    poz: k.poz,
    yil: k.yil,
    birim_fiyat: k.birim_fiyat,
    kaynak: k.kaynak,
    kaynak_url: k.kaynak_url,
    is_active: k.is_active,
  }),
  (f) => ({
    proje: f.proje,
    poz: f.poz,
    yil: f.yil,
    birim_fiyat: f.birim_fiyat.trim(),
    kaynak: f.kaynak.trim(),
    kaynak_url: f.kaynak_url.trim(),
    is_active: f.is_active,
  }),
  (f) => (!f.proje || !f.poz || !f.yil || !f.birim_fiyat.trim() ? 'Proje, poz, yıl ve birim fiyat zorunludur.' : ''),
)

onMounted(async () => {
  if (globalGorunum.value) return
  try {
    pozlar.value = await tumunuGetir(insaatApi.pozlar.liste)
    gruplar.value = await tumunuGetir(insaatApi.pozGruplari.liste)
    projeler.value = await tumunuGetir(insaatApi.projeler.liste)
  } catch (b) {
    L.hata.value = hataMesaji(b)
  }
  await L.yukle()
  await LProje.yukle()
})

// Tab değiştirildiğinde ilgili listeyi yükle
function tabDegistir(yeniTab: 'genel' | 'proje'): void {
  activeTab.value = yeniTab
  if (yeniTab === 'genel') {
    L.yukle()
  } else {
    LProje.yukle()
  }
}
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Poz Fiyatları</h1>
      </div>
      <button v-if="pozFiyatYazabilir && activeTab === 'genel'" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Fiyat</button>
      <button v-if="pozFiyatYazabilir && activeTab === 'proje'" type="button" class="birincil-dugme" @click="FmProje.yeniAc()">+ Yeni Proje Fiyatı</button>
    </div>

    <div v-if="globalGorunum" class="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      Poz fiyatlarını görüntülemek için üst menüden işlem yapılacak firmayı seçin.
    </div>

    <!-- Tab Navigation -->
    <div class="mb-5 flex gap-1 border-b border-surface-200" role="tablist" aria-label="Fiyat türü">
      <button
        type="button"
        role="tab"
        :aria-selected="activeTab === 'genel'"
        class="border-b-2 px-3 py-2 text-sm font-medium transition-colors"
        :class="activeTab === 'genel' ? 'border-primary-600 text-primary-700' : 'border-transparent text-surface-500 hover:text-surface-800'"
        @click="tabDegistir('genel')"
      >
        Genel Fiyatlar
      </button>
      <button
        type="button"
        role="tab"
        :aria-selected="activeTab === 'proje'"
        class="border-b-2 px-3 py-2 text-sm font-medium transition-colors"
        :class="activeTab === 'proje' ? 'border-primary-600 text-primary-700' : 'border-transparent text-surface-500 hover:text-surface-800'"
        @click="tabDegistir('proje')"
      >
        Proje Fiyatları
      </button>
    </div>

    <p v-if="activeTab === 'genel' && L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="activeTab === 'proje' && LProje.hata.value" class="hata-kutusu mb-4" role="alert">{{ LProje.hata.value }}</p>
    <p v-if="activeTab === 'genel' && L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <p v-if="activeTab === 'proje' && LProje.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>

    <p v-if="globalGorunum" class="rounded-xl border border-surface-200 bg-surface-50 px-4 py-6 text-center text-sm text-surface-600">
      Poz fiyatlarını görüntülemek için üst menüden işlem yapılacak firmayı seçin.
    </p>

    <!-- Genel Fiyatlar Tab -->
    <VeriTablosu v-else-if="activeTab === 'genel'" :basliklar="['Poz No', 'Poz Adı', 'Yıl', 'Dönem', 'Kaynak', 'Birim Fiyat (₺)', 'Yayın Tarihi', 'Geçerlilik Tarihi', 'Durum', pozFiyatYazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="p in L.kayitlar.value" :key="p.id" class="transition-colors hover:bg-surface-100/60">
        <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium text-surface-900">{{ pozNo(p) }}</td>
        <td class="max-w-xs truncate px-4 py-3">{{ pozAdi(p) }}</td>
        <td class="whitespace-nowrap px-4 py-3">{{ p.yil }}</td>
        <td class="px-4 py-3">{{ p.donem || '—' }}</td>
        <td class="max-w-xs truncate px-4 py-3">{{ p.kaynak }}</td>
        <td class="whitespace-nowrap px-4 py-3 font-mono text-right">{{ Number(p.birim_fiyat).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td>
        <td class="whitespace-nowrap px-4 py-3">{{ p.yayin_tarihi || '—' }}</td>
        <td class="whitespace-nowrap px-4 py-3">{{ p.gecerlilik_tarihi || '—' }}</td>
        <td class="px-4 py-3">
          <span class="durum-rozot" :class="p.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">
            {{ p.is_active ? 'Aktif' : 'Pasif' }}
          </span>
        </td>
        <td v-if="pozFiyatYazabilir" class="whitespace-nowrap px-4 py-3">
          <div class="flex items-center gap-3">
            <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(p)">Düzenle</button>
            <button type="button" class="text-sm font-medium text-danger-700 hover:underline" @click="pozFiyatiSil(p)">Sil</button>
          </div>
        </td>
      </tr>
    </VeriTablosu>

    <!-- Proje Fiyatları Tab -->
    <VeriTablosu v-else-if="activeTab === 'proje'" :basliklar="['Proje', 'Poz No', 'Poz Adı', 'Yıl', 'Kaynak', 'Birim Fiyat (₺)', 'Durum', pozFiyatYazabilir ? 'İşlem' : '']" :bos-mu="!LProje.yukleniyor.value && LProje.kayitlar.value.length === 0">
      <tr v-for="p in LProje.kayitlar.value" :key="p.id" class="transition-colors hover:bg-surface-100/60">
        <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium text-surface-900">{{ projeAdi(p) }}</td>
        <td class="whitespace-nowrap px-4 py-3 font-mono text-xs">{{ projePozNo(p) }}</td>
        <td class="max-w-xs truncate px-4 py-3">{{ projePozAdi(p) }}</td>
        <td class="px-4 py-3">{{ p.yil }}</td>
        <td class="max-w-xs truncate px-4 py-3">{{ p.kaynak }}</td>
        <td class="whitespace-nowrap px-4 py-3 font-mono text-right">{{ Number(p.birim_fiyat).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td>
        <td class="px-4 py-3">
          <span class="durum-rozot" :class="p.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">
            {{ p.is_active ? 'Aktif' : 'Pasif' }}
          </span>
        </td>
        <td v-if="pozFiyatYazabilir" class="whitespace-nowrap px-4 py-3">
          <div class="flex items-center gap-3">
            <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="FmProje.duzenleAc(p)">Düzenle</button>
            <button type="button" class="text-sm font-medium text-danger-700 hover:underline" @click="projePozFiyatiSil(p)">Sil</button>
          </div>
        </td>
      </tr>
    </VeriTablosu>

    <Sayfalama v-if="activeTab === 'genel'" :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <Sayfalama v-else-if="activeTab === 'proje'" :sayfa="LProje.sayfa.value" :toplam="LProje.toplam.value" :yukleniyor="LProje.yukleniyor.value" @sayfa-degistir="(s) => { LProje.sayfa.value = s; LProje.yukle() }" />

    <!-- Genel Fiyat Modal -->
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Fiyatı Düzenle' : 'Yeni Poz Fiyatı'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <label class="etiket">
          Poz
          <select v-model.number="Fm.form.value.poz" class="alan" required>
            <option v-for="p in pozlar" :key="p.id" :value="p.id">{{ p.poz_no }} — {{ p.ad }}</option>
          </select>
        </label>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">
            Yıl
            <input v-model.number="Fm.form.value.yil" type="number" min="2000" max="2100" class="alan" required />
          </label>
          <label class="etiket">
            Dönem (Ay)
            <select v-model="Fm.form.value.donem" class="alan">
              <option value="">Yıl bazlı (dönemsiz)</option>
              <option>Ocak</option><option>Şubat</option><option>Mart</option><option>Nisan</option>
              <option>Mayıs</option><option>Haziran</option><option>Temmuz</option><option>Ağustos</option>
              <option>Eylül</option><option>Ekim</option><option>Kasım</option><option>Aralık</option>
            </select>
          </label>
        </div>
        <label class="etiket">
          Kaynak
          <input v-model="Fm.form.value.kaynak" type="text" placeholder="Örn. ÇŞİDB 2026 tebliği" class="alan" required />
        </label>
        <label class="etiket">
          Birim Fiyat (₺)
          <input v-model="Fm.form.value.birim_fiyat" type="number" step="0.01" min="0.01" placeholder="0.00" class="alan" required />
        </label>
        <label class="etiket">
          Kaynak URL
          <input v-model="Fm.form.value.kaynak_url" type="url" placeholder="https://..." class="alan" />
        </label>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">
            Yayın Tarihi
            <input v-model="Fm.form.value.yayin_tarihi" type="date" class="alan" />
          </label>
          <label class="etiket">
            Geçerlilik Tarihi
            <input v-model="Fm.form.value.gecerlilik_tarihi" type="date" class="alan" />
          </label>
        </div>
        <label class="etiket flex items-center gap-2">
          <input v-model="Fm.form.value.is_active" type="checkbox" class="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500" />
          <span>Aktif</span>
        </label>
        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">{{ Fm.kaydediliyor.value ? 'Kaydediliyor…' : 'Kaydet' }}</button>
        </div>
      </form>
    </KayitModal>

    <!-- Proje Fiyat Modal -->
    <KayitModal v-if="FmProje.modalAcik.value" :baslik="FmProje.duzenlenen.value ? 'Proje Fiyatını Düzenle' : 'Yeni Proje Fiyatı'" @kapat="FmProje.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="FmProje.kaydet(LProje.yukle)">
        <label class="etiket">
          Proje
          <select v-model.number="FmProje.form.value.proje" class="alan" required>
            <option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option>
          </select>
        </label>
        <label class="etiket">
          Poz
          <select v-model.number="FmProje.form.value.poz" class="alan" required>
            <option v-for="p in pozlar" :key="p.id" :value="p.id">{{ p.poz_no }} — {{ p.ad }}</option>
          </select>
        </label>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">
            Yıl
            <input v-model.number="FmProje.form.value.yil" type="number" min="2000" max="2100" class="alan" required />
          </label>
          <label class="etiket">
            Birim Fiyat (₺)
            <input v-model="FmProje.form.value.birim_fiyat" type="number" step="0.01" min="0.01" placeholder="0.00" class="alan" required />
          </label>
        </div>
        <label class="etiket">
          Kaynak
          <input v-model="FmProje.form.value.kaynak" type="text" placeholder="Örn. Proje özel teklif, tedarikçi fiyatı" class="alan" />
        </label>
        <label class="etiket">
          Kaynak URL
          <input v-model="FmProje.form.value.kaynak_url" type="url" placeholder="https://..." class="alan" />
        </label>
        <label class="etiket flex items-center gap-2">
          <input v-model="FmProje.form.value.is_active" type="checkbox" class="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500" />
          <span>Aktif</span>
        </label>
        <p v-if="FmProje.formHata.value" class="hata-kutusu" role="alert">{{ FmProje.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="FmProje.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="FmProje.kaydediliyor.value" class="birincil-dugme">{{ FmProje.kaydediliyor.value ? 'Kaydediliyor…' : 'Kaydet' }}</button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>