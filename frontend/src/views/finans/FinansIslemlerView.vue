<script setup lang="ts">
import { onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { cariApi } from '@/services/cariApi'
import { finansApi } from '@/services/finansApi'
import { tumunuGetir } from '@/services/insaatApi'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import { FINANS_ISLEM_YONLERI, type FinansHesabi, type FinansalIslem } from '@/types/finans'
import type { Cari } from '@/types/cari'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = yazabilirMi(auth.kullanici?.role)
const L = useKayitListesi<FinansalIslem>('/finance/finansal-islemler/')
const hesaplar = ref<FinansHesabi[]>([])
const cariler = ref<Cari[]>([])
const modalAcik = ref(false)
const kaydediliyor = ref(false)
const formHata = ref('')
const form = ref({ hesap: 0, cari: null as number | null, yon: 'gelir', tutar: '', islem_tarihi: new Date().toISOString().slice(0, 10), aciklama: '' })

function yeniAc(): void {
  form.value = { hesap: hesaplar.value[0]?.id || 0, cari: null, yon: 'gelir', tutar: '', islem_tarihi: new Date().toISOString().slice(0, 10), aciklama: '' }
  formHata.value = ''
  modalAcik.value = true
}

async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.hesap || !form.value.tutar || Number(form.value.tutar) <= 0) {
    formHata.value = 'Hesap ve pozitif tutar zorunludur.'
    return
  }
  kaydediliyor.value = true
  try {
    await finansApi.islemler.olustur({ ...form.value, cari: form.value.cari || null, tutar: form.value.tutar })
    modalAcik.value = false
    await L.yukle()
  } catch (bilinmeyen) {
    formHata.value = hataMesaji(bilinmeyen)
  } finally {
    kaydediliyor.value = false
  }
}

async function iptalEt(islem: FinansalIslem): Promise<void> {
  if (!window.confirm('Bu finansal işlem iptal edilsin mi?')) return
  try { await finansApi.islemler.iptal(islem.id); await L.yukle() }
  catch (bilinmeyen) { L.hata.value = hataMesaji(bilinmeyen) }
}

function para(deger: string): string {
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(Number(deger))
}

onMounted(async () => {
  try {
    hesaplar.value = await tumunuGetir(finansApi.hesaplar.liste)
    cariler.value = await tumunuGetir(cariApi.cariler.liste)
  } catch (bilinmeyen) { L.hata.value = hataMesaji(bilinmeyen) }
  await L.yukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3"><div><p class="text-sm font-medium text-primary-700">Finans</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Finansal İşlemler</h1></div><button v-if="yazabilir" type="button" class="birincil-dugme" @click="yeniAc">+ Yeni İşlem</button></div>
    <div class="mb-4 flex items-center gap-2"><form class="flex flex-1 gap-2" @submit.prevent="L.aramaYap"><input v-model="L.arama.value" type="search" placeholder="Hesap veya açıklama ile ara..." class="alan w-full max-w-sm" /><button type="submit" class="ikincil-dugme">Ara</button></form><select v-model="L.filtreler.value.yon" class="alan" @change="L.sayfa.value = 1; L.yukle"><option :value="undefined">Tüm yönler</option><option v-for="(etiket, kod) in FINANS_ISLEM_YONLERI" :key="kod" :value="kod">{{ etiket }}</option></select></div>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <VeriTablosu :basliklar="['Tarih', 'Hesap', 'Yön', 'Tutar', 'Açıklama', 'Durum', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && !L.kayitlar.value.length"><tr v-for="x in L.kayitlar.value" :key="x.id" class="transition-colors hover:bg-surface-100/60"><td class="whitespace-nowrap px-4 py-3">{{ x.islem_tarihi }}</td><td class="px-4 py-3 font-mono text-xs">{{ x.hesap_kodu || x.hesap }}</td><td class="px-4 py-3">{{ FINANS_ISLEM_YONLERI[x.yon] }}</td><td class="px-4 py-3 font-medium">{{ para(x.tutar) }}</td><td class="max-w-xs truncate px-4 py-3">{{ x.aciklama || '—' }}</td><td class="px-4 py-3">{{ x.is_cancelled ? 'İptal' : 'Aktif' }}</td><td v-if="yazabilir" class="px-4 py-3"><button v-if="!x.is_cancelled" type="button" class="text-sm font-medium text-error-700 hover:underline" @click="iptalEt(x)">İptal</button></td></tr></VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="modalAcik" baslik="Yeni Finansal İşlem" @kapat="modalAcik = false"><form class="flex flex-col gap-4" @submit.prevent="kaydet"><div class="grid grid-cols-2 gap-4"><label class="etiket">Hesap<select v-model.number="form.hesap" class="alan"><option v-for="x in hesaplar" :key="x.id" :value="x.id">{{ x.kod }} / {{ x.ad }}</option></select></label><label class="etiket">Cari<select v-model="form.cari" class="alan"><option :value="null">Cari yok</option><option v-for="x in cariler" :key="x.id" :value="x.id">{{ x.ad }}</option></select></label></div><div class="grid grid-cols-3 gap-4"><label class="etiket">Yön<select v-model="form.yon" class="alan"><option v-for="(etiket, kod) in FINANS_ISLEM_YONLERI" :key="kod" :value="kod">{{ etiket }}</option></select></label><label class="etiket">Tutar<input v-model="form.tutar" type="number" min="0.01" step="0.01" class="alan" /></label><label class="etiket">Tarih<input v-model="form.islem_tarihi" type="date" class="alan" /></label></div><label class="etiket">Açıklama<input v-model="form.aciklama" type="text" class="alan" /></label><p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button type="submit" :disabled="kaydediliyor" class="birincil-dugme">{{ kaydediliyor ? 'Kaydediliyor...' : 'Kaydet' }}</button></div></form></KayitModal>
  </div>
</template>
