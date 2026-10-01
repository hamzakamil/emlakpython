<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { beniGetir, sifreDegistir } from '@/services/authApi'
import { hataMesaji } from '@/services/apiClient'
import { ROL_ETIKETLERI } from '@/utils/roller'
import { useAuthStore } from '@/stores/auth'
import type { Kullanici } from '@/types/api'

const auth = useAuthStore()
const kullanici = ref<Kullanici | null>(null)
const yukleniyor = ref(false)
const hata = ref('')
const mevcutSifre = ref('')
const yeniSifre = ref('')
const yeniSifreTekrar = ref('')
const formHata = ref('')
const basari = ref('')
const kaydediliyor = ref(false)

async function yukle(): Promise<void> {
  yukleniyor.value = true; hata.value = ''
  try { kullanici.value = await beniGetir() } catch (e) { hata.value = hataMesaji(e) } finally { yukleniyor.value = false }
}

async function kaydet(): Promise<void> {
  formHata.value = ''; basari.value = ''
  if (!mevcutSifre.value || !yeniSifre.value || !yeniSifreTekrar.value) { formHata.value = 'Tüm şifre alanları zorunludur.'; return }
  if (yeniSifre.value !== yeniSifreTekrar.value) { formHata.value = 'Yeni şifreler eşleşmiyor.'; return }
  kaydediliyor.value = true
  try {
    const yanit = await sifreDegistir({ mevcut_sifre: mevcutSifre.value, yeni_sifre: yeniSifre.value, yeni_sifre_tekrar: yeniSifreTekrar.value })
    basari.value = yanit.detail || 'Şifre değiştirildi.'
    mevcutSifre.value = ''; yeniSifre.value = ''; yeniSifreTekrar.value = ''
  } catch (e) { formHata.value = hataMesaji(e) } finally { kaydediliyor.value = false }
}

onMounted(() => { kullanici.value = auth.kullanici; void yukle() })
</script>

<template>
  <div class="mx-auto max-w-4xl">
    <div class="mb-6">
      <p class="text-sm font-medium text-primary-700">Hesap</p>
      <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Profil ve Güvenlik</h1>
    </div>
    <p v-if="hata" class="hata-kutusu mb-4" role="alert">{{ hata }}</p>
    <p v-if="yukleniyor" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <div v-if="kullanici" class="mb-6 grid gap-3 sm:grid-cols-2">
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Kullanıcı Adı</p><p class="mt-1 font-semibold">{{ kullanici.username }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Ad Soyad</p><p class="mt-1 font-semibold">{{ [kullanici.first_name, kullanici.last_name].filter(Boolean).join(' ') || '—' }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">E-posta</p><p class="mt-1 font-semibold">{{ kullanici.email || '—' }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card"><p class="text-xs font-semibold uppercase text-surface-500">Rol</p><p class="mt-1 font-semibold">{{ kullanici.role ? ROL_ETIKETLERI[kullanici.role] : '—' }}</p></div>
      <div class="rounded-xl border border-surface-200 bg-surface-50 p-4 shadow-card sm:col-span-2"><p class="text-xs font-semibold uppercase text-surface-500">Firma</p><p class="mt-1 font-semibold">{{ kullanici.tenant_ad || '—' }}</p></div>
    </div>
    <div class="rounded-xl border border-surface-200 bg-surface-50 p-5 shadow-card">
      <h2 class="font-heading text-lg font-bold text-surface-900">Şifre Değiştir</h2>
      <form class="mt-4 flex max-w-md flex-col gap-4" @submit.prevent="kaydet">
        <label class="etiket">Mevcut Şifre<input v-model="mevcutSifre" type="password" autocomplete="current-password" class="alan" /></label>
        <label class="etiket">Yeni Şifre<input v-model="yeniSifre" type="password" autocomplete="new-password" class="alan" /></label>
        <label class="etiket">Yeni Şifre (Tekrar)<input v-model="yeniSifreTekrar" type="password" autocomplete="new-password" class="alan" /></label>
        <p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p>
        <p v-if="basari" class="rounded-lg border border-success-200 bg-success-50 px-4 py-3 text-sm text-success-700" role="status">{{ basari }}</p>
        <div><button type="submit" :disabled="kaydediliyor" class="birincil-dugme">{{ kaydediliyor ? 'Kaydediliyor…' : 'Şifreyi Değiştir' }}</button></div>
      </form>
    </div>
  </div>
</template>
