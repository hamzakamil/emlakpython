<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useAuthStore } from '@/stores/auth'
import { KALITE_SONUCLARI, type KaliteKontrol } from '@/types/saha'
import type { Poz, Proje } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const kayitlar = ref<KaliteKontrol[]>([])
const projeler = ref<Proje[]>([])
const pozlar = ref<Poz[]>([])
const arama = ref('')
const durumFiltresi = ref('tum')
const yukleniyor = ref(true)
const hata = ref('')
const modalAcik = ref(false)
const kaydediliyor = ref(false)
const formHata = ref('')
const form = ref({
  proje: 0, poz: null as number | null, tarih: new Date().toISOString().slice(0, 10),
  kontrol_tipi: 'malzeme', kriter: '', durum: 'beklemede',
  olculen_deger: '', beklenen_deger: '', tolerek_aralik: '',
  aciklama: '', duzeltici_faaliyet: '',
})

const kontrolTipleri: Record<string, string> = {
  malzeme: 'Malzeme Kontrolü', iscilik: 'İşçilik Kontrolü', boyut: 'Boyut Ölçümü',
  test: 'Test / Analiz', goruntuleme: 'Görsel İnceleme', diger: 'Diğer',
}
const filtreliKayitlar = computed(() => kayitlar.value.filter((x) => {
  const metin = `${x.proje_kodu || x.proje} ${x.kriter} ${x.aciklama} ${x.duzeltici_faaliyet}`.toLocaleLowerCase('tr-TR')
  return (!arama.value || metin.includes(arama.value.toLocaleLowerCase('tr-TR')))
    && (durumFiltresi.value === 'tum' || x.durum === durumFiltresi.value)
}))
const bekleyenSayisi = computed(() => kayitlar.value.filter((x) => x.durum === 'beklemede').length)
const gecenSayisi = computed(() => kayitlar.value.filter((x) => x.durum === 'gecti' || x.durum === 'onaylandi').length)
const kalanSayisi = computed(() => kayitlar.value.filter((x) => x.durum === 'kaldi' || x.durum === 'reddedildi').length)

