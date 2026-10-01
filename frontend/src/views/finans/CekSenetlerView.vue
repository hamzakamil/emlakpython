<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { finansApi } from '@/services/finansApi'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useAuthStore } from '@/stores/auth'
import type { CekSenet, CekSenetDurumu, CekSenetTuru } from '@/types/finans'
import { CEK_SENET_DURUMLARI, CEK_SENET_TURLERI } from '@/types/finans'
import type { Proje } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const kayitlar = ref<CekSenet[]>([])
const projeler = ref<Proje[]>([])
const arama = ref('')
const durum = ref<CekSenetDurumu | ''>('')
const modalAcik = ref(false)
const hata = ref('')
const formHata = ref('')
const form = ref({ tur: 'cek' as CekSenetTuru, numara: '', proje: null as number | null, tutar: '', vade_tarihi: '', durum: 'bekliyor' as CekSenetDurumu, aciklama: '' })
const filtreli = computed(() => kayitlar.value.filter((x) => `${x.numara} ${x.aciklama}`.toLocaleLowerCase('tr-TR').includes(arama.value.toLocaleLowerCase('tr-TR')) && (!durum.value || x.durum === durum.value)))
const para = (v: string): string => Number(v).toLocaleString('tr-TR', { style: 'currency', currency: 'TRY' })
const projeAdi = (id: number | null): string => id ? projeler.value.find((x) => x.id === id)?.proje_kodu || `#${id}` : 'Genel finans'
function yeni(): void { formHata.value = ''; form.value = { tur: 'cek', numara: '', proje: projeler.value[0]?.id || null, tutar: '', vade_tarihi: '', durum: 'bekliyor', aciklama: '' }; modalAcik.value = true }
async function yukle(): Promise<void> { try { ;[kayitlar.value, projeler.value] = await Promise.all([finansApi.cekSenetler.liste().then((x) => x.results), tumunuGetir(insaatApi.projeler.liste)]) } catch (e) { hata.value = hataMesaji(e) } }
async function kaydet(): Promise<void> { formHata.value = ''; if (!form.value.numara.trim() || !(Number(form.value.tutar) > 0) || !form.value.vade_tarihi) { formHata.value = 'Belge numarası, pozitif tutar ve vade tarihi zorunludur.'; return }; try { await finansApi.cekSenetler.olustur({ ...form.value, numara: form.value.numara.trim() }); window.dispatchEvent(new CustomEvent('hatirlatma-onerisi', { detail: { tarih: form.value.vade_tarihi, baslik: 'Çek/Senet vadesi için hatırlatma kurmak ister misiniz?', payload: { ilgili_app: 'finance', ilgili_model: 'CekSenet' } } })); modalAcik.value = false; await yukle() } catch (e) { formHata.value = hataMesaji(e) } }
onMounted(yukle)
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p class="text-sm font-medium text-primary-700">Finans / Tahsilat</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Çek / Senet Takibi</h1><p class="mt-1 text-sm text-surface-500">Vade tarihlerini, proje bağlantısını ve ödeme durumunu tek ekranda yönetin.</p></div><button v-if="yazabilir" class="birincil-dugme" type="button" @click="yeni">+ Çek / Senet Ekle</button></div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <div class="mb-4 flex flex-wrap gap-2"><input v-model="arama" class="alan w-full max-w-sm" type="search" placeholder="Belge no veya açıklama ara..." /><select v-model="durum" class="alan w-48"><option value="">Tüm durumlar</option><option v-for="(etiket, anahtar) in CEK_SENET_DURUMLARI" :key="anahtar" :value="anahtar">{{ etiket }}</option></select><button class="ikincil-dugme" type="button" @click="yukle">Yenile</button></div>
    <VeriTablosu :basliklar="['Tür','Belge No','Proje','Tutar','Vade','Durum','Açıklama']" :bos-mu="!filtreli.length" bos-mesaj="Henüz çek veya senet kaydı bulunmuyor."><tr v-for="x in filtreli" :key="x.id" class="hover:bg-primary-50/40"><td class="px-4 py-3">{{ CEK_SENET_TURLERI[x.tur] }}</td><td class="px-4 py-3 font-semibold">{{ x.numara }}</td><td class="px-4 py-3">{{ projeAdi(x.proje) }}</td><td class="px-4 py-3">{{ para(x.tutar) }}</td><td class="px-4 py-3">{{ x.vade_tarihi }}</td><td class="px-4 py-3">{{ CEK_SENET_DURUMLARI[x.durum] }}</td><td class="max-w-xs truncate px-4 py-3 text-surface-500">{{ x.aciklama || '—' }}</td></tr></VeriTablosu>
    <KayitModal v-if="modalAcik" baslik="Yeni Çek / Senet" @kapat="modalAcik = false"><form class="flex flex-col gap-4" @submit.prevent="kaydet"><div class="grid grid-cols-2 gap-4"><label class="etiket">Tür<select v-model="form.tur" class="alan"><option v-for="(etiket, anahtar) in CEK_SENET_TURLERI" :key="anahtar" :value="anahtar">{{ etiket }}</option></select></label><label class="etiket">Belge No *<input v-model="form.numara" class="alan" maxlength="50" required /></label></div><label class="etiket">Proje<select v-model="form.proje" class="alan"><option :value="null">Genel finans</option><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} — {{ x.ad }}</option></select></label><div class="grid grid-cols-2 gap-4"><label class="etiket">Tutar *<input v-model="form.tutar" class="alan" type="number" min="0.01" step="0.01" required /></label><label class="etiket">Vade Tarihi *<input v-model="form.vade_tarihi" class="alan" type="date" required /></label></div><label class="etiket">Açıklama<textarea v-model="form.aciklama" class="alan" rows="3" maxlength="255" /></label><p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button><button class="birincil-dugme" type="submit">Kaydet</button></div></form></KayitModal>
  </div>
</template>
