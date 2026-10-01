<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { gayrimenkulApi, tumProjeleriGetir } from '@/services/gayrimenkulApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import { GAYRIMENKUL_DURUMLARI, type Gayrimenkul } from '@/types/gayrimenkul'
import type { Proje } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const L = useKayitListesi<Gayrimenkul>('/real-estate/gayrimenkuller/')
const projeler = ref<Proje[]>([])

interface GayrimenkulFormu {
  ad: string
  proje: number | null
  blok: string
  kat: string
  daire_no: string
  brut_m2: string
  durum: string
  tapu_adi: string
}

const Fm = useKayitFormu<Gayrimenkul, GayrimenkulFormu>(
  gayrimenkulApi.gayrimenkuller,
  bosForm,
  kayitToForm,
  formToVeri,
  formDogrula,
)

function bosForm(): GayrimenkulFormu {
  return { ad: '', proje: null, blok: '', kat: '', daire_no: '', brut_m2: '', durum: 'available', tapu_adi: '' }
}

function kayitToForm(k: Gayrimenkul): GayrimenkulFormu {
  return { ad: k.ad, proje: k.proje, blok: k.blok, kat: k.kat, daire_no: k.daire_no, brut_m2: k.brut_m2 || '', durum: k.durum, tapu_adi: k.tapu_adi }
}

function formToVeri(f: GayrimenkulFormu): Record<string, unknown> {
  return { ad: f.ad.trim(), proje: f.proje, blok: f.blok.trim(), kat: f.kat.trim(), daire_no: f.daire_no.trim(), brut_m2: f.brut_m2 || null, durum: f.durum, tapu_adi: f.tapu_adi.trim() }
}

function formDogrula(f: GayrimenkulFormu): string {
  const bos = !f.blok.trim() && !f.kat.trim() && !f.daire_no.trim() && !f.ad.trim()
  return bos ? 'Ad veya blok/kat/daire bilgisinden biri zorunludur.' : ''
}

function m2bicim(v: string | null): string {
  if (!v) return '—'
  return Number(v).toLocaleString('tr-TR', { minimumFractionDigits: 2 })
}

function konum(k: Gayrimenkul): string {
  return [k.blok, k.kat, k.daire_no].filter(Boolean).join(' / ') || '—'
}

onMounted(async () => {
  try {
    projeler.value = await tumProjeleriGetir()
  } catch (b) {
    L.hata.value = hataMesaji(b)
  }
  await L.yukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">Gayrimenkul</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Gayrimenkuller</h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Gayrimenkul</button>
    </div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Ad, blok veya daire ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.durum" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm durumlar</option>
        <option v-for="(e, k) in GAYRIMENKUL_DURUMLARI" :key="k" :value="k">{{ e }}</option>
      </select>
    </div>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <VeriTablosu :basliklar="['Konum', 'Ad', 'Proje', 'Brüt m²', 'Durum', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="k in L.kayitlar.value" :key="k.id" class="transition-colors hover:bg-surface-100/60">
        <td class="px-4 py-3 font-medium">{{ konum(k) }}</td>
        <td class="max-w-xs truncate px-4 py-3">{{ k.ad || '—' }}</td>
        <td class="px-4 py-3">{{ k.proje_kodu || '—' }}</td>
        <td class="px-4 py-3 text-right font-mono">{{ m2bicim(k.brut_m2) }}</td>
        <td class="px-4 py-3">{{ GAYRIMENKUL_DURUMLARI[k.durum] }}</td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
          <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(k)">Düzenle</button>
        </td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Gayrimenkulü Düzenle' : 'Yeni Gayrimenkul'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <label class="etiket">Ad<input v-model="Fm.form.value.ad" type="text" class="alan" /></label>
        <label class="etiket">Proje
          <select v-model.number="Fm.form.value.proje" class="alan">
            <option :value="null">—</option>
            <option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option>
          </select>
        </label>
        <div class="grid grid-cols-3 gap-4">
          <label class="etiket">Blok<input v-model="Fm.form.value.blok" type="text" class="alan" /></label>
          <label class="etiket">Kat<input v-model="Fm.form.value.kat" type="text" class="alan" /></label>
          <label class="etiket">Daire No<input v-model="Fm.form.value.daire_no" type="text" class="alan" /></label>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Brüt m²<input v-model="Fm.form.value.brut_m2" type="text" inputmode="decimal" class="alan" /></label>
          <label class="etiket">Durum
            <select v-model="Fm.form.value.durum" class="alan">
              <option v-for="(e, k) in GAYRIMENKUL_DURUMLARI" :key="k" :value="k">{{ e }}</option>
            </select>
          </label>
        </div>
        <label class="etiket">Tapu Adı Bilgisi<input v-model="Fm.form.value.tapu_adi" type="text" class="alan" /></label>
        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">{{ Fm.kaydediliyor.value ? 'Kaydediliyor…' : 'Kaydet' }}</button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>
