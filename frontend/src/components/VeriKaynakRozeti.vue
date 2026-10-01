<script setup lang="ts">
import { ref } from 'vue'

withDefaults(defineProps<{
  aktif?: boolean
  tablo: string
  sutun: string
  alan?: string
  tip?: string
  api?: string
  iliski?: string
}>(), { aktif: false, alan: '', tip: '', api: '', iliski: '' })

const acik = ref(false)
</script>

<template>
  <span v-if="aktif" class="relative inline-flex max-w-full align-middle" @mouseenter="acik = true" @mouseleave="acik = false">
    <span class="dev-kaynak-noktasi" tabindex="0" @focus="acik = true" @blur="acik = false"><slot /></span>
    <span v-if="acik" class="dev-kaynak-popup" role="tooltip">
      <strong>Veri kaynağı</strong>
      <span><b>Tablo:</b> {{ tablo }}</span>
      <span><b>Sütun:</b> {{ sutun }}</span>
      <span v-if="alan"><b>Model alanı:</b> {{ alan }}</span>
      <span v-if="tip"><b>Tip:</b> {{ tip }}</span>
      <span v-if="api"><b>API:</b> {{ api }}</span>
      <span v-if="iliski"><b>İlişki:</b> {{ iliski }}</span>
    </span>
  </span>
  <slot v-else />
</template>
