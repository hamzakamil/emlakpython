<script setup lang="ts">
import { computed, onMounted } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { insaatApi } from '@/services/insaatApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { HatirlatmaKurali } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const SEVIYELER = [
  { kod: 'kritik', etiket: 'Kritik' },
  { kod: 'uyari', etiket: 'Uyarı' },
  { kod: 'bilgi', etiket: 'Bilgi' },
] as const
const L = useKayitListesi<HatirlatmaKurali>('/construction/hatirlatma-kurallari/')
interface F { ilgili_modul: string; ilgili_model: string; tetikleyici: string; once_gun_sayisi: number; seviye: string; aktif_mi: boolean }
const Fm = useKayitFormu<HatirlatmaKurali, F>(
  insaatApi.hatirlatmaKurallari,
  () => ({ ilgili_modul: '', ilgili_model: '', tetikleyici: '', once_gun_sayisi: 0, seviye: 'uyari', aktif_mi: true }),
  (k) => ({ ilgili_modul: k.ilgili_modul, ilgili_model: '', tetikleyici: k.tetikleyici, once_gun_sayisi: k.once_gun_sayisi, seviye: k.seviye, aktif_mi: k.aktif_mi }),
  (f) => ({ ilgili_modul: f.ilgili_modul.trim(), ilgili_model: f.ilgili_model.trim(), tetikleyici: f.tetikleyici.trim(), once_gun_sayisi: f.once_gun_sayisi, seviye: f.seviye, aktif_mi: f.aktif_mi }),
  (f) => (!f.ilgili_modul.trim() || !f.tetikleyici.trim() ? 'Modül ve tetikleyici zorunludur.' : f.once_gun_sayisi < 0 ? 'Gün sayısı negatif olamaz.' : ''),
)
function filtreUygula(): void { L.sayfa.value = 1; void L.yukle() }
onMounted(L.yukle)
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat / Ayarlar</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Hatırlatma Kuralları</h1>
        <p class="mt-1 text-sm text-surface-500">Modül tarihlerinden otomatik hatırlatma üreten tenant kuralları.</p>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Kayıt</button>
    </div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <input v-model="L.filtreler.value.ilgili_modul" type="search" placeholder="Modül ile filtrele…" class="alan w-full max-w-xs" @change="filtreUygula()" />
      <input v-model="L.filtreler.value.tetikleyici" type="search" placeholder="Tetikleyici ile filtrele…" class="alan w-full max-w-xs" @change="filtreUygula()" />
      <select v-model="L.filtreler.value.seviye" class="alan" @change="filtreUygula()">
        <option :value="undefined">Tüm seviyeler</option>
        <option v-for="s in SEVIYELER" :key="s.kod" :value="s.kod">{{ s.etiket }}</option>
      </select>
      <select v-model="L.filtreler.value.aktif_mi" class="alan" @change="filtreUygula()">
        <option :value="undefined">Tümü</option>
        <option :value="true">Aktif</option>
        <option :value="false">Pasif</option>
      </select>
    </div>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <VeriTablosu :basliklar="['Modül', 'Tetikleyici', 'Önce (gün)', 'Seviye', 'Durum', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="k in L.kayitlar.value" :key="k.id" class="transition-colors hover:bg-surface-100/60">
        <td class="px-4 py-3 font-medium">{{ k.ilgili_modul }}</td>
        <td class="px-4 py-3">{{ k.tetikleyici }}</td>
        <td class="px-4 py-3 text-right font-mono">{{ k.once_gun_sayisi }}</td>
        <td class="px-4 py-3">{{ SEVIYELER.find((s) => s.kod === k.seviye)?.etiket || k.seviye }}</td>
        <td class="px-4 py-3"><span class="durum-rozot" :class="k.aktif_mi ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">{{ k.aktif_mi ? 'Aktif' : 'Pasif' }}</span></td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3"><button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(k)">Düzenle</button></td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Kaydı Düzenle' : 'Yeni Kayıt'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">İlgili Modül<input v-model="Fm.form.value.ilgili_modul" type="text" maxlength="80" placeholder="örn. hakedis" class="alan" /></label>
          <label class="etiket">Tetikleyici<input v-model="Fm.form.value.tetikleyici" type="text" maxlength="80" placeholder="örn. vade_tarihi" class="alan" /></label>
        </div>
        <label class="etiket">İlgili Model (opsiyonel)<input v-model="Fm.form.value.ilgili_model" type="text" maxlength="120" placeholder="örn. finance.Fatura" class="alan" /></label>
        <div class="grid grid-cols-3 gap-4">
          <label class="etiket">Önce (gün)<input v-model.number="Fm.form.value.once_gun_sayisi" type="number" min="0" class="alan" /></label>
          <label class="etiket">Seviye<select v-model="Fm.form.value.seviye" class="alan"><option v-for="s in SEVIYELER" :key="s.kod" :value="s.kod">{{ s.etiket }}</option></select></label>
          <label class="flex items-end gap-2 pb-2 text-sm"><input v-model="Fm.form.value.aktif_mi" type="checkbox" /> Aktif</label>
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
