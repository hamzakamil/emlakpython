<script setup lang="ts">
/**
 * FAZ 3B — Stok Hareketleri: salt okunur liste (depo eksenli bakiye hareketleri).
 * Kayıtlar mal kabul onayıyla üretilir; doğrudan yazma/silme kapalı (backend 400).
 * Backend: /api/v1/purchase-stok-hareketleri/.
 */
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { ApiHatasi } from '@/services/zarf'
import axios from 'axios'
import { satinAlmaApi } from '@/services/satinAlmaApi'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import type { Depo, MalKabul, MalKabulKalemi, StokHareketi } from '@/types/satinAlma'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import type { Mahal, Malzeme, Proje } from '@/types/insaat'
import { useAuthStore } from '@/stores/auth'
import { satinAlmaYazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => satinAlmaYazabilirMi(auth.kullanici?.role))
const L = useKayitListesi<StokHareketi>('/purchase-stok-hareketleri/')
const depolar = ref<Depo[]>([])
const malzemeler = ref<Malzeme[]>([])
const projeler = ref<Proje[]>([])
const mahaller = ref<Mahal[]>([])
const malKabuller = ref<MalKabul[]>([])
const iadeKalemleri = ref<MalKabulKalemi[]>([])

type IslemTuru = 'transfer' | 'tuketim' | 'iade'
const modalAcik = ref(false)
const islemTuru = ref<IslemTuru>('transfer')
const formHata = ref('')
const basari = ref('')
const kaydediliyor = ref(false)
const form = ref({
  kaynak_depo: null as number | null,
  hedef_depo: null as number | null,
  depo: null as number | null,
  malzeme: null as number | null,
  miktar: '',
  proje: null as number | null,
  mahal: null as number | null,
  mal_kabul: null as number | null,
  mal_kabul_kalemi: null as number | null,
  aciklama: '',
})

const para = (v: string): string => Number(v).toLocaleString('tr-TR', { minimumFractionDigits: 2 })

function islemAc(tur: IslemTuru): void {
  islemTuru.value = tur
  formHata.value = ''; basari.value = ''
  form.value = {
    kaynak_depo: null, hedef_depo: null, depo: depolar.value[0]?.id || null,
    malzeme: null, miktar: '', proje: null, mahal: null,
    mal_kabul: null, mal_kabul_kalemi: null, aciklama: '',
  }
  iadeKalemleri.value = []
  modalAcik.value = true
}

async function iadeKalemYukle(): Promise<void> {
  iadeKalemleri.value = []
  form.value.mal_kabul_kalemi = null
  if (!form.value.mal_kabul) return
  try {
    iadeKalemleri.value = await tumunuGetir(satinAlmaApi.malKabulKalemleri.liste, { mal_kabul: form.value.mal_kabul })
  } catch (bilinmeyen) { formHata.value = hataMesaji(bilinmeyen) }
}

