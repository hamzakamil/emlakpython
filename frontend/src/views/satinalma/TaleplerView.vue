<script setup lang="ts">
/**
 * Satın Alma Talepleri — liste + oluşturma/düzenleme + onay akışı + siparişe dönüşüm.
 * Backend: /api/v1/purchase-requests/ (+ /onaya-gonder/, /onayla/, /reddet/, /iptal-et/,
 * /talepten-siparis-olustur/). Fiziksel silme yok (backend iptale çeker).
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
import type { Proje, Malzeme, Tedarikci } from '@/types/insaat'
import { TALEP_DURUMLARI, type SatinAlmaTalebi, type TalepDurumu } from '@/types/satinAlma'
import { satinAlmaYazabilirMi } from '@/utils/yetki'

const router = useRouter()
const auth = useAuthStore()
const yazabilir = computed(() => satinAlmaYazabilirMi(auth.kullanici?.role))

const L = useKayitListesi<SatinAlmaTalebi>('/purchase-requests/')
const projeler = ref<Proje[]>([])
const malzemeler = ref<Malzeme[]>([])
const tedarikciler = ref<Tedarikci[]>([])

const durumEtiketi = (d: TalepDurumu): string =>
  TALEP_DURUMLARI.find((x) => x.deger === d)?.etiket ?? d
const durumSinifi = (d: TalepDurumu): string =>
  d === 'onaylandi' || d === 'siparise_donustu'
    ? 'text-success-700'
    : d === 'reddedildi' || d === 'iptal'
      ? 'text-error-600'
      : 'text-surface-500'

/* --- Talep modalı --- */
const modalAcik = ref(false)
const duzenlenen = ref<SatinAlmaTalebi | null>(null)
const kaydediliyor = ref(false)
const formHata = ref('')
const form = ref({ proje: null as number | null, aciklama: '' })
const satirlar = ref<{ malzeme: number; miktar: string }[]>([])

function yeniAc(): void {
  duzenlenen.value = null
  form.value = { proje: null, aciklama: '' }
  satirlar.value = []
  formHata.value = ''
  modalAcik.value = true
}

function duzenleAc(k: SatinAlmaTalebi): void {
  duzenlenen.value = k
  form.value = { proje: k.proje, aciklama: k.aciklama || '' }
  satirlar.value = []
  formHata.value = ''
  modalAcik.value = true
}

function satirEkle(): void {
  satirlar.value.push({ malzeme: 0, miktar: '' })
}

function satirSil(i: number): void {
  satirlar.value.splice(i, 1)
}

