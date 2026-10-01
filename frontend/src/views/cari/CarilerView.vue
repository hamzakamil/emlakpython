<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import IlIlceSecimi from '@/components/IlIlceSecimi.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import ExcelAktarim, { type ExcelSutun } from '@/components/ExcelAktarim.vue'
import VeriKaynakRozeti from '@/components/VeriKaynakRozeti.vue'
import { cariApi } from '@/services/cariApi'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import { CARI_TIPLERI, CARI_TURLERI, type Cari } from '@/types/cari'
import { yazabilirMi } from '@/utils/yetki'
import type { Proje } from '@/types/insaat'

const auth = useAuthStore()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))
const aktifTenantVar = computed(() => Boolean(auth.kullanici?.tenant || auth.seciliTenantId))
const L = useKayitListesi<Cari>('/cari/cariler/')
const excelSutunlari: ExcelSutun[] = [
  { key: 'ad', label: 'Ad / Unvan', required: true }, { key: 'tip', label: 'Tip', templateValue: 'diger' },
  { key: 'tur', label: 'Tür', templateValue: 'bireysel' }, { key: 'vergi_no', label: 'Vergi No' },
  { key: 'telefon', label: 'Telefon' }, { key: 'eposta', label: 'E-posta' },
]
async function excelAl(rows: Record<string, unknown>[]): Promise<void> {
  try {
    for (const row of rows) await cariApi.cariler.olustur(row)
    await L.yukle()
    L.hata.value = ''
  } catch (error) {
    L.hata.value = `Excel içe aktarma kısmi olarak tamamlandı: ${error instanceof Error ? error.message : 'geçersiz veri.'}`
    await L.yukle()
  }
}

type Form = {
  ad: string
  tip: string
  tur: string
  vergi_no: string
  vergi_dairesi: string
  tc_kimlik_no: string
  ticaret_sicil_no: string
  mersis_no: string
  telefon: string
  telefonlar: string[]
  iban: string
  adres: string
  fatura_adresi: string
  sevk_adresi: string
  il: string
  ilce: string
  posta_kodu: string
  yetkili_kisi: string
  yetkili_telefon: string
  yetkili_kisiler: Array<{ ad: string; telefon: string }>
  cep_telefonu: string
  cep_telefonlari: string[]
  eposta: string
  epostalar: string[]
  ulke: string
  eski_adres: string
  web_sitesi: string
  banka_adi: string
  sube_adi: string
  odeme_sekli: string
  vade_gunu: number
  iskonto_orani: string
  risk_limiti: string
  para_birimi: string
  muhasebe_hesap_kodu: string
  e_fatura_profili: string
  grup: string
  proje: number | null
  notlar: string
  is_active: boolean
}

