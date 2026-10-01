<script setup lang="ts">
import { onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { sahaApi } from '@/services/sahaApi'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { Proje } from '@/types/insaat'
import type { SantiyeGunlugu } from '@/types/saha'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore(); const yazabilir = yazabilirMi(auth.kullanici?.role)
const L = useKayitListesi<SantiyeGunlugu>('/construction/santiye-gunlukleri/')
const projeler = ref<Proje[]>([]); const modalAcik = ref(false); const kaydediliyor = ref(false); const formHata = ref('')
const form = ref({
  proje: 0,
  tarih: new Date().toISOString().slice(0, 10),
  hava_durumu: 'gunesli',
  sicaklik_min: null as number | null,
  sicaklik_max: null as number | null,
  isci_sayisi: 0,
  isci_tipi: 'genel',
  calisma_saati: 8,
  yapilan_isler: '',
  malzeme_giris: '',
  malzeme_cikis: '',
  ekipmanlar: '',
  sorunlar: '',
  notlar: '',
})
const taslakAnahtari = 'emlak_erp_santiye_gunlugu_taslak'
const taslakVar = ref(false)
function formuSifirla(): void {
  form.value = {
    proje: projeler.value[0]?.id || 0,
    tarih: new Date().toISOString().slice(0, 10),
    hava_durumu: 'gunesli',
    sicaklik_min: null,
    sicaklik_max: null,
    isci_sayisi: 0,
    isci_tipi: 'genel',
    calisma_saati: 8,
    yapilan_isler: '',
    malzeme_giris: '',
    malzeme_cikis: '',
    ekipmanlar: '',
    sorunlar: '',
    notlar: '',
  }
}
function yeniAc(): void { formuSifirla(); formHata.value = ''; modalAcik.value = true }
function taslagiKaydet(): void {
  localStorage.setItem(taslakAnahtari, JSON.stringify(form.value))
  taslakVar.value = true
  formHata.value = 'Taslak cihazınıza kaydedildi. İnternet bağlantısı geldiğinde tekrar Kaydet ile gönderebilirsiniz.'
}
function taslagiYukle(): void {
  const taslak = localStorage.getItem(taslakAnahtari)
  if (!taslak) return
  try {
    form.value = { ...form.value, ...JSON.parse(taslak) }
    taslakVar.value = true
    formHata.value = 'Kaydedilmiş çevrimdışı taslak yüklendi.'
  } catch {
    localStorage.removeItem(taslakAnahtari)
  }
}
async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.proje || !form.value.yapilan_isler.trim()) {
    formHata.value = 'Proje ve yapılan işler alanları zorunludur.'
    return
  }
  kaydediliyor.value = true
  try {
    await sahaApi.gunlukler.olustur({
      ...form.value,
      yapilan_isler: form.value.yapilan_isler.trim(),
      malzeme_giris: form.value.malzeme_giris.trim(),
      malzeme_cikis: form.value.malzeme_cikis.trim(),
      ekipmanlar: form.value.ekipmanlar.trim(),
      sorunlar: form.value.sorunlar.trim(),
      notlar: form.value.notlar.trim(),
    })
    localStorage.removeItem(taslakAnahtari)
    taslakVar.value = false
    modalAcik.value = false
    await L.yukle()
  } catch (e) {
    formHata.value = `${hataMesaji(e)} Bağlantı yoksa "Taslağı Kaydet" seçeneğini kullanabilirsiniz.`
  } finally {
    kaydediliyor.value = false
  }
}
onMounted(async () => { try { projeler.value = await tumunuGetir(insaatApi.projeler.liste) } catch (e) { L.hata.value = hataMesaji(e) }; await L.yukle() })
</script>
<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex items-center justify-between gap-3">
      <div><p class="text-sm font-medium text-primary-700">İnşaat</p><h1 class="font-heading text-2xl font-bold text-surface-900">Şantiye Günlüğü</h1></div>
      <div class="flex gap-2">
        <button v-if="taslakVar" class="ikincil-dugme" type="button" @click="taslagiYukle">Taslağı Yükle</button>
        <button v-if="yazabilir" class="birincil-dugme" type="button" @click="yeniAc">+ Günlük Kaydı</button>
      </div>
    </div>
    <form class="mb-4 flex gap-2" @submit.prevent="L.aramaYap"><input v-model="L.arama.value" class="alan w-full max-w-sm" type="search" placeholder="Proje veya günlük metni ile ara..." /><button class="ikincil-dugme" type="submit">Ara</button></form>
    <p v-if="L.hata.value" class="hata-kutusu mb-4">{{ L.hata.value }}</p>
    <VeriTablosu :basliklar="['Tarih','Proje','Hava','İşçi','Çalışma','Yapılan İşler','Malzeme','Sorunlar','Notlar']" :bos-mu="!L.yukleniyor.value && !L.kayitlar.value.length">
      <tr v-for="x in L.kayitlar.value" :key="x.id" class="hover:bg-surface-100/60">
        <td class="whitespace-nowrap px-4 py-3">{{ x.tarih }}</td><td class="px-4 py-3 font-medium">{{ x.proje_kodu || x.proje }}</td><td class="px-4 py-3">{{ x.hava_durumu || '—' }}</td><td class="px-4 py-3">{{ x.isci_sayisi }} / {{ x.isci_tipi }}</td><td class="px-4 py-3">{{ x.calisma_saati }} saat</td><td class="max-w-xs truncate px-4 py-3">{{ x.yapilan_isler }}</td><td class="max-w-xs truncate px-4 py-3">{{ x.malzeme_giris || '—' }}</td><td class="max-w-xs truncate px-4 py-3">{{ x.sorunlar || '—' }}</td><td class="max-w-xs truncate px-4 py-3">{{ x.notlar || '—' }}</td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="modalAcik" baslik="Şantiye Günlüğü" @kapat="modalAcik = false">
      <form class="flex flex-col gap-4" @submit.prevent="kaydet">
        <div class="grid grid-cols-2 gap-4"><label class="etiket">Proje *<select v-model.number="form.proje" class="alan"><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} / {{ x.ad }}</option></select></label><label class="etiket">Tarih *<input v-model="form.tarih" class="alan" type="date" required /></label></div>
        <div class="grid grid-cols-2 gap-4"><label class="etiket">Hava Durumu<select v-model="form.hava_durumu" class="alan"><option value="gunesli">Güneşli</option><option value="parcali_bulutlu">Parçalı Bulutlu</option><option value="bulutlu">Bulutlu</option><option value="yagmurlu">Yağmurlu</option><option value="saganak">Sağanak</option><option value="karli">Karlı</option><option value="sisli">Sisli</option></select></label><label class="etiket">Çalışma Saati<input v-model.number="form.calisma_saati" class="alan" type="number" min="0" max="24" /></label></div>
        <div class="grid grid-cols-3 gap-4"><label class="etiket">İşçi Sayısı<input v-model.number="form.isci_sayisi" class="alan" type="number" min="0" /></label><label class="etiket">Min. Sıcaklık<input v-model.number="form.sicaklik_min" class="alan" type="number" /></label><label class="etiket">Max. Sıcaklık<input v-model.number="form.sicaklik_max" class="alan" type="number" /></label></div>
        <label class="etiket">Yapılan İşler *<textarea v-model="form.yapilan_isler" class="alan" rows="3" required /></label>
        <div class="grid grid-cols-2 gap-4"><label class="etiket">Malzeme Girişi<textarea v-model="form.malzeme_giris" class="alan" rows="2" /></label><label class="etiket">Malzeme Çıkışı<textarea v-model="form.malzeme_cikis" class="alan" rows="2" /></label></div>
        <label class="etiket">Ekipmanlar<textarea v-model="form.ekipmanlar" class="alan" rows="2" /></label><label class="etiket">Sorunlar<textarea v-model="form.sorunlar" class="alan" rows="2" /></label><label class="etiket">Notlar<textarea v-model="form.notlar" class="alan" rows="2" /></label>
        <p v-if="formHata" class="hata-kutusu">{{ formHata }}</p>
        <div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="taslagiKaydet">Taslağı Kaydet</button><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button type="submit" class="birincil-dugme" :disabled="kaydediliyor">Kaydet</button></div>
      </form>
    </KayitModal>
  </div>
</template>
