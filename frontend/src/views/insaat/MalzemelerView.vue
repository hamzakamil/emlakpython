<script setup lang="ts">
import { computed, onMounted } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import ExcelAktarim, { type ExcelSutun } from '@/components/ExcelAktarim.vue'
import { insaatApi } from '@/services/insaatApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { Malzeme } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const L = useKayitListesi<Malzeme>('/construction/malzemeler/')
const excelSutunlari: ExcelSutun[] = [
  { key: 'malzeme_kodu', label: 'Kod', required: true }, { key: 'ad', label: 'Ad', required: true },
  { key: 'birim', label: 'Birim', required: true }, { key: 'ts_no', label: 'TS No' },
]
async function excelAl(rows: Record<string, unknown>[]): Promise<void> {
  try {
    for (const row of rows) await insaatApi.malzemeler.olustur(row)
    await L.yukle()
    L.hata.value = ''
  } catch (error) {
    L.hata.value = `Excel içe aktarma kısmi olarak tamamlandı: ${error instanceof Error ? error.message : 'geçersiz veri.'}`
    await L.yukle()
  }
}
interface F { malzeme_kodu: string; ad: string; birim: string; ts_no: string }
const Fm = useKayitFormu<Malzeme, F>(
  insaatApi.malzemeler,
  () => ({ malzeme_kodu: '', ad: '', birim: '', ts_no: '' }),
  (k) => ({ malzeme_kodu: k.malzeme_kodu, ad: k.ad, birim: k.birim, ts_no: k.ts_no || '' }),
  (f) => ({ malzeme_kodu: f.malzeme_kodu.trim(), ad: f.ad.trim(), birim: f.birim.trim(), ts_no: f.ts_no.trim() }),
  (f) => (!f.malzeme_kodu.trim() || !f.ad.trim() || !f.birim.trim() ? 'Kod, ad ve birim zorunludur.' : ''),
)
onMounted(L.yukle)
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat / Kütüphane</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Malzemeler</h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Kayıt</button>
    </div>
    <div class="mb-4"><ExcelAktarim :rows="L.kayitlar.value as unknown as Record<string, unknown>[]" :columns="excelSutunlari" filename="malzemeler" @imported="excelAl" /></div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Kod, ad veya TS no ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.is_active" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tümü</option>
        <option :value="true">Aktif</option>
        <option :value="false">Pasif</option>
      </select>
    </div>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <VeriTablosu :basliklar="['Kod', 'Ad', 'Birim', 'TS No', 'Durum', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="k in L.kayitlar.value" :key="k.id" class="transition-colors hover:bg-surface-100/60">
        <td class="px-4 py-3 font-medium">{{ k.malzeme_kodu }}</td>
        <td class="px-4 py-3">{{ k.ad }}</td>
        <td class="px-4 py-3">{{ k.birim }}</td>
        <td class="px-4 py-3">{{ k.ts_no || '—' }}</td>
        <td class="px-4 py-3"><span class="durum-rozot" :class="k.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">{{ k.is_active ? 'Aktif' : 'Pasif' }}</span></td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3"><button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(k)">Düzenle</button></td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Kaydı Düzenle' : 'Yeni Kayıt'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Malzeme Kodu<input v-model="Fm.form.value.malzeme_kodu" type="text" maxlength="30" placeholder="örn. DEM-001" class="alan" /></label>
          <label class="etiket">Ölçü Birimi<input v-model="Fm.form.value.birim" type="text" maxlength="20" placeholder="örn. KG" class="alan" /></label>
        </div>
        <label class="etiket">Malzeme Adı<input v-model="Fm.form.value.ad" type="text" maxlength="255" placeholder="örn. İnşaat demiri" class="alan" /></label>
        <label class="etiket">TS / TS EN Referansı<input v-model="Fm.form.value.ts_no" type="text" maxlength="100" placeholder="örn. TS 708" class="alan" /></label>
        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">{{ Fm.kaydediliyor.value ? 'Kaydediliyor…' : 'Kaydet' }}</button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>
