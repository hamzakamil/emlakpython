<script setup lang="ts">
import { computed } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { ayarApi, type Ayar } from '@/services/ayarApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const liste = useKayitListesi<Ayar>('/finance/ayarlar/')
const ayarSecenekleri: Record<string, string> = {
  site_adi: 'Site adı',
  vergi_no: 'Vergi numarası',
  telefon: 'Telefon',
  eposta: 'E-posta',
  para_birimi_default: 'Varsayılan para birimi',
}

type Form = { anahtar: string; deger: string; aciklama: string }
const form = useKayitFormu<Ayar, Form>(
  ayarApi,
  () => ({ anahtar: 'site_adi', deger: '', aciklama: '' }),
  (ayar) => ({ anahtar: ayar.anahtar, deger: ayar.deger, aciklama: ayar.aciklama || '' }),
  (deger) => ({ ...deger, deger: deger.deger.trim(), aciklama: deger.aciklama.trim() }),
  (deger) => !deger.deger.trim() ? 'Ayar değeri zorunludur.' : '',
)

void liste.yukle()
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p class="text-sm font-medium text-primary-700">Finans</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Ayarlar</h1><p class="mt-1 text-sm text-surface-500">Bu firmanın genel iletişim ve para birimi ayarlarını yönetin.</p></div><button v-if="yazabilir" type="button" class="birincil-dugme" @click="form.yeniAc">+ Yeni Ayar</button></div>
    <div class="mb-4 flex gap-2"><form class="flex flex-1 gap-2" @submit.prevent="liste.aramaYap"><input v-model="liste.arama.value" type="search" class="alan w-full max-w-md" placeholder="Anahtar veya değer ile ara..." /><button type="submit" class="ikincil-dugme">Ara</button></form></div>
    <p v-if="liste.hata.value" class="hata-kutusu mb-4" role="alert">{{ liste.hata.value }}</p>
    <VeriTablosu :basliklar="['Ayar', 'Değer', 'Açıklama', yazabilir ? 'İşlem' : '']" :bos-mu="!liste.yukleniyor.value && !liste.kayitlar.value.length"><tr v-for="ayar in liste.kayitlar.value" :key="ayar.id" class="transition-colors hover:bg-surface-100/60"><td class="px-4 py-3 font-medium">{{ ayarSecenekleri[ayar.anahtar] || ayar.anahtar }}</td><td class="px-4 py-3">{{ ayar.deger }}</td><td class="px-4 py-3 text-surface-600">{{ ayar.aciklama || '—' }}</td><td v-if="yazabilir" class="px-4 py-3"><button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="form.duzenleAc(ayar)">Düzenle</button></td></tr></VeriTablosu>
    <Sayfalama :sayfa="liste.sayfa.value" :toplam="liste.toplam.value" :yukleniyor="liste.yukleniyor.value" @sayfa-degistir="(s) => { liste.sayfa.value = s; liste.yukle() }" />
    <KayitModal v-if="form.modalAcik.value" :baslik="form.duzenlenen.value ? 'Ayarı Düzenle' : 'Yeni Ayar'" @kapat="form.modalAcik.value = false"><form class="flex flex-col gap-4" @submit.prevent="form.kaydet(liste.yukle)"><label class="etiket">Anahtar<select v-model="form.form.value.anahtar" class="alan" :disabled="Boolean(form.duzenlenen.value)"><option v-for="(etiket, kod) in ayarSecenekleri" :key="kod" :value="kod">{{ etiket }}</option></select></label><label class="etiket">Değer<input v-model="form.form.value.deger" type="text" class="alan" /></label><label class="etiket">Açıklama<textarea v-model="form.form.value.aciklama" rows="3" class="alan" /></label><p v-if="form.formHata.value" class="hata-kutusu" role="alert">{{ form.formHata.value }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="form.modalAcik.value = false">Vazgeç</button><button type="submit" :disabled="form.kaydediliyor.value" class="birincil-dugme">{{ form.kaydediliyor.value ? 'Kaydediliyor...' : 'Kaydet' }}</button></div></form></KayitModal>
  </div>
</template>
