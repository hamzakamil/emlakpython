<script setup lang="ts">
/**
 * FAZ 3C — Depo tanımları: liste + oluşturma/düzenleme.
 * Backend: /api/v1/purchase-depolar/.
 */
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { satinAlmaApi } from '@/services/satinAlmaApi'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { Depo } from '@/types/satinAlma'
import { satinAlmaYazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => satinAlmaYazabilirMi(auth.kullanici?.role))

const L = useKayitListesi<Depo>('/purchase-depolar/')

const modalAcik = ref(false)
const duzenlenen = ref<Depo | null>(null)
const kaydediliyor = ref(false)
const formHata = ref('')
const form = ref({ kod: '', ad: '', aciklama: '' })

function yeniAc(): void {
  duzenlenen.value = null
  form.value = { kod: '', ad: '', aciklama: '' }
  formHata.value = ''
  modalAcik.value = true
}

function duzenleAc(k: Depo): void {
  duzenlenen.value = k
  form.value = { kod: k.kod, ad: k.ad, aciklama: k.aciklama || '' }
  formHata.value = ''
  modalAcik.value = true
}

async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.kod.trim() || !form.value.ad.trim()) {
    formHata.value = 'Depo kodu ve adı zorunludur.'
    return
  }
  kaydediliyor.value = true
  try {
    const payload = { kod: form.value.kod.trim(), ad: form.value.ad.trim(), aciklama: form.value.aciklama.trim() }
    if (duzenlenen.value) {
      await satinAlmaApi.depolar.guncelle(duzenlenen.value.id, payload)
    } else {
      await satinAlmaApi.depolar.olustur(payload)
    }
    modalAcik.value = false
    await L.yukle()
  } catch (bilinmeyen) {
    formHata.value = hataMesaji(bilinmeyen)
  } finally {
    kaydediliyor.value = false
  }
}

onMounted(() => {
  void L.yukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">Satın Alma / Stok</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Depolar</h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="yeniAc()">+ Yeni Depo</button>
    </div>

    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>

    <VeriTablosu
      :basliklar="['Kod', 'Ad', yazabilir ? 'İşlem' : '']"
      :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0"
    >
      <template v-for="k in L.kayitlar.value" :key="k.id">
        <tr class="transition-colors hover:bg-surface-100/60">
          <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium">{{ k.kod }}</td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.ad }}</td>
          <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
            <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="duzenleAc(k)">Düzenle</button>
          </td>
        </tr>
      </template>
    </VeriTablosu>
    <Sayfalama
      :sayfa="L.sayfa.value"
      :toplam="L.toplam.value"
      :yukleniyor="L.yukleniyor.value"
      @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }"
    />

    <KayitModal v-if="modalAcik" :baslik="duzenlenen ? 'Depoyu Düzenle' : 'Yeni Depo'" @kapat="modalAcik = false">
      <form class="flex flex-col gap-4" @submit.prevent="kaydet">
        <label class="etiket">Depo Kodu<input v-model="form.kod" type="text" class="alan" /></label>
        <label class="etiket">Depo Adı<input v-model="form.ad" type="text" class="alan" /></label>
        <label class="etiket">Açıklama<textarea v-model="form.aciklama" rows="2" class="alan"></textarea></label>
        <p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button>
          <button type="submit" :disabled="kaydediliyor" class="birincil-dugme">
            {{ kaydediliyor ? 'Kaydediliyor…' : 'Kaydet' }}
          </button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>
