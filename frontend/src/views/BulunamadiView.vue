<script setup lang="ts">
// 404 — bulunamayan yollar için Türkçe sayfa.
</script>

<template>
  <div class="flex min-h-screen flex-col items-center justify-center gap-4 bg-surface-50 p-6">
    <p class="font-heading text-6xl font-bold text-primary-800">404</p>
    <h1 class="font-heading text-xl font-semibold text-surface-900">Sayfa bulunamadı</h1>
    <p class="text-sm text-surface-500">Aradığınız sayfa taşınmış veya hiç var olmamış olabilir.</p>
    <RouterLink
      to="/"
      class="mt-2 rounded-lg bg-primary-800 px-4 py-2.5 text-sm font-medium text-white transition-all hover:bg-primary-700"
    >
      Panele Dön
    </RouterLink>
  </div>
</template>