function projeAdi(id: number): string {
  const proje = projeler.value.find((x) => x.id === id)
  return proje ? `${proje.proje_kodu} / ${proje.ad}` : `Proje #${id}`
}
function yeniAc(): void {
  form.value = {
    proje: projeler.value[0]?.id || 0, poz: null, tarih: new Date().toISOString().slice(0, 10),
    kontrol_tipi: 'malzeme', kriter: '', durum: 'beklemede', olculen_deger: '',
    beklenen_deger: '', tolerek_aralik: '', aciklama: '', duzeltici_faaliyet: '',
  }
  formHata.value = ''
  modalAcik.value = true
}
async function yukle(): Promise<void> {
  yukleniyor.value = true
  try {
    kayitlar.value = await tumunuGetir(insaatApi.kaliteKontrolleri.liste)
  } catch (e) {
    hata.value = hataMesaji(e)
  } finally {
    yukleniyor.value = false
  }
}
async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.proje || !form.value.kriter.trim()) {
    formHata.value = 'Proje ve kontrol kriteri zorunludur.'
    return
  }
  kaydediliyor.value = true
  try {
    await insaatApi.kaliteKontrolleri.olustur({
      ...form.value,
      kriter: form.value.kriter.trim(),
      aciklama: form.value.aciklama.trim(),
      duzeltici_faaliyet: form.value.duzeltici_faaliyet.trim(),
    })
    modalAcik.value = false
    await yukle()
  } catch (e) {
    formHata.value = hataMesaji(e)
  } finally {
    kaydediliyor.value = false
  }
}
onMounted(async () => {
  try {
    ;[projeler.value, pozlar.value] = await Promise.all([
      tumunuGetir(insaatApi.projeler.liste),
      tumunuGetir(insaatApi.pozlar.liste),
    ])
    await yukle()
  } catch (e) {
    hata.value = hataMesaji(e)
    yukleniyor.value = false
  }
})
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat / Saha Güvencesi</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Kalite ve İSG Kontrol Listeleri</h1>
        <p class="mt-1 text-sm text-surface-500">Poz veya proje bazlı kabul kriterlerini, ölçümleri ve düzeltici faaliyetleri izleyin.</p>
      </div>
      <button v-if="yazabilir" class="birincil-dugme" type="button" @click="yeniAc">+ Kontrol Kaydı</button>
    </div>
    <div class="mb-6 grid gap-3 sm:grid-cols-3">
      <div class="rounded-2xl border border-amber-200 bg-amber-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-amber-700">Bekleyen</p><p class="mt-2 text-2xl font-bold text-amber-900">{{ bekleyenSayisi }}</p></div>
      <div class="rounded-2xl border border-emerald-200 bg-emerald-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-emerald-700">Geçen / Onaylanan</p><p class="mt-2 text-2xl font-bold text-emerald-900">{{ gecenSayisi }}</p></div>
      <div class="rounded-2xl border border-red-200 bg-red-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-red-700">Kalan / Reddedilen</p><p class="mt-2 text-2xl font-bold text-red-900">{{ kalanSayisi }}</p></div>
    </div>
    <div class="mb-4 flex flex-wrap gap-2">
      <input v-model="arama" class="alan w-full max-w-sm" type="search" placeholder="Proje, kriter veya faaliyet ara..." />
      <select v-model="durumFiltresi" class="alan"><option value="tum">Tüm durumlar</option><option v-for="(etiket, kod) in KALITE_SONUCLARI" :key="kod" :value="kod">{{ etiket }}</option></select>
      <button class="ikincil-dugme" type="button" @click="yukle">Yenile</button>
    </div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <VeriTablosu :basliklar="['Tarih','Proje / Poz','Kontrol Tipi','Kriter','Durum','Düzeltici Faaliyet']" :bos-mu="!yukleniyor && filtreliKayitlar.length === 0">
      <tr v-for="x in filtreliKayitlar" :key="x.id" class="hover:bg-primary-50/40">
        <td class="px-4 py-3">{{ x.tarih }}</td>
        <td class="px-4 py-3"><div class="font-medium">{{ projeAdi(x.proje) }}</div><div v-if="x.poz_no" class="text-xs text-surface-500">{{ x.poz_no }}</div></td>
        <td class="px-4 py-3">{{ kontrolTipleri[x.kontrol_tipi] || x.kontrol_tipi }}</td>
        <td class="max-w-xs truncate px-4 py-3">{{ x.kriter }}</td>
        <td class="px-4 py-3"><span class="rounded-full bg-surface-100 px-2.5 py-1 text-xs font-semibold">{{ KALITE_SONUCLARI[x.durum] || x.durum }}</span></td>
        <td class="max-w-xs truncate px-4 py-3">{{ x.duzeltici_faaliyet || '—' }}</td>
      </tr>
    </VeriTablosu>
    <KayitModal v-if="modalAcik" baslik="Kalite / İSG Kontrol Kaydı" @kapat="modalAcik = false">
      <form class="flex flex-col gap-4" @submit.prevent="kaydet">
        <div class="grid grid-cols-2 gap-4"><label class="etiket">Proje *<select v-model.number="form.proje" class="alan"><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} / {{ x.ad }}</option></select></label><label class="etiket">Poz / İş Kalemi<select v-model="form.poz" class="alan"><option :value="null">Proje geneli</option><option v-for="x in pozlar" :key="x.id" :value="x.id">{{ x.poz_no }} / {{ x.ad }}</option></select></label></div>
        <div class="grid grid-cols-3 gap-4"><label class="etiket">Tarih *<input v-model="form.tarih" class="alan" type="date" required /></label><label class="etiket">Kontrol Tipi<select v-model="form.kontrol_tipi" class="alan"><option v-for="(etiket, kod) in kontrolTipleri" :key="kod" :value="kod">{{ etiket }}</option></select></label><label class="etiket">Durum<select v-model="form.durum" class="alan"><option v-for="(etiket, kod) in KALITE_SONUCLARI" :key="kod" :value="kod">{{ etiket }}</option></select></label></div>
        <label class="etiket">Kabul Kriteri *<input v-model="form.kriter" class="alan" maxlength="255" placeholder="Örn. Beton basınç dayanımı C30 olmalı" required /></label>
        <div class="grid grid-cols-3 gap-4"><label class="etiket">Ölçülen Değer<input v-model="form.olculen_deger" class="alan" maxlength="255" /></label><label class="etiket">Beklenen Değer<input v-model="form.beklenen_deger" class="alan" maxlength="255" /></label><label class="etiket">Tolerans<input v-model="form.tolerek_aralik" class="alan" maxlength="255" /></label></div>
        <label class="etiket">Açıklama<textarea v-model="form.aciklama" class="alan" rows="2" /></label><label class="etiket">Düzeltici Faaliyet<textarea v-model="form.duzeltici_faaliyet" class="alan" rows="2" placeholder="Uygunsuzluk varsa alınacak aksiyon..." /></label>
        <p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button type="submit" class="birincil-dugme" :disabled="kaydediliyor">{{ kaydediliyor ? 'Kaydediliyor...' : 'Kaydı Oluştur' }}</button></div>
      </form>
    </KayitModal>
  </div>
</template>
