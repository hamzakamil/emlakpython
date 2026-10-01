<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import { hataMesaji } from '@/services/apiClient'
import { cariApi } from '@/services/cariApi'
import { faturaApi } from '@/services/faturaApi'
import { finansApi } from '@/services/finansApi'
import { tumunuGetir } from '@/services/insaatApi'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import { FATURA_DURUMLARI, FATURA_TURLERI, PARA_BIRIMLERI, type Fatura, type FaturaKalemi, type VergiProfili } from '@/types/fatura'
import type { Cari } from '@/types/cari'
import type { FinansHesabi } from '@/types/finans'
import { yazabilirMi } from '@/utils/yetki'

const auth = useAuthStore()
const router = useRouter()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const liste = useKayitListesi<Fatura>('/finance/faturalar/')
const cariler = ref<Cari[]>([])
const hesaplar = ref<FinansHesabi[]>([])
const vergiProfilleri = ref<VergiProfili[]>([])
const modalAcik = ref(false)
const panelKucuk = ref(false)
const panelBuyuk = ref(false)
const kaydediliyor = ref(false)
const formHata = ref('')
const duzenlenenId = ref<number | null>(null)
const bugun = () => new Date().toISOString().slice(0, 10)
type FaturaVeriFormu = Omit<Fatura, 'id' | 'kalemler' | 'created_at' | 'updated_at' | 'cari_ad' | 'hesap_ad'> & { kalemler: FaturaKalemi[] }
const bosSatir = (): FaturaKalemi => ({ aciklama: '', miktar: '1', birim: 'ADET', birim_fiyat: '0', kdv_orani: '20', tevkifat_orani: '0', stopaj_orani: '0', poz_no: '', iskonto_orani: '0' })
const bosForm = (): FaturaVeriFormu => ({ No: '', cari: null, kasa_banka_hesabi: null, durum: 'taslak', tarih: bugun(), vade_tarihi: '', tutar: '0', alacakli: false, aciklama: '', fatura_turu: 'satis', senaryo: 'kagit', para_birimi: 'TRY', kur: '1', kdv_dahil_mi: false, iskonto_tutari: '0', odenen_tutar: '0', e_fatura_uuid: '', e_fatura_durum: 'gonderilmedi', kalemler: [bosSatir()] })
const form = ref<FaturaVeriFormu>(bosForm())
const kalemSutunlari = ref([
  { anahtar: 'poz', etiket: 'Poz', genislik: 110 },
  { anahtar: 'aciklama', etiket: 'Açıklama', genislik: 260 },
  { anahtar: 'miktar', etiket: 'Miktar', genislik: 82 },
  { anahtar: 'birim', etiket: 'Birim', genislik: 92 },
  { anahtar: 'fiyat', etiket: 'Birim fiyat', genislik: 112 },
  { anahtar: 'iskonto', etiket: 'İskonto', genislik: 100 },
  { anahtar: 'profil', etiket: 'Vergi profili', genislik: 125 },
  { anahtar: 'kdv', etiket: 'KDV', genislik: 92 },
  { anahtar: 'tevkifat', etiket: 'Tevkifat', genislik: 100 },
  { anahtar: 'stopaj', etiket: 'Stopaj', genislik: 100 },
  { anahtar: 'islem', etiket: '', genislik: 44 },
])
const kalemIzgaraStili = computed(() => ({
  gridTemplateColumns: kalemSutunlari.value
    .map((sutun) => `minmax(0, ${Math.max(1, Number(sutun.genislik) || 1)}fr)`)
    .join(' '),
}))
function kalemBoyutlariniSakla(): void {
  localStorage.setItem('emlak_erp_fatura_kalem_sutunlari', JSON.stringify(kalemSutunlari.value.map((sutun) => sutun.genislik)))
}
function kalemBoyutlariniYukle(): void {
  try {
    const boyutlar = JSON.parse(localStorage.getItem('emlak_erp_fatura_kalem_sutunlari') || 'null') as number[] | null
    if (Array.isArray(boyutlar) && boyutlar.length === kalemSutunlari.value.length) {
      kalemSutunlari.value.forEach((sutun, index) => { sutun.genislik = Math.max(44, Math.min(420, Number(boyutlar[index]) || sutun.genislik)) })
    }
  } catch {
    localStorage.removeItem('emlak_erp_fatura_kalem_sutunlari')
  }
}
const FATURA_TASLAK_ANAHTARI = 'emlak_erp_acik_fatura_taslagi'
function taslagiYayinla(): void {
  window.dispatchEvent(new CustomEvent('fatura-taslagi-degisti'))
}
function taslagiKaydet(): void {
  if (!modalAcik.value) return
  localStorage.setItem(FATURA_TASLAK_ANAHTARI, JSON.stringify({ form: form.value, duzenlenenId: duzenlenenId.value }))
  taslagiYayinla()
}
function taslagiKapat(): void {
  modalAcik.value = false
  panelKucuk.value = false
  panelBuyuk.value = false
  localStorage.removeItem(FATURA_TASLAK_ANAHTARI)
  taslagiYayinla()
}
watch(form, taslagiKaydet, { deep: true })
const varsayilanVergiler: Record<string, { kdv: string; tevkifat: string; stopaj: string }> = { satis: { kdv: '20', tevkifat: '0', stopaj: '0' }, kira: { kdv: '20', tevkifat: '0', stopaj: '20' }, hakedis: { kdv: '20', tevkifat: '40', stopaj: '0' }, aidat: { kdv: '0', tevkifat: '0', stopaj: '0' }, hizmet: { kdv: '20', tevkifat: '0', stopaj: '0' }, proforma: { kdv: '20', tevkifat: '0', stopaj: '0' }, iade: { kdv: '20', tevkifat: '0', stopaj: '0' } }
watch(() => form.value.fatura_turu, (tur) => {
  const oran = varsayilanVergiler[tur || 'satis']
  if (!oran) return
  form.value.kalemler.forEach((satir) => {
    satir.kdv_orani = oran.kdv
    satir.tevkifat_orani = oran.tevkifat
    satir.stopaj_orani = oran.stopaj
  })
})
const satirMatrahi = (x: FaturaKalemi): number => {
  const brut = Number(x.miktar || 0) * Number(x.birim_fiyat || 0)
  return brut - brut * Number(x.iskonto_orani || 0) / 100
}
const araToplam = computed(() => form.value.kalemler.reduce((t, x) => t + satirMatrahi(x), 0))
const kdvToplam = computed(() => form.value.kalemler.reduce((t, x) => t + satirMatrahi(x) * Number(x.kdv_orani || 0) / 100, 0))
const tevkifatToplam = computed(() => form.value.kalemler.reduce((t, x) => t + Number(x.miktar || 0) * Number(x.birim_fiyat || 0) * Number(x.kdv_orani || 0) / 100 * Number(x.tevkifat_orani || 0) / 100, 0))
const stopajToplam = computed(() => form.value.kalemler.reduce((t, x) => t + satirMatrahi(x) * Number(x.stopaj_orani || 0) / 100, 0))
const genelToplam = computed(() => araToplam.value + kdvToplam.value - tevkifatToplam.value - stopajToplam.value)
const toplamTutar = computed(() => liste.kayitlar.value.reduce((t, x) => t + Number(x.tutar), 0))
function para(v: number | string, currency = 'TRY'): string { return new Intl.NumberFormat('tr-TR', { style: 'currency', currency }).format(Number(v)) }
function yeniAc(): void { localStorage.removeItem(FATURA_TASLAK_ANAHTARI); duzenlenenId.value = null; form.value = bosForm(); formHata.value = ''; panelKucuk.value = false; panelBuyuk.value = false; modalAcik.value = true; taslagiKaydet() }
function duzenle(x: Fatura): void { duzenlenenId.value = x.id; form.value = { No: x.No, cari: x.cari, kasa_banka_hesabi: x.kasa_banka_hesabi, durum: x.durum, tarih: x.tarih, vade_tarihi: x.vade_tarihi || '', tutar: x.tutar, alacakli: x.alacakli, aciklama: x.aciklama, fatura_turu: x.fatura_turu || 'satis', senaryo: x.senaryo || 'kagit', para_birimi: x.para_birimi || 'TRY', kur: x.kur || '1', kdv_dahil_mi: x.kdv_dahil_mi || false, iskonto_tutari: x.iskonto_tutari || '0', odenen_tutar: x.odenen_tutar || '0', e_fatura_uuid: x.e_fatura_uuid || '', e_fatura_durum: x.e_fatura_durum || 'gonderilmedi', kalemler: x.kalemler?.length ? x.kalemler.map((k) => ({ ...k, id: undefined })) : [bosSatir()] }; formHata.value = ''; panelKucuk.value = false; panelBuyuk.value = false; modalAcik.value = true; taslagiKaydet() }
function durumSinifi(durum: Fatura['durum']): string { return { taslak: 'bg-amber-100 text-amber-800', aktif: 'bg-blue-100 text-blue-800', odendi: 'bg-emerald-100 text-emerald-800', iptal: 'bg-red-100 text-red-800' }[durum] }
function satirTutar(x: FaturaKalemi): number { return satirMatrahi(x) * (1 + Number(x.kdv_orani || 0) / 100) - satirMatrahi(x) * Number(x.stopaj_orani || 0) / 100 - satirMatrahi(x) * Number(x.kdv_orani || 0) / 100 * Number(x.tevkifat_orani || 0) / 100 }
function vergiProfilUygula(satir: FaturaKalemi, profilId: string): void {
  const profil = vergiProfilleri.value.find((x) => String(x.id) === profilId)
  if (!profil) return
  satir.kdv_orani = profil.kdv_orani
  satir.tevkifat_orani = profil.tevkifat_orani
  satir.stopaj_orani = profil.stopaj_orani
}
async function kaydet(): Promise<void> {
  formHata.value = ''
  if (auth.seciciGosterilsinMi && auth.seciliTenantId === null) { formHata.value = 'Fatura oluşturmak için üst menüden firma seçmelisiniz.'; return }
  if (!form.value.No.trim() || !form.value.tarih || form.value.kalemler.some((x) => !x.aciklama.trim() || Number(x.miktar) <= 0 || Number(x.birim_fiyat) < 0)) { formHata.value = 'Fatura numarası, tarih ve geçerli satır bilgileri zorunludur.'; return }
  if (form.value.vade_tarihi && form.value.vade_tarihi < form.value.tarih) { formHata.value = 'Vade tarihi fatura tarihinden önce olamaz.'; return }
  kaydediliyor.value = true
  try {
    const veri = { ...form.value, No: form.value.No.trim(), aciklama: form.value.aciklama.trim(), vade_tarihi: form.value.vade_tarihi || null, tutar: genelToplam.value.toFixed(2), kalemler: form.value.kalemler.map(({ id, ...x }) => x) }
    if (duzenlenenId.value) await faturaApi.guncelle(duzenlenenId.value, veri)
    else await faturaApi.olustur(veri)
    if (form.value.vade_tarihi) window.dispatchEvent(new CustomEvent('hatirlatma-onerisi', { detail: { tarih: form.value.vade_tarihi, baslik: 'Fatura vadesi için hatırlatma kurmak ister misiniz?', payload: { ilgili_app: 'finance', ilgili_model: 'Fatura' } } }))
    taslagiKapat()
    await liste.yukle()
  } catch (e) { formHata.value = hataMesaji(e) } finally { kaydediliyor.value = false }
}
async function iptalEt(x: Fatura): Promise<void> { if (x.durum === 'iptal' || !confirm(`${x.No} numaralı fatura iptal edilsin mi?`)) return; try { await faturaApi.sil(x.id); await liste.yukle() } catch (e) { liste.hata.value = hataMesaji(e) } }
async function secenekleriYukle(): Promise<void> { try { cariler.value = await tumunuGetir(cariApi.cariler.liste); hesaplar.value = await tumunuGetir(finansApi.hesaplar.liste); vergiProfilleri.value = await tumunuGetir(finansApi.vergiProfilleri.liste, { is_active: true }) } catch (e) { liste.hata.value = hataMesaji(e) } }
onMounted(async () => {
  kalemBoyutlariniYukle()
  const kayitliTaslak = localStorage.getItem(FATURA_TASLAK_ANAHTARI)
  if (kayitliTaslak) {
    try {
      const taslak = JSON.parse(kayitliTaslak) as { form?: FaturaVeriFormu; duzenlenenId?: number | null }
      if (taslak.form) {
        form.value = taslak.form
        duzenlenenId.value = taslak.duzenlenenId ?? null
        modalAcik.value = true
      }
    } catch {
      localStorage.removeItem(FATURA_TASLAK_ANAHTARI)
    }
  }
  await secenekleriYukle(); await liste.yukle()
})
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4"><div><p class="text-sm font-medium text-primary-700">Finans / Ticari Belgeler</p><h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Faturalar</h1><p class="mt-1 text-sm text-surface-500">Satır bazlı tutar, KDV, tevkifat ve vade akışını tek belgede yönetin.</p></div><button v-if="yazabilir" class="birincil-dugme" type="button" @click="yeniAc">+ Yeni Fatura</button></div>
    <div class="mb-5 grid gap-3 sm:grid-cols-4"><div class="rounded-2xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Toplam</p><p class="mt-2 text-xl font-bold">{{ para(toplamTutar) }}</p></div><div class="rounded-2xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Açık</p><p class="mt-2 text-xl font-bold text-blue-700">{{ liste.kayitlar.value.filter((x) => x.durum === 'aktif').length }}</p></div><div class="rounded-2xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Taslak</p><p class="mt-2 text-xl font-bold text-amber-700">{{ liste.kayitlar.value.filter((x) => x.durum === 'taslak').length }}</p></div><div class="rounded-2xl border border-surface-200 bg-surface-50 p-4"><p class="text-xs font-semibold uppercase tracking-wide text-surface-500">Kayıt</p><p class="mt-2 text-xl font-bold">{{ liste.toplam.value }}</p></div></div>
    <div class="mb-4 flex flex-wrap gap-2"><form class="flex min-w-[260px] flex-1 gap-2" @submit.prevent="liste.aramaYap"><input v-model="liste.arama.value" class="alan w-full max-w-md" type="search" placeholder="Fatura no, cari veya açıklama..." /><button class="ikincil-dugme" type="submit">Ara</button></form><select v-model="liste.filtreler.value.durum" class="alan" @change="liste.sayfa.value = 1; liste.yukle()"><option :value="undefined">Tüm durumlar</option><option v-for="(etiket, kod) in FATURA_DURUMLARI" :key="kod" :value="kod">{{ etiket }}</option></select><select v-model="liste.filtreler.value.fatura_turu" class="alan" @change="liste.sayfa.value = 1; liste.yukle()"><option :value="undefined">Tüm türler</option><option v-for="(etiket, kod) in FATURA_TURLERI" :key="kod" :value="kod">{{ etiket }}</option></select><select v-model="liste.filtreler.value.para_birimi" class="alan" @change="liste.sayfa.value = 1; liste.yukle()"><option :value="undefined">Tüm para birimleri</option><option v-for="birim in PARA_BIRIMLERI" :key="birim" :value="birim">{{ birim }}</option></select></div>
    <p v-if="liste.hata.value" class="hata-kutusu mb-4" role="alert">{{ liste.hata.value }}</p>
    <VeriTablosu :basliklar="['Fatura No','Tür / Para','Cari','Tarih / Vade','Matrah','KDV / Tevkifat / Stopaj','Ödenecek / Ödenen','Durum',yazabilir ? 'İşlem' : '']" :bos-mu="!liste.yukleniyor.value && !liste.kayitlar.value.length"><tr v-for="x in liste.kayitlar.value" :key="x.id" class="cursor-pointer hover:bg-primary-50/40" @click="router.push({ name: 'fatura-detay', params: { id: x.id } })"><td class="px-4 py-3 font-medium">{{ x.No }}</td><td class="px-4 py-3"><div>{{ FATURA_TURLERI[x.fatura_turu || 'satis'] }}</div><div class="text-xs text-surface-500">{{ x.para_birimi || 'TRY' }}</div></td><td class="px-4 py-3">{{ x.cari_ad || 'Cari seçilmedi' }}</td><td class="px-4 py-3 text-sm">{{ x.tarih }}<div class="text-surface-500">Vade: {{ x.vade_tarihi || '—' }}</div></td><td class="px-4 py-3">{{ para(x.matrah || x.ara_toplam || x.tutar, x.para_birimi || 'TRY') }}</td><td class="px-4 py-3 text-xs">KDV {{ para(x.kdv || x.kdv_tutari || '0', x.para_birimi || 'TRY') }}<br />TV {{ para(x.tevkifat || x.tevkifat_tutari || '0', x.para_birimi || 'TRY') }} · ST {{ para(x.stopaj || x.stopaj_tutari || '0', x.para_birimi || 'TRY') }}</td><td class="px-4 py-3">{{ para(x.odenecek || x.tutar, x.para_birimi || 'TRY') }}<div class="text-xs text-surface-500">Ödenen {{ para(x.odenen_tutar || '0', x.para_birimi || 'TRY') }}</div></td><td class="px-4 py-3"><span class="rounded-full px-2.5 py-1 text-xs font-semibold" :class="durumSinifi(x.durum)">{{ FATURA_DURUMLARI[x.durum] }}</span><div class="mt-1 text-xs text-surface-500">{{ x.e_fatura_durum || 'gonderilmedi' }}</div></td><td v-if="yazabilir" class="px-4 py-3 whitespace-nowrap" @click.stop><button v-if="x.durum === 'taslak'" class="mr-3 text-sm font-semibold text-primary-700 hover:underline" type="button" @click="duzenle(x)">Düzenle</button><button v-if="x.durum !== 'iptal'" class="text-sm font-semibold text-red-700 hover:underline" type="button" @click="iptalEt(x)">İptal</button></td></tr></VeriTablosu>
    <Sayfalama :sayfa="liste.sayfa.value" :toplam="liste.toplam.value" :yukleniyor="liste.yukleniyor.value" @sayfa-degistir="(s) => { liste.sayfa.value = s; liste.yukle() }" />
    <KayitModal v-if="modalAcik" :baslik="duzenlenenId ? 'Taslak Faturayı Düzenle' : 'Yeni Fatura Belgesi'" :kalici="true" :tasinabilir="true" :kontrollu="true" :buyuk="panelBuyuk" :kucuk="panelKucuk" :genis-icerik="true" :dis-tiklama-kapat="false" @kapat="taslagiKapat" @kucult="panelKucuk = !panelKucuk" @buyut="panelBuyuk = !panelBuyuk"><form class="flex flex-col gap-4" @submit.prevent="kaydet">
      <div class="grid grid-cols-2 gap-4"><label class="etiket">Fatura No *<input v-model="form.No" class="alan" maxlength="30" required /></label><label class="etiket">Belge Durumu<select v-model="form.durum" class="alan"><option value="taslak">Taslak</option><option value="aktif">Aktif</option></select></label></div>
      <div class="grid grid-cols-2 gap-4"><label class="etiket">Fatura Türü<select v-model="form.fatura_turu" class="alan"><option v-for="(etiket, kod) in FATURA_TURLERI" :key="kod" :value="kod">{{ etiket }}</option></select></label><label class="etiket">Senaryo<select v-model="form.senaryo" class="alan"><option value="kagit">Kağıt</option><option value="e_arsiv">e-Arşiv</option><option value="e_fatura">e-Fatura</option></select></label></div>
      <div class="grid grid-cols-3 gap-4"><label class="etiket">Para Birimi<select v-model="form.para_birimi" class="alan"><option v-for="birim in PARA_BIRIMLERI" :key="birim" :value="birim">{{ birim }}</option></select></label><label class="etiket">Kur<input v-model="form.kur" class="alan" type="number" min="0.000001" step="0.000001" /></label><label class="flex items-end gap-2 pb-2 text-sm"><input v-model="form.kdv_dahil_mi" type="checkbox" /> KDV dahil</label></div>
      <div class="grid grid-cols-2 gap-4"><label class="etiket">Cari / Müşteri<select v-model="form.cari" class="alan"><option :value="null">Cari seçilmedi</option><option v-for="x in cariler" :key="x.id" :value="x.id">{{ x.ad }}</option></select></label><label class="etiket">Tahsilat Hesabı<select v-model="form.kasa_banka_hesabi" class="alan"><option :value="null">Hesap seçilmedi</option><option v-for="x in hesaplar" :key="x.id" :value="x.id">{{ x.kod }} / {{ x.ad }}</option></select></label></div>
      <div class="grid grid-cols-2 gap-4"><label class="etiket">Fatura Tarihi *<input v-model="form.tarih" class="alan" type="date" required /></label><label class="etiket">Vade Tarihi<input v-model="form.vade_tarihi" class="alan" type="date" /></label></div>
      <div class="kayit-genis-bolum rounded-2xl border border-surface-200 bg-surface-50 p-4"><div class="mb-3 flex flex-wrap items-start justify-between gap-3"><div><h3 class="font-semibold text-surface-900">Fatura Kalemleri</h3><p class="text-xs text-surface-500">Sütunları yatay kaydırabilir, aşağıdaki ayarlardan genişliklerini kendinize göre değiştirebilirsiniz.</p></div><div class="flex gap-2"><details class="relative"><summary class="ikincil-dugme cursor-pointer list-none">Sütunları ayarla</summary><div class="absolute right-0 top-10 z-10 grid w-72 gap-2 rounded-xl border border-surface-200 bg-white p-3 shadow-xl"><div v-for="sutun in kalemSutunlari.filter((x) => x.etiket)" :key="sutun.anahtar" class="grid grid-cols-[1fr_auto] items-center gap-2 text-xs"><label :for="`sutun-${sutun.anahtar}`">{{ sutun.etiket }}</label><input :id="`sutun-${sutun.anahtar}`" v-model.number="sutun.genislik" type="range" min="60" max="420" step="4" class="w-32" @change="kalemBoyutlariniSakla" /></div></div></details><button class="birincil-dugme" type="button" @click="form.kalemler.push(bosSatir())">+ Satır Ekle</button></div></div><div class="kalemler-scroll"><div class="kalemler-baslik grid gap-2 px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-surface-500" :style="kalemIzgaraStili"><span v-for="sutun in kalemSutunlari" :key="sutun.anahtar">{{ sutun.etiket }}</span></div><div v-for="(x, i) in form.kalemler" :key="i" class="kalem-satir mb-3 grid gap-2 rounded-xl border border-surface-200 bg-white p-3" :style="kalemIzgaraStili"><input v-model="x.poz_no" class="alan" placeholder="Poz no" /><input v-model="x.aciklama" class="alan" placeholder="Mal / hizmet açıklaması" /><input v-model="x.miktar" class="alan" type="number" min="0.0001" step="0.0001" placeholder="Miktar" /><select v-model="x.birim" class="alan"><option>ADET</option><option>SAAT</option><option>KG</option><option>M2</option><option>TON</option></select><input v-model="x.birim_fiyat" class="alan" type="number" min="0" step="0.01" placeholder="Birim fiyat" /><input v-model="x.iskonto_orani" class="alan" type="number" min="0" max="100" step="0.01" placeholder="İskonto %" /><select class="alan" aria-label="Vergi profili" @change="vergiProfilUygula(x, ($event.target as HTMLSelectElement).value)"><option value="">Özel oranlar</option><option v-for="profil in vergiProfilleri" :key="profil.id" :value="profil.id">{{ profil.ad }}</option></select><input v-model="x.kdv_orani" class="alan" type="number" min="0" max="100" step="0.01" placeholder="KDV %" /><input v-model="x.tevkifat_orani" class="alan" type="number" min="0" max="100" step="0.01" placeholder="Tevkifat %" /><input v-model="x.stopaj_orani" class="alan" type="number" min="0" max="100" step="0.01" placeholder="Stopaj %" /><button v-if="form.kalemler.length > 1" class="text-red-700" type="button" title="Satırı kaldır" @click="form.kalemler.splice(i, 1)">×</button><div class="grid-col-span-full flex justify-end text-sm text-surface-600">Satır: <strong class="ml-1">{{ para(satirTutar(x)) }}</strong></div></div></div></div>
      <div class="ml-auto w-full max-w-sm space-y-2 rounded-2xl border border-primary-100 bg-primary-50 p-4 text-sm"><div class="flex justify-between"><span>Ara toplam</span><strong>{{ para(araToplam) }}</strong></div><div class="flex justify-between"><span>KDV</span><strong>{{ para(kdvToplam) }}</strong></div><div class="flex justify-between"><span>Tevkifat</span><strong class="text-red-700">- {{ para(tevkifatToplam) }}</strong></div><div class="flex justify-between"><span>Stopaj</span><strong class="text-red-700">- {{ para(stopajToplam) }}</strong></div><div class="flex justify-between border-t border-primary-200 pt-2 text-base font-bold"><span>Genel toplam</span><strong>{{ para(genelToplam) }}</strong></div></div>
      <label class="flex items-center gap-2 text-sm"><input v-model="form.alacakli" type="checkbox" /> Alacaklı / satış faturası</label><label class="etiket">Açıklama<textarea v-model="form.aciklama" class="alan" rows="2" /></label><p v-if="formHata" class="hata-kutusu" role="alert">{{ formHata }}</p><div class="flex justify-end gap-2"><button class="ikincil-dugme" type="button" @click="modalAcik = false">Vazgeç</button><button class="birincil-dugme" type="submit" :disabled="kaydediliyor">{{ kaydediliyor ? 'Kaydediliyor...' : 'Faturayı Kaydet' }}</button></div>
    </form></KayitModal>
  </div>
</template>

<style scoped>
.kalemler-scroll {
  overflow-x: auto;
  overscroll-behavior-inline: contain;
  padding-bottom: .35rem;
}

.kalemler-baslik,
.kalem-satir {
  width: 100%;
  min-width: 0;
}

.kalem-satir > :last-child {
  grid-column: 1 / -1;
}

.kalem-satir .alan {
  min-width: 0;
}

@media (max-width: 680px) {
  .kalemler-baslik,
  .kalem-satir {
    min-width: 760px;
  }
}
</style>
