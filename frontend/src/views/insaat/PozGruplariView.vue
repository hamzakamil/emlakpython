<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import ExcelAktarim, { type ExcelSutun } from '@/components/ExcelAktarim.vue'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { PozGrubu } from '@/types/insaat'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const L = useKayitListesi<PozGrubu>('/construction/poz-gruplari/')
const gruplar = ref<PozGrubu[]>([])
const excelSutunlari: ExcelSutun[] = [
  { key: 'kod', label: 'Kod', required: true }, { key: 'ad', label: 'Poz grubu', required: true },
  { key: 'ust_grup', label: 'Üst grup' }, { key: 'is_active', label: 'Aktif', templateValue: true },
]
async function excelAl(rows: Record<string, unknown>[]): Promise<void> {
  try {
    for (const row of rows) await insaatApi.pozGruplari.olustur(row)
    await yukle()
    L.hata.value = ''
  } catch (error) {
    L.hata.value = `Excel içe aktarma kısmi olarak tamamlandı: ${error instanceof Error ? error.message : 'geçersiz veri.'}`
    await yukle()
  }
}

interface F { kod: string; ad: string; ust_grup: number | null; is_active: boolean }
const Fm = useKayitFormu<PozGrubu, F>(
  insaatApi.pozGruplari,
  () => ({ kod: '', ad: '', ust_grup: null, is_active: true }),
  (k) => ({ kod: k.kod, ad: k.ad, ust_grup: k.ust_grup, is_active: k.is_active }),
  (f) => ({ kod: f.kod.trim().toLocaleUpperCase('tr-TR'), ad: f.ad.trim(), ust_grup: f.ust_grup, is_active: f.is_active }),
  (f) => (!f.kod.trim() || !f.ad.trim() ? 'Grup kodu ve grup adı zorunludur.' : ''),
)

const ustGrupAdi = (id: number | null): string => gruplar.value.find((g) => g.id === id)?.ad || 'Ana grup'

async function yukle() {
  gruplar.value = await tumunuGetir(insaatApi.pozGruplari.liste)
  await L.yukle()
}

onMounted(async () => {
  try { await yukle() } catch (e) { L.hata.value = e instanceof Error ? e.message : 'Poz grupları yüklenemedi.' }
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat / Poz Kütüphanesi</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Poz Grupları</h1>
        <p class="mt-1 text-sm text-surface-500">Poz eklerken kullanılacak ana ve alt grupları burada tanımlayın.</p>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Poz Grubu</button>
    </div>
    <div class="mb-4"><ExcelAktarim :rows="L.kayitlar.value as unknown as Record<string, unknown>[]" :columns="excelSutunlari" filename="poz-gruplari" @imported="excelAl" /></div>
    <div class="mb-4 flex items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Kod veya grup adı ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
    </div>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <VeriTablosu :basliklar="['Kod', 'Poz grubu', 'Üst grup', 'Durum', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="grup in L.kayitlar.value" :key="grup.id" class="transition-colors hover:bg-surface-100/60">
        <td class="px-4 py-3 font-mono text-xs font-medium text-surface-900">{{ grup.kod }}</td>
        <td class="px-4 py-3 font-medium">{{ grup.ad }}</td>
        <td class="px-4 py-3">{{ ustGrupAdi(grup.ust_grup) }}</td>
        <td class="px-4 py-3"><span class="durum-rozot" :class="grup.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">{{ grup.is_active ? 'Aktif' : 'Pasif' }}</span></td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3"><button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(grup)">Düzenle</button></td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Poz Grubunu Düzenle' : 'Yeni Poz Grubu'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(yukle)">
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Grup Kodu *<input v-model="Fm.form.value.kod" type="text" placeholder="örn. BETON" class="alan" maxlength="20" /></label>
          <label class="etiket">Grup Adı *<input v-model="Fm.form.value.ad" type="text" placeholder="örn. Beton İşleri" class="alan" /></label>
        </div>
        <label class="etiket">Üst Grup
          <select v-model="Fm.form.value.ust_grup" class="alan">
            <option :value="null">Ana grup</option>
            <option v-for="grup in gruplar.filter((x) => x.id !== Fm.duzenlenen.value?.id)" :key="grup.id" :value="grup.id">{{ grup.kod }} — {{ grup.ad }}</option>
          </select>
        </label>
        <label class="flex items-center gap-2 text-sm text-surface-700"><input v-model="Fm.form.value.is_active" type="checkbox" /> Aktif</label>
        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">{{ Fm.kaydediliyor.value ? 'Kaydediliyor…' : 'Kaydet' }}</button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>