async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.proje) {
    formHata.value = 'Proje seçimi zorunludur.'
    return
  }
  kaydediliyor.value = true
  try {
    let talepId = duzenlenen.value?.id
    if (duzenlenen.value) {
      await satinAlmaApi.talepler.guncelle(duzenlenen.value.id, {
        proje: form.value.proje,
        aciklama: form.value.aciklama.trim(),
      })
    } else {
      const olusan = await satinAlmaApi.talepler.olustur({
        proje: form.value.proje,
        aciklama: form.value.aciklama.trim(),
      })
      talepId = olusan.id
    }
    for (const s of satirlar.value) {
      if (s.malzeme > 0 && Number(s.miktar) > 0 && talepId) {
        await satinAlmaApi.talepKalemleri.olustur({
          talep: talepId,
          malzeme: s.malzeme,
          miktar: s.miktar,
        })
      }
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
  k: SatinAlmaTalebi,
  islem: 'onayaGonder' | 'onayla' | 'reddet' | 'iptalEt',
  soru: string,
): Promise<void> {
  if (!window.confirm(`${k.talep_no} — ${soru}`)) return
  L.hata.value = ''
  try {
    await satinAlmaApi.talepler[islem](k.id)
    await L.yukle()
  } catch (bilinmeyen) {
    L.hata.value = hataMesaji(bilinmeyen)
  }
}

/* --- Siparişe dönüşüm --- */
const donusumAcik = ref(false)
const donusumTalep = ref<SatinAlmaTalebi | null>(null)
const donusumTedarikci = ref<number | null>(null)
const donusumHata = ref('')

function donusumAc(k: SatinAlmaTalebi): void {
  donusumTalep.value = k
  donusumTedarikci.value = null
  donusumHata.value = ''
  donusumAcik.value = true
}

async function donusumuKaydet(): Promise<void> {
  donusumHata.value = ''
  if (!donusumTalep.value || !donusumTedarikci.value) {
    donusumHata.value = 'Tedarikçi seçimi zorunludur.'
    return
  }
  try {
    const siparis = await satinAlmaApi.talepler.taleptenSiparisOlustur(donusumTalep.value.id, {
      tedarikci: donusumTedarikci.value,
    })
    donusumAcik.value = false
    await L.yukle()
    await router.push({ name: 'siparis-detay', params: { id: siparis.id } })
  } catch (bilinmeyen) {
    donusumHata.value = hataMesaji(bilinmeyen)
  }
}

function detayaGit(k: SatinAlmaTalebi): void {
  void router.push({ name: 'talep-detay', params: { id: k.id } })
}

onMounted(async () => {
  try {
    projeler.value = await tumunuGetir(insaatApi.projeler.liste)
    malzemeler.value = await tumunuGetir(insaatApi.malzemeler.liste)
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
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Satın Alma Talepleri</h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="yeniAc()">+ Yeni Talep</button>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Talep no veya proje kodu ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.durum" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm durumlar</option>
        <option v-for="d in TALEP_DURUMLARI" :key="d.deger" :value="d.deger">{{ d.etiket }}</option>
      </select>
    </div>

    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>

    <VeriTablosu
      :basliklar="['Talep No', 'Proje', 'Sahibi', 'Durum', 'Kalem', yazabilir ? 'İşlem' : '']"
      :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0"
    >
      <template v-for="k in L.kayitlar.value" :key="k.id">
        <tr class="transition-colors hover:bg-surface-100/60">
          <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium">
            <button type="button" class="text-primary-700 hover:underline" @click="detayaGit(k)">{{ k.talep_no }}</button>
          </td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.proje_kodu ?? `#${k.proje}` }}</td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.talep_sahibi_adi ?? '—' }}</td>
          <td class="whitespace-nowrap px-4 py-3 font-medium" :class="durumSinifi(k.durum)">{{ durumEtiketi(k.durum) }}</td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.kalemler.length }}</td>
          <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
            <div class="flex flex-wrap items-center gap-2">
              <button v-if="k.durum === 'taslak'" type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="duzenleAc(k)">Düzenle</button>
              <button v-if="k.durum === 'taslak'" type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="aksiyon(k, 'onayaGonder', 'onaya gönderilsin mi?')">Onaya Gönder</button>
              <button v-if="k.durum === 'onaya_gonderildi'" type="button" class="text-sm font-medium text-success-700 hover:underline" @click="aksiyon(k, 'onayla', 'onaylansın mı?')">Onayla</button>
              <button v-if="k.durum === 'onaya_gonderildi'" type="button" class="text-sm font-medium text-error-600 hover:underline" @click="aksiyon(k, 'reddet', 'reddedilsin mi?')">Reddet</button>
              <button v-if="k.durum === 'onaylandi'" type="button" class="text-sm font-medium text-success-700 hover:underline" @click="donusumAc(k)">Siparişe Dönüştür</button>
              <button v-if="k.durum !== 'siparise_donustu' && k.durum !== 'iptal'" type="button" class="text-sm font-medium text-error-600 hover:underline" @click="aksiyon(k, 'iptalEt', 'iptal edilsin mi?')">İptal</button>
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

    <KayitModal v-if="modalAcik" :baslik="duzenlenen ? 'Talebi Düzenle' : 'Yeni Talep'" @kapat="modalAcik = false">
      <form class="flex flex-col gap-4" @submit.prevent="kaydet">
        <label class="etiket">
          Proje
          <select v-model.number="form.proje" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option>
          </select>
        </label>
        <label class="etiket">Açıklama<textarea v-model="form.aciklama" rows="2" class="alan"></textarea></label>

        <div v-if="!duzenlenen" class="rounded-lg border border-surface-200 p-3">
          <div class="mb-2 flex items-center justify-between">
            <p class="text-xs font-semibold uppercase tracking-wider text-surface-500">Kalemler (malzeme · miktar)</p>
            <button type="button" class="ikincil-dugme px-2 py-1 text-xs" @click="satirEkle">+ Kalem</button>
          </div>
          <div v-for="(s, i) in satirlar" :key="i" class="mt-2 grid grid-cols-[1fr_1fr_auto] items-end gap-2">
            <label class="etiket">
              Malzeme
              <select v-model.number="s.malzeme" class="alan">
                <option :value="0">— Seçiniz —</option>
                <option v-for="m in malzemeler" :key="m.id" :value="m.id">{{ m.malzeme_kodu }} — {{ m.ad }}</option>
              </select>
            </label>
            <label class="etiket">Miktar<input v-model="s.miktar" type="text" inputmode="decimal" class="alan" /></label>
            <button type="button" class="text-sm font-medium text-error-600 hover:underline" @click="satirSil(i)">Sil</button>
          </div>
        </div>

        <p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button>
          <button type="submit" :disabled="kaydediliyor" class="birincil-dugme">
            {{ kaydediliyor ? 'Kaydediliyor…' : 'Kaydet' }}
          </button>
        </div>
      </form>
    </KayitModal>

    <KayitModal v-if="donusumAcik" baslik="Talebi Siparişe Dönüştür" @kapat="donusumAcik = false">
      <form class="flex flex-col gap-4" @submit.prevent="donusumuKaydet">
        <p class="text-sm text-surface-500">
          {{ donusumTalep?.talep_no }} — kalemlerde seçili tekliflerin <span class="font-medium">aynı tedarikçiye</span> ait
          olması gerekir. Fiyatlar dönüşüm anında sabitlenir.
        </p>
        <label class="etiket">
          Tedarikçi
          <select v-model.number="donusumTedarikci" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="t in tedarikciler" :key="t.id" :value="t.id">{{ t.firma_adi }}</option>
          </select>
        </label>
        <p v-if="donusumHata" class="hata-kutusu" role="alert">{{ donusumHata }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="donusumAcik = false">Vazgeç</button>
          <button type="submit" class="birincil-dugme">Sipariş Oluştur</button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>