const projeler = ref<Proje[]>([])
const aktifSekme = ref<'genel' | 'finans'>('genel')
const kimlikGirisi = ref('')
const turUyarisi = ref('')
const eskiAdresAcik = ref(false)
const ulkeAramaAcik = ref(false)
let turUyariZamani: ReturnType<typeof setTimeout> | undefined
const ulkeSecenekleri = ['Türkiye', 'Almanya', 'Amerika Birleşik Devletleri', 'Birleşik Krallık', 'Fransa', 'Hollanda']
const filtreliUlkeler = computed(() => {
  const arama = Fm.form.value.ulke.trim().toLocaleLowerCase('tr-TR')
  return ulkeSecenekleri.filter((ulke) => !arama || ulke.toLocaleLowerCase('tr-TR').includes(arama))
})
const Fm = useKayitFormu<Cari, Form>(
  cariApi.cariler,
  () => ({ ad: '', tip: 'diger', tur: 'bireysel', vergi_no: '', vergi_dairesi: '', tc_kimlik_no: '', ticaret_sicil_no: '', mersis_no: '', telefon: '', telefonlar: [''], iban: '', adres: '', eski_adres: '', ulke: 'Türkiye', fatura_adresi: '', sevk_adresi: '', il: '', ilce: '', posta_kodu: '', yetkili_kisi: '', yetkili_telefon: '', yetkili_kisiler: [{ ad: '', telefon: '' }], cep_telefonu: '', cep_telefonlari: [''], eposta: '', epostalar: [''], web_sitesi: '', banka_adi: '', sube_adi: '', odeme_sekli: 'havale', vade_gunu: 0, iskonto_orani: '0', risk_limiti: '0', para_birimi: 'TRY', muhasebe_hesap_kodu: '', e_fatura_profili: 'kagit', grup: '', proje: null, notlar: '', is_active: true }),
  (c) => ({ ad: c.ad, tip: c.tip, tur: c.tur, vergi_no: c.vergi_no || '', vergi_dairesi: c.vergi_dairesi || '', tc_kimlik_no: c.tc_kimlik_no || '', ticaret_sicil_no: c.ticaret_sicil_no || '', mersis_no: c.mersis_no || '', telefon: c.telefon || '', telefonlar: c.telefonlar?.length ? c.telefonlar : [c.telefon || ''], iban: '', adres: c.adres || '', eski_adres: c.eski_adres || '', ulke: c.ulke || 'Türkiye', fatura_adresi: c.fatura_adresi || '', sevk_adresi: c.sevk_adresi || '', il: c.il || '', ilce: c.ilce || '', posta_kodu: c.posta_kodu || '', yetkili_kisi: c.yetkili_kisi || '', yetkili_telefon: c.yetkili_telefon || '', yetkili_kisiler: c.yetkili_kisiler?.length ? c.yetkili_kisiler : [{ ad: c.yetkili_kisi || '', telefon: c.yetkili_telefon || '' }], cep_telefonu: c.cep_telefonu || '', cep_telefonlari: c.cep_telefonlari?.length ? c.cep_telefonlari : [c.cep_telefonu || ''], eposta: c.eposta || '', epostalar: c.epostalar?.length ? c.epostalar : [c.eposta || ''], web_sitesi: c.web_sitesi || '', banka_adi: c.banka_adi || '', sube_adi: c.sube_adi || '', odeme_sekli: c.odeme_sekli || 'havale', vade_gunu: c.vade_gunu || 0, iskonto_orani: c.iskonto_orani || '0', risk_limiti: c.risk_limiti || '0', para_birimi: c.para_birimi || 'TRY', muhasebe_hesap_kodu: c.muhasebe_hesap_kodu || '', e_fatura_profili: c.e_fatura_profili || 'kagit', grup: c.grup || '', proje: c.proje || null, notlar: c.notlar || '', is_active: c.is_active }),
  (f) => ({ ...f, ad: f.ad.trim(), vergi_no: f.vergi_no.trim(), vergi_dairesi: f.vergi_dairesi.trim(), tc_kimlik_no: f.tc_kimlik_no.trim(), telefon: f.telefon.trim(), iban: f.iban.trim(), adres: f.adres.trim(), fatura_adresi: f.fatura_adresi.trim(), sevk_adresi: f.sevk_adresi.trim(), eposta: f.eposta.trim(), web_sitesi: f.web_sitesi.trim() }),
  (f) => {
    if (!aktifTenantVar.value) return 'Cari açmak için önce üst menüden bir firma seçmelisiniz.'
    if (!f.ad.trim()) return 'Ad / unvan zorunludur.'
    if (f.vergi_no && !/^\d{10}$/.test(f.vergi_no.trim())) return 'VKN 10 hane olmalıdır.'
    if (f.iban && !/^TR\d{24}$/i.test(f.iban.replace(/\s/g, ''))) return 'IBAN, TR ile başlayan 26 karakter olmalıdır.'
    if (f.tc_kimlik_no && !/^\d{11}$/.test(f.tc_kimlik_no)) return 'T.C. kimlik no 11 hane olmalıdır.'
    if (!f.vergi_no && !f.tc_kimlik_no) return 'VKN / T.C. Kimlik No alanına 10 veya 11 hane girilmelidir.'
    if (f.vade_gunu < 0 || f.vade_gunu > 365) return 'Vade günü 0 ile 365 arasında olmalıdır.'
    if (Number(f.iskonto_orani) < 0 || Number(f.iskonto_orani) > 100) return 'İskonto oranı 0 ile 100 arasında olmalıdır.'
    if (Number(f.risk_limiti) < 0) return 'Risk limiti 0’dan küçük olamaz.'
    return ''
  },
)
const kimlikNo = computed({
  get: () => kimlikGirisi.value,
  set: (deger: string) => {
    const temiz = deger.replace(/\D/g, '').slice(0, 11)
    kimlikGirisi.value = temiz
    Fm.form.value.vergi_no = temiz.length === 10 ? temiz : ''
    Fm.form.value.tc_kimlik_no = temiz.length === 11 ? temiz : ''
    if (temiz.length === 10) Fm.form.value.tur = 'kurumsal'
    else if (temiz.length === 11) Fm.form.value.tur = 'bireysel'
    if (turUyariZamani) clearTimeout(turUyariZamani)
    if (temiz.length === 10) turUyarisi.value = '10 hane algılandı: Kurumsal öneriliyor.'
    else if (temiz.length === 11) turUyarisi.value = '11 hane algılandı: Bireysel öneriliyor.'
    else turUyarisi.value = ''
    if (turUyarisi.value) turUyariZamani = setTimeout(() => { turUyarisi.value = '' }, 3000)
  },
})
function yeniCariAc(): void {
  if (!aktifTenantVar.value) {
    Fm.formHata.value = 'Cari açmak için önce üst menüden bir firma seçmelisiniz.'
    return
  }
  aktifSekme.value = 'genel'
  kimlikGirisi.value = ''
  eskiAdresAcik.value = false
  turUyarisi.value = ''
  Fm.yeniAc()
}

