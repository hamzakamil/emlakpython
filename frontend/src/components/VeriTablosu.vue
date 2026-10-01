<script setup lang="ts">
/**
 * Veri tablosu — liste ekranları için ortak tablo iskeleti.
 * Sütunlarüst bilgi (slot), satırlar ve boş durum metni dışarıdan verilir.
 */
defineProps<{
  basliklar: string[]
  bosMesaj?: string
  bosMu: boolean
}>()
</script>

<template>
  <div class="overflow-x-auto rounded-xl border border-surface-200 bg-surface-50 shadow-card">
    <table class="min-w-full divide-y divide-surface-200 text-sm">
      <thead class="bg-surface-100">
        <tr>
          <th
            v-for="baslik in basliklar"
            :key="baslik"
            scope="col"
            class="whitespace-nowrap px-4 py-3 text-left font-heading text-xs font-semibold uppercase tracking-wider text-surface-500"
          >
            {{ baslik }}
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-surface-100">
        <slot />
        <tr v-if="bosMu">
          <td :colspan="basliklar.length" class="px-4 py-8 text-center text-sm text-surface-400">
            {{ bosMesaj || 'Kayıt bulunamadı.' }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
