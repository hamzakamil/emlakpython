<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useAuthStore } from '@/stores/auth'
import type { LeaseAssistance, Proje } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const kayitlar = ref<LeaseAssistance[]>([])
const projeler = ref<Proje[]>([])
const arama = ref('')
const modalAcik = ref(false)
const duzenlenenId = ref<number | null>(null)
const hata = ref('')
const formHata = ref('')
const kaydediliyor = ref(false)
const form = ref({ proje: 0, kira_yardim_id: '', tahliye_sikligi: 'Başvuru bekliyor', aciklama: '', banka_iban: '', banka_adi: '', odeme_notu: '' })
const filtreli = computed(() => kayitlar.value.filter((x) => `${x.kira_yardim_id} ${x.tahliye_sikligi} ${x.proje_kodu || ''}`.toLocaleLowerCase('tr-TR').includes(arama.value.toLocaleLowerCase('tr-TR'))))
const projeAdi = (id: number) => projeler.value.find((x) => x.id === id)?.ad || `Proje #${id}`

function duzenle(x: LeaseAssistance): void {
  duzenlenenId.value = x.id
  form.value = {
    proje: x.proje,
    kira_yardim_id: x.kira_yardim_id,
    tahliye_sikligi: x.tahliye_sikligi,
    aciklama: x.aciklama || '',
    banka_iban: x.banka_iban || '',
    banka_adi: x.banka_adi || '',
    odeme_notu: x.odeme_notu || '',
  }
  modalAcik.value = true
}
async function yukle(): Promise<void> {
  try { ;[kayitlar.value, projeler.value] = await Promise.all([tumunuGetir(insaatApi.leaseAssistances.liste), tumunuGetir(insaatApi.projeler.liste)]) }
  catch (e) { hata.value = hataMesaji(e) }
}
async function kaydet(): Promise<void> {
  formHata.value = ''
  kaydediliyor.value = true
  try {
    if (duzenlenenId.value) {
      await insaatApi.leaseAssistances.guncelle(duzenlenenId.value, {
        banka_iban: form.value.banka_iban,
        banka_adi: form.value.banka_adi,
        odeme_notu: form.value.odeme_notu,
        aciklama: form.value.aciklama,
      })
    }
    modalAcik.value = false
    await yukle()
  }
  catch (e) { formHata.value = hataMesaji(e) } finally { kaydediliyor.value = false }
}
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p class="text-sm font-medium text-primary-700">İnşaat / Kentsel Dönüşüm</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Kira Yardımı ve Tahliye</h1><p class="mt-1 text-sm text-surface-500">Kayıtlar yalnızca Riskli Yapı Süreci terminal aşamaya geldiğinde otomatik oluşturulur.</p></div></div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <div class="mb-4 flex gap-2"><input v-model="arama" class="alan w-full max-w-md" type="search" placeholder="Başvuru no, proje veya durum ara..." /><button class="ikincil-dugme" type="button" @click="yukle">Yenile</button></div>
    <VeriTablosu :basliklar="['Kira Yardımı ID','Proje','Tahliye Süreci','Açıklama','Kayıt','İşlem']" :bos-mu="!filtreli.length" bos-mesaj="Henüz kira yardımı veya tahliye kaydı bulunmuyor."><tr v-for="x in filtreli" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-semibold">{{ x.kira_yardim_id }}</td><td class="px-4 py-3">{{ x.proje_kodu || projeAdi(x.proje) }}</td><td class="px-4 py-3">{{ x.tahliye_sikligi }}</td><td class="max-w-xl truncate px-4 py-3 text-surface-500">{{ x.aciklama || '—' }}</td><td class="px-4 py-3 text-surface-500">{{ new Date(x.created_at).toLocaleDateString('tr-TR') }}</td><td class="px-4 py-3"><button v-if="yazabilir" type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="duzenle(x)">Ödeme Bilgilerini Düzenle</button></td></tr></VeriTablosu>
    <KayitModal v-if="modalAcik" baslik="Kira Yardımı Ödeme Bilgileri" @kapat="modalAcik = false"><form class="flex flex-col gap-4" @submit.prevent="kaydet"><label class="etiket">Banka IBAN<input v-model="form.banka_iban" class="alan" maxlength="34" /></label><label class="etiket">Banka Adı<input v-model="form.banka_adi" class="alan" maxlength="150" /></label><label class="etiket">Ödeme Notu<textarea v-model="form.odeme_notu" class="alan" rows="4" /></label><p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button class="birincil-dugme" type="submit" :disabled="kaydediliyor">Kaydet</button></div></form></KayitModal>
  </div>
</template>
