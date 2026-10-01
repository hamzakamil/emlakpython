<script setup lang="ts">
/**
 * FAZ 3C — Stok Durumu: depo seçimi + bakiye tablosu + transfer/tüketim/iade modalları.
 * Bakiye backend'de Σ GİRİŞ − Σ ÇIKIŞ ile hesaplanır (değerleme yok).
 */
import { computed, onMounted, ref, watch } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { satinAlmaApi } from '@/services/satinAlmaApi'
import { useAuthStore } from '@/stores/auth'
import type { Mahal, Malzeme, Proje } from '@/types/insaat'
import type { Depo } from '@/types/satinAlma'
import { satinAlmaYazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => satinAlmaYazabilirMi(auth.kullanici?.role))

const depolar = ref<Depo[]>([])
const malzemeler = ref<Malzeme[]>([])
const projeler = ref<Proje[]>([])
const mahaller = ref<Mahal[]>([])
const seciliDepo = ref<number | null>(null)
const satirlar = ref<{ malzeme_id: number; bakiye: string }[]>([])
const hata = ref('')
const yukleniyor = ref(false)

const malzemeAdi = (id: number): string => {
  const m = malzemeler.value.find((x) => x.id === id)
  return m ? `${m.malzeme_kodu} — ${m.ad}` : `#${id}`
}

async function bakiyeleriYukle(): Promise<void> {
  if (!seciliDepo.value) {
    satirlar.value = []
    return
  }
  yukleniyor.value = true
  hata.value = ''
  try {
    const sonuc = await satinAlmaApi.stokHareketleri.bakiye(seciliDepo.value)
    satirlar.value = sonuc.kalemler ?? []
  } catch (bilinmeyen) {
    hata.value = hataMesaji(bilinmeyen)
  } finally {
    yukleniyor.value = false
  }
}

watch(seciliDepo, () => {
  void bakiyeleriYukle()
})

/* --- Ortak modal iskeleti --- */
type IslemTuru = 'transfer' | 'tuketim' | 'iade'
const modal = ref<null | { tur: IslemTuru }>(null)
const kaydediliyor = ref(false)
const formHata = ref('')
const form = ref({
  hedef_depo: null as number | null,
  malzeme: null as number | null,
  miktar: '',
  proje: null as number | null,
  mahal: null as number | null,
  mal_kabul_kalemi: '',
  aciklama: '',
})

function modalAc(tur: IslemTuru): void {
  modal.value = { tur }
  form.value = {
    hedef_depo: null, malzeme: null, miktar: '', proje: null,
    mahal: null, mal_kabul_kalemi: '', aciklama: '',
  }
  formHata.value = ''
}

async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!seciliDepo.value) {
    formHata.value = 'Önce depo seçin.'
    return
  }
  if (!form.value.malzeme || Number(form.value.miktar) <= 0) {
    formHata.value = 'Malzeme ve pozitif miktar zorunludur.'
    return
  }
  kaydediliyor.value = true
  try {
    const tur = modal.value?.tur
    if (tur === 'transfer') {
      if (!form.value.hedef_depo || form.value.hedef_depo === seciliDepo.value) {
        formHata.value = 'Farklı bir hedef depo seçin.'
        return
      }
      await satinAlmaApi.stokHareketleri.transferOlustur({
        kaynak_depo: seciliDepo.value,
        hedef_depo: form.value.hedef_depo,
        malzeme: form.value.malzeme,
        miktar: form.value.miktar,
        aciklama: form.value.aciklama.trim(),
      })
    } else if (tur === 'tuketim') {
      if (!form.value.proje || !form.value.mahal) {
        formHata.value = 'Tüketimde proje ve mahal zorunludur.'
        return
      }
      await satinAlmaApi.stokHareketleri.tuketimOlustur({
        depo: seciliDepo.value,
        malzeme: form.value.malzeme,
        miktar: form.value.miktar,
        proje: form.value.proje,
        mahal: form.value.mahal,
        aciklama: form.value.aciklama.trim(),
      })
    } else {
      if (!form.value.mal_kabul_kalemi) {
        formHata.value = 'Kabul kalem kimliği zorunludur.'
        return
      }
      await satinAlmaApi.stokHareketleri.iadeOlustur({
        mal_kabul_kalemi: Number(form.value.mal_kabul_kalemi),
        miktar: form.value.miktar,
        aciklama: form.value.aciklama.trim(),
      })
    }
    modal.value = null
    await bakiyeleriYukle()
  } catch (bilinmeyen) {
    formHata.value = hataMesaji(bilinmeyen)
  } finally {
    kaydediliyor.value = false
  }
}

