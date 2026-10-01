<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import KayitModal from '@/components/KayitModal.vue'
import { hataMesaji } from '@/services/apiClient'
import { insaatApi, tumunuGetir } from '@/services/insaatApi'
import type { Poz, Proje, YaklasikMaliyet, YaklasikMaliyetSatiri } from '@/types/insaat'

const projeler = ref<Proje[]>([])
const pozlar = ref<Poz[]>([])
const maliyetler = ref<YaklasikMaliyet[]>([])
const secili = ref<YaklasikMaliyet | null>(null)
const satirlar = ref<YaklasikMaliyetSatiri[]>([])
const proje = ref<number | null>(null)
const modalAcik = ref(false)
const satirModalAcik = ref(false)
const hata = ref('')
const yukleniyor = ref(false)
const form = ref({ proje: null as number | null, yil: new Date().getFullYear(), ad: 'Yaklaşık Maliyet', aciklama: '' })
const satirForm = ref({ poz: null as number | null, mahal: null as number | null, miktar: '', aciklama: '' })

const filtreli = computed(() => proje.value ? maliyetler.value.filter((x) => x.proje === proje.value) : maliyetler.value)
const satirToplami = computed(() => satirlar.value.reduce((sum, x) => sum + Number(x.toplam_tutar || x.satir_tutari || 0), 0))
const aktifToplam = computed(() => Number(secili.value?.toplam_tutar || satirToplami.value))
const para = (value: string | number) => new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 2 }).format(Number(value) || 0)
const projeAdi = (id: number) => projeler.value.find((x) => x.id === id)?.ad || `#${id}`
const pozAdi = (id: number) => pozlar.value.find((x) => x.id === id)?.ad || `Poz #${id}`

async function yukle(): Promise<void> {
  yukleniyor.value = true; hata.value = ''
  try {
    maliyetler.value = await tumunuGetir(insaatApi.yaklasikMaliyetler.liste, proje.value ? { proje: proje.value } : {})
    if (secili.value) {
      secili.value = maliyetler.value.find((x) => x.id === secili.value?.id) || null
      if (secili.value) await detayYukle(secili.value)
    }
  } catch (e) { hata.value = hataMesaji(e) } finally { yukleniyor.value = false }
}
async function detayYukle(item: YaklasikMaliyet): Promise<void> {
  secili.value = item
  try {
    const cevap = await insaatApi.yaklasikMaliyetler.tek(item.id)
    secili.value = cevap
    satirlar.value = cevap.satirlar || await tumunuGetir(insaatApi.yaklasikMaliyetSatirlari.liste, { yaklasik_maliyet: item.id })
  } catch (e) { hata.value = hataMesaji(e) }
}
function yeniAc(): void {
  form.value = { proje: proje.value, yil: new Date().getFullYear(), ad: 'Yaklaşık Maliyet', aciklama: '' }; modalAcik.value = true
}
async function kaydet(): Promise<void> {
  if (!form.value.proje) { hata.value = 'Proje seçmelisiniz.'; return }
  try { const yeni = await insaatApi.yaklasikMaliyetler.olustur(form.value); modalAcik.value = false; await yukle(); await detayYukle(yeni) }
  catch (e) { hata.value = hataMesaji(e) }
}
async function satirKaydet(): Promise<void> {
  if (!secili.value || !satirForm.value.poz || !satirForm.value.miktar) { hata.value = 'Poz ve miktar zorunludur.'; return }
  try {
    await insaatApi.yaklasikMaliyetSatirlari.olustur({ ...satirForm.value, yaklasik_maliyet: secili.value.id })
    await insaatApi.yaklasikMaliyetler.hesapla(secili.value.id)
    satirModalAcik.value = false; await yukle()
  } catch (e) { hata.value = hataMesaji(e) }
}
async function hesapla(): Promise<void> {
  if (!secili.value) return
  try { await insaatApi.yaklasikMaliyetler.hesapla(secili.value.id); await yukle() } catch (e) { hata.value = hataMesaji(e) }
}
async function revize(): Promise<void> {
  if (!secili.value) return
  try { const yeni = await insaatApi.yaklasikMaliyetler.revize(secili.value.id, { ad: `${secili.value.ad} — Revizyon` }); await yukle(); await detayYukle(yeni) }
  catch (e) { hata.value = hataMesaji(e) }
}
async function mahaldenOlustur(): Promise<void> {
  if (!secili.value) return
  try { await insaatApi.yaklasikMaliyetler.mahalListesindenOlustur(secili.value.id); await yukle() } catch (e) { hata.value = hataMesaji(e) }
}
onMounted(async () => {
  try { [projeler.value, pozlar.value] = await Promise.all([tumunuGetir(insaatApi.projeler.liste), tumunuGetir(insaatApi.pozlar.liste)]) } catch (e) { hata.value = hataMesaji(e) }
  await yukle()
})
</script>

