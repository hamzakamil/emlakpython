<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { raporApi, type CariRaporSatiri, type FinansRaporu } from '@/services/raporApi'

const finans = ref<FinansRaporu>({ gelir: '0', gider: '0', transfer: '0' })
const cariler = ref<CariRaporSatiri[]>([])
const yukleniyor = ref(false)
const hata = ref('')
const cariArama = ref('')

const filtrelenmisCariler = computed(() => {
  const arama = cariArama.value.trim().toLocaleLowerCase('tr-TR')
  return arama ? cariler.value.filter((satir) => satir.cari_ad.toLocaleLowerCase('tr-TR').includes(arama)) : cariler.value
})

function para(deger: string | number): string {
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(Number(deger))
}

async function yukle(): Promise<void> {
  yukleniyor.value = true
  hata.value = ''
  try {
    const [finansOzeti, cariOzeti] = await Promise.all([raporApi.finansOzeti(), raporApi.cariOzeti()])
    finans.value = finansOzeti
    cariler.value = cariOzeti
  } catch (bilinmeyen) {
    hata.value = hataMesaji(bilinmeyen)
  } finally {
    yukleniyor.value = false
  }
}

onMounted(() => void yukle())
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p class="text-sm font-medium text-primary-700">Finans</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Raporlar</h1><p class="mt-1 text-sm text-surface-500">Finans hareketleri ve cari bakiyeler için güncel özetler.</p></div><button type="button" class="ikincil-dugme" :disabled="yukleniyor" @click="yukle">Yenile</button></div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <div class="mb-8 grid gap-3 sm:grid-cols-3"><div class="rounded-xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Gelir</p><p class="mt-2 text-xl font-bold text-emerald-700">{{ para(finans.gelir) }}</p></div><div class="rounded-xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Gider</p><p class="mt-2 text-xl font-bold text-red-700">{{ para(finans.gider) }}</p></div><div class="rounded-xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Transfer</p><p class="mt-2 text-xl font-bold text-blue-700">{{ para(finans.transfer) }}</p></div></div>
    <div class="mb-4 flex items-center justify-between gap-3"><h2 class="font-heading text-lg font-semibold text-surface-900">Cari Bakiye Özeti</h2><input v-model="cariArama" type="search" class="alan w-full max-w-xs" placeholder="Cari ara..." /></div>
    <VeriTablosu :basliklar="['Cari', 'Borç', 'Alacak', 'Bakiye']" :bos-mu="!yukleniyor && !filtrelenmisCariler.length"><tr v-for="satir in filtrelenmisCariler" :key="satir.cari" class="transition-colors hover:bg-surface-100/60"><td class="px-4 py-3 font-medium">{{ satir.cari_ad }}</td><td class="px-4 py-3">{{ para(satir.borc) }}</td><td class="px-4 py-3">{{ para(satir.alacak) }}</td><td class="px-4 py-3 font-semibold">{{ para(satir.bakiye) }}</td></tr></VeriTablosu>
  </div>
</template>
