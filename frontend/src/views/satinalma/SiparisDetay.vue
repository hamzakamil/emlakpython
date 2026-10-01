<script setup lang="ts">
/**
 * Sipariş Detay — başlık + kalemler (fiyatlar sabit) + onay işlemleri.
 * Backend: /api/v1/purchase-orders/:id/ (kalemler gömülü gelir).
 */
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { hataMesaji } from '@/services/apiClient'
import { satinAlmaApi } from '@/services/satinAlmaApi'
import { useAuthStore } from '@/stores/auth'
import { SIPARIS_DURUMLARI, type SatinAlmaSiparisi } from '@/types/satinAlma'
import { satinAlmaYazabilirMi } from '@/utils/yetki'

const route = useRoute()
const auth = useAuthStore()
const yazabilir = computed(() => satinAlmaYazabilirMi(auth.kullanici?.role))

const id = Number(route.params.id)
const yukleniyor = ref(true)
const hata = ref('')
const siparis = ref<SatinAlmaSiparisi | null>(null)

const durumEtiketi = (d: string): string =>
  SIPARIS_DURUMLARI.find((x) => x.deger === d)?.etiket ?? d
const para = (v: string | null | undefined): string =>
  v === null || v === undefined ? '—' : Number(v).toLocaleString('tr-TR', { minimumFractionDigits: 2 })
const toplam = computed(() =>
  (siparis.value?.kalemler ?? []).reduce((t, k) => t + Number(k.toplam_tutar ?? 0), 0),
)

async function yukle(): Promise<void> {
  yukleniyor.value = true
  hata.value = ''
  try {
    siparis.value = await satinAlmaApi.siparisler.tek(id)
  } catch (bilinmeyen) {
    hata.value = hataMesaji(bilinmeyen)
  } finally {
    yukleniyor.value = false
  }
}

async function aksiyon(
  islem: 'onayaGonder' | 'onayla' | 'iptalEt',
  soru: string,
): Promise<void> {
  if (!siparis.value || !window.confirm(`${siparis.value.siparis_no} — ${soru}`)) return
  hata.value = ''
  try {
    await satinAlmaApi.siparisler[islem](siparis.value.id)
    await yukle()
  } catch (bilinmeyen) {
    hata.value = hataMesaji(bilinmeyen)
  }
}

onMounted(() => {
  void yukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <button type="button" class="mb-4 text-sm font-medium text-primary-700 hover:underline" @click="$router.push({ name: 'siparisler' })">← Siparişler</button>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <p v-if="yukleniyor" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>

    <template v-if="siparis">
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-sm font-medium text-primary-700">Satın Alma / Sipariş</p>
          <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">{{ siparis.siparis_no }}</h1>
          <p class="text-sm text-surface-500">{{ siparis.tedarikci_adi }} · {{ siparis.proje_kodu }} — {{ durumEtiketi(siparis.durum) }}</p>
        </div>
        <div v-if="yazabilir" class="flex flex-wrap gap-2">
          <button v-if="siparis.durum === 'taslak'" type="button" class="ikincil-dugme" @click="aksiyon('onayaGonder', 'onaya gönderilsin mi?')">Onaya Gönder</button>
          <button v-if="siparis.durum === 'onay_bekliyor'" type="button" class="birincil-dugme" @click="aksiyon('onayla', 'onaylansın mı?')">Onayla</button>
          <button v-if="siparis.durum !== 'tamamlandi' && siparis.durum !== 'iptal'" type="button" class="ikincil-dugme" @click="aksiyon('iptalEt', 'iptal edilsin mi?')">İptal</button>
        </div>
      </div>

      <div class="mb-6 rounded-lg border border-surface-200 p-4">
        <p class="text-sm text-surface-500">Tarih: <span class="font-medium text-surface-900">{{ siparis.tarih }}</span></p>
        <p class="text-sm text-surface-500">Teslim: <span class="font-medium text-surface-900">{{ siparis.teslim_tarihi ?? '—' }}</span></p>
        <p class="text-sm text-surface-500">Para Birimi: <span class="font-medium text-surface-900">{{ siparis.para_birimi }} (kur {{ siparis.kur }})</span></p>
        <p v-if="siparis.kaynak_talep" class="text-sm text-surface-500">Kaynak Talep: <span class="font-medium text-surface-900">#{{ siparis.kaynak_talep }}</span></p>
        <p v-if="siparis.aciklama" class="mt-2 text-sm text-surface-700">{{ siparis.aciklama }}</p>
      </div>

      <h2 class="mb-3 text-lg font-semibold text-surface-900">
        Kalemler ({{ siparis.kalemler.length }}) — Toplam {{ para(String(toplam)) }} ₺
      </h2>
      <div class="overflow-x-auto rounded-lg border border-surface-200">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-surface-100/60 text-left text-xs uppercase tracking-wider text-surface-500">
              <th class="px-4 py-2">Malzeme</th>
              <th class="px-4 py-2">Miktar</th>
              <th class="px-4 py-2">Birim Fiyat</th>
              <th class="px-4 py-2">Toplam</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="k in siparis.kalemler" :key="k.id" class="border-t border-surface-200">
              <td class="px-4 py-2">{{ k.malzeme_kodu }} — {{ k.malzeme_adi }}</td>
              <td class="px-4 py-2">{{ k.miktar }} {{ k.birim }}</td>
              <td class="px-4 py-2">{{ para(k.birim_fiyat) }}</td>
              <td class="px-4 py-2 font-medium">{{ para(k.toplam_tutar) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="mt-2 text-xs text-surface-500">Birim fiyatlar sipariş anında sabitlenmiştir; teklif değişse bile geriye dönük değişmez.</p>
    </template>
  </div>
</template>
