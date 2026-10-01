<script setup lang="ts">
import { computed, onMounted } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { finansApi } from '@/services/finansApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { VergiProfili } from '@/types/fatura'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const L = useKayitListesi<VergiProfili>('/finance/vergi-profilleri/')
interface F { kod: string; ad: string; kdv_orani: string; tevkifat_orani: string; stopaj_orani: string }
const oranKontrol = (v: string): boolean => v !== '' && Number(v) >= 0 && Number(v) <= 100
const Fm = useKayitFormu<VergiProfili, F>(
  finansApi.vergiProfilleri,
  () => ({ kod: '', ad: '', kdv_orani: '20', tevkifat_orani: '0', stopaj_orani: '0' }),
  (k) => ({ kod: k.kod, ad: k.ad, kdv_orani: k.kdv_orani, tevkifat_orani: k.tevkifat_orani, stopaj_orani: k.stopaj_orani }),
  (f) => ({ kod: f.kod.trim(), ad: f.ad.trim(), kdv_orani: f.kdv_orani, tevkifat_orani: f.tevkifat_orani, stopaj_orani: f.stopaj_orani }),
  (f) => (!f.kod.trim() || !f.ad.trim() ? 'Kod ve ad zorunludur.' : ![f.kdv_orani, f.tevkifat_orani, f.stopaj_orani].every(oranKontrol) ? 'Oranlar 0-100 arasında olmalıdır.' : ''),
)
onMounted(L.yukle)
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">Finans / Ayarlar</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Vergi Profilleri</h1>
        <p class="mt-1 text-sm text-surface-500">Fatura kalemlerinde tekrar kullanılan KDV, tevkifat ve stopaj kuralları.</p>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Kayıt</button>
    </div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Kod veya ad ile ara…" class="alan w-full max-w-sm" />
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
    <VeriTablosu :basliklar="['Kod', 'Ad', 'KDV %', 'Tevkifat %', 'Stopaj %', 'Durum', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="k in L.kayitlar.value" :key="k.id" class="transition-colors hover:bg-surface-100/60">
        <td class="px-4 py-3 font-medium">{{ k.kod }}</td>
        <td class="px-4 py-3">{{ k.ad }}</td>
        <td class="px-4 py-3 text-right font-mono">{{ k.kdv_orani }}</td>
        <td class="px-4 py-3 text-right font-mono">{{ k.tevkifat_orani }}</td>
        <td class="px-4 py-3 text-right font-mono">{{ k.stopaj_orani }}</td>
        <td class="px-4 py-3"><span class="durum-rozot" :class="k.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">{{ k.is_active ? 'Aktif' : 'Pasif' }}</span></td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3"><button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(k)">Düzenle</button></td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Kaydı Düzenle' : 'Yeni Kayıt'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Profil Kodu<input v-model="Fm.form.value.kod" type="text" maxlength="40" placeholder="örn. GENEL-20" class="alan" /></label>
          <label class="etiket">Profil Adı<input v-model="Fm.form.value.ad" type="text" maxlength="120" placeholder="örn. Genel %20" class="alan" /></label>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <label class="etiket">KDV %<input v-model="Fm.form.value.kdv_orani" type="number" min="0" max="100" step="0.01" class="alan" /></label>
          <label class="etiket">Tevkifat %<input v-model="Fm.form.value.tevkifat_orani" type="number" min="0" max="100" step="0.01" class="alan" /></label>
          <label class="etiket">Stopaj %<input v-model="Fm.form.value.stopaj_orani" type="number" min="0" max="100" step="0.01" class="alan" /></label>
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
