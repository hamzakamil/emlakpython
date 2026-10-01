<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { satinAlmaApi } from '@/services/satinAlmaApi'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { muhasebeApi } from '@/services/muhasebeApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { StokHesapEsleme } from '@/types/satinAlma'
import type { HesapPlani } from '@/types/muhasebe'
import type { Malzeme } from '@/types/insaat'
import { satinAlmaYazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => satinAlmaYazabilirMi(auth.kullanici?.role))
const L = useKayitListesi<StokHesapEsleme>('/purchase-stok-hesap-esleme/')
const malzemeler = ref<Malzeme[]>([])
const hesaplar = ref<HesapPlani[]>([])
const TUR_ETIKET: Record<string, string> = { stok: 'Stok Hesabı', kdv: 'KDV Hesabı' }
interface F { malzeme: number | null; hesap_turu: string; hesap: number | null }
const Fm = useKayitFormu<StokHesapEsleme, F>(
  satinAlmaApi.stokHesapEsleme,
  () => ({ malzeme: null, hesap_turu: 'stok', hesap: null }),
  (k) => ({ malzeme: k.malzeme, hesap_turu: k.hesap_turu, hesap: k.hesap }),
  (f) => ({ malzeme: f.malzeme, hesap_turu: f.hesap_turu, hesap: f.hesap }),
  (f) => (!f.hesap ? 'Hesap seçimi zorunludur.' : !['stok', 'kdv'].includes(f.hesap_turu) ? 'Hesap türü stok veya kdv olmalıdır.' : ''),
)
function filtreUygula(): void { L.sayfa.value = 1; void L.yukle() }
onMounted(async () => {
  await L.yukle()
  try {
    malzemeler.value = await tumunuGetir(insaatApi.malzemeler.liste)
    hesaplar.value = await tumunuGetir(muhasebeApi.hesapPlani.liste, { is_active: true })
  } catch { /* seçim listeleri boş kalır, kayıt yine listelenir */ }
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">Satın Alma / Ayarlar</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Stok Hesap Eşleme</h1>
        <p class="mt-1 text-sm text-surface-500">Malzeme boşsa tenant varsayılanıdır; muhasebeleşmede malzemeye özel → varsayılan sırası kullanılır.</p>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Kayıt</button>
    </div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Hesap/malzeme kodu veya adı ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.hesap_turu" class="alan" @change="filtreUygula()">
        <option :value="undefined">Tüm türler</option>
        <option value="stok">Stok Hesabı</option>
        <option value="kdv">KDV Hesabı</option>
      </select>
      <select v-model="L.filtreler.value.is_active" class="alan" @change="filtreUygula()">
        <option :value="undefined">Tümü</option>
        <option :value="true">Aktif</option>
        <option :value="false">Pasif</option>
      </select>
    </div>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <VeriTablosu :basliklar="['Malzeme', 'Tür', 'Hesap', 'Durum', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="k in L.kayitlar.value" :key="k.id" class="transition-colors hover:bg-surface-100/60">
        <td class="px-4 py-3 font-medium">{{ k.malzeme_kodu ? `${k.malzeme_kodu} — ${k.malzeme_adi}` : 'VARSAYILAN' }}</td>
        <td class="px-4 py-3">{{ TUR_ETIKET[k.hesap_turu] || k.hesap_turu }}</td>
        <td class="px-4 py-3">{{ k.hesap_kodu }} — {{ k.hesap_adi }}</td>
        <td class="px-4 py-3"><span class="durum-rozot" :class="k.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">{{ k.is_active ? 'Aktif' : 'Pasif' }}</span></td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3"><button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(k)">Düzenle</button></td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Kaydı Düzenle' : 'Yeni Kayıt'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <label class="etiket">Malzeme (boş = tenant varsayılanı)
          <select v-model.number="Fm.form.value.malzeme" class="alan">
            <option :value="null">Varsayılan</option>
            <option v-for="x in malzemeler" :key="x.id" :value="x.id">{{ x.malzeme_kodu }} — {{ x.ad }}</option>
          </select>
        </label>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Hesap Türü
            <select v-model="Fm.form.value.hesap_turu" class="alan">
              <option value="stok">Stok Hesabı</option>
              <option value="kdv">KDV Hesabı</option>
            </select>
          </label>
          <label class="etiket">Hesap
            <select v-model.number="Fm.form.value.hesap" class="alan">
              <option :value="null">Hesap seçin</option>
              <option v-for="x in hesaplar" :key="x.id" :value="x.id">{{ x.kod }} — {{ x.ad }}</option>
            </select>
          </label>
        </div>
        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">{{ Fm.kaydediliyor.value ? 'Kaydediliyor…' : 'Kaydet' }}</button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>
