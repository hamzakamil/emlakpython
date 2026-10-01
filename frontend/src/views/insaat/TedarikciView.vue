/**
 * TedarikciView.vue — Tedarikçi firma kartları listesi (CRUD)
 */
<script setup lang="ts">
import { computed, onMounted } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { insaatApi } from '@/services/insaatApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import { type Tedarikci } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const L = useKayitListesi<Tedarikci>('/construction/tedarikciler/')

interface F { firma_adi: string; firma_kodu: string; il: string; ilce: string; telefon: string; email: string; adres: string; is_active: boolean }
const Fm = useKayitFormu<Tedarikci, F>(
  insaatApi.tedarikciler,
  () => ({ firma_adi: '', firma_kodu: '', il: '', ilce: '', telefon: '', email: '', adres: '', is_active: true }),
  (k) => ({ firma_adi: k.firma_adi, firma_kodu: k.firma_kodu, il: k.il || '', ilce: k.ilce || '', telefon: k.telefon || '', email: k.email || '', adres: k.adres || '', is_active: k.is_active }),
  (f) => ({ firma_adi: f.firma_adi.trim(), firma_kodu: f.firma_kodu.trim(), il: f.il.trim(), ilce: f.ilce.trim(), telefon: f.telefon.trim(), email: f.email.trim(), adres: f.adres.trim(), is_active: f.is_active }),
  (f) => (!f.firma_adi.trim() || !f.firma_kodu.trim() ? 'Firma adı ve kodu zorunludur.' : ''),
)

onMounted(async () => {
  await L.yukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Tedarikçiler</h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Tedarikçi</button>
    </div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Firma adı veya kodu ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
    </div>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <VeriTablosu :basliklar="['Firma Kodu', 'Firma Adı', 'İl', 'İlçe', 'Telefon', 'E-posta', 'Durum', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="t in L.kayitlar.value" :key="t.id" class="transition-colors hover:bg-surface-100/60">
        <td class="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium text-surface-900">{{ t.firma_kodu }}</td>
        <td class="max-w-xs truncate px-4 py-3">{{ t.firma_adi }}</td>
        <td class="px-4 py-3">{{ t.il || '—' }}</td>
        <td class="px-4 py-3">{{ t.ilce || '—' }}</td>
        <td class="px-4 py-3">{{ t.telefon || '—' }}</td>
        <td class="px-4 py-3">{{ t.email || '—' }}</td>
        <td class="px-4 py-3"><span class="durum-rozot" :class="t.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">{{ t.is_active ? 'Aktif' : 'Pasif' }}</span></td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3"><button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(t)">Düzenle</button></td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Tedarikçi Düzenle' : 'Yeni Tedarikçi'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <label class="etiket">Firma Kodu<input v-model="Fm.form.value.firma_kodu" type="text" placeholder="örn. TED-001" class="alan" /></label>
        <label class="etiket">Firma Adı<input v-model="Fm.form.value.firma_adi" type="text" class="alan" /></label>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">İl<input v-model="Fm.form.value.il" type="text" class="alan" /></label>
          <label class="etiket">İlçe<input v-model="Fm.form.value.ilce" type="text" class="alan" /></label>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Telefon<input v-model="Fm.form.value.telefon" type="text" class="alan" /></label>
          <label class="etiket">E-posta<input v-model="Fm.form.value.email" type="email" class="alan" /></label>
        </div>
        <label class="etiket">Adres<textarea v-model="Fm.form.value.adres" rows="3" class="alan" /></label>
        <label class="etiket flex items-center gap-2"><input v-model="Fm.form.value.is_active" type="checkbox" class="w-4 h-4" /> Aktif</label>
        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">{{ Fm.kaydediliyor.value ? 'Kaydediliyor…' : 'Kaydet' }}</button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>