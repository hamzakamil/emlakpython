<script setup lang="ts">
/**
 * Sayfalama — DRF PageNumberPagination (PAGE_SIZE=25) ile uyumlu
 * basit önceki/sonraki gezgini.
 */
defineProps<{
  sayfa: number
  toplam: number
  sayfaBoyutu?: number
  yukleniyor?: boolean
}>()

const emit = defineEmits<{
  (e: 'sayfa-degistir', sayfa: number): void
}>()
</script>

<template>
  <div class="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-surface-500">
    <p>
      Toplam <span class="font-medium text-surface-700">{{ toplam }}</span> kayıt
      <span v-if="toplam > 0">
        — Sayfa {{ sayfa }} / {{ Math.max(1, Math.ceil(toplam / (sayfaBoyutu || 25))) }}
      </span>
    </p>
    <div class="flex items-center gap-2">
      <button
        type="button"
        :disabled="sayfa <= 1 || yukleniyor"
        class="rounded-lg border border-surface-200 px-3 py-1.5 text-sm text-surface-700 transition-all hover:bg-surface-100 disabled:cursor-not-allowed disabled:opacity-50"
        @click="emit('sayfa-degistir', sayfa - 1)"
      >
        ← Önceki
      </button>
      <button
        type="button"
        :disabled="sayfa >= Math.ceil(toplam / (sayfaBoyutu || 25)) || yukleniyor"
        class="rounded-lg border border-surface-200 px-3 py-1.5 text-sm text-surface-700 transition-all hover:bg-surface-100 disabled:cursor-not-allowed disabled:opacity-50"
        @click="emit('sayfa-degistir', sayfa + 1)"
      >
        Sonraki →
      </button>
    </div>
  </div>
</template>
