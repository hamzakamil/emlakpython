<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useAuthStore } from '@/stores/auth'
import type { RiskStructure, Proje } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const kayitlar = ref<RiskStructure[]>([])
const projeler = ref<Proje[]>([])
const arama = ref('')
const modalAcik = ref(false)
const formHata = ref('')
const hata = ref('')
const form = ref({ proje: 0, risk_durumu: 'Tespit bekliyor', aciklama: '', son_durum_tarihi: '', is_active: true })
const filtreli = computed(() => kayitlar.value.filter((x) => `${x.risk_durumu} ${x.aciklama}`.toLocaleLowerCase('tr-TR').includes(arama.value.toLocaleLowerCase('tr-TR'))))
function yeni(): void { formHata.value = ''; form.value = { proje: projeler.value[0]?.id || 0, risk_durumu: 'Tespit bekliyor', aciklama: '', son_durum_tarihi: '', is_active: true }; modalAcik.value = true }
async function yukle(): Promise<void> { try { [kayitlar.value, projeler.value] = await Promise.all([tumunuGetir(insaatApi.riskStructures.liste), tumunuGetir(insaatApi.projeler.liste)]) } catch (e) { hata.value = hataMesaji(e) } }
async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.proje || !form.value.risk_durumu.trim()) { formHata.value = 'Proje ve risk durumu zorunludur.'; return }
  try { await insaatApi.riskStructures.olustur({ ...form.value, risk_durumu: form.value.risk_durumu.trim(), son_durum_tarihi: form.value.son_durum_tarihi || null }); modalAcik.value = false; await yukle() } catch (e) { formHata.value = hataMesaji(e) }
}
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p class="text-sm font-medium text-primary-700">İnşaat / Kentsel Dönüşüm</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Riskli Yapı Süreç Takibi</h1><p class="mt-1 text-sm text-surface-500">6306 kapsamındaki süreç adımlarını bilgi amaçlı operasyon notlarıyla takip edin.</p></div><button v-if="yazabilir" class="birincil-dugme" type="button" @click="yeni">+ Süreç Kaydı</button></div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <div class="mb-4 flex gap-2"><input v-model="arama" class="alan w-full max-w-md" type="search" placeholder="Durum veya açıklama ara..." /><button class="ikincil-dugme" type="button" @click="yukle">Yenile</button></div>
    <VeriTablosu :basliklar="['Risk Durumu','Son Durum Tarihi','Açıklama','Durum']" :bos-mu="!filtreli.length" bos-mesaj="Henüz riskli yapı süreç kaydı bulunmuyor."><tr v-for="x in filtreli" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-semibold">{{ x.risk_durumu }}</td><td class="px-4 py-3">{{ x.son_durum_tarihi || '—' }}</td><td class="max-w-xl truncate px-4 py-3 text-surface-500">{{ x.aciklama || '—' }}</td><td class="px-4 py-3">{{ x.is_active ? 'Aktif' : 'Pasif' }}</td></tr></VeriTablosu>
    <KayitModal v-if="modalAcik" baslik="Yeni Riskli Yapı Süreci" @kapat="modalAcik = false"><form class="flex flex-col gap-4" @submit.prevent="kaydet"><label class="etiket">Proje *<select v-model.number="form.proje" class="alan" required><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} — {{ x.ad }}</option></select></label><label class="etiket">Risk Durumu *<input v-model="form.risk_durumu" class="alan" maxlength="50" required placeholder="Örn. Tespit bekliyor" /></label><label class="etiket">Son Durum Tarihi<input v-model="form.son_durum_tarihi" class="alan" type="date" /></label><label class="etiket">Açıklama<textarea v-model="form.aciklama" class="alan" rows="5" maxlength="5000" /></label><p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button class="birincil-dugme" type="submit">Kaydet</button></div></form></KayitModal>
  </div>
</template>
