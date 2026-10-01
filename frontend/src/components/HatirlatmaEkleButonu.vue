<script setup lang="ts">
import { ref } from 'vue'
import { BellPlus } from 'lucide-vue-next'
import KayitModal from './KayitModal.vue'
import { notificationsApi } from '@/services/notificationsApi'
import type { HatirlatmaPayload } from '@/types/notifications'

const acik = ref(false)
const kaydediliyor = ref(false)
const hata = ref('')
const form = ref<HatirlatmaPayload>({
  baslik: '',
  aciklama: '',
  hatirlatma_tarihi: new Date().toISOString().slice(0, 10),
  seviye: 'bilgi',
  tekrarlama: 'yok',
})

async function kaydet(): Promise<void> {
  if (!form.value.baslik.trim() || !form.value.hatirlatma_tarihi) {
    hata.value = 'Başlık ve tarih zorunludur.'
    return
  }
  kaydediliyor.value = true
  hata.value = ''
  try {
    await notificationsApi.olustur(form.value)
    acik.value = false
    window.dispatchEvent(new Event('hatirlatmalar-degisti'))
  } catch {
    hata.value = 'Hatırlatma kaydedilemedi.'
  } finally {
    kaydediliyor.value = false
  }
}
</script>

<template>
  <button type="button" class="notification-button" title="Hatırlatma ekle" aria-label="Hatırlatma ekle" @click="acik = true">
    <BellPlus class="h-4 w-4" />
  </button>
  <KayitModal v-if="acik" baslik="Yeni Hatırlatma" :kontrollu="true" :kirli="kaydediliyor" @kapat="acik = false">
    <form class="grid max-w-2xl gap-3 p-4" @submit.prevent="kaydet">
      <label class="grid gap-1 text-sm">Başlık<input v-model="form.baslik" class="alan" required /></label>
      <label class="grid gap-1 text-sm">Tarih<input v-model="form.hatirlatma_tarihi" class="alan" type="date" required /></label>
      <label class="grid gap-1 text-sm">Açıklama<textarea v-model="form.aciklama" class="alan min-h-20" /></label>
      <div class="grid grid-cols-2 gap-3">
        <label class="grid gap-1 text-sm">Seviye<select v-model="form.seviye" class="alan"><option value="bilgi">Bilgi</option><option value="uyari">Uyarı</option><option value="kritik">Kritik</option></select></label>
        <label class="grid gap-1 text-sm">Tekrarlama<select v-model="form.tekrarlama" class="alan"><option value="yok">Yok</option><option value="gunluk">Günlük</option><option value="haftalik">Haftalık</option><option value="aylik">Aylık</option><option value="yillik">Yıllık</option></select></label>
      </div>
      <p v-if="hata" class="hata-kutusu" role="alert">{{ hata }}</p>
      <button class="birincil-dugme" type="submit" :disabled="kaydediliyor">{{ kaydediliyor ? 'Kaydediliyor…' : 'Kaydet' }}</button>
    </form>
  </KayitModal>
</template>