<template>
  <div class="yaklasik-sayfa">
    <header class="sayfa-baslik"><div><p class="eyebrow">İNŞAAT / FİYAT ÇALIŞMASI</p><h1>Yaklaşık Maliyet</h1><p class="aciklama">Poz fiyatlarını tek bir görünür bütçede toplayın; revizyonları ve snapshot tutarları izleyin.</p></div><button class="birincil-dugme" type="button" @click="yeniAc">+ Yeni maliyet</button></header>
    <div class="toolbar"><select v-model="proje" class="alan" @change="yukle"><option :value="null">Tüm projeler</option><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} · {{ x.ad }}</option></select><span class="kayit-sayisi">{{ filtreli.length }} kayıt</span></div>
    <p v-if="hata" class="hata-kutusu" role="alert">{{ hata }}</p>
    <div class="maliyet-grid">
      <section class="liste-karti"><div class="liste-ust"><span>Maliyet kayıtları</span><span class="durum">{{ yukleniyor ? 'Yükleniyor…' : 'Güncel' }}</span></div><div class="tablo-kaydir"><table><thead><tr><th>Proje / başlık</th><th>Yıl</th><th>Versiyon</th><th class="sag">Toplam</th></tr></thead><tbody><tr v-for="x in filtreli" :key="x.id" :class="{ secili: x.id === secili?.id }" @click="detayYukle(x)"><td><strong>{{ x.ad }}</strong><small>{{ projeAdi(x.proje) }}</small></td><td>{{ x.yil }}</td><td>v{{ x.versiyon }}</td><td class="sag fiyat">{{ para(x.toplam_tutar) }}</td></tr><tr v-if="!filtreli.length"><td colspan="4" class="bos">Henüz yaklaşık maliyet kaydı yok.</td></tr></tbody></table></div></section>
      <aside class="ozet-karti"><template v-if="secili"><div class="ozet-etiket">SEÇİLİ ÇALIŞMA</div><h2>{{ secili.ad }}</h2><p class="muted">{{ projeAdi(secili.proje) }} · {{ secili.yil }} · v{{ secili.versiyon }}</p><div class="toplam"><span>Genel toplam</span><strong>{{ para(aktifToplam) }}</strong></div><div class="istatistik"><div><span>Satır</span><b>{{ satirlar.length }}</b></div><div><span>Ortalama</span><b>{{ para(satirlar.length ? aktifToplam / satirlar.length : 0) }}</b></div></div><div class="aksiyonlar"><button class="birincil-dugme" type="button" @click="hesapla">↻ Hesapla</button><button class="ikincil-dugme" type="button" @click="satirModalAcik = true">+ Poz satırı</button><button class="ikincil-dugme" type="button" @click="revize">Yeni revizyon</button><button class="ikincil-dugme soluk" type="button" @click="mahaldenOlustur">Mahallerden üret</button></div><div class="satir-baslik"><span>Satırlar</span><span>{{ satirlar.length }}</span></div><ul class="satir-listesi"><li v-for="x in satirlar" :key="x.id"><span><b>{{ x.poz_no || pozAdi(x.poz) }}</b><small>{{ x.miktar }} × {{ para(x.birim_fiyat_snapshot) }}</small></span><strong>{{ para(x.toplam_tutar || x.satir_tutari || 0) }}</strong></li><li v-if="!satirlar.length" class="bos">Bu maliyete henüz satır eklenmedi.</li></ul></template><p v-else class="bos ozet-bos">Detay görmek için bir kayıt seçin.</p></aside>
    </div>
    <KayitModal v-if="modalAcik" baslik="Yeni Yaklaşık Maliyet" :genis-icerik="true" @kapat="modalAcik = false"><form class="form-grid" @submit.prevent="kaydet"><label class="etiket">Proje *<select v-model="form.proje" class="alan" required><option :value="null">Seçiniz</option><option v-for="x in projeler" :key="x.id" :value="x.id">{{ x.proje_kodu }} · {{ x.ad }}</option></select></label><label class="etiket">Fiyat yılı *<input v-model.number="form.yil" class="alan" type="number" min="2000" max="2100" required /></label><label class="etiket col-span-2">Başlık<input v-model="form.ad" class="alan" required /></label><label class="etiket col-span-2">Açıklama<textarea v-model="form.aciklama" class="alan" rows="3" /></label><button class="birincil-dugme col-span-2" type="submit">Kaydı oluştur</button></form></KayitModal>
    <KayitModal v-if="satirModalAcik" baslik="Poz satırı ekle" :genis-icerik="true" @kapat="satirModalAcik = false"><form class="form-grid" @submit.prevent="satirKaydet"><label class="etiket col-span-2">Poz *<select v-model="satirForm.poz" class="alan" required><option :value="null">Seçiniz</option><option v-for="x in pozlar" :key="x.id" :value="x.id">{{ x.poz_no }} · {{ x.ad }}</option></select></label><label class="etiket">Miktar *<input v-model="satirForm.miktar" class="alan" type="number" min="0.0001" step="0.0001" required /></label><label class="etiket">Mahal ID<input v-model.number="satirForm.mahal" class="alan" type="number" min="1" /></label><label class="etiket col-span-2">Açıklama<textarea v-model="satirForm.aciklama" class="alan" rows="2" /></label><button class="birincil-dugme col-span-2" type="submit">Satırı ekle</button></form></KayitModal>
  </div>
