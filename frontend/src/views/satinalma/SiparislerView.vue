<script setup lang="ts">
/**
 * Satın Alma Siparişleri — liste + oluşturma/düzenleme + onay akışı.
 * Backend: /api/v1/purchase-orders/ (+ /onaya-gonder/, /onayla/, /iptal-et/).
 * Bu fazda muhasebe fişi üretilmez.
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { satinAlmaApi } from '@/services/satinAlmaApi'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { Proje, Tedarikci } from '@/types/insaat'
import { SIPARIS_DURUMLARI, type SatinAlmaSiparisi, type SiparisDurumu } from '@/types/satinAlma'
import { satinAlmaYazabilirMi } from '@/utils/yetki'

const router = useRouter()
const auth = useAuthStore()
const yazabilir = computed(() => satinAlmaYazabilirMi(auth.kullanici?.role))

const L = useKayitListesi<SatinAlmaSiparisi>('/purchase-orders/')
const projeler = ref<Proje[]>([])
const tedarikciler = ref<Tedarikci[]>([])

const durumEtiketi = (d: SiparisDurumu): string =>
  SIPARIS_DURUMLARI.find((x) => x.deger === d)?.etiket ?? d
const durumSinifi = (d: SiparisDurumu): string =>
  d === 'onaylandi' || d === 'tamamlandi'
    ? 'text-success-700'
    : d === 'iptal'
      ? 'text-error-600'
      : 'text-surface-500'

const modalAcik = ref(false)
const duzenlenen = ref<SatinAlmaSiparisi | null>(null)
const kaydediliyor = ref(false)
const formHata = ref('')
const form = ref({
  tedarikci: null as number | null,
  proje: null as number | null,
  teslim_tarihi: '',
  aciklama: '',
})

function yeniAc(): void {
  duzenlenen.value = null
  form.value = { tedarikci: null, proje: null, teslim_tarihi: '', aciklama: '' }
  formHata.value = ''
  modalAcik.value = true
}

function duzenleAc(k: SatinAlmaSiparisi): void {
  duzenlenen.value = k
  form.value = {
    tedarikci: k.tedarikci,
    proje: k.proje,
    teslim_tarihi: k.teslim_tarihi ?? '',
    aciklama: k.aciklama || '',
  }
  formHata.value = ''
  modalAcik.value = true
}

async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.tedarikci || !form.value.proje) {
    formHata.value = 'Tedarikçi ve proje seçimi zorunludur.'
    return
  }
  kaydediliyor.value = true
  try {
    const payload = {
      tedarikci: form.value.tedarikci,
      proje: form.value.proje,
      teslim_tarihi: form.value.teslim_tarihi || null,
      aciklama: form.value.aciklama.trim(),
    }
    if (duzenlenen.value) {
      await satinAlmaApi.siparisler.guncelle(duzenlenen.value.id, payload)
    } else {
      await satinAlmaApi.siparisler.olustur(payload)
    }
    modalAcik.value = false
    await L.yukle()
  } catch (bilinmeyen) {
    formHata.value = hataMesaji(bilinmeyen)
  } finally {
    kaydediliyor.value = false
  }
}

async function aksiyon(
  k: SatinAlmaSiparisi,
  islem: 'onayaGonder' | 'onayla' | 'iptalEt',
  soru: string,
): Promise<void> {
  if (!window.confirm(`${k.siparis_no} — ${soru}`)) return
  L.hata.value = ''
  try {
    await satinAlmaApi.siparisler[islem](k.id)
    await L.yukle()
  } catch (bilinmeyen) {
    L.hata.value = hataMesaji(bilinmeyen)
  }
}

function detayaGit(k: SatinAlmaSiparisi): void {
  void router.push({ name: 'siparis-detay', params: { id: k.id } })
}

onMounted(async () => {
  try {
    projeler.value = await tumunuGetir(insaatApi.projeler.liste)
    tedarikciler.value = await tumunuGetir(insaatApi.tedarikciler.liste)
  } catch (bilinmeyen) {
    L.hata.value = hataMesaji(bilinmeyen)
  }
  await L.yukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">Satın Alma</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Satın Alma Siparişleri</h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="yeniAc()">+ Yeni Sipariş</button>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Sipariş no veya tedarikçi ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.durum" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm durumlar</option>
        <option v-for="d in SIPARIS_DURUMLARI" :key="d.deger" :value="d.deger">{{ d.etiket }}</option>
      </select>
    </div>

    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>

    <VeriTablosu
      :basliklar="['Sipariş No', 'Tedarikçi', 'Proje', 'Durum', 'Kalem', yazabilir ? 'İşlem' : '']"
      :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0"
    >
      <template v-for="k in L.kayitlar.value" :key="k.id">
        <tr class="transition-colors hover:bg-surface-100/60">
          <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium">
            <button type="button" class="text-primary-700 hover:underline" @click="detayaGit(k)">{{ k.siparis_no }}</button>
          </td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.tedarikci_adi ?? `#${k.tedarikci}` }}</td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.proje_kodu ?? `#${k.proje}` }}</td>
          <td class="whitespace-nowrap px-4 py-3 font-medium" :class="durumSinifi(k.durum)">{{ durumEtiketi(k.durum) }}</td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.kalemler.length }}</td>
          <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
            <div class="flex flex-wrap items-center gap-2">
              <button v-if="k.durum === 'taslak'" type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="duzenleAc(k)">Düzenle</button>
              <button v-if="k.durum === 'taslak'" type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="aksiyon(k, 'onayaGonder', 'onaya gönderilsin mi?')">Onaya Gönder</button>
              <button v-if="k.durum === 'onay_bekliyor'" type="button" class="text-sm font-medium text-success-700 hover:underline" @click="aksiyon(k, 'onayla', 'onaylansın mı?')">Onayla</button>
              <button v-if="k.durum !== 'tamamlandi' && k.durum !== 'iptal'" type="button" class="text-sm font-medium text-error-600 hover:underline" @click="aksiyon(k, 'iptalEt', 'iptal edilsin mi?')">İptal</button>
            </div>
          </td>
        </tr>
      </template>
    </VeriTablosu>
    <Sayfalama
      :sayfa="L.sayfa.value"
      :toplam="L.toplam.value"
      :yukleniyor="L.yukleniyor.value"
      @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }"
    />

    <KayitModal v-if="modalAcik" :baslik="duzenlenen ? 'Siparişi Düzenle' : 'Yeni Sipariş'" @kapat="modalAcik = false">
      <form class="flex flex-col gap-4" @submit.prevent="kaydet">
        <label class="etiket">
          Tedarikçi
          <select v-model.number="form.tedarikci" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="t in tedarikciler" :key="t.id" :value="t.id">{{ t.firma_adi }}</option>
          </select>
        </label>
        <label class="etiket">
          Proje
          <select v-model.number="form.proje" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option>
          </select>
        </label>
        <label class="etiket">Teslim Tarihi<input v-model="form.teslim_tarihi" type="date" class="alan" /></label>
        <label class="etiket">Açıklama<textarea v-model="form.aciklama" rows="2" class="alan"></textarea></label>
        <p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button>
          <button type="submit" :disabled="kaydediliyor" class="birincil-dugme">
            {{ kaydediliyor ? 'Kaydediliyor…' : 'Kaydet' }}
          </button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>
