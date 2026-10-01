<script setup lang="ts">
/**
 * Hakedişler — dönemsel hakediş CRUD + satır üretimi + onay akışı.
 * Onay: backend Cari Hareket + Muhasebe Fişi üretir (çift taraflı, zarf korunur).
 * Fiziksel silme yok: taslak → iptal (backend destroy iptale çeker).
 * Backend: /api/v1/construction/hakedisler/ (+ /satirlari-olustur/, /onayla/).
 */
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { get, hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { Sayfali } from '@/types/api'
import {
  HAKEDIS_DURUMLARI,
  type Hakedis,
  type HakedisDurumu,
  type HakedisSatiri,
  type Poz,
  type Proje,
} from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

/** Cari kartı (sadece liste için gereken alanlar). */
interface CariSecim {
  id: number
  ad: string
}

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))

const L = useKayitListesi<Hakedis>('/construction/hakedisler/')
const projeler = ref<Proje[]>([])
const pozlar = ref<Poz[]>([])
const cariler = ref<CariSecim[]>([])

const para = (v: string): string => Number(v).toLocaleString('tr-TR', { minimumFractionDigits: 2 })
const miktarStr = (v: string): string => Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 4 })
const cariAdi = (id: number | null): string =>
  id === null ? '—' : cariler.value.find((c) => c.id === id)?.ad ?? `#${id}`
const durumSinifi = (d: HakedisDurumu): string =>
  d === 'onaylandi' ? 'text-success-700' : d === 'iptal' ? 'text-error-600' : 'text-surface-500'

/* --- Modal (kayıt + satırlar) --- */
const modalAcik = ref(false)
const duzenlenen = ref<Hakedis | null>(null)
const kaydediliyor = ref(false)
const formHata = ref('')
const form = ref({ proje: null as number | null, donem: '', cari: null as number | null, aciklama: '' })
const satirlar = ref<HakedisSatiri[]>([])

function yeniAc(): void {
  duzenlenen.value = null
  form.value = { proje: null, donem: new Date().toISOString().slice(0, 7), cari: null, aciklama: '' }
  satirlar.value = []
  formHata.value = ''
  modalAcik.value = true
}

function duzenleAc(k: Hakedis): void {
  duzenlenen.value = k
  form.value = { proje: k.proje, donem: k.donem, cari: k.cari, aciklama: k.aciklama || '' }
  satirlar.value = k.satirlar.map((s) => ({ poz: s.poz, miktar: s.miktar, birim_fiyat: s.birim_fiyat }))
  formHata.value = ''
  modalAcik.value = true
}

function satirEkle(): void {
  satirlar.value.push({ poz: 0, miktar: '', birim_fiyat: '' })
}

function satirSil(i: number): void {
  satirlar.value.splice(i, 1)
}

/** Poz planlarındaki gerçekleşen metrajdan satır üretir (yalnız taslak). */
async function planlardanSatirUret(k: Hakedis): Promise<void> {
  if (k.durum !== 'taslak') return
  L.hata.value = ''
  try {
    const sonuc = await insaatApi.hakedisSatirlariUret(k.id)
    if (duzenlenen.value?.id === k.id) {
      satirlar.value = sonuc.hakedis.satirlar.map((s) => ({
        poz: s.poz, miktar: s.miktar, birim_fiyat: s.birim_fiyat,
      }))
    }
  } catch (bilinmeyen) {
    L.hata.value = hataMesaji(bilinmeyen)
  }
}

async function kaydet(): Promise<void> {
  formHata.value = ''
  if (!form.value.proje) {
    formHata.value = 'Proje seçimi zorunludur.'
    return
  }
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(form.value.donem)) {
    formHata.value = 'Dönem YYYY-AA biçiminde olmalıdır (örn. 2026-03).'
    return
  }
  const temizSatirlar = satirlar.value.filter((s) => s.poz > 0 && Number(s.miktar) > 0 && Number(s.birim_fiyat) > 0)
  if (temizSatirlar.length !== satirlar.value.length) {
    formHata.value = 'Her satırda poz seçili ve miktar/birim fiyat 0’dan büyük olmalıdır.'
    return
  }
  const payload = {
    proje: form.value.proje,
    donem: form.value.donem,
    cari: form.value.cari,
    aciklama: form.value.aciklama.trim(),
    satirlar: temizSatirlar,
  }
  kaydediliyor.value = true
  try {
    if (duzenlenen.value) {
      await insaatApi.hakedisler.guncelle(duzenlenen.value.id, payload)
    } else {
      await insaatApi.hakedisler.olustur(payload)
    }
    modalAcik.value = false
    await L.yukle()
  } catch (bilinmeyen) {
    formHata.value = hataMesaji(bilinmeyen)
  } finally {
    kaydediliyor.value = false
  }
}

