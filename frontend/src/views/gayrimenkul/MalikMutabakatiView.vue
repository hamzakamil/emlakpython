<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { gayrimenkulApi, tumunuGetir } from '@/services/gayrimenkulApi'
import { useAuthStore } from '@/stores/auth'
import type { KatKarsiligiSenaryo, MalikMutabakati, MalikOyDurumu } from '@/types/gayrimenkul'
import { MALIK_OY_DURUMLARI } from '@/types/gayrimenkul'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const kayitlar = ref<MalikMutabakati[]>([])
const senaryolar = ref<KatKarsiligiSenaryo[]>([])
const arama = ref('')
const filtre = ref<MalikOyDurumu | ''>('')
const modalAcik = ref(false)
const kaydediliyor = ref(false)
const hata = ref('')
const formHata = ref('')
const form = ref({ senaryo: 0, malik_adi: '', pay_orani: '', oy_durumu: 'bekliyor' as MalikOyDurumu, notlar: '' })

const filtreliKayitlar = computed(() => kayitlar.value.filter((x) => {
  const metin = `${x.malik_adi} ${x.senaryo_adi || ''}`.toLocaleLowerCase('tr-TR')
  return metin.includes(arama.value.toLocaleLowerCase('tr-TR')) && (!filtre.value || x.oy_durumu === filtre.value)
}))
const toplamPay = computed(() => kayitlar.value.reduce((toplam, x) => toplam + Number(x.pay_orani), 0))
const kabulSayisi = computed(() => kayitlar.value.filter((x) => x.oy_durumu === 'kabul').length)
const bekleyenSayisi = computed(() => kayitlar.value.filter((x) => x.oy_durumu === 'bekliyor').length)
const senaryoAdi = (id: number) => senaryolar.value.find((x) => x.id === id)?.senaryo_adi || `Senaryo #${id}`

function yeni(): void {
  formHata.value = ''
  form.value = { senaryo: senaryolar.value[0]?.id || 0, malik_adi: '', pay_orani: '', oy_durumu: 'bekliyor', notlar: '' }
  modalAcik.value = true
}
async function yukle(): Promise<void> {
  try {
    ;[kayitlar.value, senaryolar.value] = await Promise.all([
      tumunuGetir(gayrimenkulApi.malikMutabakatlari.liste),
      tumunuGetir(gayrimenkulApi.senaryolar.liste),
    ])
  } catch (e) { hata.value = hataMesaji(e) }
}
async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.senaryo || !form.value.malik_adi.trim() || Number(form.value.pay_orani) < 0 || Number(form.value.pay_orani) > 100) {
    formHata.value = 'Senaryo, malik adı ve 0-100 arası geçerli pay oranı zorunludur.'
    return
  }
  const digerPay = kayitlar.value.filter((x) => x.senaryo === form.value.senaryo).reduce((toplam, x) => toplam + Number(x.pay_orani), 0)
  if (digerPay + Number(form.value.pay_orani) > 100) {
    formHata.value = `Bu senaryoda kalan pay %${Math.max(0, 100 - digerPay).toFixed(2)}.`
    return
  }
  kaydediliyor.value = true
  try {
    await gayrimenkulApi.malikMutabakatlari.olustur({ ...form.value, malik_adi: form.value.malik_adi.trim() })
    modalAcik.value = false
    await yukle()
  } catch (e) { formHata.value = hataMesaji(e) } finally { kaydediliyor.value = false }
}
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div><p class="text-sm font-medium text-primary-700">Gayrimenkul / Kat Karşılığı</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Malik Mutabakatı</h1><p class="mt-1 text-sm text-surface-500">Malik paylarını ve karar durumlarını senaryo bazında takip edin.</p></div>
      <button v-if="yazabilir" class="birincil-dugme" type="button" @click="yeni">+ Malik Ekle</button>
    </div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <div class="mb-5 grid gap-3 sm:grid-cols-3"><div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Toplam Pay</p><p class="mt-1 text-2xl font-bold text-primary-800">%{{ toplamPay.toFixed(2) }}</p></div><div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Kabul</p><p class="mt-1 text-2xl font-bold text-emerald-700">{{ kabulSayisi }}</p></div><div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Bekleyen</p><p class="mt-1 text-2xl font-bold text-amber-700">{{ bekleyenSayisi }}</p></div></div>
    <div class="mb-4 flex flex-wrap gap-2"><input v-model="arama" class="alan w-full max-w-sm" type="search" placeholder="Malik veya senaryo ara..." /><select v-model="filtre" class="alan w-44"><option value="">Tüm durumlar</option><option v-for="(etiket, anahtar) in MALIK_OY_DURUMLARI" :key="anahtar" :value="anahtar">{{ etiket }}</option></select><button class="ikincil-dugme" type="button" @click="yukle">Yenile</button></div>
    <VeriTablosu :basliklar="['Malik','Senaryo','Pay','Oy Durumu','Notlar']" :bos-mu="!filtreliKayitlar.length" bos-mesaj="Henüz malik mutabakatı kaydı bulunmuyor."><tr v-for="x in filtreliKayitlar" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-semibold">{{ x.malik_adi }}</td><td class="px-4 py-3">{{ x.senaryo_adi || senaryoAdi(x.senaryo) }}</td><td class="px-4 py-3">%{{ x.pay_orani }}</td><td class="px-4 py-3">{{ MALIK_OY_DURUMLARI[x.oy_durumu] }}</td><td class="max-w-xs truncate px-4 py-3 text-surface-500">{{ x.notlar || '—' }}</td></tr></VeriTablosu>
    <KayitModal v-if="modalAcik" baslik="Yeni Malik Mutabakatı" @kapat="modalAcik = false"><form class="flex flex-col gap-4" @submit.prevent="kaydet"><label class="etiket">Senaryo *<select v-model.number="form.senaryo" class="alan"><option v-for="x in senaryolar" :key="x.id" :value="x.id">{{ x.senaryo_adi }}</option></select></label><label class="etiket">Malik Adı *<input v-model="form.malik_adi" class="alan" required maxlength="200" /></label><label class="etiket">Pay Oranı (%) *<input v-model="form.pay_orani" class="alan" type="number" min="0" max="100" step="0.01" required /></label><label class="etiket">Oy Durumu<select v-model="form.oy_durumu" class="alan"><option v-for="(etiket, anahtar) in MALIK_OY_DURUMLARI" :key="anahtar" :value="anahtar">{{ etiket }}</option></select></label><label class="etiket">Notlar<textarea v-model="form.notlar" class="alan" rows="3" maxlength="2000" /></label><p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button class="birincil-dugme" type="submit" :disabled="kaydediliyor">{{ kaydediliyor ? 'Kaydediliyor...' : 'Kaydet' }}</button></div></form></KayitModal>
  </div>
</template>
