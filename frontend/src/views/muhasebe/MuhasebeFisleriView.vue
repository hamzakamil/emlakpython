<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { muhasebeApi } from '@/services/muhasebeApi'
import { tumunuGetir } from '@/services/insaatApi'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { HesapPlani, MizanSatiri, MuhasebeFisi, FisSatiri } from '@/types/muhasebe'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = yazabilirMi(auth.kullanici?.role)
const L = useKayitListesi<MuhasebeFisi>('/accounting/fisler/')
const hesaplar = ref<HesapPlani[]>([])
const mizan = ref<MizanSatiri[]>([])
const modalAcik = ref(false)
const kaydediliyor = ref(false)
const formHata = ref('')
const form = ref({ fis_no: '', fis_tarihi: new Date().toISOString().slice(0, 10), aciklama: '', satirlar: [] as FisSatiri[] })
const toplamBorc = computed(() => form.value.satirlar.reduce((toplam, satir) => toplam + Number(satir.borc || 0), 0))
const toplamAlacak = computed(() => form.value.satirlar.reduce((toplam, satir) => toplam + Number(satir.alacak || 0), 0))
const dengeli = computed(() => toplamBorc.value > 0 && toplamBorc.value === toplamAlacak.value)

function bosSatir(): FisSatiri { return { hesap: 0, borc: '0', alacak: '0', aciklama: '' } }
function yeniAc(): void { form.value = { fis_no: '', fis_tarihi: new Date().toISOString().slice(0, 10), aciklama: '', satirlar: [bosSatir(), bosSatir()] }; formHata.value = ''; modalAcik.value = true }
function satirEkle(): void { form.value.satirlar.push(bosSatir()) }
function satirSil(index: number): void { if (form.value.satirlar.length > 2) form.value.satirlar.splice(index, 1) }
async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.fis_no.trim() || !dengeli.value || form.value.satirlar.some((x) => !x.hesap || (Number(x.borc) > 0 && Number(x.alacak) > 0) || (Number(x.borc) === 0 && Number(x.alacak) === 0))) { formHata.value = 'Fiş no, hesaplar ve dengeli borç/alacak satırları zorunludur.'; return }
  kaydediliyor.value = true
  try { await muhasebeApi.fisler.olustur(form.value); modalAcik.value = false; await L.yukle(); await mizanGetir() }
  catch (bilinmeyen) { formHata.value = hataMesaji(bilinmeyen) }
  finally { kaydediliyor.value = false }
}
async function mizanGetir(): Promise<void> { try { mizan.value = await muhasebeApi.fisler.mizan() } catch (bilinmeyen) { L.hata.value = hataMesaji(bilinmeyen) } }
function para(deger: string): string { return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(Number(deger)) }
onMounted(async () => { try { hesaplar.value = await tumunuGetir(muhasebeApi.hesapPlani.liste) } catch (bilinmeyen) { L.hata.value = hataMesaji(bilinmeyen) }; await L.yukle(); await mizanGetir() })
</script>

<template>
  <div class="mx-auto max-w-6xl"><div class="mb-6 flex flex-wrap items-center justify-between gap-3"><div><p class="text-sm font-medium text-primary-700">Muhasebe</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Fişler ve Mizan</h1></div><button v-if="yazabilir" type="button" class="birincil-dugme" @click="yeniAc">+ Yeni Fiş</button></div>
    <div class="mb-8"><h2 class="mb-3 font-heading text-lg font-semibold text-surface-900">Mizan</h2><VeriTablosu :basliklar="['Hesap', 'Hesap Adı', 'Borç', 'Alacak', 'Bakiye']" :bos-mu="!mizan.length"><tr v-for="x in mizan" :key="x.hesap_kodu"><td class="px-4 py-3 font-mono text-xs">{{ x.hesap_kodu }}</td><td class="px-4 py-3">{{ x.hesap_adi }}</td><td class="px-4 py-3">{{ para(x.borc) }}</td><td class="px-4 py-3">{{ para(x.alacak) }}</td><td class="px-4 py-3 font-medium">{{ para(x.bakiye) }}</td></tr></VeriTablosu></div>
    <div class="mb-4 flex gap-2"><form class="flex flex-1 gap-2" @submit.prevent="L.aramaYap"><input v-model="L.arama.value" type="search" placeholder="Fiş no veya açıklama ile ara..." class="alan w-full max-w-sm" /><button type="submit" class="ikincil-dugme">Ara</button></form></div><p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p><VeriTablosu :basliklar="['Fiş No', 'Tarih', 'Açıklama', 'Durum', 'Toplam']" :bos-mu="!L.yukleniyor.value && !L.kayitlar.value.length"><tr v-for="x in L.kayitlar.value" :key="x.id" class="transition-colors hover:bg-surface-100/60"><td class="px-4 py-3 font-mono text-xs">{{ x.fis_no }}</td><td class="px-4 py-3">{{ x.fis_tarihi }}</td><td class="px-4 py-3">{{ x.aciklama || '—' }}</td><td class="px-4 py-3">{{ x.durum }}</td><td class="px-4 py-3">{{ para(x.satirlar.reduce((t, s) => t + Number(s.borc || 0), 0).toString()) }}</td></tr></VeriTablosu><Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="modalAcik" baslik="Yeni Muhasebe Fişi" @kapat="modalAcik = false"><form class="flex flex-col gap-4" @submit.prevent="kaydet"><div class="grid grid-cols-2 gap-4"><label class="etiket">Fiş No<input v-model="form.fis_no" type="text" class="alan" /></label><label class="etiket">Fiş Tarihi<input v-model="form.fis_tarihi" type="date" class="alan" /></label></div><label class="etiket">Açıklama<input v-model="form.aciklama" type="text" class="alan" /></label><div class="border-t border-surface-200 pt-3"><div v-for="(satir, index) in form.satirlar" :key="index" class="mb-2 grid grid-cols-[1fr_9rem_9rem_auto] items-end gap-2"><label class="etiket">Hesap<select v-model.number="satir.hesap" class="alan"><option :value="0">Seçiniz</option><option v-for="x in hesaplar" :key="x.id" :value="x.id">{{ x.kod }} / {{ x.ad }}</option></select></label><label class="etiket">Borç<input v-model="satir.borc" type="number" min="0" step="0.01" class="alan" /></label><label class="etiket">Alacak<input v-model="satir.alacak" type="number" min="0" step="0.01" class="alan" /></label><button type="button" class="px-2 py-2 text-error-700" :disabled="form.satirlar.length <= 2" @click="satirSil(index)">×</button></div><button type="button" class="ikincil-dugme" @click="satirEkle">+ Satır</button></div><p class="text-right text-sm text-surface-600">Borç: <b>{{ para(toplamBorc.toString()) }}</b> · Alacak: <b>{{ para(toplamAlacak.toString()) }}</b></p><p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button type="submit" :disabled="kaydediliyor || !dengeli" class="birincil-dugme">{{ kaydediliyor ? 'Kaydediliyor...' : 'Kaydet' }}</button></div></form></KayitModal>
  </div>
</template>