onMounted(async () => {
  try {
    const [d, m, p, h] = await Promise.all([
      tumunuGetir(satinAlmaApi.depolar.liste),
      tumunuGetir(insaatApi.malzemeler.liste),
      tumunuGetir(insaatApi.projeler.liste),
      tumunuGetir(insaatApi.mahaller.liste),
    ])
    depolar.value = d
    malzemeler.value = m
    projeler.value = p
    mahaller.value = h
    if (d.length > 0) seciliDepo.value = d[0].id
  } catch (bilinmeyen) {
    hata.value = hataMesaji(bilinmeyen)
  }
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">Satın Alma / Stok</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Stok Durumu</h1>
      </div>
      <div v-if="yazabilir" class="flex flex-wrap gap-2">
        <button type="button" class="ikincil-dugme" @click="modalAc('transfer')">Transfer</button>
        <button type="button" class="ikincil-dugme" @click="modalAc('tuketim')">Tüketim</button>
        <button type="button" class="ikincil-dugme" @click="modalAc('iade')">İade</button>
      </div>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <label class="etiket">
        Depo
        <select v-model.number="seciliDepo" class="alan">
          <option :value="null">— Seçiniz —</option>
          <option v-for="d in depolar" :key="d.id" :value="d.id">{{ d.kod }} — {{ d.ad }}</option>
        </select>
      </label>
    </div>

    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <p v-if="yukleniyor" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>

    <div class="overflow-x-auto rounded-lg border border-surface-200">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-100/60 text-left text-xs uppercase tracking-wider text-surface-500">
            <th class="px-4 py-2">Malzeme</th>
            <th class="px-4 py-2">Bakiye</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in satirlar" :key="s.malzeme_id" class="border-t border-surface-200">
            <td class="px-4 py-2">{{ malzemeAdi(s.malzeme_id) }}</td>
            <td class="px-4 py-2 font-medium">{{ s.bakiye }}</td>
          </tr>
          <tr v-if="satirlar.length === 0 && !yukleniyor">
            <td colspan="2" class="px-4 py-3 text-sm text-surface-400">Kayıt yok.</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="mt-2 text-xs text-surface-500">Bakiye = Σ GİRİŞ − Σ ÇIKIŞ (aktif hareketler). Negatif stok oluşamaz.</p>

    <KayitModal v-if="modal" :baslik="modal.tur === 'transfer' ? 'Depo Transferi' : modal.tur === 'tuketim' ? 'Tüketim Çıkışı' : 'Tedarikçiye İade'" @kapat="modal = null">
      <form class="flex flex-col gap-4" @submit.prevent="kaydet">
        <label v-if="modal.tur === 'transfer'" class="etiket">
          Hedef Depo
          <select v-model.number="form.hedef_depo" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="d in depolar.filter((x) => x.id !== seciliDepo)" :key="d.id" :value="d.id">{{ d.kod }} — {{ d.ad }}</option>
          </select>
        </label>
        <label v-if="modal.tur !== 'iade'" class="etiket">
          Malzeme
          <select v-model.number="form.malzeme" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="m in malzemeler" :key="m.id" :value="m.id">{{ m.malzeme_kodu }} — {{ m.ad }}</option>
          </select>
        </label>
        <label v-if="modal.tur === 'tuketim'" class="etiket">
          Proje
          <select v-model.number="form.proje" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option>
          </select>
        </label>
        <label v-if="modal.tur === 'tuketim'" class="etiket">
          Mahal
          <select v-model.number="form.mahal" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="h in mahaller" :key="h.id" :value="h.id">{{ h.mahal_no }} — {{ h.mahal_adi }}</option>
          </select>
        </label>
        <label v-if="modal.tur === 'iade'" class="etiket">
          Kabul Kalem ID
          <input v-model="form.mal_kabul_kalemi" type="text" inputmode="numeric" class="alan" />
        </label>
        <label v-if="modal.tur !== 'iade'" class="etiket">Miktar<input v-model="form.miktar" type="text" inputmode="decimal" class="alan" /></label>
        <label v-if="modal.tur === 'iade'" class="etiket">İade Miktarı<input v-model="form.miktar" type="text" inputmode="decimal" class="alan" /></label>
        <label class="etiket">Açıklama<textarea v-model="form.aciklama" rows="2" class="alan"></textarea></label>
        <p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="modal = null">Vazgeç</button>
          <button type="submit" :disabled="kaydediliyor" class="birincil-dugme">
            {{ kaydediliyor ? 'Kaydediliyor…' : 'Kaydet' }}
          </button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>
