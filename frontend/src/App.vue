<script setup lang="ts">
// Kök bileşen — görünümler RouterView üzerinden açılır.
// Girişli sayfalar AppLayout (sidebar + topbar), konuk sayfalar (giriş) doğrudan açılır.
import GelistiriciVeriInspectoru from '@/components/GelistiriciVeriInspectoru.vue'
import { Toaster } from 'vue-sonner'
</script>

<template>
  <GelistiriciVeriInspectoru />
  <Toaster position="top-right" />
  <RouterView />
</template>
