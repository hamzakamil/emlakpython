<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import KayitModal from '@/components/KayitModal.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useAuthStore } from '@/stores/auth'
import type { Proje, TaseronSozlesi } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const router = useRouter()
const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const sozlesmeler = ref<TaseronSozlesi[]>([])
const projeler = ref<Proje[]>([])
const arama = ref('')
const durum = ref('tum')
const yukleniyor = ref(true)
const hata = ref('')
const modalAcik = ref(false)
const kaydediliyor = ref(false)
const formHata = ref('')
const form = ref({ proje: 0, taseron_firma: '', sosyal_unvan: '', sicil_no: '', tarih_baslangic: new Date().toISOString().slice(0, 10), tarih_bitis: '', tutar: '', durum: 'taslak', aciklama: '' })

const durumlar: Record<string, string> = { taslak: 'Taslak', onaylandi: 'Onaylandı', aktif: 'Aktif', tamamlandi: 'Tamamlandı', iptal: 'İptal' }
const durumRenkleri: Record<string, string> = { taslak: 'bg-amber-100 text-amber-800', onaylandi: 'bg-blue-100 text-blue-800', aktif: 'bg-emerald-100 text-emerald-800', tamamlandi: 'bg-surface-200 text-surface-700', iptal: 'bg-red-100 text-red-800' }
const filtreli = computed(() => sozlesmeler.value.filter((x) => {
  const metin = `${x.taseron_firma} ${x.sosyal_unvan} ${projeAdi(x.proje)}`.toLocaleLowerCase('tr-TR')
  return (!arama.value || metin.includes(arama.value.toLocaleLowerCase('tr-TR'))) && (durum.value === 'tum' || x.durum === durum.value)
}))
const toplamTutar = computed(() => filtreli.value.reduce((toplam, x) => toplam + Number(x.tutar || 0), 0))
function projeAdi(id: number): string { const p = projeler.value.find((x) => x.id === id); return p ? `${p.proje_kodu} / ${p.ad}` : `Proje #${id}` }
function para(value: string): string { return Number(value).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
function yeniAc(): void {
  form.value = { proje: projeler.value[0]?.id || 0, taseron_firma: '', sosyal_unvan: '', sicil_no: '', tarih_baslangic: new Date().toISOString().slice(0, 10), tarih_bitis: '', tutar: '', durum: 'taslak', aciklama: '' }
  formHata.value = ''
  modalAcik.value = true
}
async function yukle(): Promise<void> {
  yukleniyor.value = true
  try {
    const [s, p] = await Promise.all([tumunuGetir(insaatApi.taseronSozlesi.liste), tumunuGetir(insaatApi.projeler.liste)])
    sozlesmeler.value = s
    projeler.value = p
  } catch (e) { hata.value = hataMesaji(e) } finally { yukleniyor.value = false }
}
async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.proje || !form.value.taseron_firma.trim() || Number(form.value.tutar) <= 0) {
    formHata.value = 'Proje, taşeron firma ve sıfırdan büyük sözleşme tutarı zorunludur.'
    return
  }
  if (form.value.tarih_bitis && form.value.tarih_bitis < form.value.tarih_baslangic) {
    formHata.value = 'Bitiş tarihi başlangıçtan önce olamaz.'
    return
  }
  kaydediliyor.value = true
  try {
    await insaatApi.taseronSozlesi.olustur({ ...form.value, tarih_bitis: form.value.tarih_bitis || null, tutar: form.value.tutar, taseron_firma: form.value.taseron_firma.trim(), sosyal_unvan: form.value.sosyal_unvan.trim(), sicil_no: form.value.sicil_no.trim(), aciklama: form.value.aciklama.trim() })
    modalAcik.value = false
    await yukle()
  } catch (e) { formHata.value = hataMesaji(e) } finally { kaydediliyor.value = false }
}
async function iptalEt(x: TaseronSozlesi): Promise<void> {
  if (x.durum === 'iptal' || !confirm(`${x.taseron_firma} sözleşmesini iptal etmek istiyor musunuz?`)) return
  try { await insaatApi.taseronSozlesi.sil(x.id); await yukle() } catch (e) { hata.value = hataMesaji(e) }
}
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div><p class="text-sm font-medium text-primary-700">İnşaat / Sözleşmeler</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Taşeron Sözleşmeleri</h1><p class="mt-1 text-sm text-surface-500">Sözleşme tutarlarını ve hakediş öncesi durum akışını tek ekrandan yönetin.</p></div>
      <button v-if="yazabilir" class="birincil-dugme" type="button" @click="yeniAc">+ Yeni Sözleşme</button>
    </div>
    <div class="mb-6 grid gap-3 sm:grid-cols-3">
      <div class="rounded-2xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Toplam sözleşme</p><p class="mt-2 text-2xl font-bold text-surface-900">{{ filtreli.length }}</p></div>
      <div class="rounded-2xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Filtrelenen tutar</p><p class="mt-2 text-2xl font-bold text-primary-800">{{ para(String(toplamTutar)) }} ₺</p></div>
      <div class="rounded-2xl border border-amber-200 bg-amber-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-amber-700">Aksiyon bekleyen</p><p class="mt-2 text-2xl font-bold text-amber-900">{{ filtreli.filter((x) => x.durum === 'taslak').length }}</p></div>
    </div>
    <div class="mb-4 flex flex-wrap gap-2"><input v-model="arama" class="alan w-full max-w-sm" type="search" placeholder="Firma veya proje ara..." /><select v-model="durum" class="alan"><option value="tum">Tüm durumlar</option><option v-for="(etiket, kod) in durumlar" :key="kod" :value="kod">{{ etiket }}</option></select><button class="ikincil-dugme" type="button" @click="yukle">Yenile</button></div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <VeriTablosu :basliklar="['Proje','Taşeron Firma','Başlangıç / Bitiş','Sözleşme Tutarı','Durum','İşlem']" :bos-mu="!yukleniyor && filtreli.length === 0">
      <tr v-for="x in filtreli" :key="x.id" class="transition-colors hover:bg-primary-50/40"><td class="px-4 py-4 font-medium text-surface-900">{{ projeAdi(x.proje) }}</td><td class="px-4 py-4"><div>{{ x.taseron_firma }}</div><div class="text-xs text-surface-500">{{ x.sicil_no || x.sosyal_unvan || 'Firma bilgisi' }}</div></td><td class="px-4 py-4 text-sm text-surface-600">{{ x.tarih_baslangic }}<span v-if="x.tarih_bitis"> → {{ x.tarih_bitis }}</span></td><td class="px-4 py-4 font-semibold text-primary-800">{{ para(x.tutar) }} ₺</td><td class="px-4 py-4"><span class="rounded-full px-2.5 py-1 text-xs font-semibold" :class="durumRenkleri[x.durum]">{{ durumlar[x.durum] || x.durum }}</span></td><td class="whitespace-nowrap px-4 py-4"><button class="text-sm font-semibold text-primary-700 hover:underline" type="button" @click="router.push({ name: 'hakedisler' })">Hakedişler</button><button v-if="yazabilir && x.durum !== 'iptal'" class="ml-3 text-sm font-semibold text-red-700 hover:underline" type="button" @click="iptalEt(x)">İptal</button></td></tr>
    </VeriTablosu>
    <KayitModal v-if="modalAcik" baslik="Yeni Taşeron Sözleşmesi" @kapat="modalAcik = false">
      <form class="flex flex-col gap-4" @submit.prevent="kaydet"><label class="etiket">Proje *<select v-model.number="form.proje" class="alan"><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} / {{ x.ad }}</option></select></label><label class="etiket">Taşeron Firma *<input v-model="form.taseron_firma" class="alan" maxlength="255" placeholder="Örn. ABC Yapı Taahhüt Ltd." required /></label><div class="grid grid-cols-2 gap-4"><label class="etiket">Sosyal Ünvan<input v-model="form.sosyal_unvan" class="alan" maxlength="255" /></label><label class="etiket">Sicil No<input v-model="form.sicil_no" class="alan" maxlength="50" /></label></div><div class="grid grid-cols-3 gap-4"><label class="etiket">Başlangıç *<input v-model="form.tarih_baslangic" class="alan" type="date" required /></label><label class="etiket">Bitiş<input v-model="form.tarih_bitis" class="alan" type="date" /></label><label class="etiket">Tutar (₺) *<input v-model="form.tutar" class="alan" type="number" min="0.01" step="0.01" required /></label></div><label class="etiket">Durum<select v-model="form.durum" class="alan"><option v-for="(etiket, kod) in durumlar" :key="kod" :value="kod">{{ etiket }}</option></select></label><label class="etiket">Açıklama<textarea v-model="form.aciklama" class="alan" rows="3" placeholder="İş kapsamı, ödeme ve özel şartlar..." /></label><p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button type="submit" class="birincil-dugme" :disabled="kaydediliyor">{{ kaydediliyor ? 'Kaydediliyor...' : 'Sözleşmeyi Kaydet' }}</button></div></form>
    </KayitModal>
  </div>
</template>
