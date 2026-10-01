<script setup lang="ts">
/**
 * Talep Detay — başlık + kalemler + teklif seçimi + onay işlemleri.
 * Backend: /api/v1/purchase-requests/:id/ (kalemler gömülü gelir).
 */
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { satinAlmaApi } from '@/services/satinAlmaApi'
import { useAuthStore } from '@/stores/auth'
import type { Malzeme, TedarikciTeklifi } from '@/types/insaat'
import { TALEP_DURUMLARI, type SatinAlmaTalebi } from '@/types/satinAlma'
import { satinAlmaYazabilirMi } from '@/utils/yetki'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const yazabilir = computed(() => satinAlmaYazabilirMi(auth.kullanici?.role))

const id = Number(route.params.id)
const yukleniyor = ref(true)
const hata = ref('')
const talep = ref<SatinAlmaTalebi | null>(null)
const malzemeler = ref<Malzeme[]>([])
const teklifSecimleri = ref<Record<number, number | null>>({})

const durumEtiketi = (d: string): string =>
  TALEP_DURUMLARI.find((x) => x.deger === d)?.etiket ?? d

async function yukle(): Promise<void> {
  yukleniyor.value = true
  hata.value = ''
  try {
    talep.value = await satinAlmaApi.talepler.tek(id)
    teklifSecimleri.value = {}
    for (const k of talep.value.kalemler) {
      teklifSecimleri.value[k.id] = k.secili_teklif
    }
  } catch (bilinmeyen) {
    hata.value = hataMesaji(bilinmeyen)
  } finally {
    yukleniyor.value = false
  }
}

async function aksiyon(
  islem: 'onayaGonder' | 'onayla' | 'reddet' | 'iptalEt',
  soru: string,
): Promise<void> {
  if (!talep.value || !window.confirm(`${talep.value.talep_no} — ${soru}`)) return
  hata.value = ''
  try {
    await satinAlmaApi.talepler[islem](talep.value.id)
    await yukle()
  } catch (bilinmeyen) {
    hata.value = hataMesaji(bilinmeyen)
  }
}

async function teklifSec(kalemId: number): Promise<void> {
  const secim = teklifSecimleri.value[kalemId]
  hata.value = ''
  try {
    await satinAlmaApi.talepKalemleri.guncelle(kalemId, { secili_teklif: secim })
    await yukle()
  } catch (bilinmeyen) {
    hata.value = hataMesaji(bilinmeyen)
  }
}

async function sipariseDonustur(): Promise<void> {
  if (!talep.value) return
  await router.push({ name: 'talepler', query: { donustur: talep.value.id } })
}

onMounted(async () => {
  try {
    malzemeler.value = await tumunuGetir(insaatApi.malzemeler.liste)
  } catch (bilinmeyen) {
    hata.value = hataMesaji(bilinmeyen)
  }
  await yukle()
})

async function kalemTeklifleri(proje: number, malzeme: number): Promise<TedarikciTeklifi[]> {
  return tumunuGetir(insaatApi.tedarikciTeklifleri.liste, { proje, malzeme })
}

const kalemTeklifSecenekleri = ref<Record<number, TedarikciTeklifi[]>>({})

async function teklifSecenekleriniYukle(): Promise<void> {
  if (!talep.value) return
  const sonuc: Record<number, TedarikciTeklifi[]> = {}
  for (const k of talep.value.kalemler) {
    sonuc[k.id] = await kalemTeklifleri(talep.value.proje, k.malzeme)
  }
  kalemTeklifSecenekleri.value = sonuc
}

onMounted(() => {
  void teklifSecenekleriniYukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <button type="button" class="mb-4 text-sm font-medium text-primary-700 hover:underline" @click="$router.push({ name: 'talepler' })">← Talepler</button>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <p v-if="yukleniyor" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>

    <template v-if="talep">
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-sm font-medium text-primary-700">Satın Alma / Talep</p>
          <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">{{ talep.talep_no }}</h1>
          <p class="text-sm text-surface-500">{{ talep.proje_kodu }} — {{ durumEtiketi(talep.durum) }}</p>
        </div>
        <div v-if="yazabilir" class="flex flex-wrap gap-2">
          <button v-if="talep.durum === 'taslak'" type="button" class="ikincil-dugme" @click="aksiyon('onayaGonder', 'onaya gönderilsin mi?')">Onaya Gönder</button>
          <button v-if="talep.durum === 'onaya_gonderildi'" type="button" class="birincil-dugme" @click="aksiyon('onayla', 'onaylansın mı?')">Onayla</button>
          <button v-if="talep.durum === 'onaya_gonderildi'" type="button" class="ikincil-dugme" @click="aksiyon('reddet', 'reddedilsin mi?')">Reddet</button>
          <button v-if="talep.durum === 'onaylandi'" type="button" class="birincil-dugme" @click="sipariseDonustur">Siparişe Dönüştür</button>
          <button v-if="talep.durum !== 'siparise_donustu' && talep.durum !== 'iptal'" type="button" class="ikincil-dugme" @click="aksiyon('iptalEt', 'iptal edilsin mi?')">İptal</button>
        </div>
      </div>

      <div class="mb-6 rounded-lg border border-surface-200 p-4">
        <p class="text-sm text-surface-500">Talep Sahibi: <span class="font-medium text-surface-900">{{ talep.talep_sahibi_adi ?? '—' }}</span></p>
        <p class="text-sm text-surface-500">Tarih: <span class="font-medium text-surface-900">{{ talep.tarih }}</span></p>
        <p v-if="talep.aciklama" class="mt-2 text-sm text-surface-700">{{ talep.aciklama }}</p>
      </div>

      <h2 class="mb-3 text-lg font-semibold text-surface-900">Kalemler ({{ talep.kalemler.length }})</h2>
      <div class="overflow-x-auto rounded-lg border border-surface-200">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-surface-100/60 text-left text-xs uppercase tracking-wider text-surface-500">
              <th class="px-4 py-2">Malzeme</th>
              <th class="px-4 py-2">Miktar</th>
              <th class="px-4 py-2">Tahmini Fiyat</th>
              <th class="px-4 py-2">Seçili Teklif</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="k in talep.kalemler" :key="k.id" class="border-t border-surface-200">
              <td class="px-4 py-2">{{ k.malzeme_kodu }} — {{ k.malzeme_adi }}</td>
              <td class="px-4 py-2">{{ k.miktar }} {{ k.birim }}</td>
              <td class="px-4 py-2">{{ k.tahmini_birim_fiyat ?? '—' }}</td>
              <td class="px-4 py-2">
                <div v-if="yazabilir && talep.durum === 'taslak'" class="flex items-center gap-2">
                  <select v-model.number="teklifSecimleri[k.id]" class="alan py-1 text-xs">
                    <option :value="null">— Seçiniz —</option>
                    <option v-for="t in kalemTeklifSecenekleri[k.id] ?? []" :key="t.id" :value="t.id">
                      {{ t.tedarikci_adi }} · {{ t.birim_fiyat }} ₺
                    </option>
                  </select>
                  <button type="button" class="text-xs font-medium text-primary-700 hover:underline" @click="teklifSec(k.id)">Kaydet</button>
                </div>
                <span v-else class="text-xs text-surface-500">{{ k.secili_teklif ? `Teklif #${k.secili_teklif}` : '—' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