</template>

<style scoped>
.yaklasik-sayfa { --ink: #17343b; --muted: #6d8588; --line: #dce8e5; --mint: #e7f4f0; color: var(--ink); max-width: 1420px; margin: 0 auto; }
.sayfa-baslik { display:flex; justify-content:space-between; align-items:end; gap:1rem; margin-bottom:1.4rem; }.sayfa-baslik h1 { margin:.2rem 0; font:700 2rem/1.1 Georgia, serif; letter-spacing:-.04em; }.eyebrow,.ozet-etiket { color:#0f6973; font-size:.68rem; font-weight:800; letter-spacing:.14em; }.aciklama,.muted { color:var(--muted); font-size:.85rem; }.toolbar { display:flex; align-items:center; gap:1rem; margin-bottom:1rem; }.toolbar .alan { max-width:28rem; }.kayit-sayisi,.durum { color:var(--muted); font-size:.75rem; }.maliyet-grid { display:grid; grid-template-columns:minmax(0,1fr) 24rem; gap:1rem; align-items:start; }.liste-karti,.ozet-karti { border:1px solid var(--line); border-radius:1.1rem; background:#fff; box-shadow:0 12px 32px rgba(30,75,73,.06); overflow:hidden; }.liste-ust { padding:1rem 1.2rem; display:flex; justify-content:space-between; font-size:.78rem; font-weight:800; text-transform:uppercase; letter-spacing:.1em; background:var(--mint); }.tablo-kaydir { overflow:auto; } table { width:100%; min-width:650px; border-collapse:collapse; font-size:.83rem; } th { color:var(--muted); text-align:left; font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; padding:.8rem 1rem; } td { padding:1rem; border-top:1px solid #edf3f1; } tr { cursor:pointer; transition:background .15s; } tbody tr:hover, tr.secili { background:#f1faf7; } td small, .satir-listesi small { display:block; color:var(--muted); margin-top:.25rem; font-size:.72rem; }.sag { text-align:right; }.fiyat { font-variant-numeric:tabular-nums; font-weight:700; }.ozet-karti { padding:1.35rem; position:sticky; top:1rem; }.ozet-karti h2 { margin:.3rem 0; font-size:1.15rem; }.toplam { margin:1.5rem 0 1rem; padding:1rem; border-radius:.8rem; background:var(--ink); color:white; }.toplam span { display:block; color:#abd2ca; font-size:.72rem; }.toplam strong { display:block; margin-top:.3rem; font-size:1.65rem; letter-spacing:-.04em; }.istatistik { display:grid; grid-template-columns:1fr 1fr; gap:.6rem; }.istatistik div { padding:.7rem; border:1px solid var(--line); border-radius:.7rem; }.istatistik span { display:block; color:var(--muted); font-size:.7rem; }.aksiyonlar { display:grid; gap:.5rem; margin:1.1rem 0; }.aksiyonlar button { width:100%; }.soluk { color:#0f6973; }.satir-baslik { display:flex; justify-content:space-between; border-bottom:1px solid var(--line); padding-bottom:.6rem; font-weight:800; font-size:.8rem; }.satir-listesi { list-style:none; padding:0; margin:.4rem 0 0; }.satir-listesi li { display:flex; justify-content:space-between; gap:.5rem; padding:.7rem 0; border-bottom:1px solid #edf3f1; font-size:.78rem; }.satir-listesi li > strong { white-space:nowrap; }.bos { color:var(--muted); text-align:center; padding:2rem 1rem; }.ozet-bos { padding:5rem 1rem; }.form-grid { display:grid; grid-template-columns:1fr 1fr; gap:.8rem; }.col-span-2 { grid-column:span 2; }
@media (max-width: 900px) { .maliyet-grid { grid-template-columns:1fr; }.ozet-karti { position:static; }.sayfa-baslik { align-items:start; flex-direction:column; } }
@media (max-width: 520px) { .form-grid { grid-template-columns:1fr; }.col-span-2 { grid-column:auto; }.sayfa-baslik h1 { font-size:1.7rem; } }
</style>
