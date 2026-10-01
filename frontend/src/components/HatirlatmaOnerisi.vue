<script setup lang="ts">
import { computed, ref } from 'vue'
import { notificationsApi } from '@/services/notificationsApi'
import type { HatirlatmaPayload } from '@/types/notifications'

const props = withDefaults(defineProps<{
  tarih: string | null
  baslik?: string
  payload?: Partial<HatirlatmaPayload>
  acik?: boolean
}>(), { baslik: 'Bu tarihe hatırlatma kurmak ister misiniz?', acik: true })
const emit = defineEmits<{ (e: 'kapat'): void; (e: 'kaydedildi'): void }>()
const gun = ref(3)
const kaydediliyor = ref(false)
const hedefTarih = computed(() => {
  if (!props.tarih) return ''
  const tarih = new Date(`${props.tarih}T00:00:00`)
  tarih.setDate(tarih.getDate() - gun.value)
  return tarih.toISOString().slice(0, 10)
})

async function kaydet(): Promise<void> {
  if (!props.tarih || !hedefTarih.value) return
  kaydediliyor.value = true
  try {
    await notificationsApi.olustur({
      baslik: props.payload?.baslik || props.baslik,
      aciklama: props.payload?.aciklama,
      hatirlatma_tarihi: hedefTarih.value,
      ilgili_app: props.payload?.ilgili_app,
      ilgili_model: props.payload?.ilgili_model,
      ilgili_kayit_id: props.payload?.ilgili_kayit_id,
      seviye: props.payload?.seviye || 'uyari',
      tekrarlama: props.payload?.tekrarlama || 'yok',
    })
    emit('kaydedildi')
    emit('kapat')
  } finally {
    kaydediliyor.value = false
  }
}
</script>

<template>
  <div v-if="acik && tarih" class="rounded-xl border border-primary-100 bg-primary-50 p-3 shadow-sm">
    <p class="text-sm font-semibold text-primary-900">{{ baslik }}</p>
    <div class="mt-2 flex items-center gap-2">
      <label class="text-xs text-primary-800">Kaç gün önce?</label>
      <input v-model.number="gun" class="alan w-20" type="number" min="0" />
      <button class="birincil-dugme" type="button" :disabled="kaydediliyor" @click="kaydet">Evet</button>
      <button class="ikincil-dugme" type="button" @click="emit('kapat')">Hayır</button>
    </div>
  </div>
</template>