function cariDuzenleAc(cari: Cari): void {
  aktifSekme.value = 'genel'
  kimlikGirisi.value = cari.vergi_no || cari.tc_kimlik_no || ''
  eskiAdresAcik.value = false
  turUyarisi.value = ''
  Fm.duzenleAc(cari)
}

function satirEkle(alan: 'telefonlar' | 'cep_telefonlari' | 'epostalar'): void {
  Fm.form.value[alan].push('')
}

function yetkiliEkle(): void {
  Fm.form.value.yetkili_kisiler.push({ ad: '', telefon: '' })
}

function ulkeSec(value: string): void {
  Fm.form.value.ulke = value
  ulkeAramaAcik.value = false
}

function ulkeAramasiniKapat(): void {
  window.setTimeout(() => { ulkeAramaAcik.value = false }, 120)
}

async function yukle(): Promise<void> {
  await L.yukle()
}

void yukle()
onMounted(async () => {
  try {
    projeler.value = await tumunuGetir(insaatApi.projeler.liste, { is_active: true })
  } catch {
    projeler.value = []
  }
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">Cari</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Cari Kartlar</h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" :disabled="!aktifTenantVar" :title="aktifTenantVar ? 'Yeni cari kartı oluştur' : 'Önce bir firma seçin'" @click="yeniCariAc">+ Yeni Cari</button>
    </div>
    <div class="mb-4"><ExcelAktarim :rows="L.kayitlar.value as unknown as Record<string, unknown>[]" :columns="excelSutunlari" filename="cariler" @imported="excelAl" /></div>

    <p v-if="yazabilir && !aktifTenantVar" class="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800" role="status">
      Cari kartı oluşturmak için aktif bir firma kapsamı seçilmelidir. Üst menüdeki <strong>Firma</strong> seçicisinden işlem yapılacak firmayı seçin.
    </p>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap()">
        <input v-model="L.arama.value" type="search" placeholder="Ad veya vergi dairesi ile ara..." class="alan w-full max-w-sm" />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.tip" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm tipler</option>
        <option v-for="(etiket, kod) in CARI_TIPLERI" :key="kod" :value="kod">{{ etiket }}</option>
      </select>
    </div>

    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>
    <VeriTablosu :basliklar="['Ad / Unvan', 'Tip', 'Tür', 'Telefon', 'Durum', yazabilir ? 'İşlem' : '']" :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0">
      <tr v-for="c in L.kayitlar.value" :key="c.id" class="transition-colors hover:bg-surface-100/60">
        <td class="max-w-xs truncate px-4 py-3 font-medium"><VeriKaynakRozeti :aktif="auth.gelistiriciModu" tablo="cari_cari" sutun="ad" alan="Cari.ad" tip="varchar(255)" api="GET /api/v1/cari/cariler/" :iliski="`tenant_id=${c.tenant}`">{{ c.ad }}</VeriKaynakRozeti></td>
        <td class="px-4 py-3"><VeriKaynakRozeti :aktif="auth.gelistiriciModu" tablo="cari_cari" sutun="tip" alan="Cari.tip" tip="varchar(20)">{{ CARI_TIPLERI[c.tip] || c.tip }}</VeriKaynakRozeti></td>
        <td class="px-4 py-3"><VeriKaynakRozeti :aktif="auth.gelistiriciModu" tablo="cari_cari" sutun="tur" alan="Cari.tur" tip="varchar(20)">{{ CARI_TURLERI[c.tur] || c.tur }}</VeriKaynakRozeti></td>
        <td class="px-4 py-3 text-surface-600">{{ c.telefon_maskeli || '—' }}</td>
        <td class="px-4 py-3"><span :class="c.is_active ? 'durum-aktif' : 'durum-pasif'">{{ c.is_active ? 'Aktif' : 'Pasif' }}</span></td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">        <button type="button" class="text-sm font-medium text-primary-700 hover:underline" @click="cariDuzenleAc(c)">Düzenle</button></td>
      </tr>
    </VeriTablosu>
    <Sayfalama :sayfa="L.sayfa.value" :toplam="L.toplam.value" :yukleniyor="L.yukleniyor.value" @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }" />

    <KayitModal v-if="Fm.modalAcik.value" :baslik="Fm.duzenlenen.value ? 'Cariyi Düzenle' : 'Yeni Cari'" @kapat="Fm.modalAcik.value = false">
      <form class="cari-form" @submit.prevent="Fm.kaydet(L.yukle)">
        <nav class="cari-sekmeler" aria-label="Cari kart bölümleri">
          <button type="button" :class="{ aktif: aktifSekme === 'genel' }" :aria-selected="aktifSekme === 'genel'" @click="aktifSekme = 'genel'">Genel Bilgiler</button>
          <button type="button" :class="{ aktif: aktifSekme === 'finans' }" :aria-selected="aktifSekme === 'finans'" @click="aktifSekme = 'finans'">Finansal &amp; Sınıflandırma</button>
        </nav>

        <section v-if="aktifSekme === 'genel'" class="cari-sekme-icerik" aria-label="Genel Bilgiler">
          <div class="cari-bolum">
            <h3>Genel Bilgiler</h3>
            <div class="cari-form-grid cari-form-grid-genel">
              <label class="etiket cari-tam"><span class="etiket-baslik">Ad / Unvan <span class="text-red-600">*</span></span><input v-model="Fm.form.value.ad" required maxlength="255" type="text" class="alan" placeholder="Örn. Ahmet Yılmaz veya ABC İnşaat A.Ş." /></label>
              <label class="etiket"><span class="etiket-baslik">VKN / T.C. Kimlik No</span><input v-model="kimlikNo" inputmode="numeric" maxlength="11" type="text" class="alan" placeholder="10 veya 11 hane" /><small v-if="turUyarisi" class="cari-tur-uyarisi" role="status">{{ turUyarisi }}</small></label>
              <label class="etiket">Vergi Dairesi<input v-model="Fm.form.value.vergi_dairesi" maxlength="150" type="text" class="alan" /></label>
            </div>
            <div class="cari-kompakt-grid">
              <label class="etiket">Cari Tipi<select v-model="Fm.form.value.tip" class="alan"><option v-for="(etiket, kod) in CARI_TIPLERI" :key="kod" :value="kod">{{ etiket }}</option></select></label>
              <label class="etiket"><span class="etiket-baslik">Tür <span class="text-red-600">*</span></span><select v-model="Fm.form.value.tur" class="alan"><option v-for="(etiket, kod) in CARI_TURLERI" :key="kod" :value="kod">{{ etiket }}</option></select></label>
              <label class="etiket">Ticaret Sicil No<input v-model="Fm.form.value.ticaret_sicil_no" maxlength="50" type="text" class="alan" /></label>
              <label class="etiket">MERSİS No<input v-model="Fm.form.value.mersis_no" maxlength="16" inputmode="numeric" type="text" class="alan" /></label>
            </div>
          </div>

          <div class="cari-bolum">
            <h3>Adres Bilgileri</h3>
            <div class="cari-form-grid">
              <IlIlceSecimi v-model:il="Fm.form.value.il" v-model:ilce="Fm.form.value.ilce" />
              <label class="etiket cari-tam">Fatura Adresi<textarea v-model="Fm.form.value.fatura_adresi" rows="3" class="alan" /></label>
              <label class="etiket cari-tam">Sevk Adresi<textarea v-model="Fm.form.value.sevk_adresi" rows="3" class="alan" /></label>
              <label class="etiket">Posta Kodu<input v-model="Fm.form.value.posta_kodu" maxlength="10" type="text" class="alan" /></label>
              <label class="etiket ülke-alanı">Ülke<input v-model="Fm.form.value.ulke" class="alan" maxlength="100" autocomplete="country-name" placeholder="Ülke yazın veya seçin" @focus="ulkeAramaAcik = true" @blur="ulkeAramasiniKapat" /><div v-if="ulkeAramaAcik && filtreliUlkeler.length" class="autocomplete-list" role="listbox" aria-label="Ülke önerileri"><button v-for="ulke in filtreliUlkeler" :key="ulke" type="button" class="autocomplete-option" @mousedown.prevent="ulkeSec(ulke)">{{ ulke }}</button></div></label>
              <label class="etiket cari-tam">Adres<textarea v-model="Fm.form.value.adres" rows="2" class="alan" /><button v-if="Fm.form.value.eski_adres" type="button" class="eski-adres-link" @click="eskiAdresAcik = !eskiAdresAcik">{{ eskiAdresAcik ? 'Eski adresi gizle' : 'Eski adresi göster' }}</button><small v-if="eskiAdresAcik" class="eski-adres">{{ Fm.form.value.eski_adres }}</small></label>
            </div>
          </div>

          <div class="cari-bolum">
            <h3>İletişim</h3>
            <div class="cari-form-grid">
              <div class="etiket"><span class="etiket-baslik">Cep Telefonu</span><div v-for="(_, index) in Fm.form.value.cep_telefonlari" :key="index" class="cari-coklu-satir"><input v-model="Fm.form.value.cep_telefonlari[index]" maxlength="20" type="tel" class="alan" /><button v-if="index === Fm.form.value.cep_telefonlari.length - 1" type="button" class="coklu-ekle" aria-label="Cep telefonu ekle" @click="satirEkle('cep_telefonlari')">+</button></div></div>
              <div class="etiket"><span class="etiket-baslik">Telefon</span><div v-for="(_, index) in Fm.form.value.telefonlar" :key="index" class="cari-coklu-satir"><input v-model="Fm.form.value.telefonlar[index]" maxlength="20" type="tel" class="alan" /><button v-if="index === Fm.form.value.telefonlar.length - 1" type="button" class="coklu-ekle" aria-label="Telefon ekle" @click="satirEkle('telefonlar')">+</button></div></div>
              <div class="etiket"><span class="etiket-baslik">E-posta</span><div v-for="(_, index) in Fm.form.value.epostalar" :key="index" class="cari-coklu-satir"><input v-model="Fm.form.value.epostalar[index]" type="email" class="alan" /><button v-if="index === Fm.form.value.epostalar.length - 1" type="button" class="coklu-ekle" aria-label="E-posta ekle" @click="satirEkle('epostalar')">+</button></div></div>
              <label class="etiket">Web Sitesi<input v-model="Fm.form.value.web_sitesi" type="url" class="alan" placeholder="https://" /></label>
              <div class="etiket yetkili-iletisim"><div v-for="(yetkili, index) in Fm.form.value.yetkili_kisiler" :key="index" class="yetkili-satir"><label class="etiket"><span class="etiket-baslik">Yetkili Kişi</span><input v-model="yetkili.ad" maxlength="150" type="text" class="alan" placeholder="Yetkili kişi" /></label><label class="etiket"><span class="etiket-baslik">Yetkili Telefon</span><input v-model="yetkili.telefon" maxlength="20" type="tel" class="alan" placeholder="Yetkili telefon" /></label><button v-if="index === Fm.form.value.yetkili_kisiler.length - 1" type="button" class="coklu-ekle" aria-label="Yetkili kişi ekle" @click="yetkiliEkle">+</button></div></div>
            </div>
          </div>
        </section>

        <section v-else class="cari-sekme-icerik" aria-label="Finansal ve Sınıflandırma">
          <div class="cari-form-grid">
          <label class="etiket">Banka Adı<input v-model="Fm.form.value.banka_adi" maxlength="150" type="text" class="alan" /></label>
          <label class="etiket">Şube Adı<input v-model="Fm.form.value.sube_adi" maxlength="150" type="text" class="alan" /></label>
          <label class="etiket">IBAN<input v-model="Fm.form.value.iban" maxlength="34" type="text" class="alan" placeholder="TR..." /></label>
          <label class="etiket">Ödeme Şekli<select v-model="Fm.form.value.odeme_sekli" class="alan"><option value="havale">Havale</option><option value="nakit">Nakit</option><option value="cek">Çek</option><option value="senet">Senet</option><option value="kredi_karti">Kredi Kartı</option><option value="takas">Takas</option></select></label>
          <label class="etiket">Vade Günü<input v-model.number="Fm.form.value.vade_gunu" min="0" max="365" type="number" class="alan" /></label>
          <label class="etiket">İskonto Oranı<input v-model="Fm.form.value.iskonto_orani" min="0" max="100" step="0.01" type="number" class="alan" /></label>
          <label class="etiket">Risk Limiti<input v-model="Fm.form.value.risk_limiti" min="0" step="0.01" type="number" class="alan" /></label>
          <label class="etiket">Para Birimi<select v-model="Fm.form.value.para_birimi" class="alan"><option>TRY</option><option>USD</option><option>EUR</option><option>GBP</option></select></label>
          <label class="etiket">Muhasebe Hesap Kodu<input v-model="Fm.form.value.muhasebe_hesap_kodu" maxlength="30" type="text" class="alan" placeholder="120.01.001" /></label>
          <label class="etiket">e-Fatura Profili<select v-model="Fm.form.value.e_fatura_profili" class="alan"><option value="e_fatura">e-Fatura</option><option value="e_arsiv">e-Arşiv</option><option value="kagit">Kağıt</option></select></label>
          <label class="etiket">Grup<input v-model="Fm.form.value.grup" maxlength="150" type="text" class="alan" placeholder="A Grubu Tedarikçi" /></label>
          <label class="etiket">Proje<select v-model="Fm.form.value.proje" class="alan"><option :value="null">Proje seçilmedi</option><option v-for="proje in projeler" :key="proje.id" :value="proje.id">{{ proje.proje_kodu }} — {{ proje.ad }}</option></select></label>
          </div>
        </section>

        <section class="cari-notlar" aria-label="Notlar">
          <div class="cari-notlar-baslik"><span>Notlar</span><small>Sekmeler arasında geçiş yaparken görünür kalır</small></div>
          <textarea v-model="Fm.form.value.notlar" rows="3" class="alan" placeholder="Cari kartla ilgili notlar, özel koşullar veya hatırlatmalar..." />
        </section>

        <label class="flex items-center gap-2 text-sm text-surface-700"><input v-model="Fm.form.value.is_active" type="checkbox" /> Aktif</label>
        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2"><button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button><button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">{{ Fm.kaydediliyor.value ? 'Kaydediliyor...' : 'Kaydet' }}</button></div>
      </form>
    </KayitModal>
  </div>
</template>

<style scoped>
.cari-form {
  width: min(100%, 58rem);
  margin: 0 auto;
  gap: .75rem;
}

.cari-sekmeler {
  display: flex;
  gap: .25rem;
  overflow-x: auto;
  border-bottom: 1px solid #dbe4e8;
  padding: 0 .25rem;
}

.cari-sekmeler button {
  position: relative;
  flex: 0 0 auto;
  padding: .6rem .75rem .55rem;
  color: #64748b;
  font-size: .72rem;
  font-weight: 700;
  letter-spacing: .01em;
  white-space: nowrap;
  transition: color .16s ease, background-color .16s ease;
}

.cari-sekmeler button:hover {
  background: #f0f7f7;
  color: #0f6973;
}

.cari-sekmeler button.aktif {
  color: #0f6973;
}

.cari-sekmeler button.aktif::after {
  position: absolute;
  right: .55rem;
  bottom: -.0625rem;
  left: .55rem;
  height: 2px;
  border-radius: 999px;
  background: #0f6973;
  content: '';
}

.cari-sekme-icerik {
  min-height: 13rem;
  padding: .85rem .25rem .25rem;
}

.cari-bolum {
  border-bottom: 1px solid #e2e8f0;
  padding: .25rem 0 1rem;
  margin-bottom: 1rem;
}

.cari-bolum:last-child {
  border-bottom: 0;
  margin-bottom: 0;
}

.cari-bolum h3 {
  display: flex;
  align-items: center;
  gap: .5rem;
  margin: 0 0 .7rem;
  color: #0f6973;
  font-size: .72rem;
  font-weight: 850;
  letter-spacing: .1em;
  text-transform: uppercase;
}

.cari-bolum h3::after {
  height: 1px;
  flex: 1;
  background: #dbe4e8;
  content: '';
}

.cari-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: .6rem .85rem;
}

