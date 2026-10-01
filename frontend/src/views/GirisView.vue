<script setup lang="ts">
/**
 * Giriş ekranı — JWT token alır (POST /api/v1/auth/token/, proxy üzerinden).
 * Hata mesajları backend Türkçe zarfından gelir (hataMesaji).
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Building2, EyeOff, Eye } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { hataMesaji } from '@/services/apiClient'

const router = useRouter()
const auth = useAuthStore()

const kullaniciAdi = ref('')
const sifre = ref('')
const yukleniyor = ref(false)
const hata = ref('')
const rememberMe = ref(false)
const showPassword = ref(false)

async function girisYap(): Promise<void> {
  hata.value = ''
  if (!kullaniciAdi.value.trim() || !sifre.value) {
    hata.value = 'Kullanıcı adı ve şifre zorunludur.'
    return
  }
  yukleniyor.value = true
  try {
    await auth.giris(kullaniciAdi.value.trim(), sifre.value, rememberMe.value)
    await router.push({ name: 'panel' })
  } catch (bilinmeyen) {
    hata.value = hataMesaji(bilinmeyen)
  } finally {
    yukleniyor.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-surface-100 p-4">
    <div class="w-full max-w-md">
      <div class="mb-8 flex flex-col items-center gap-3">
        <span
          class="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-800 font-heading text-lg font-bold text-white"
          >E</span
        >
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Emlak ERP</h1>
        <p class="text-sm text-surface-500">
          Gayrimenkul, İnşaat, Muhasebe ve Finans yönetim sistemi
        </p>
      </div>

      <form
        class="rounded-2xl border border-surface-200 bg-surface-50 p-8 shadow-soft"
        @submit.prevent="girisYap"
      >
        <div class="flex flex-col gap-4">
          <label class="flex flex-col gap-1.5">
            <span class="text-sm font-medium text-surface-700">Kullanıcı Adı</span>
            <input
              v-model="kullaniciAdi"
              type="text"
              name="kullanici-adi"
              autocomplete="username"
              class="rounded-lg border border-surface-300 bg-white px-4 py-2.5 text-sm outline-none transition-all focus:border-primary-600 focus:ring-2 focus:ring-primary-600/20"
              placeholder="örn. admin"
            />
          </label>

          <label class="flex flex-col gap-1.5">
            <span class="text-sm font-medium text-surface-700">Şifre</span>
            <div class="relative w-full">
              <input
                v-model="sifre"
                :type="showPassword ? 'text' : 'password'"
                name="sifre"
                autocomplete="current-password"
                class="rounded-lg border border-surface-300 bg-white px-4 py-2.5 text-sm outline-none transition-all focus:border-primary-600 focus:ring-2 focus:ring-primary-600/20 pr-10"
                placeholder="••••••••"
              />
              <button
                @click="showPassword = !showPassword"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-500"
              >
                <EyeOff v-if="!showPassword" class="h-4 w-4" />
                <Eye v-if="showPassword" class="h-4 w-4" />
              </button>
            </div>
          </label>

          <label class="flex items-center gap-2">
            <input
              type="checkbox"
              v-model="rememberMe"
              class="h-4 w-4 text-primary-600 focus:ring-primary-500"
            />
            <span class="text-sm text-surface-700">Beni hatırla</span>
          </label>

          <p
            v-if="hata"
            class="rounded-lg border border-error-200 bg-error-50 px-4 py-3 text-sm text-error-700"
            role="alert"
          >
            {{ hata }}
          </p>

          <button
            type="submit"
            :disabled="yukleniyor"
            class="mt-2 rounded-lg bg-primary-800 px-4 py-2.5 text-sm font-medium text-white transition-all hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {{ yukleniyor ? 'Giriş yapılıyor…' : 'Giriş Yap' }}
          </button>
        </div>
      </form>

      <p class="mt-6 flex items-center justify-center gap-2 text-xs text-surface-400">
        <Building2 class="h-3.5 w-3.5" />
        Kullanıcınız tek firmaya bağlıdır; firmalar arası geçiş süper admin yetkisidir
      </p>
    </div>
  </div>
</template>
