<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { constructionApi } from '@/services/constructionApi'
import { get, hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useAuthStore } from '@/stores/auth'
import { yazabilirMi } from '@/utils/yetki'
import type { Proje } from '@/types/insaat'
import type { Malzeme } from '@/types/insaat'

const auth = useAuthStore()
const yazabilir = yazabilirMi(auth.kullanici?.role)
const projeler = ref<Proje[]>([])
const malzemeler = ref<Malzeme[]>([])
const hareketler = ref<any[]>([])
const hata = ref('')
const arama = ref('')
const form = ref({ proje: 0, malzeme: 0, yon: 'giris', miktar: 1, qr_kodu: '', notlar: '' })

async function yukle(): Promise<void> {
  try {
    const veri = await constructionApi.malzemeHareketleri.liste({ search: arama.value || undefined })
    hareketler.value = veri.results
  } catch (e) { hata.value = hataMesaji(e) }
}
async function kaydet(): Promise<void> {
  hata.value = ''
  if (!form.value.proje || !form.value.miktar || (!form.value.malzeme && !form.value.qr_kodu.trim())) {
    hata.value = 'Proje, miktar ve malzeme veya QR kodu zorunludur.'
    return
  }
  try {
    await constructionApi.malzemeHareketleri.olustur({ ...form.value, qr_kodu: form.value.qr_kodu.trim(), gerceklesme_zamani: new Date().toISOString() })
    form.value = { ...form.value, miktar: 1, qr_kodu: '', notlar: '' }
    await yukle()
  } catch (e) { hata.value = hataMesaji(e) }
}
onMounted(async () => {
  try {
    projeler.value = await tumunuGetir(insaatApi.projeler.liste)
    const result = await get<{ results: Malzeme[] }>('/construction/malzemeler/')
    malzemeler.value = (result as any).results || []
  } catch (e) { hata.value = hataMesaji(e) }
  await yukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6"><p class="text-sm font-medium text-primary-700">İnşaat</p><h1 class="font-heading text-2xl font-bold text-surface-900">Saha Giriş / Çıkış ve Malzeme</h1><p class="mt-1 text-sm text-surface-600">QR etiketi okutun veya üzerindeki opak kodu elle girin.</p></div>
    <form v-if="yazabilir" class="mb-6 grid gap-3 rounded-xl border border-surface-200 bg-white p-4 md:grid-cols-6" @submit.prevent="kaydet">
      <select v-model.number="form.proje" class="alan"><option :value="0">Proje seçin</option><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} / {{ x.ad }}</option></select>
      <select v-model="form.yon" class="alan"><option value="giris">Malzeme girişi</option><option value="cikis">Malzeme çıkışı</option></select>
      <select v-model.number="form.malzeme" class="alan"><option :value="0">Malzeme kartı</option><option v-for="x in malzemeler" :key="x.id" :value="x.id">{{ x.malzeme_kodu }} / {{ x.ad }}</option></select>
      <input v-model="form.qr_kodu" class="alan" placeholder="QR / manuel kod" />
      <input v-model.number="form.miktar" class="alan" type="number" min="0.0001" step="0.0001" placeholder="Miktar" />
      <button class="birincil-dugme" type="submit">Hareketi Kaydet</button>
    </form>
    <form class="mb-4 flex gap-2" @submit.prevent="yukle"><input v-model="arama" class="alan w-full max-w-sm" placeholder="Proje, malzeme veya kod ara..." /><button class="ikincil-dugme">Ara</button></form>
    <p v-if="hata" class="hata-kutusu mb-4">{{ hata }}</p>
    <div class="overflow-x-auto rounded-xl border border-surface-200 bg-white"><table class="w-full text-left text-sm"><thead><tr class="border-b bg-surface-50"><th class="px-4 py-3">Zaman</th><th class="px-4 py-3">Proje</th><th class="px-4 py-3">Malzeme</th><th class="px-4 py-3">Hareket</th><th class="px-4 py-3">Miktar</th><th class="px-4 py-3">Kod</th></tr></thead><tbody><tr v-for="x in hareketler" :key="x.id" class="border-b"><td class="px-4 py-3">{{ new Date(x.gerceklesme_zamani).toLocaleString('tr-TR') }}</td><td class="px-4 py-3">{{ x.proje_kodu }}</td><td class="px-4 py-3">{{ x.malzeme_adi }}</td><td class="px-4 py-3">{{ x.yon === 'giris' ? 'Giriş' : 'Çıkış' }}</td><td class="px-4 py-3">{{ x.miktar }} {{ x.birim }}</td><td class="px-4 py-3 font-mono">{{ x.qr_kodu }}</td></tr></tbody></table></div>
  </div>
</template>