.cari-form-grid-genel {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.cari-kompakt-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: .55rem;
  margin-top: .65rem;
}

.cari-kompakt-grid .etiket {
  min-width: 0;
  font-size: .64rem;
}

.cari-kompakt-grid .alan {
  min-height: 1.95rem;
  padding: .32rem .45rem;
  font-size: .72rem;
}

.cari-tam {
  grid-column: 1 / -1;
}

.ülke-alanı {
  position: relative;
}

.ülke-alanı .autocomplete-list {
  position: absolute;
  z-index: 20;
  top: calc(100% + .2rem);
  right: 0;
  left: 0;
  max-height: 13rem;
  overflow-y: auto;
  border: 1px solid #b8d2d5;
  border-radius: .5rem;
  background: #fff;
  box-shadow: 0 .5rem 1.25rem rgb(15 105 115 / 14%);
}

.ülke-alanı .autocomplete-option {
  display: block;
  width: 100%;
  border: 0;
  padding: .48rem .65rem;
  background: transparent;
  color: #334155;
  font-size: .75rem;
  text-align: left;
}

.ülke-alanı .autocomplete-option:hover,
.ülke-alanı .autocomplete-option:focus-visible {
  background: #e8f4f4;
  color: #0f6973;
  outline: none;
}

.cari-form :deep(.etiket) {
  gap: .25rem;
  color: #475569;
  font-size: .69rem;
  font-weight: 700;
}

