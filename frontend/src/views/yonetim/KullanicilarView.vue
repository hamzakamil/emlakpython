<script setup lang="ts">
/**
 * Süper admin kullanıcı yönetimi — firma bazlı kullanıcı ekleme (parola ile),
 * rol/tenant atama, düzenleme ve silme. Yalnızca süper admin (backend IsSuperUser).
 */
import { onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { yonetimApi } from '@/services/yonetimApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { ROL_ETIKETLERI } from '@/utils/roller'
import type { KullaniciYonetim, Rol, Tenant } from '@/types/api'

const L = useKayitListesi<KullaniciYonetim>('/kullanicilar/')
const firmalar = ref<Tenant[]>([])

interface F {
  username: string
  email: string
  first_name: string
  last_name: string
  role: Rol
  tenant: number | null
  is_active: boolean
  password: string
}
const Fm = useKayitFormu<KullaniciYonetim, F>(
  yonetimApi.kullanicilar,
  () => ({ username: '', email: '', first_name: '', last_name: '', role: 'kullanici', tenant: null, is_active: true, password: '' }),
  (k) => ({
    username: k.username,
    email: k.email,
    first_name: k.first_name || '',
    last_name: k.last_name || '',
    role: k.role,
    tenant: k.tenant,
    is_active: k.is_active,
    password: '',
  }),
  (f) => {
    const veri: Record<string, unknown> = {
      username: f.username.trim(),
      email: f.email.trim(),
      first_name: f.first_name.trim(),
      last_name: f.last_name.trim(),
      role: f.role,
      tenant: f.tenant,
      is_active: f.is_active,
    }
    if (f.password) veri.password = f.password
    return veri
  },
  (f) => {
    if (!f.username.trim() || !f.email.trim()) return 'Kullanıcı adı ve e-posta zorunludur.'
    if (!Fm.duzenlenen.value && !f.password) return 'Yeni kullanıcı için parola zorunludur.'
    if (f.role !== 'super_admin' && !f.tenant) return 'Süper admin dışındaki kullanıcılar için firma seçilmelidir.'
    return ''
  },
)

const rolSecenekleri = Object.entries(ROL_ETIKETLERI) as [Rol, string][]

async function firmalariYukle(): Promise<void> {
  try {
    const sayfa = await yonetimApi.firmalar.liste({ page_size: 100 })
    firmalar.value = sayfa.results
  } catch (e) {
    L.hata.value = hataMesaji(e)
  }
}

onMounted(async () => {
  await firmalariYukle()
  await L.yukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">Süper Admin Yönetimi</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Kullanıcılar</h1>
      </div>
      <button type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Kullanıcı</button>
    </div>
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Kullanıcı adı veya e-posta ile ara…" class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
    </div>
    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <p v-if="L.yukleniyor.value" class="mb-4 text-sm text-surface-500">Yükleniyor…</p>
    <VeriTablosu :basliklar="['Kullanıcı', 'E-posta', 'Rol', 'Firma', 'Durum', 'İşlem']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="k in L.kayitlar.value" :key="k.id" class="transition-colors hover:bg-surface-100/60">
        <td class="px-4 py-3 font-medium">{{ k.username }}</td>
        <td class="px-4 py-3 text-sm text-surface-600">{{ k.email }}</td>
        <td class="px-4 py-3"><span class="durum-rozot bg-primary-100 text-primary-700">{{ ROL_ETIKETLERI[k.role] || k.role }}</span></td>
        <td class="px-4 py-3 text-sm">{{ firmalar.find((f) => f.id === k.tenant)?.name || (k.role === 'super_admin' ? '—' : 'Firma yok') }}</td>
        <td class="px-4 py-3"><span class="durum-rozot" :class="k.is_active ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'">{{ k.is_active ? 'Aktif' : 'Pasif' }}</span></td>
        <td class="whitespace-nowrap px-4 py-3">
          <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(k)">Düzenle</button>
        </td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />
    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Kullanıcıyı Düzenle' : 'Yeni Kullanıcı'" @kapat="Fm.modalAcik.value = false">
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Kullanıcı Adı<input v-model="Fm.form.value.username" type="text" class="alan" /></label>
          <label class="etiket">E-posta<input v-model="Fm.form.value.email" type="email" class="alan" /></label>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Ad<input v-model="Fm.form.value.first_name" type="text" class="alan" /></label>
          <label class="etiket">Soyad<input v-model="Fm.form.value.last_name" type="text" class="alan" /></label>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">Rol<select v-model="Fm.form.value.role" class="alan"><option v-for="(etiket, deger) in rolSecenekleri" :key="deger" :value="deger">{{ etiket }}</option></select></label>
          <label class="etiket">Firma<select v-model="Fm.form.value.tenant" class="alan"><option :value="null">— Firma yok —</option><option v-for="f in firmalar" :key="f.id" :value="f.id">{{ f.name }}</option></select></label>
        </div>
        <label class="etiket">Parola<input v-model="Fm.form.value.password" type="password" autocomplete="new-password" :placeholder="Fm.duzenlenen.value ? 'Boş bırakılırsa korunur' : 'Zorunlu'" class="alan" /></label>
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