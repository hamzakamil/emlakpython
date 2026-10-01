<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useAuthStore } from '@/stores/auth'
import type { ContractTemplate } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const TIPLER: Record<string, string> = {
  kat_karsiligi: 'Kat karşılığı',
  hasilat_paylasimli: 'Hasılat paylaşımlı',
  taseron: 'Taşeron',
  tedarik: 'Tedarik',
}
const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const kayitlar = ref<ContractTemplate[]>([])
const arama = ref('')
const tipFiltresi = ref('')
const modalAcik = ref(false)
const hata = ref('')
const formHata = ref('')
const kaydediliyor = ref(false)
const form = ref({ name: '', type: 'kat_karsiligi', content: '', is_active: true })
const filtreliKayitlar = computed(() => kayitlar.value.filter((x) => {
  const aramaEslesir = `${x.name} ${x.content}`.toLocaleLowerCase('tr-TR').includes(arama.value.toLocaleLowerCase('tr-TR'))
  return aramaEslesir && (!tipFiltresi.value || x.type === tipFiltresi.value)
}))

function yeni(): void {
  formHata.value = ''
  form.value = { name: '', type: 'kat_karsiligi', content: '', is_active: true }
  modalAcik.value = true
}
async function yukle(): Promise<void> {
  try { kayitlar.value = await tumunuGetir(insaatApi.contractTemplates.liste) }
  catch (e) { hata.value = hataMesaji(e) }
}
async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.name.trim() || !form.value.content.trim()) {
    formHata.value = 'Şablon adı ve içerik zorunludur.'
    return
  }
  kaydediliyor.value = true
  try {
    await insaatApi.contractTemplates.olustur({ ...form.value, name: form.value.name.trim(), content: form.value.content.trim() })
    modalAcik.value = false
    await yukle()
  } catch (e) { formHata.value = hataMesaji(e) }
  finally { kaydediliyor.value = false }
}
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div><p class="text-sm font-medium text-primary-700">İnşaat / Kentsel Dönüşüm</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Sözleşme Şablonları</h1><p class="mt-1 text-sm text-surface-500">Tekrarlanan sözleşme metinlerini tiplerine göre yönetin ve yeni belge hazırlığını hızlandırın.</p></div>
      <button v-if="yazabilir" class="birincil-dugme" type="button" @click="yeni">+ Şablon Ekle</button>
    </div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <div class="mb-4 flex flex-wrap gap-2"><input v-model="arama" class="alan w-full max-w-sm" type="search" placeholder="Şablon adı veya içerik ara..." /><select v-model="tipFiltresi" class="alan w-52"><option value="">Tüm şablon tipleri</option><option v-for="(etiket, anahtar) in TIPLER" :key="anahtar" :value="anahtar">{{ etiket }}</option></select><button class="ikincil-dugme" type="button" @click="yukle">Yenile</button></div>
    <VeriTablosu :basliklar="['Şablon','Tip','İçerik önizleme','Durum']" :bos-mu="!filtreliKayitlar.length" bos-mesaj="Henüz sözleşme şablonu oluşturulmamış."><tr v-for="x in filtreliKayitlar" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-semibold">{{ x.name }}</td><td class="px-4 py-3">{{ TIPLER[x.type] || x.type }}</td><td class="max-w-xl truncate px-4 py-3 text-surface-500">{{ x.content }}</td><td class="px-4 py-3">{{ x.is_active ? 'Aktif' : 'Pasif' }}</td></tr></VeriTablosu>
    <KayitModal v-if="modalAcik" baslik="Yeni Sözleşme Şablonu" @kapat="modalAcik = false"><form class="flex flex-col gap-4" @submit.prevent="kaydet"><label class="etiket">Şablon Adı *<input v-model="form.name" class="alan" maxlength="200" required /></label><label class="etiket">Şablon Tipi *<select v-model="form.type" class="alan"><option v-for="(etiket, anahtar) in TIPLER" :key="anahtar" :value="anahtar">{{ etiket }}</option></select></label><label class="etiket">Sözleşme İçeriği *<textarea v-model="form.content" class="alan min-h-48" rows="8" required placeholder="Taraflar, kapsam, bedel, süre ve özel hükümleri yazın..." /></label><p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button class="birincil-dugme" type="submit" :disabled="kaydediliyor">{{ kaydediliyor ? 'Kaydediliyor...' : 'Kaydet' }}</button></div></form></KayitModal>
  </div>
</template>
