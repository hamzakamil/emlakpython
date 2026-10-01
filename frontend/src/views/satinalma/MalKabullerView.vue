<script setup lang="ts">
/**
 * FAZ 3B — Mal Kabuller: liste + oluşturma + onay/iptal.
 * Onayda GİRİŞ stok hareketleri üretilir (backend); iptalde ters hareket açılır.
 * Backend: /api/v1/purchase-mal-kabul/ (+ /onayla/, /iptal-et/).
 */
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { satinAlmaApi } from '@/services/satinAlmaApi'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { Proje, Tedarikci } from '@/types/insaat'
import {
  MAL_KABUL_DURUMLARI,
  type Depo,
  type MalKabul,
  type MalKabulDurumu,
  type SatinAlmaSiparisi,
} from '@/types/satinAlma'
import { satinAlmaYazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => satinAlmaYazabilirMi(auth.kullanici?.role))

const L = useKayitListesi<MalKabul>('/purchase-mal-kabul/')
const depolar = ref<Depo[]>([])
const siparisler = ref<SatinAlmaSiparisi[]>([])
const projeler = ref<Proje[]>([])
const tedarikciler = ref<Tedarikci[]>([])

const durumEtiketi = (d: MalKabulDurumu): string =>
  MAL_KABUL_DURUMLARI.find((x) => x.deger === d)?.etiket ?? d
const durumSinifi = (d: MalKabulDurumu): string =>
  d === 'onaylandi' || d === 'tamamlandi'
    ? 'text-success-700'
    : d === 'iptal'
      ? 'text-error-600'
      : 'text-surface-500'

const modalAcik = ref(false)
const kaydediliyor = ref(false)
const formHata = ref('')
const form = ref({ siparis: null as number | null, depo: null as number | null, aciklama: '' })
const satirlar = ref<{ siparis_kalemi: number; kabul_miktari: string; red_miktari: string }[]>([])

function yeniAc(): void {
  form.value = { siparis: null, depo: null, aciklama: '' }
  satirlar.value = []
  formHata.value = ''
  modalAcik.value = true
}

function satirEkle(): void {
  satirlar.value.push({ siparis_kalemi: 0, kabul_miktari: '', red_miktari: '0' })
}

function satirSil(i: number): void {
  satirlar.value.splice(i, 1)
}

const seciliSiparis = computed(() => siparisler.value.find((s) => s.id === form.value.siparis) ?? null)