.cari-form :deep(.etiket-baslik) {
  display: block;
  min-height: 1rem;
  line-height: 1rem;
}

.cari-form :deep(.alan) {
  min-height: 2.15rem;
  max-width: 100%;
  border-radius: .45rem;
  padding: .42rem .6rem;
  font-size: .78rem;
}

.cari-tur-bilgi {
  display: flex;
  min-height: 2.15rem;
  align-items: center;
  border-radius: .45rem;
  padding: .42rem .6rem;
  font-size: .78rem;
  font-weight: 800;
}

.cari-tur-bilgi.kurumsal {
  border: 1px solid #93c5fd;
  background: #eff6ff;
  color: #1d4ed8;
}

.cari-tur-bilgi.bireysel {
  border: 1px solid #86efac;
  background: #f0fdf4;
  color: #15803d;
}

.cari-tur-bilgi.bekliyor {
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #64748b;
  font-weight: 600;
}

.cari-tur-uyarisi {
  color: #b45309;
  font-size: .68rem;
  font-weight: 700;
}

.cari-coklu-satir {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  align-items: center;
  gap: .35rem;
  margin-bottom: .35rem;
}

.yetkili-iletisim {
  grid-column: 1 / -1;
}

.yetkili-satir {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  align-items: end;
  gap: .55rem;
}

