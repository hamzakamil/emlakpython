<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { muhasebeApi } from '@/services/muhasebeApi'
import type { MizanSatiri } from '@/types/muhasebe'

const satirlar = ref<MizanSatiri[]>([])
const arama = ref('')
const yukleniyor = ref(false)
const hata = ref('')

const filtrelenmis = computed(() => {
  const metin = arama.value.trim().toLocaleLowerCase('tr-TR')
  if (!metin) return satirlar.value
  return satirlar.value.filter((satir) => `${satir.hesap_kodu} ${satir.hesap_adi}`.toLocaleLowerCase('tr-TR').includes(metin))
})

const toplamBorc = computed(() => satirlar.value.reduce((toplam, satir) => toplam + Number(satir.borc), 0))
const toplamAlacak = computed(() => satirlar.value.reduce((toplam, satir) => toplam + Number(satir.alacak), 0))
const bakiye = computed(() => toplamBorc.value - toplamAlacak.value)

function para(deger: string | number): string {
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(Number(deger))
}

async function yukle(): Promise<void> {
  yukleniyor.value = true
  hata.value = ''
  try {
    satirlar.value = await muhasebeApi.fisler.mizan()
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
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div><p class="text-sm font-medium text-primary-700">Muhasebe</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Mizan Raporu</h1><p class="mt-1 text-sm text-surface-500">Hesap planındaki borç, alacak ve bakiyeleri izleyin.</p></div>
      <button type="button" class="ikincil-dugme" :disabled="yukleniyor" @click="yukle">Yenile</button>
    </div>
    <div class="mb-5 grid gap-3 sm:grid-cols-3"><div class="rounded-xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Toplam borç</p><p class="mt-2 text-xl font-bold text-red-700">{{ para(toplamBorc) }}</p></div><div class="rounded-xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Toplam alacak</p><p class="mt-2 text-xl font-bold text-blue-700">{{ para(toplamAlacak) }}</p></div><div class="rounded-xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Net bakiye</p><p class="mt-2 text-xl font-bold text-surface-900">{{ para(bakiye) }}</p></div></div>
    <div class="mb-4 flex gap-2"><input v-model="arama" type="search" class="alan w-full max-w-md" placeholder="Hesap kodu veya adı ile ara..." /></div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <VeriTablosu :basliklar="['Hesap Kodu', 'Hesap Adı', 'Borç', 'Alacak', 'Bakiye']" :bos-mu="!yukleniyor && !filtrelenmis.length"><tr v-for="satir in filtrelenmis" :key="satir.hesap_kodu" class="transition-colors hover:bg-surface-100/60"><td class="px-4 py-3 font-mono text-xs">{{ satir.hesap_kodu }}</td><td class="px-4 py-3 font-medium">{{ satir.hesap_adi }}</td><td class="px-4 py-3">{{ para(satir.borc) }}</td><td class="px-4 py-3">{{ para(satir.alacak) }}</td><td class="px-4 py-3 font-semibold">{{ para(satir.bakiye) }}</td></tr></VeriTablosu>
  </div>
</template>