async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.siparis || !form.value.depo) {
    formHata.value = 'Sipariş ve depo seçimi zorunludur.'
    return
  }
  kaydediliyor.value = true
  try {
    const kabul = await satinAlmaApi.malKabuller.olustur({
      siparis: form.value.siparis,
      depo: form.value.depo,
      proje: siparisler.value.find((s) => s.id === form.value.siparis)?.proje,
      aciklama: form.value.aciklama.trim(),
    })
    for (const s of satirlar.value) {
      const kaynak = seciliSiparis.value?.kalemler.find((k) => k.id === s.siparis_kalemi)
      if (kaynak && (Number(s.kabul_miktari) > 0 || Number(s.red_miktari) > 0)) {
        await satinAlmaApi.malKabulKalemleri.olustur({
          mal_kabul: kabul.id,
          siparis_kalemi: kaynak.id,
          malzeme: kaynak.malzeme,
          kabul_miktari: s.kabul_miktari || '0',
          red_miktari: s.red_miktari || '0',
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

async function aksiyon(k: MalKabul, islem: 'onayla' | 'iptalEt', soru: string): Promise<void> {
  if (!window.confirm(`${k.belge_no} — ${soru}`)) return
  L.hata.value = ''
  try {
    await satinAlmaApi.malKabuller[islem](k.id)
    await L.yukle()
  } catch (bilinmeyen) {
    L.hata.value = hataMesaji(bilinmeyen)
  }
}

onMounted(async () => {
  try {
    const [d, s, p, t] = await Promise.all([
      tumunuGetir(satinAlmaApi.depolar.liste),
      tumunuGetir(satinAlmaApi.siparisler.liste),
      tumunuGetir(insaatApi.projeler.liste),
      tumunuGetir(insaatApi.tedarikciler.liste),
    ])
    depolar.value = d
    siparisler.value = s
    projeler.value = p
    tedarikciler.value = t
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
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Mal Kabuller</h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="yeniAc()">+ Yeni Kabul</button>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Belge no ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.durum" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm durumlar</option>
        <option v-for="d in MAL_KABUL_DURUMLARI" :key="d.deger" :value="d.deger">{{ d.etiket }}</option>
      </select>
    </div>

    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>

    <VeriTablosu
      :basliklar="['Belge No', 'Proje', 'Depo', 'Durum', 'Kalem', 'Muhasebe', yazabilir ? 'İşlem' : '']"
      :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0"
    >
      <template v-for="k in L.kayitlar.value" :key="k.id">
        <tr class="transition-colors hover:bg-surface-100/60">
          <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium">{{ k.belge_no }}</td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.proje_kodu ?? `#${k.proje}` }}</td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.depo_kodu ?? `#${k.depo}` }}</td>
          <td class="whitespace-nowrap px-4 py-3 font-medium" :class="durumSinifi(k.durum)">{{ durumEtiketi(k.durum) }}</td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.kalemler.length }}</td>
          <td class="whitespace-nowrap px-4 py-3 font-mono text-xs">
            <template v-if="k.muhasebe?.fatura_no">{{ k.muhasebe.fatura_no }} · {{ k.muhasebe.fis_no }}</template>
            <template v-else><span title="Tedarikçiye cari kart bağlanmadıysa muhasebe kaydı oluşmaz">Muhasebesiz</span></template>
          </td>
          <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
            <div class="flex flex-wrap items-center gap-2">
              <button v-if="k.durum === 'taslak'" type="button" class="text-sm font-medium text-success-700 hover:underline" @click="aksiyon(k, 'onayla', 'onaylansın mı? Stok giriş hareketleri üretilir.')">Onayla</button>
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

    <KayitModal v-if="modalAcik" baslik="Yeni Mal Kabul" @kapat="modalAcik = false">
      <form class="flex flex-col gap-4" @submit.prevent="kaydet">
        <label class="etiket">
          Sipariş (onaylı/kısmi teslim)
          <select v-model.number="form.siparis" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="s in siparisler" :key="s.id" :value="s.id">{{ s.siparis_no }} — {{ s.tedarikci_adi }}</option>
          </select>
        </label>
        <label class="etiket">
          Depo
          <select v-model.number="form.depo" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="d in depolar" :key="d.id" :value="d.id">{{ d.kod }} — {{ d.ad }}</option>
          </select>
        </label>
        <label class="etiket">Açıklama<textarea v-model="form.aciklama" rows="2" class="alan"></textarea></label>

        <div class="rounded-lg border border-surface-200 p-3">
          <div class="mb-2 flex items-center justify-between">
            <p class="text-xs font-semibold uppercase tracking-wider text-surface-500">Kalemler (sipariş kalemi · kabul · red)</p>
            <button type="button" class="ikincil-dugme px-2 py-1 text-xs" @click="satirEkle">+ Kalem</button>
          </div>
          <p v-if="!seciliSiparis" class="text-xs text-surface-400">Önce sipariş seçin.</p>
          <div v-for="(s, i) in satirlar" :key="i" class="mt-2 grid grid-cols-[1fr_1fr_1fr_auto] items-end gap-2">
            <label class="etiket">
              Sipariş Kalemi
              <select v-model.number="s.siparis_kalemi" class="alan">
                <option :value="0">— Seçiniz —</option>
                <option v-for="k in seciliSiparis?.kalemler ?? []" :key="k.id" :value="k.id">
                  {{ k.malzeme_kodu }} · {{ k.miktar }} {{ k.birim }}
                </option>
              </select>
            </label>
            <label class="etiket">Kabul<input v-model="s.kabul_miktari" type="text" inputmode="decimal" class="alan" /></label>
            <label class="etiket">Red<input v-model="s.red_miktari" type="text" inputmode="decimal" class="alan" /></label>
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
  </div>
</template>
