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
import type { YapiSinifi } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const L = useKayitListesi<YapiSinifi>('/construction/yapi-sinifi-birim-maliyetleri/')
const excelSutunlari: ExcelSutun[] = [
  { key: 'sinif_kodu', label: 'Sınıf', required: true }, { key: 'yil', label: 'Yıl', required: true },
  { key: 'birim_maliyet', label: 'Birim Maliyet', required: true },
]
async function excelAl(rows: Record<string, unknown>[]): Promise<void> {
  try {
    for (const row of rows) await insaatApi.yapiSinifi.olustur(row)
    await L.yukle()
    L.hata.value = ''
  } catch (error) {
    L.hata.value = `Excel içe aktarma kısmi olarak tamamlandı: ${error instanceof Error ? error.message : 'geçersiz veri.'}`
    await L.yukle()
  }
}
interface F { sinif_kodu: string; yil: number; birim_maliyet: string }
const Fm = useKayitFormu<YapiSinifi, F>(
  insaatApi.yapiSinifi,
  () => ({ sinif_kodu: '', yil: new Date().getFullYear(), birim_maliyet: '' }),
  (k) => ({ sinif_kodu: k.sinif_kodu, yil: k.yil, birim_maliyet: k.birim_maliyet }),
  (f) => ({ sinif_kodu: f.sinif_kodu.trim().toLocaleUpperCase('tr-TR'), yil: f.yil, birim_maliyet: f.birim_maliyet }),
  (f) => (!f.sinif_kodu.trim() || !f.yil || !f.birim_maliyet ? 'Sınıf kodu, yıl ve birim maliyet zorunludur.' : ''),
)
const para = (v: string): string => Number(v).toLocaleString('tr-TR', { minimumFractionDigits: 2 })
onMounted(L.yukle)
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Yapı Sınıfı Birim Maliyetleri</h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Kayıt</button>
    </div>
    <div class="mb-4"><ExcelAktarim :rows="L.kayitlar.value as unknown as Record<string, unknown>[]" :columns="excelSutunlari" filename="yapi-sinifi" @imported="excelAl" /></div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Sınıf kodu ile ara (örn. IV-A)…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
    </div>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <VeriTablosu :basliklar="['Sınıf', 'Yıl', 'Birim Maliyet (₺/m²)', 'Durum', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="k in L.kayitlar.value" :key="k.id" class="transition-colors hover:bg-surface-100/60">
        <td class="px-4 py-3 font-medium">{{ k.sinif_kodu }}</td>
        <td class="px-4 py-3">{{ k.yil }}</td>
        <td class="px-4 py-3 text-right font-mono">{{ para(k.birim_maliyet) }}</td>
        <td class="px-4 py-3"><span class="durum-rozot" :class="k.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">{{ k.is_active ? 'Aktif' : 'Arşiv' }}</span></td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3"><button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(k)">Düzenle</button></td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Kaydı Düzenle' : 'Yeni Kayıt'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <label class="etiket">Sınıf Kodu (4A girişi IV-A olur)<input v-model="Fm.form.value.sinif_kodu" type="text" placeholder="örn. IV-A" class="alan" /></label>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Tebliğ Yılı<input v-model.number="Fm.form.value.yil" type="number" min="2000" max="2100" class="alan" /></label>
          <label class="etiket">Birim Maliyet (₺)<input v-model="Fm.form.value.birim_maliyet" type="text" inputmode="decimal" placeholder="örn. 12500.00" class="alan" /></label>
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
