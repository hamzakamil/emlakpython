<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { hataMesaji } from '@/services/apiClient'
import { faturaApi } from '@/services/faturaApi'
import type { Fatura } from '@/types/fatura'

type FaturaOzet = Fatura & {
  kalem_detaylari?: Array<Record<string, string>>
}

const route = useRoute()
const router = useRouter()
const fatura = ref<FaturaOzet | null>(null)
const hata = ref('')
const yukleniyor = ref(true)
const para = (value: string | number, currency = 'TRY') => new Intl.NumberFormat('tr-TR', { style: 'currency', currency }).format(Number(value))
const tarih = (value: string | null) => {
  if (!value) return '-'
  const [y, m, d] = value.slice(0, 10).split('-')
  return y && m && d ? `${d}.${m}.${y}` : value
}
const yazdir = () => window.print()

async function yukle(): Promise<void> {
  try {
    fatura.value = await faturaApi.hesapOzeti(Number(route.params.id)) as FaturaOzet
  } catch (error) {
    hata.value = hataMesaji(error)
  } finally {
    yukleniyor.value = false
  }
}

async function eFaturaGonder(): Promise<void> {
  if (!fatura.value) return
  try { fatura.value = await faturaApi.eFaturaGonder(fatura.value.id) as FaturaOzet } catch (error) { hata.value = hataMesaji(error) }
}

async function iadeOlustur(): Promise<void> {
  if (!fatura.value) return
  try {
    const iade = await faturaApi.iadeOlustur(fatura.value.id)
    router.push({ name: 'fatura-detay', params: { id: iade.id } })
  } catch (error) { hata.value = hataMesaji(error) }
}

onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl space-y-5">
    <div v-if="yukleniyor" class="rounded-2xl border border-surface-200 bg-white p-6">Yükleniyor...</div>
    <p v-else-if="hata" class="hata-kutusu" role="alert">{{ hata }}</p>
    <template v-else-if="fatura">
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div><p class="text-sm font-medium text-primary-700">Finans / Fatura Detayı</p><h1 class="font-heading text-2xl font-bold">{{ fatura.No }}</h1><p class="text-sm text-surface-500">{{ tarih(fatura.tarih) }} · {{ fatura.cari_ad || 'Cari seçilmedi' }}</p></div>
        <div class="flex flex-wrap gap-2"><button class="ikincil-dugme" type="button" @click="router.back()">Geri</button><button class="ikincil-dugme" type="button" @click="yazdir">Yazdır</button><button v-if="fatura.senaryo === 'e_fatura' && fatura.fatura_turu !== 'proforma'" class="ikincil-dugme" type="button" @click="eFaturaGonder">e-Fatura Gönder</button><button v-if="fatura.fatura_turu !== 'iade'" class="ikincil-dugme" type="button" @click="iadeOlustur">İade Oluştur</button></div>
      </div>
      <div class="grid gap-3 sm:grid-cols-3 lg:grid-cols-6"><div class="rounded-xl border bg-white p-3"><span class="text-xs text-surface-500">Tür</span><strong class="block">{{ fatura.fatura_turu }}</strong></div><div class="rounded-xl border bg-white p-3"><span class="text-xs text-surface-500">Durum</span><strong class="block">{{ fatura.durum }}</strong></div><div class="rounded-xl border bg-white p-3"><span class="text-xs text-surface-500">Senaryo</span><strong class="block">{{ fatura.senaryo }}</strong></div><div class="rounded-xl border bg-white p-3"><span class="text-xs text-surface-500">Para Birimi</span><strong class="block">{{ fatura.para_birimi }} / {{ fatura.kur }}</strong></div><div class="rounded-xl border bg-white p-3"><span class="text-xs text-surface-500">e-Fatura</span><strong class="block">{{ fatura.e_fatura_durum }}</strong></div><div class="rounded-xl border bg-white p-3"><span class="text-xs text-surface-500">Vade</span><strong class="block">{{ tarih(fatura.vade_tarihi) }}</strong></div></div>
      <div class="overflow-x-auto rounded-2xl border border-surface-200 bg-white"><table class="min-w-full text-sm"><thead class="bg-surface-50 text-left"><tr><th class="p-3">Poz</th><th class="p-3">Açıklama</th><th class="p-3">Miktar</th><th class="p-3">Birim</th><th class="p-3">Birim Fiyat</th><th class="p-3">İskonto</th><th class="p-3">KDV</th><th class="p-3">Tevkifat</th><th class="p-3">Stopaj</th><th class="p-3">Satır Tutarı</th></tr></thead><tbody><tr v-for="(kalem, index) in fatura.kalemler" :key="kalem.id || index" class="border-t"><td class="p-3">{{ kalem.poz_no || '—' }}</td><td class="p-3">{{ kalem.aciklama }}</td><td class="p-3">{{ kalem.miktar }}</td><td class="p-3">{{ kalem.birim }}</td><td class="p-3">{{ para(kalem.birim_fiyat, fatura.para_birimi) }}</td><td class="p-3">{{ kalem.iskonto_orani || '0' }}%</td><td class="p-3">{{ kalem.kdv_orani }}%</td><td class="p-3">{{ kalem.tevkifat_orani }}%</td><td class="p-3">{{ kalem.stopaj_orani }}%</td><td class="p-3 font-semibold">{{ para(kalem.satir_toplami || '0', fatura.para_birimi) }}</td></tr></tbody></table></div>
      <div class="ml-auto grid max-w-sm gap-2 rounded-2xl border border-primary-100 bg-primary-50 p-4 text-sm"><div class="flex justify-between"><span>Matrah</span><strong>{{ para(fatura.matrah || '0', fatura.para_birimi) }}</strong></div><div class="flex justify-between"><span>KDV</span><strong>{{ para(fatura.kdv || '0', fatura.para_birimi) }}</strong></div><div class="flex justify-between"><span>Tevkifat</span><strong>{{ para(fatura.tevkifat || '0', fatura.para_birimi) }}</strong></div><div class="flex justify-between"><span>Stopaj</span><strong>{{ para(fatura.stopaj || '0', fatura.para_birimi) }}</strong></div><div class="flex justify-between border-t pt-2"><span>Genel toplam</span><strong>{{ para(fatura.odenecek || fatura.tutar, fatura.para_birimi) }}</strong></div><div class="flex justify-between"><span>Ödenen</span><strong>{{ para(fatura.odenen_tutar || '0', fatura.para_birimi) }}</strong></div><div class="flex justify-between"><span>Kalan</span><strong>{{ para(String(Number(fatura.odenecek || fatura.tutar) - Number(fatura.odenen_tutar || 0)), fatura.para_birimi) }}</strong></div><div v-if="fatura.para_birimi !== 'TRY'" class="flex justify-between font-semibold"><span>TL karşılığı</span><strong>{{ para(fatura.tl_karsiligi || '0') }}</strong></div></div>
    </template>
  </div>
</template>
