<script setup lang="ts">
/**
 * Süper admin firma (tenant) yönetimi — ekle, düzenle, sil, limitler.
 * Yalnızca süper admin erişebilir (router meta + backend IsSuperUser).
 */
import { onMounted } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { yonetimApi } from '@/services/yonetimApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import type { Tenant } from '@/types/api'

const L = useKayitListesi<Tenant>('/tenants-yonetim/')

interface F {
  name: string
  slug: string
  is_active: boolean
  max_users: number
  max_projects: number
  max_storage_gb: number
}
const Fm = useKayitFormu<Tenant, F>(
  yonetimApi.firmalar,
  () => ({ name: '', slug: '', is_active: true, max_users: 5, max_projects: 1, max_storage_gb: 5 }),
  (k) => ({
    name: k.name,
    slug: k.slug,
    is_active: k.is_active,
    max_users: k.max_users,
    max_projects: k.max_projects,
    max_storage_gb: k.max_storage_gb,
  }),
  (f) => ({
    name: f.name.trim(),
    slug: f.slug.trim().toLocaleLowerCase('tr-TR'),
    is_active: f.is_active,
    max_users: f.max_users,
    max_projects: f.max_projects,
    max_storage_gb: f.max_storage_gb,
  }),
  (f) => (!f.name.trim() || !f.slug.trim() ? 'Firma adı ve kısa ad zorunludur.' : ''),
)

onMounted(L.yukle)
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">Süper Admin Yönetimi</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Firmalar</h1>
      </div>
      <button type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Firma</button>
    </div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Firma adı veya kısa ad ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
    </div>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <VeriTablosu :basliklar="['Firma Adı', 'Kısa Ad', 'Kullanıcı', 'Proje', 'Depolama (GB)', 'Durum', 'İşlem']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="k in L.kayitlar.value" :key="k.id" class="transition-colors hover:bg-surface-100/60">
        <td class="px-4 py-3 font-medium">{{ k.name }}</td>
        <td class="px-4 py-3 font-mono text-xs">{{ k.slug }}</td>
        <td class="px-4 py-3">{{ k.max_users }}</td>
        <td class="px-4 py-3">{{ k.max_projects }}</td>
        <td class="px-4 py-3">{{ k.max_storage_gb }}</td>
        <td class="px-4 py-3"><span class="durum-rozot" :class="k.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">{{ k.is_active ? 'Aktif' : 'Pasif' }}</span></td>
        <td class="whitespace-nowrap px-4 py-3">
          <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(k)">Düzenle</button>
        </td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Firmayı Düzenle' : 'Yeni Firma'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <label class="etiket">Firma Adı<input v-model="Fm.form.value.name" type="text" placeholder="örn. Demo Firma A.Ş." class="alan" /></label>
        <label class="etiket">Kısa Ad (slug)<input v-model="Fm.form.value.slug" type="text" placeholder="örn. demo" class="alan" /></label>
        <div class="grid grid-cols-3 gap-4">
          <label class="etiket">Maks. Kullanıcı<input v-model.number="Fm.form.value.max_users" type="number" min="1" class="alan" /></label>
          <label class="etiket">Maks. Proje<input v-model.number="Fm.form.value.max_projects" type="number" min="1" class="alan" /></label>
          <label class="etiket">Depolama (GB)<input v-model.number="Fm.form.value.max_storage_gb" type="number" min="1" class="alan" /></label>
        </div>
        <label class="flex items-center gap-2 text-sm text-surface-700">
          <input v-model="Fm.form.value.is_active" type="checkbox" class="h-4 w-4 rounded border-surface-300 text-primary-700" />
          Aktif
        </label>
        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">{{ Fm.kaydediliyor.value ? 'Kaydediliyor…' : 'Kaydet' }}</button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>