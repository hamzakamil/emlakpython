<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { gayrimenkulApi, tumunuGetir } from '@/services/gayrimenkulApi'
import { useAuthStore } from '@/stores/auth'
import type { Ada, KatKarsiligiSenaryo, Parsel } from '@/types/gayrimenkul'
import { IMAR_DURUMLARI } from '@/types/gayrimenkul'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const adalar = ref<Ada[]>([])
const parseller = ref<Parsel[]>([])
const sekme = ref<'ada' | 'parsel' | 'senaryo'>('ada')
const arama = ref('')
const modalAcik = ref(false)
const kayitTuru = ref<'ada' | 'parsel'>('ada')
const kaydediliyor = ref(false)
const hata = ref('')
const formHata = ref('')
const adaForm = ref({ ada_no: '', mahalle: '', ilce: '', il: '', is_active: true })
const parselForm = ref({ ada: 0, parsel_no: '', pafta: '', alan_m2: '', imar_durumu: 'belirsiz', kat_karsiligi_orani: '0', malik_sayisi: 1, is_active: true })
const senaryolar = ref<KatKarsiligiSenaryo[]>([])
const senaryoForm = ref({ parsel: 0, senaryo_adi: '', arsa_pay_orani: '0', kat_karsiligi_orani: '0', bagimsiz_bolum_m2: '', toplam_birim_sayisi: 1, is_active: true })
const filtreliAdalar = computed(() => adalar.value.filter((x) => `${x.ada_no} ${x.mahalle} ${x.ilce} ${x.il}`.toLocaleLowerCase('tr-TR').includes(arama.value.toLocaleLowerCase('tr-TR'))))
const filtreliParseller = computed(() => parseller.value.filter((x) => `${x.ada_no} ${x.parsel_no} ${x.pafta} ${x.imar_durumu}`.toLocaleLowerCase('tr-TR').includes(arama.value.toLocaleLowerCase('tr-TR'))))
const filtreliSenaryolar = computed(() => senaryolar.value.filter((x) => `${x.senaryo_adi} ${x.parsel_no}`.toLocaleLowerCase('tr-TR').includes(arama.value.toLocaleLowerCase('tr-TR'))))
function adaAdi(id: number): string { const ada = adalar.value.find((x) => x.id === id); return ada ? `Ada ${ada.ada_no}` : `Ada #${id}` }
function yeni(tur: 'ada' | 'parsel'): void { kayitTuru.value = tur; formHata.value = ''; if (tur === 'ada') adaForm.value = { ada_no: '', mahalle: '', ilce: '', il: '', is_active: true }; else parselForm.value = { ada: adalar.value[0]?.id || 0, parsel_no: '', pafta: '', alan_m2: '', imar_durumu: 'belirsiz', kat_karsiligi_orani: '0', malik_sayisi: 1, is_active: true }; modalAcik.value = true }
function yeniSenaryo(): void { kayitTuru.value = 'parsel'; formHata.value = ''; senaryoForm.value = { parsel: parseller.value[0]?.id || 0, senaryo_adi: '', arsa_pay_orani: '0', kat_karsiligi_orani: '0', bagimsiz_bolum_m2: '', toplam_birim_sayisi: 1, is_active: true }; modalAcik.value = true }
async function yukle(): Promise<void> { try { ;[adalar.value, parseller.value, senaryolar.value] = await Promise.all([tumunuGetir(gayrimenkulApi.adalar.liste), tumunuGetir(gayrimenkulApi.parseller.liste), tumunuGetir(gayrimenkulApi.senaryolar.liste)]) } catch (e) { hata.value = hataMesaji(e) } }
async function kaydet(): Promise<void> {
  formHata.value = ''
  try {
    if (sekme.value === 'senaryo') {
      if (!senaryoForm.value.parsel || !senaryoForm.value.senaryo_adi.trim() || Number(senaryoForm.value.bagimsiz_bolum_m2) <= 0 || senaryoForm.value.toplam_birim_sayisi <= 0) { formHata.value = 'Parsel, senaryo adı, pozitif alan ve birim sayısı zorunludur.'; return }
      if ([senaryoForm.value.arsa_pay_orani, senaryoForm.value.kat_karsiligi_orani].some((x) => Number(x) < 0 || Number(x) > 100)) { formHata.value = 'Oranlar 0-100 arasında olmalıdır.'; return }
      await gayrimenkulApi.senaryolar.olustur({ ...senaryoForm.value, senaryo_adi: senaryoForm.value.senaryo_adi.trim() })
    } else if (kayitTuru.value === 'ada') {
      if (!adaForm.value.ada_no.trim()) { formHata.value = 'Ada numarası zorunludur.'; return }
      await gayrimenkulApi.adalar.olustur({ ...adaForm.value, ada_no: adaForm.value.ada_no.trim() })
    } else {
      if (!parselForm.value.ada || !parselForm.value.parsel_no.trim() || Number(parselForm.value.alan_m2) <= 0) { formHata.value = 'Ada, parsel numarası ve pozitif alan zorunludur.'; return }
      if (Number(parselForm.value.kat_karsiligi_orani) < 0 || Number(parselForm.value.kat_karsiligi_orani) > 100) { formHata.value = 'Kat karşılığı oranı 0-100 arasında olmalıdır.'; return }
      await gayrimenkulApi.parseller.olustur({ ...parselForm.value, parsel_no: parselForm.value.parsel_no.trim() })
    }
    modalAcik.value = false
    await yukle()
  } catch (e) { formHata.value = hataMesaji(e) } finally { kaydediliyor.value = false }
}
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p class="text-sm font-medium text-primary-700">Gayrimenkul / Kentsel Dönüşüm</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Ada, Parsel ve İmar</h1><p class="mt-1 text-sm text-surface-500">Tapu alanlarını, imar durumunu ve malik özetini tek yerde yönetin.</p></div><div v-if="yazabilir" class="flex gap-2"><button class="ikincil-dugme" type="button" @click="yeni('ada')">+ Ada</button><button class="birincil-dugme" type="button" @click="yeni('parsel')">+ Parsel</button></div></div>
    <div class="mb-4 flex flex-wrap gap-2"><button type="button" class="rounded-lg px-4 py-2 text-sm font-semibold" :class="sekme === 'ada' ? 'bg-primary-800 text-white' : 'bg-surface-100 text-surface-600'" @click="sekme = 'ada'">Ada Kartları ({{ adalar.length }})</button><button type="button" class="rounded-lg px-4 py-2 text-sm font-semibold" :class="sekme === 'parsel' ? 'bg-primary-800 text-white' : 'bg-surface-100 text-surface-600'" @click="sekme = 'parsel'">Parseller ({{ parseller.length }})</button><button type="button" class="rounded-lg px-4 py-2 text-sm font-semibold" :class="sekme === 'senaryo' ? 'bg-primary-800 text-white' : 'bg-surface-100 text-surface-600'" @click="sekme = 'senaryo'">Kat Karşılığı Senaryoları ({{ senaryolar.length }})</button><button v-if="yazabilir && sekme === 'senaryo'" class="birincil-dugme" type="button" @click="yeniSenaryo">+ Senaryo</button><input v-model="arama" class="alan ml-auto w-full max-w-sm" type="search" placeholder="Ada, parsel, senaryo veya pafta ara..." /><button class="ikincil-dugme" type="button" @click="yukle">Yenile</button></div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <VeriTablosu v-if="sekme === 'ada'" :basliklar="['Ada','Konum','Parsel Sayısı','Durum']" :bos-mu="!filtreliAdalar.length"><tr v-for="x in filtreliAdalar" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-semibold">Ada {{ x.ada_no }}</td><td class="px-4 py-3">{{ [x.mahalle, x.ilce, x.il].filter(Boolean).join(' / ') || 'Konum belirtilmedi' }}</td><td class="px-4 py-3">{{ parseller.filter((p) => p.ada === x.id).length }}</td><td class="px-4 py-3">{{ x.is_active ? 'Aktif' : 'Pasif' }}</td></tr></VeriTablosu>
    <VeriTablosu v-else-if="sekme === 'parsel'" :basliklar="['Ada / Parsel','Pafta','Alan (m²)','İmar Durumu','Kat Karşılığı','Malik']" :bos-mu="!filtreliParseller.length"><tr v-for="x in filtreliParseller" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-semibold">{{ adaAdi(x.ada) }} / {{ x.parsel_no }}</td><td class="px-4 py-3">{{ x.pafta || '—' }}</td><td class="px-4 py-3">{{ x.alan_m2 || '—' }}</td><td class="px-4 py-3">{{ IMAR_DURUMLARI[x.imar_durumu] || x.imar_durumu }}</td><td class="px-4 py-3">%{{ x.kat_karsiligi_orani }}</td><td class="px-4 py-3">{{ x.malik_sayisi }}</td></tr></VeriTablosu>
    <VeriTablosu v-else :basliklar="['Senaryo','Parsel','Arsa Payı','Kat Karşılığı','Birim','Alan']" :bos-mu="!filtreliSenaryolar.length"><tr v-for="x in filtreliSenaryolar" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3 font-semibold">{{ x.senaryo_adi }}</td><td class="px-4 py-3">{{ x.parsel_no || adaAdi(x.parsel) }}</td><td class="px-4 py-3">%{{ x.arsa_pay_orani }}</td><td class="px-4 py-3">%{{ x.kat_karsiligi_orani }}</td><td class="px-4 py-3">{{ x.toplam_birim_sayisi }}</td><td class="px-4 py-3">{{ x.bagimsiz_bolum_m2 }} m²</td></tr></VeriTablosu>
    <KayitModal v-if="modalAcik" :baslik="sekme === 'senaryo' ? 'Yeni Kat Karşılığı Senaryosu' : kayitTuru === 'ada' ? 'Yeni Ada Kartı' : 'Yeni Parsel Kaydı'" @kapat="modalAcik = false"><form class="flex flex-col gap-4" @submit.prevent="kaydet"><template v-if="sekme === 'senaryo'"><label class="etiket">Parsel *<select v-model.number="senaryoForm.parsel" class="alan"><option v-for="x in parseller" :key="x.id" :value="x.id">{{ adaAdi(x.ada) }} / {{ x.parsel_no }}</option></select></label><label class="etiket">Senaryo Adı *<input v-model="senaryoForm.senaryo_adi" class="alan" required /></label><div class="grid grid-cols-2 gap-4"><label class="etiket">Arsa Payı (%)<input v-model="senaryoForm.arsa_pay_orani" class="alan" type="number" min="0" max="100" step="0.01" /></label><label class="etiket">Kat Karşılığı (%)<input v-model="senaryoForm.kat_karsiligi_orani" class="alan" type="number" min="0" max="100" step="0.01" /></label></div><div class="grid grid-cols-2 gap-4"><label class="etiket">Bölüm Alanı (m²) *<input v-model="senaryoForm.bagimsiz_bolum_m2" class="alan" type="number" min="0.01" step="0.01" required /></label><label class="etiket">Toplam Birim Sayısı *<input v-model.number="senaryoForm.toplam_birim_sayisi" class="alan" type="number" min="1" required /></label></div></template><template v-else><template v-if="kayitTuru === 'ada'"><label class="etiket">Ada No *<input v-model="adaForm.ada_no" class="alan" maxlength="50" required /></label><div class="grid grid-cols-3 gap-4"><label class="etiket">Mahalle<input v-model="adaForm.mahalle" class="alan" maxlength="150" /></label><label class="etiket">İlçe<input v-model="adaForm.ilce" class="alan" maxlength="150" /></label><label class="etiket">İl<input v-model="adaForm.il" class="alan" maxlength="150" /></label></div></template><template v-else><div class="grid grid-cols-2 gap-4"><label class="etiket">Ada *<select v-model.number="parselForm.ada" class="alan"><option v-for="x in adalar" :key="x.id" :value="x.id">Ada {{ x.ada_no }}</option></select></label><label class="etiket">Parsel No *<input v-model="parselForm.parsel_no" class="alan" required /></label></div></template></template><p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button class="birincil-dugme" type="submit">Kaydet</button></div></form></KayitModal>
  </div>
</template>
