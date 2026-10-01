<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6"><p class="text-sm font-medium text-primary-700">Muhasebe</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Genel Muhasebe Defteri</h1><p class="mt-1 text-sm text-surface-500">Muhasebe fişlerini ve mizan özetini tek çalışma alanından yönetin.</p></div>
    <div class="grid gap-4 sm:grid-cols-2"><button type="button" class="rounded-xl border border-surface-200 bg-surface-50 p-5 text-left transition hover:border-primary-300 hover:bg-primary-50" @click="router.push({ name: 'muhasebeFisleri' })"><span class="font-heading font-semibold text-surface-900">Muhasebe Fişleri</span><span class="mt-1 block text-sm text-surface-500">Fiş oluşturma ve çift taraflı kayıt ekranı</span></button><button type="button" class="rounded-xl border border-surface-200 bg-surface-50 p-5 text-left transition hover:border-primary-300 hover:bg-primary-50" @click="router.push({ name: 'mizan' })"><span class="font-heading font-semibold text-surface-900">Mizan Raporu</span><span class="mt-1 block text-sm text-surface-500">Hesap bazlı borç, alacak ve bakiye özeti</span></button></div>
  </div>
</template>
