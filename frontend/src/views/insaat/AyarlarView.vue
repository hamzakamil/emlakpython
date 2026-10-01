<script setup lang="ts">
import { RouterLink } from 'vue-router'

interface AyarKarti {
  ad: string
  aciklama: string
  to: string
}

const kartlar: AyarKarti[] = [
  { ad: 'Firma Bilgileri', aciklama: 'Site adı, vergi numarası, telefon, e-posta ve varsayılan para birimi.', to: '/finans/ayarlar' },
  { ad: 'Kullanıcı Yönetimi', aciklama: 'Firma kullanıcıları ekleme, rol atama ve parola yönetimi.', to: '/yonetim/kullanicilar' },
  { ad: 'Firma / Tenant Yönetimi', aciklama: 'Firmalar, aktiflik durumu ve kullanıcı/proje/depolama limitleri.', to: '/yonetim/firmalar' },
  { ad: 'Projeler', aciklama: 'Proje tanımları, yapı sınıfı bağlantısı ve durum yönetimi.', to: '/insaat/projeler' },
  { ad: 'Hesap Planı', aciklama: 'Muhasebe hesapları, hiyerarşi ve tekdüzen hesap eşleşmeleri.', to: '/muhasebe/hesap-plani' },
  { ad: 'Stok Hesap Eşleme', aciklama: 'Malzeme bazında stok/KDV hesap eşlemeleri (boş malzeme = varsayılan).', to: '/finans/stok-hesap-esleme' },
  { ad: 'Profil ve Güvenlik', aciklama: 'Profil bilgileri görüntüleme ve kendi şifreni değiştirme.', to: '/profil' },
  { ad: 'Vergi Profilleri', aciklama: 'Fatura kalemlerinde kullanılan KDV, tevkifat ve stopaj kuralları.', to: '/finans/vergi-profilleri' },
  { ad: 'Hatırlatma Kuralları', aciklama: 'Modül tarihlerinden otomatik hatırlatma üreten kurallar.', to: '/insaat/hatirlatma-kurallari' },
]

interface YetkiSatiri {
  modul: string
  yazarlar: string
  not?: string
}

/** Backend permission dosyalarıyla senkron (salt-görünüm; tek doğruluk kaynağı backend'dir). */
const yetkiMatrisi: YetkiSatiri[] = [
  { modul: 'İnşaat', yazarlar: 'Süper Admin, Tenant Admin, Firma Admin, Maliyet Mühendisi, Proje Yöneticisi' },
  { modul: 'Satın Alma', yazarlar: 'Süper Admin, Tenant Admin, Firma Admin, Maliyet Mühendisi, Proje Yöneticisi', not: 'Finans ve Muhasebe rolleri satın almada yazamaz (görev ayrılığı).' },
  { modul: 'Cari / Finans', yazarlar: 'Süper Admin, Tenant Admin, Firma Admin, Muhasebe, Finans' },
  { modul: 'Muhasebe', yazarlar: 'Süper Admin, Tenant Admin, Firma Admin, Muhasebe', not: 'Finans rolü muhasebeye yazamaz.' },
  { modul: 'Veritabanı Yönetimi', yazarlar: 'Süper Admin', not: 'Yalnızca süper admin.' },
]
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Ayarlar</h1>
        <p class="mt-1 text-sm text-surface-500">Firma, kullanıcı ve sistem ayarlarına tek ekrandan erişin; kayıtlar mevcut ekranlarda yönetilir.</p>
      </div>
    </div>
    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <div v-for="x in kartlar" :key="x.ad" class="flex flex-col rounded-xl border border-surface-200 bg-surface-50 p-5 shadow-card">
        <p class="font-heading text-base font-bold text-surface-900">{{ x.ad }}</p>
        <p class="mt-1 flex-1 text-sm text-surface-600">{{ x.aciklama }}</p>
        <div class="mt-4"><RouterLink :to="x.to" class="ikincil-dugme">Ayarları Aç →</RouterLink></div>
      </div>
    </div>

    <h2 class="mb-3 mt-8 font-heading text-lg font-bold text-surface-900">Rol ve Yetkiler</h2>
    <p class="mb-3 text-sm text-surface-600">Okuma tüm giriş yapmış kullanıcılara açıktır; yazma rollerine göre kısıtlanır. Değişiklik backend yetki kurallarıyla yapılır.</p>
    <div class="overflow-x-auto rounded-xl border border-surface-200 bg-surface-50 shadow-card">
      <table class="min-w-full divide-y divide-surface-200 text-sm">
        <thead class="bg-surface-100"><tr><th class="px-4 py-3 text-left">Modül</th><th class="px-4 py-3 text-left">Yazabilir Roller</th><th class="px-4 py-3 text-left">Not</th></tr></thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="x in yetkiMatrisi" :key="x.modul" class="hover:bg-primary-50/40">
            <td class="px-4 py-3 font-medium">{{ x.modul }}</td>
            <td class="px-4 py-3">{{ x.yazarlar }}</td>
            <td class="px-4 py-3 text-surface-600">{{ x.not || '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
