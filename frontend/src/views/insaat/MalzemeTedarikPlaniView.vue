<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useAuthStore } from '@/stores/auth'
import type { Malzeme, MalzemeTedarikciIliskisi, Tedarikci } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const malzemeler = ref<Malzeme[]>([])
const tedarikciler = ref<Tedarikci[]>([])
const siparisler = ref<MalzemeTedarikciIliskisi[]>([])
const arama = ref('')
const hata = ref('')
const modalAcik = ref(false)
const kaydediliyor = ref(false)
const form = ref({ malzeme: 0, tedarikci: 0, miktar: '', birim: 'adet', durum: 'basliyor', teslim_tarihi: '', aciklama: '' })

const gorunenSiparisler = computed(() => siparisler.value.filter((x) => {
  const metin = `${malzemeAdi(x.malzeme)} ${tedarikciAdi(x.tedarikci)}`.toLocaleLowerCase('tr-TR')
  return !arama.value || metin.includes(arama.value.toLocaleLowerCase('tr-TR'))
}))
function malzemeAdi(id: number): string { return malzemeler.value.find((x) => x.id === id)?.ad || `Malzeme #${id}` }
function tedarikciAdi(id: number): string { return tedarikciler.value.find((x) => x.id === id)?.firma_adi || `Tedarikçi #${id}` }
function yeniAc(): void {
  form.value = { malzeme: malzemeler.value[0]?.id || 0, tedarikci: tedarikciler.value[0]?.id || 0, miktar: '', birim: 'adet', durum: 'basliyor', teslim_tarihi: '', aciklama: '' }
  hata.value = ''
  modalAcik.value = true
}
async function yukle(): Promise<void> {
  try {
    const [m, t, s] = await Promise.all([
      tumunuGetir(insaatApi.malzemeler.liste),
      tumunuGetir(insaatApi.tedarikciler.liste),
      tumunuGetir(insaatApi.malzemeTedarikciIliskileri.liste),
    ])
    malzemeler.value = m
    tedarikciler.value = t
    siparisler.value = s
  } catch (e) { hata.value = hataMesaji(e) }
}
async function kaydet(): Promise<void> {
  hata.value = ''
  if (!form.value.malzeme || !form.value.tedarikci || Number(form.value.miktar) <= 0) {
    hata.value = 'Malzeme, tedarikçi ve sıfırdan büyük miktar zorunludur.'
    return
  }
  kaydediliyor.value = true
  try {
    await insaatApi.malzemeTedarikciIliskileri.olustur({
      ...form.value,
      miktar: form.value.miktar,
      teslim_tarihi: form.value.teslim_tarihi || null,
      aciklama: form.value.aciklama.trim(),
    })
    modalAcik.value = false
    await yukle()
  } catch (e) { hata.value = hataMesaji(e) } finally { kaydediliyor.value = false }
}
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex items-center justify-between gap-3">
      <div><p class="text-sm font-medium text-primary-700">İnşaat</p><h1 class="font-heading text-2xl font-bold text-surface-900">Malzeme / Tedarik Planı</h1><p class="mt-1 text-sm text-surface-500">Malzeme ihtiyacını tedarikçi, miktar ve teslim tarihiyle takip edin.</p></div>
      <button v-if="yazabilir" class="birincil-dugme" type="button" @click="yeniAc">+ Tedarik Planı</button>
    </div>
    <div class="mb-4 flex gap-2"><input v-model="arama" class="alan w-full max-w-sm" type="search" placeholder="Malzeme veya tedarikçi ara..." /><button class="ikincil-dugme" type="button" @click="yukle">Yenile</button></div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <VeriTablosu :basliklar="['Malzeme','Tedarikçi','Miktar','Birim','Durum','Teslim Tarihi','Açıklama']" :bos-mu="gorunenSiparisler.length === 0">
      <tr v-for="x in gorunenSiparisler" :key="x.id" class="hover:bg-surface-100/60"><td class="px-4 py-3 font-medium">{{ malzemeAdi(x.malzeme) }}</td><td class="px-4 py-3">{{ tedarikciAdi(x.tedarikci) }}</td><td class="px-4 py-3">{{ x.miktar }}</td><td class="px-4 py-3">{{ x.birim }}</td><td class="px-4 py-3">{{ x.durum }}</td><td class="px-4 py-3">{{ x.teslim_tarihi || '—' }}</td><td class="max-w-xs truncate px-4 py-3">{{ x.aciklama || '—' }}</td></tr>
    </VeriTablosu>
    <KayitModal v-if="modalAcik" baslik="Yeni Malzeme Tedarik Planı" @kapat="modalAcik = false">
      <form class="flex flex-col gap-4" @submit.prevent="kaydet">
        <label class="etiket">Malzeme<select v-model.number="form.malzeme" class="alan"><option v-for="x in malzemeler" :key="x.id" :value="x.id">{{ x.malzeme_kodu }} / {{ x.ad }}</option></select></label>
        <label class="etiket">Tedarikçi<select v-model.number="form.tedarikci" class="alan"><option v-for="x in tedarikciler" :key="x.id" :value="x.id">{{ x.firma_kodu }} / {{ x.firma_adi }}</option></select></label>
        <div class="grid grid-cols-2 gap-4"><label class="etiket">Miktar<input v-model="form.miktar" class="alan" type="number" min="0.0001" step="0.0001" required /></label><label class="etiket">Birim<input v-model="form.birim" class="alan" maxlength="20" required /></label></div>
        <div class="grid grid-cols-2 gap-4"><label class="etiket">Durum<select v-model="form.durum" class="alan"><option value="basliyor">Başlıyor</option><option value="aktif">Aktif</option><option value="gecikiyor">Gecikiyor</option><option value="tamamlandi">Tamamlandı</option><option value="iptal">İptal</option></select></label><label class="etiket">Teslim Tarihi<input v-model="form.teslim_tarihi" class="alan" type="date" /></label></div>
        <label class="etiket">Açıklama<textarea v-model="form.aciklama" class="alan" rows="3" /></label>
        <div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button type="submit" class="birincil-dugme" :disabled="kaydediliyor">Kaydet</button></div>
      </form>
    </KayitModal>
  </div>
</template>