/** Backend stringleşmiş validasyon detayını anlaşılır Türkçe'ye çevirir (salt-okuma). */
function islemHataMesaji(bilinmeyen: unknown): string {
  let detay: unknown = null
  if (axios.isAxiosError(bilinmeyen)) {
    const govde = bilinmeyen.response?.data as { errors?: Record<string, unknown> } | undefined
    detay = govde?.errors?.detail
  } else if (bilinmeyen instanceof ApiHatasi && bilinmeyen.hatalar && typeof bilinmeyen.hatalar === 'object') {
    detay = (bilinmeyen.hatalar as Record<string, unknown>).detail
  }
  if (typeof detay === 'string') {
    if (detay.includes('Kümülatif iade')) return 'Kümülatif iade, kabul miktarını aşamaz.'
    if (detay.includes('Yetersiz stok')) {
      const eslesme = detay.match(/Yetersiz stok[^']*/)
      return eslesme ? eslesme[0] + '.' : 'Yetersiz stok.'
    }
    if (detay.includes('cari kart')) return 'Tedarikçiye cari kart bağlanmalıdır.'
  }
  return hataMesaji(bilinmeyen)
}

async function kaydet(): Promise<void> {
  formHata.value = ''; basari.value = ''
  const miktar = Number(form.value.miktar)
  if (!form.value.malzeme && islemTuru.value !== 'iade') { formHata.value = 'Malzeme seçimi zorunludur.'; return }
  if (!(miktar > 0)) { formHata.value = 'Miktar sıfırdan büyük olmalıdır.'; return }
  if (islemTuru.value === 'transfer' && (!form.value.kaynak_depo || !form.value.hedef_depo)) { formHata.value = 'Kaynak ve hedef depo zorunludur.'; return }
  if (islemTuru.value === 'transfer' && form.value.kaynak_depo === form.value.hedef_depo) { formHata.value = 'Kaynak ve hedef depo farklı olmalıdır.'; return }
  if (islemTuru.value === 'tuketim' && (!form.value.depo || !form.value.proje || !form.value.mahal)) { formHata.value = 'Depo, proje ve mahal zorunludur.'; return }
  if (islemTuru.value === 'iade' && !form.value.mal_kabul_kalemi) { formHata.value = 'İade edilecek kabul kalemi zorunludur.'; return }
  kaydediliyor.value = true
  try {
    if (islemTuru.value === 'transfer') {
      await satinAlmaApi.stokHareketleri.transferOlustur({
        kaynak_depo: form.value.kaynak_depo, hedef_depo: form.value.hedef_depo,
        malzeme: form.value.malzeme, miktar: form.value.miktar, aciklama: form.value.aciklama,
      })
      basari.value = 'Transfer oluşturuldu (çıkış + giriş).'
    } else if (islemTuru.value === 'tuketim') {
      await satinAlmaApi.stokHareketleri.tuketimOlustur({
        depo: form.value.depo, malzeme: form.value.malzeme, miktar: form.value.miktar,
        proje: form.value.proje, mahal: form.value.mahal, aciklama: form.value.aciklama,
      })
      basari.value = 'Tüketim kaydedildi.'
    } else {
      const yanit = await satinAlmaApi.stokHareketleri.iadeOlustur({
        mal_kabul_kalemi: form.value.mal_kabul_kalemi, miktar: form.value.miktar, aciklama: form.value.aciklama,
      })
      basari.value = `İade kaydedildi.${yanit.iade_fatura_no ? ` İade faturası: ${yanit.iade_fatura_no}.` : ''}`
    }
    await L.yukle()
  } catch (bilinmeyen) { formHata.value = islemHataMesaji(bilinmeyen) } finally { kaydediliyor.value = false }
}

onMounted(async () => {
  try {
    const [d, m, p, mh, mk] = await Promise.all([
      tumunuGetir(satinAlmaApi.depolar.liste),
      tumunuGetir(insaatApi.malzemeler.liste, { is_active: true }),
      tumunuGetir(insaatApi.projeler.liste, { is_active: true }),
      tumunuGetir(insaatApi.mahaller.liste),
      tumunuGetir(satinAlmaApi.malKabuller.liste),
    ])
    depolar.value = d; malzemeler.value = m; projeler.value = p; mahaller.value = mh; malKabuller.value = mk
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
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Stok Hareketleri</h1>
      </div>
      <div v-if="yazabilir" class="flex flex-wrap gap-2">
        <button type="button" class="ikincil-dugme" @click="islemAc('transfer')">Transfer</button>
        <button type="button" class="ikincil-dugme" @click="islemAc('tuketim')">Tüketim</button>
        <button type="button" class="ikincil-dugme" @click="islemAc('iade')">İade</button>
      </div>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Malzeme veya depo kodu ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.hareket_tipi" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm hareketler</option>
        <option value="giris">Giriş</option>
        <option value="cikis">Çıkış</option>
      </select>
    </div>

    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <p class="mb-4 text-xs text-surface-500">Hareketler mal kabul onayıyla otomatik üretilir; doğrudan kayıt/silme kapalıdır. Transfer, tüketim ve iade işlemleri yukarıdaki butonlarla yapılır.</p>

    <VeriTablosu
      :basliklar="['Tarih', 'Depo', 'Malzeme', 'Yön', 'Miktar', 'Birim Maliyet']"
      :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0"
    >
      <template v-for="k in L.kayitlar.value" :key="k.id">
        <tr class="transition-colors hover:bg-surface-100/60">
          <td class="whitespace-nowrap px-4 py-3">{{ k.tarih }}</td>
          <td class="whitespace-nowrap px-4 py-3 font-mono text-xs">{{ k.depo_kodu ?? `#${k.depo}` }}</td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.malzeme_adi ?? `#${k.malzeme}` }}</td>
          <td class="whitespace-nowrap px-4 py-3 font-medium">{{ k.hareket_tipi === 'giris' ? 'Giriş' : 'Çıkış' }}</td>
          <td class="whitespace-nowrap px-4 py-3 text-right">{{ k.miktar }} {{ k.birim }}</td>
          <td class="whitespace-nowrap px-4 py-3 text-right">{{ para(k.maliyet) }}</td>
        </tr>
      </template>
    </VeriTablosu>
    <Sayfalama
      :sayfa="L.sayfa.value"
      :toplam="L.toplam.value"
      :yukleniyor="L.yukleniyor.value"
      @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }"
    />
    <KayitModal v-if="modalAcik" :baslik="islemTuru === 'transfer' ? 'Depolar Arası Transfer' : islemTuru === 'tuketim' ? 'Projeye Tüketim' : 'Tedarikçiye İade'" @kapat="modalAcik = false">
      <form class="flex flex-col gap-4" @submit.prevent="kaydet">
        <template v-if="islemTuru === 'transfer'">
          <div class="grid grid-cols-2 gap-4">
            <label class="etiket">Kaynak Depo<select v-model.number="form.kaynak_depo" class="alan"><option :value="null">Seçin</option><option v-for="x in depolar" :key="x.id" :value="x.id">{{ x.kod }} — {{ x.ad }}</option></select></label>
            <label class="etiket">Hedef Depo<select v-model.number="form.hedef_depo" class="alan"><option :value="null">Seçin</option><option v-for="x in depolar" :key="x.id" :value="x.id">{{ x.kod }} — {{ x.ad }}</option></select></label>
          </div>
          <label class="etiket">Malzeme<select v-model.number="form.malzeme" class="alan"><option :value="null">Seçin</option><option v-for="x in malzemeler" :key="x.id" :value="x.id">{{ x.malzeme_kodu }} — {{ x.ad }}</option></select></label>
        </template>
        <template v-else-if="islemTuru === 'tuketim'">
          <div class="grid grid-cols-2 gap-4">
            <label class="etiket">Depo<select v-model.number="form.depo" class="alan"><option :value="null">Seçin</option><option v-for="x in depolar" :key="x.id" :value="x.id">{{ x.kod }} — {{ x.ad }}</option></select></label>
            <label class="etiket">Malzeme<select v-model.number="form.malzeme" class="alan"><option :value="null">Seçin</option><option v-for="x in malzemeler" :key="x.id" :value="x.id">{{ x.malzeme_kodu }} — {{ x.ad }}</option></select></label>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <label class="etiket">Proje<select v-model.number="form.proje" class="alan"><option :value="null">Seçin</option><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} — {{ x.ad }}</option></select></label>
            <label class="etiket">Mahal<select v-model.number="form.mahal" class="alan"><option :value="null">Seçin</option><option v-for="x in mahaller.filter((m) => !form.proje || m.proje === form.proje)" :key="x.id" :value="x.id">{{ x.mahal_no }} — {{ x.mahal_adi }}</option></select></label>
          </div>
        </template>
        <template v-else>
          <label class="etiket">Mal Kabul Belgesi<select v-model.number="form.mal_kabul" class="alan" @change="iadeKalemYukle()"><option :value="null">Seçin</option><option v-for="x in malKabuller" :key="x.id" :value="x.id">{{ x.belge_no }}</option></select></label>
          <label class="etiket">Kabul Kalemi<select v-model.number="form.mal_kabul_kalemi" class="alan"><option :value="null">Önce belge seçin</option><option v-for="x in iadeKalemleri" :key="x.id" :value="x.id">{{ x.malzeme_adi || ('#' + x.malzeme) }} — kabul {{ x.kabul_miktari }}</option></select></label>
          <p class="text-xs text-surface-500">İade, stok çıkışı ile birlikte iade faturası ve fişi üretir.</p>
        </template>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Miktar<input v-model="form.miktar" type="number" min="0.0001" step="0.0001" class="alan" /></label>
          <label class="etiket">Açıklama<input v-model="form.aciklama" type="text" maxlength="255" class="alan" /></label>
        </div>
        <p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p>
        <p v-if="basari" class="rounded-lg border border-success-200 bg-success-50 px-4 py-3 text-sm text-success-700" role="status">{{ basari }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="modalAcik = false">Vazgeç</button>
          <button type="submit" :disabled="kaydediliyor" class="birincil-dugme">{{ kaydediliyor ? 'Kaydediliyor…' : 'Kaydet' }}</button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>
