<script setup lang="ts">
import { computed } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { muhasebeApi } from '@/services/muhasebeApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import { MUHASEBE_HESAP_TIPLERI, type HesapPlani } from '@/types/muhasebe'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const L = useKayitListesi<HesapPlani>('/accounting/hesap-plani/')
type Form = { kod: string; ad: string; tip: string; is_active: boolean }
const Fm = useKayitFormu<HesapPlani, Form>(muhasebeApi.hesapPlani, () => ({ kod: '', ad: '', tip: 'aktif', is_active: true }), (x) => ({ kod: x.kod, ad: x.ad, tip: x.tip, is_active: x.is_active }), (x) => ({ ...x, kod: x.kod.trim(), ad: x.ad.trim() }), (x) => !x.kod.trim() || !x.ad.trim() ? 'Hesap kodu ve adı zorunludur.' : '')
void L.yukle()
</script>

<template>
  <div class="mx-auto max-w-6xl"><div class="mb-6 flex flex-wrap items-center justify-between gap-3"><div><p class="text-sm font-medium text-primary-700">Muhasebe</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Hesap Planı</h1></div><button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">+ Yeni Hesap</button></div><div class="mb-4 flex gap-2"><form class="flex flex-1 gap-2" @submit.prevent="L.aramaYap()"><input v-model="L.arama.value" type="search" placeholder="Hesap kodu veya adı ile ara..." class="alan w-full max-w-sm" /><button type="submit" class="ikincil-dugme">Ara</button></form><select v-model="L.filtreler.value.tip" class="alan" @change="L.sayfa.value = 1; L.yukle()"><option :value="undefined">Tüm tipler</option><option v-for="(etiket, kod) in MUHASEBE_HESAP_TIPLERI" :key="kod" :value="kod">{{ etiket }}</option></select></div><p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p><VeriTablosu :basliklar="['Kod', 'Hesap Adı', 'Tip', 'Durum', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && !L.kayitlar.value.length"><tr v-for="x in L.kayitlar.value" :key="x.id" class="transition-colors hover:bg-surface-100/60"><td class="px-4 py-3 font-mono text-xs">{{ x.kod }}</td><td class="px-4 py-3 font-medium">{{ x.ad }}</td><td class="px-4 py-3">{{ MUHASEBE_HESAP_TIPLERI[x.tip] || x.tip }}</td><td class="px-4 py-3">{{ x.is_active ? 'Aktif' : 'Pasif' }}</td><td v-if="yazabilir" class="px-4 py-3"><button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="Fm.duzenleAc(x)">Düzenle</button></td></tr></VeriTablosu><Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" /><KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Hesabı Düzenle' : 'Yeni Hesap'" @kapat="Fm.modalAcik.value = false"><form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)"><div class="grid grid-cols-2 gap-4"><label class="etiket">Hesap Kodu<input v-model="Fm.form.value.kod" type="text" class="alan" /></label><label class="etiket">Hesap Adı<input v-model="Fm.form.value.ad" type="text" class="alan" /></label></div><label class="etiket">Tip<select v-model="Fm.form.value.tip" class="alan"><option v-for="(etiket, kod) in MUHASEBE_HESAP_TIPLERI" :key="kod" :value="kod">{{ etiket }}</option></select></label><label class="flex items-center gap-2 text-sm"><input v-model="Fm.form.value.is_active" type="checkbox" /> Aktif</label><p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p><div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button><button type="submit" class="birincil-dugme">Kaydet</button></div></form></KayitModal></div>
</template>