/** Onay: Cari Hareket + Muhasebe Fişi üretilir (tersine çevrilemez). */
async function onayla(k: Hakedis): Promise<void> {
  if (!window.confirm(`${k.proje_kodu ?? ''} / ${k.donem} hakedişi onaylansın mı? Onayda Cari Hareket ve Muhasebe Fişi üretilir.`)) {
    return
  }
  L.hata.value = ''
  try {
    await insaatApi.hakedisOnayla(k.id)
    await L.yukle()
  } catch (bilinmeyen) {
    L.hata.value = hataMesaji(bilinmeyen)
  }
}

/** Fiziksel silme yok — taslak iptale çekilir (onaylı hakedişte backend 400 döner). */
async function iptalEt(k: Hakedis): Promise<void> {
  if (!window.confirm(`${k.proje_kodu ?? ''} / ${k.donem} hakedişi iptal edilsin mi?`)) {
    return
  }
  L.hata.value = ''
  try {
    await insaatApi.hakedisIptal(k.id)
    await L.yukle()
  } catch (bilinmeyen) {
    L.hata.value = hataMesaji(bilinmeyen)
  }
}

onMounted(async () => {
  try {
    projeler.value = await tumunuGetir(insaatApi.projeler.liste)
    pozlar.value = await tumunuGetir(insaatApi.pozlar.liste)
    // Cari listesi (taşeron/yüklenici seçimi) — sayfalı kaynağı gez.
    const hepsi: CariSecim[] = []
    for (let sayfa = 1; sayfa <= 20; sayfa += 1) {
      const veri = await get<Sayfali<CariSecim>>('/cari/cariler/', { page: sayfa })
      hepsi.push(...veri.results)
      if (!veri.next) break
    }
    cariler.value = hepsi
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
        <p class="text-sm font-medium text-primary-700">İnşaat</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Hakedişler</h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="yeniAc()">+ Yeni Hakediş</button>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Proje kodu veya dönem ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.durum" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm durumlar</option>
        <option v-for="(e, k) in HAKEDIS_DURUMLARI" :key="k" :value="k">{{ e }}</option>
      </select>
    </div>

    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>

    <VeriTablosu
      :basliklar="['Proje', 'Dönem', 'Cari', 'Durum', 'Toplam (₺)', 'Muhasebe', yazabilir ? 'İşlem' : '']"
      :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0"
    >
      <template v-for="k in L.kayitlar.value" :key="k.id">
        <tr class="transition-colors hover:bg-surface-100/60">
          <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium">{{ k.proje_kodu ?? `#${k.proje}` }}</td>
          <td class="whitespace-nowrap px-4 py-3">{{ k.donem }}</td>
          <td class="max-w-xs truncate px-4 py-3">{{ cariAdi(k.cari) }}</td>
          <td class="whitespace-nowrap px-4 py-3 font-medium" :class="durumSinifi(k.durum)">
            {{ HAKEDIS_DURUMLARI[k.durum] }}
          </td>
          <td class="whitespace-nowrap px-4 py-3 text-right">{{ para(k.toplam_tutar) }}</td>
          <td class="whitespace-nowrap px-4 py-3 text-xs text-surface-500">
            <template v-if="k.muhasebe_fisi">Fiş #{{ k.muhasebe_fisi }} · Hareket #{{ k.cari_hareket }}</template>
            <template v-else>—</template>
          </td>
          <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
            <div class="flex items-center gap-2">
              <button
                v-if="k.durum === 'taslak'"
                type="button"
                class="text-sm font-medium text-primary-700 hover:underline"
                title="Poz planlarındaki gerçekleşen metrajdan satır üret"
                @click="planlardanSatirUret(k)"
              >Satır Üret</button>
              <button
                v-if="k.durum === 'taslak'"
                type="button"
                class="text-sm font-medium text-primary-700 hover:underline"
                @click="duzenleAc(k)"
              >Düzenle</button>
              <button
                v-if="k.durum === 'taslak'"
                type="button"
                class="text-sm font-medium text-success-700 hover:underline"
                @click="onayla(k)"
              >Onayla</button>
              <button
                v-if="k.durum !== 'onaylandi'"
                type="button"
                class="text-sm font-medium text-error-600 hover:underline"
                @click="iptalEt(k)"
              >İptal</button>
            </div>
          </td>
        </tr>
        <tr v-if="k.satirlar.length > 0" class="bg-surface-100/40">
          <td :colspan="yazabilir ? 7 : 6" class="px-4 py-2">
            <p class="mb-1 text-xs font-semibold uppercase tracking-wider text-surface-400">
              Satırlar — {{ k.satirlar.length }} poz, toplam {{ para(k.toplam_tutar) }} ₺
            </p>
            <p class="text-xs leading-relaxed text-surface-500">
              <span v-for="s in k.satirlar" :key="s.poz" class="mr-3 inline-block whitespace-nowrap">
                <span class="font-mono">{{ s.poz_no ?? `#${s.poz}` }}</span>
                · {{ miktarStr(s.miktar) }} × {{ para(s.birim_fiyat) }} = {{ para(s.satir_tutar ?? '0') }} ₺
              </span>
            </p>
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

    <KayitModal
      v-if="modalAcik"
      :baslik="duzenlenen ? 'Hakedişi Düzenle' : 'Yeni Hakediş'"
      @kapat="modalAcik = false"
    >
      <form class="flex flex-col gap-4" @submit.prevent="kaydet">
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">
            Proje
            <select v-model.number="form.proje" class="alan">
              <option :value="null">— Seçiniz —</option>
              <option v-for="p in projeler" :key="p.id" :value="p.id">{{ p.proje_kodu }} — {{ p.ad }}</option>
            </select>
          </label>
          <label class="etiket">Dönem<input v-model="form.donem" type="month" class="alan" /></label>
        </div>
        <label class="etiket">
          Yüklenici / Taşeron (Cari)
          <select v-model.number="form.cari" class="alan">
            <option :value="null">— Seçiniz —</option>
            <option v-for="c in cariler" :key="c.id" :value="c.id">{{ c.ad }}</option>
          </select>
        </label>
        <label class="etiket">Açıklama<textarea v-model="form.aciklama" rows="2" class="alan"></textarea></label>

        <div class="rounded-lg border border-surface-200 p-3">
          <div class="mb-2 flex items-center justify-between">
            <p class="text-xs font-semibold uppercase tracking-wider text-surface-500">
              Satırlar (poz · miktar · birim fiyat)
            </p>
            <button type="button" class="ikincil-dugme px-2 py-1 text-xs" @click="satirEkle">+ Satır</button>
          </div>
          <p v-if="satirlar.length === 0" class="text-xs text-surface-400">
            Satır yok — kaydettikten sonra listede "Satır Üret" ile poz planlarından otomatik üretebilirsiniz.
          </p>
          <div v-for="(s, i) in satirlar" :key="i" class="mt-2 grid grid-cols-[1fr_1fr_1fr_auto] items-end gap-2">
            <label class="etiket">
              Poz
              <select v-model.number="s.poz" class="alan">
                <option :value="0">— Seçiniz —</option>
                <option v-for="p in pozlar" :key="p.id" :value="p.id">{{ p.poz_no }} — {{ p.ad }}</option>
              </select>
            </label>
            <label class="etiket">Miktar<input v-model="s.miktar" type="text" inputmode="decimal" class="alan" /></label>
            <label class="etiket">Birim Fiyat (₺)<input v-model="s.birim_fiyat" type="text" inputmode="decimal" class="alan" /></label>
            <button type="button" class="text-sm font-medium text-error-600 hover:underline" @click="satirSil(i)">Sil</button>
          </div>
        </div>

        <p class="text-xs text-surface-500">
          Onayda: cariye <span class="font-medium">borç</span> Cari Hareketi ve
          740/120 (çift taraflı) Muhasebe Fişi otomatik üretilir; onay sonrası satırlar kilitlenir.
        </p>
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