.yetkili-satir > .etiket {
  min-width: 0;
}

.coklu-ekle {
  display: inline-flex;
  width: 2rem;
  height: 2rem;
  align-items: center;
  justify-content: center;
  border: 1px solid #99c2c6;
  border-radius: .45rem;
  color: #0f6973;
  font-size: 1.1rem;
  font-weight: 800;
}

.eski-adres-link {
  align-self: flex-start;
  color: #0f6973;
  font-size: .68rem;
  font-weight: 700;
  text-align: left;
}

.eski-adres {
  border-left: 2px solid #cbd5e1;
  padding-left: .5rem;
  color: #64748b;
  font-size: .7rem;
  font-weight: 500;
  white-space: pre-wrap;
}

.cari-form textarea.alan {
  min-height: 4.3rem;
  resize: vertical;
}

.cari-notlar {
  border-top: 1px solid #dbe4e8;
  padding: .7rem .25rem 0;
}

.cari-notlar-baslik {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: .75rem;
  margin-bottom: .3rem;
  color: #334155;
  font-size: .72rem;
  font-weight: 800;
}

.cari-notlar-baslik small {
  color: #94a3b8;
  font-size: .64rem;
  font-weight: 500;
}

.cari-notlar .alan {
  width: 100%;
  max-width: none;
}

@media (max-width: 640px) {
  .cari-form-grid,
  .cari-form-grid-genel {
    grid-template-columns: minmax(0, 1fr);
  }

  .cari-kompakt-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .cari-coklu-satir {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .cari-coklu-satir .alan:first-child {
    grid-column: 1 / -1;
  }

  .yetkili-satir {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  }

  .cari-sekme-icerik {
    min-height: 0;
  }

  .cari-notlar-baslik {
    align-items: flex-start;
    flex-direction: column;
    gap: .1rem;
  }
}
</style>
