<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Building2,
  ChevronRight,
  AlertCircle,
  FileText,
  Landmark,
  Plus,
  ReceiptText,
  RefreshCw,
  Users,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { hataMesaji } from '@/services/apiClient'
import { raporApi, type CariRaporSatiri, type FinansRaporu } from '@/services/raporApi'
import { notificationsApi } from '@/services/notificationsApi'
import type { Hatirlatma } from '@/types/notifications'
import { ROL_ETIKETLERI } from '@/utils/roller'
import type { Rol } from '@/types/api'

const auth = useAuthStore()
const loading = ref(true)
const error = ref('')
const finans = ref<FinansRaporu>({ gelir: '0', gider: '0', transfer: '0' })
const cariler = ref<CariRaporSatiri[]>([])
const dogalDilSorusu = ref('')
const dogalDilSonucu = ref<Awaited<ReturnType<typeof raporApi.dogalDil>> | null>(null)
const dogalDilYukleniyor = ref(false)
const dogalDilHata = ref('')
const hatirlatmalar = ref<Hatirlatma[]>([])

const kullaniciAdi = computed(() => auth.kullanici?.username || 'Kullanıcı')
const rolEtiketi = computed(() => {
  const rol: Rol | undefined = auth.kullanici?.role
  return rol ? ROL_ETIKETLERI[rol] : 'Oturum'
})
const firmaAdi = computed(() => auth.kullanici?.tenant_ad || 'Tüm firmalar')
const gelir = computed(() => Number(finans.value.gelir || 0))
const gider = computed(() => Number(finans.value.gider || 0))
const net = computed(() => gelir.value - gider.value)
const toplamBakiye = computed(() => cariler.value.reduce((sum, item) => sum + Number(item.bakiye || 0), 0))
const aktifCariler = computed(() => cariler.value.length)

const hizliIslemler = [
  { label: 'Yeni fatura', detail: 'Satış veya alış faturası oluştur', to: '/finans/faturalar', icon: FileText, accent: 'gold' },
  { label: 'Cari aç', detail: 'Müşteri veya tedarikçi ekle', to: '/cari/cariler', icon: Users, accent: 'teal' },
  { label: 'Tahsilat gir', detail: 'Kasa veya banka işlemi kaydet', to: '/finans/islemler', icon: ReceiptText, accent: 'blue' },
  { label: 'Raporları aç', detail: 'Finansal görünümü incele', to: '/finans/raporlar', icon: BarChart3, accent: 'slate' },
]

const moduller = [
  { label: 'Gayrimenkul', detail: 'Proje, blok ve bağımsız bölümler', to: '/gayrimenkul/gayrimenkuller', icon: Building2, state: 'active' },
  { label: 'Cari & Finans', detail: 'Cari, hesap, tahsilat ve fatura', to: '/cari/cariler', icon: Users, state: 'active' },
  { label: 'Muhasebe', detail: 'Hesap planı, fiş ve mizan', to: '/muhasebe/fisler', icon: Landmark, state: 'active' },
  { label: 'İnşaat', detail: 'Poz, metraj ve hakediş süreçleri', to: '/insaat/projeler', icon: Building2, state: 'active' },
  { label: 'Kira & Personel', detail: 'Sözleşme, tahsilat ve özlük süreçleri', to: '', icon: Users, state: 'planned' },
  { label: 'Stok & E-belge', detail: 'Stok, e-fatura ve entegrasyonlar', to: '/finans/faturalar', icon: FileText, state: 'planned' },
]

function para(value: number): string {
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(value)
}

async function yukle(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const [finansSonuc, cariSonuc, hatirlatmaSonuc] = await Promise.all([
      raporApi.finansOzeti(),
      raporApi.cariOzeti(),
      notificationsApi.gunluk().catch(() => []),
    ])
    finans.value = finansSonuc
    cariler.value = cariSonuc
    hatirlatmalar.value = hatirlatmaSonuc
  } catch (e) {
    error.value = hataMesaji(e)
  } finally {
    loading.value = false
  }

}

async function dogalDilSor(): Promise<void> {
  if (!dogalDilSorusu.value.trim()) {
    dogalDilHata.value = 'Örnek: “Bu ay gelir ve gider durumum nedir?”'
    dogalDilSonucu.value = null
    return
  }
  dogalDilYukleniyor.value = true
  dogalDilHata.value = ''
  try {
    dogalDilSonucu.value = await raporApi.dogalDil(dogalDilSorusu.value.trim())
  } catch (e) {
    dogalDilHata.value = hataMesaji(e)
    dogalDilSonucu.value = null
  } finally {
    dogalDilYukleniyor.value = false
  }
}

onMounted(() => void yukle())
</script>

<template>
  <div class="dashboard-shell">
    <section class="dashboard-hero">
      <div>
        <p class="dashboard-eyebrow">İŞLETME KUMANDA MERKEZİ · {{ firmaAdi }}</p>
        <h1>Günaydın, {{ kullaniciAdi }}.</h1>
        <p class="dashboard-intro">Bugünün finansal görünümünü tek ekranda takip edin. İşinizi hızlandırmak için bir işlem seçin.</p>
      </div>
      <div class="dashboard-hero-meta">
        <span class="role-pill">{{ rolEtiketi }}</span>
        <button class="refresh-button" type="button" title="Verileri yenile" @click="yukle">
          <RefreshCw :class="{ 'animate-spin': loading }" class="h-4 w-4" />
          Yenile
        </button>
      </div>
    </section>

    <p v-if="error" class="hata-kutusu mt-5"><AlertCircle class="inline h-4 w-4 mr-2" />{{ error }}</p>

    <section class="kpi-grid" aria-label="Finansal özet">
      <article class="kpi-card kpi-income">
        <div class="kpi-icon"><ArrowUpRight class="h-5 w-5" /></div>
        <div><p>Toplam gelir</p><strong>{{ loading ? '—' : para(gelir) }}</strong><span>Bu dönem</span></div>
      </article>
      <article class="kpi-card kpi-expense">
        <div class="kpi-icon"><ArrowDownRight class="h-5 w-5" /></div>
        <div><p>Toplam gider</p><strong>{{ loading ? '—' : para(gider) }}</strong><span>Bu dönem</span></div>
      </article>
      <article class="kpi-card kpi-net">
        <div class="kpi-icon"><BarChart3 class="h-5 w-5" /></div>
        <div><p>Net nakit akışı</p><strong>{{ loading ? '—' : para(net) }}</strong><span :class="net >= 0 ? 'positive' : 'negative'">{{ net >= 0 ? 'Sağlıklı görünüm' : 'İnceleme gerekli' }}</span></div>
      </article>
      <article class="kpi-card kpi-cari">
        <div class="kpi-icon"><Users class="h-5 w-5" /></div>
        <div><p>Cari bakiye</p><strong>{{ loading ? '—' : para(Math.abs(toplamBakiye)) }}</strong><span>{{ aktifCariler }} aktif cari hesabı</span></div>
      </article>
    </section>

    <section class="dashboard-main-grid">
      <article class="dashboard-panel quick-panel">
        <div class="panel-heading"><div><p class="panel-kicker">HIZLI İŞLEMLER</p><h2>Bugün ne yapmak istiyorsunuz?</h2></div><Plus class="panel-mark h-5 w-5" /></div>
        <div class="quick-grid">
          <RouterLink v-for="action in hizliIslemler" :key="action.label" :to="action.to" class="quick-action" :class="`quick-${action.accent}`">
            <span class="quick-icon"><component :is="action.icon" class="h-5 w-5" /></span>
            <span><strong>{{ action.label }}</strong><small>{{ action.detail }}</small></span>
            <ChevronRight class="quick-arrow h-4 w-4" />
          </RouterLink>
        </div>
      </article>

      <article class="dashboard-panel balance-panel">
        <div class="panel-heading"><div><p class="panel-kicker">CARİ DURUMU</p><h2>En yüksek bakiyeler</h2></div><RouterLink class="panel-link" to="/cari/hareketler">Tümünü gör <ChevronRight class="inline h-3 w-3" /></RouterLink></div>
        <div v-if="loading" class="empty-state">Veriler yükleniyor…</div>
        <div v-else-if="!cariler.length" class="empty-state">Henüz cari hareket bulunmuyor.</div>
        <div v-else class="balance-list">
          <div v-for="item in cariler.slice(0, 4)" :key="item.cari" class="balance-row">
            <span class="avatar">{{ item.cari_ad.slice(0, 1).toUpperCase() }}</span>
            <span class="balance-name"><strong>{{ item.cari_ad }}</strong><small>{{ Number(item.borc) > 0 ? 'Borçlu cari' : 'Alacaklı cari' }}</small></span>
            <strong :class="Number(item.bakiye) >= 0 ? 'positive' : 'negative'">{{ para(Math.abs(Number(item.bakiye))) }}</strong>
          </div>
        </div>
      </article>
    </section>

    <section class="dashboard-panel mt-6">
      <div class="panel-heading">
        <div><p class="panel-kicker">MERKEZİ HATIRLATMALAR</p><h2>Bugünün Hatırlatmaları</h2></div>
        <RouterLink class="panel-link" to="/insaat/projeler">İnşaat modülüne git <ChevronRight class="inline h-3 w-3" /></RouterLink>
      </div>
      <div v-if="!hatirlatmalar.length" class="empty-state">Bugün için bekleyen hatırlatma yok.</div>
      <div v-else class="balance-list">
        <div v-for="hatirlatma in hatirlatmalar.slice(0, 5)" :key="hatirlatma.id" class="balance-row">
          <span class="avatar">{{ hatirlatma.seviye === 'kritik' ? '!' : '•' }}</span>
          <span class="balance-name"><strong>{{ hatirlatma.baslik }}</strong><small>{{ hatirlatma.aciklama }}</small></span>
          <span class="text-xs text-slate-500">{{ hatirlatma.hatirlatma_tarihi }}</span>
        </div>
      </div>
    </section>

    <section class="dashboard-panel mt-6">
      <div class="panel-heading">
        <div><p class="panel-kicker">YÖNETİCİ ÖZETİ</p><h2>Raporu doğal dille sorun</h2></div>
        <span class="text-xs text-slate-500">Gelir · cari · mizan</span>
      </div>
      <form class="mt-4 flex flex-col gap-3 md:flex-row" @submit.prevent="dogalDilSor">
        <input v-model="dogalDilSorusu" class="alan flex-1" type="search" placeholder="Örn. Bu ay gelir ve gider durumum nedir?" aria-label="Doğal dil rapor sorusu" />
        <button class="birincil-dugme" type="submit" :disabled="dogalDilYukleniyor">{{ dogalDilYukleniyor ? 'Hazırlanıyor…' : 'Raporla' }}</button>
      </form>
      <p v-if="dogalDilHata" class="hata-kutusu mt-3" role="alert">{{ dogalDilHata }}</p>
      <article v-if="dogalDilSonucu" class="mt-4 rounded-xl border border-primary-100 bg-primary-50/50 p-4">
        <p class="text-sm font-semibold text-slate-900">{{ dogalDilSonucu.ozet }}</p>
        <p class="mt-2 text-xs text-slate-500">{{ dogalDilSonucu.veri_notu }}</p>
        <div v-if="dogalDilSonucu.metrikler" class="mt-3 grid gap-2 sm:grid-cols-3">
          <span class="rounded-lg bg-white px-3 py-2 text-xs">Gelir: <strong>{{ para(Number(dogalDilSonucu.metrikler.gelir)) }}</strong></span>
          <span class="rounded-lg bg-white px-3 py-2 text-xs">Gider: <strong>{{ para(Number(dogalDilSonucu.metrikler.gider)) }}</strong></span>
          <span class="rounded-lg bg-white px-3 py-2 text-xs">Net: <strong>{{ para(Number(dogalDilSonucu.metrikler.net)) }}</strong></span>
        </div>
      </article>
    </section>

    <section class="dashboard-panel module-panel">
      <div class="panel-heading"><div><p class="panel-kicker">ÇALIŞMA ALANLARI</p><h2>İşletmenizin tamamı burada</h2></div><span class="module-count">4 aktif · 2 planlanıyor</span></div>
      <div class="module-grid">
        <RouterLink v-for="module in moduller.filter((item) => item.state === 'active')" :key="module.label" :to="module.to" class="module-tile">
          <span class="module-icon"><component :is="module.icon" class="h-5 w-5" /></span><span><strong>{{ module.label }}</strong><small>{{ module.detail }}</small></span><ChevronRight class="h-4 w-4 text-slate-400" />
        </RouterLink>
        <div v-for="module in moduller.filter((item) => item.state === 'planned')" :key="module.label" class="module-tile module-planned">
          <span class="module-icon"><component :is="module.icon" class="h-5 w-5" /></span><span><strong>{{ module.label }}</strong><small>{{ module.detail }}</small></span><span class="planned-badge">Yakında</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dashboard-shell { max-width: 1380px; margin: 0 auto; }
.dashboard-hero { display:flex; justify-content:space-between; align-items:flex-end; gap:2rem; padding: 1.5rem 0 2rem; }
.dashboard-eyebrow, .panel-kicker { margin:0 0 .55rem; color:#0f6973; font-size:.68rem; font-weight:800; letter-spacing:.16em; }
.dashboard-hero h1 { margin:0; color:#102a43; font-family:'Plus Jakarta Sans',sans-serif; font-size:clamp(1.7rem,3vw,2.5rem); letter-spacing:-.04em; }
.dashboard-intro { max-width:620px; margin:.7rem 0 0; color:#64748b; font-size:.95rem; line-height:1.6; }
.dashboard-hero-meta { display:flex; align-items:center; gap:.7rem; }
.role-pill { border:1px solid #d6b45b; border-radius:999px; background:#fff8e8; color:#946f1d; padding:.45rem .75rem; font-size:.72rem; font-weight:700; }
.refresh-button { display:flex; align-items:center; gap:.4rem; border:1px solid #dbe4ed; border-radius:.7rem; background:#fff; color:#476176; padding:.55rem .75rem; font-size:.75rem; font-weight:700; }
.kpi-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:1rem; }
.kpi-card { display:flex; gap:.85rem; min-height:112px; padding:1.1rem; border:1px solid #e2e8f0; border-radius:1rem; background:#fff; box-shadow:0 10px 24px rgba(16,42,67,.05); }
.kpi-icon { display:flex; align-items:center; justify-content:center; width:2.35rem; height:2.35rem; border-radius:.7rem; }
.kpi-card p,.kpi-card strong,.kpi-card span { display:block; }
.kpi-card p { margin:0 0 .35rem; color:#64748b; font-size:.72rem; font-weight:700; }
.kpi-card strong { color:#102a43; font-size:1.32rem; letter-spacing:-.03em; }
.kpi-card span { margin-top:.35rem; color:#94a3b8; font-size:.7rem; }
.kpi-income .kpi-icon { background:#dff7ef; color:#087f68; }.kpi-expense .kpi-icon { background:#fff0e4; color:#c35c22; }.kpi-net .kpi-icon { background:#e4effa; color:#2d5a8a; }.kpi-cari .kpi-icon { background:#f4e9ff; color:#8152a8; }
.dashboard-main-grid { display:grid; grid-template-columns:1.2fr .8fr; gap:1rem; margin-top:1rem; }
.dashboard-panel { border:1px solid #e2e8f0; border-radius:1rem; background:#fff; padding:1.25rem; box-shadow:0 10px 24px rgba(16,42,67,.04); }
.panel-heading { display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; margin-bottom:1.1rem; }
.panel-heading h2 { margin:0; color:#102a43; font-family:'Plus Jakarta Sans',sans-serif; font-size:1rem; letter-spacing:-.02em; }
.panel-mark { color:#d4a843; }.panel-link { color:#0f6973; font-size:.72rem; font-weight:700; }
.quick-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.7rem; }
.quick-action { display:flex; align-items:center; gap:.7rem; min-height:78px; padding:.85rem; border:1px solid #edf1f5; border-radius:.8rem; transition:.2s ease; }
.quick-action:hover { transform:translateY(-2px); border-color:#b8d9d8; box-shadow:0 8px 18px rgba(15,105,115,.08); }
.quick-icon { display:flex; align-items:center; justify-content:center; width:2.25rem; height:2.25rem; border-radius:.65rem; }.quick-gold .quick-icon { background:#fff4d7; color:#ad7b17; }.quick-teal .quick-icon { background:#dff7ef; color:#087f68; }.quick-blue .quick-icon { background:#e4effa; color:#2d5a8a; }.quick-slate .quick-icon { background:#edf2f7; color:#476176; }
.quick-action strong,.quick-action small { display:block; }.quick-action strong { color:#183b56; font-size:.78rem; }.quick-action small { margin-top:.22rem; color:#94a3b8; font-size:.68rem; line-height:1.35; }.quick-arrow { margin-left:auto; color:#a6b6c5; }
.balance-list { display:flex; flex-direction:column; gap:.2rem; }.balance-row { display:flex; align-items:center; gap:.7rem; padding:.65rem .2rem; border-bottom:1px solid #f0f3f6; }.balance-row:last-child { border-bottom:0; }.avatar { display:flex; align-items:center; justify-content:center; width:2rem; height:2rem; border-radius:50%; background:#e4effa; color:#2d5a8a; font-size:.75rem; font-weight:800; }.balance-name { flex:1; }.balance-name strong,.balance-name small { display:block; }.balance-name strong { color:#183b56; font-size:.76rem; }.balance-name small { margin-top:.15rem; color:#94a3b8; font-size:.65rem; }.balance-row > strong { font-size:.76rem; }.positive { color:#087f68!important; }.negative { color:#c35c22!important; }
.empty-state { padding:2rem 0; color:#94a3b8; text-align:center; font-size:.78rem; }
.module-panel { margin-top:1rem; }.module-count { color:#94a3b8; font-size:.7rem; }.module-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.7rem; }.module-tile { display:flex; align-items:center; gap:.7rem; min-height:72px; padding:.75rem; border:1px solid #edf1f5; border-radius:.75rem; }.module-tile:not(.module-planned):hover { border-color:#afd3d3; background:#f7fcfc; }.module-icon { display:flex; align-items:center; justify-content:center; width:2.15rem; height:2.15rem; border-radius:.6rem; background:#eef8f7; color:#0f6973; }.module-tile span:nth-child(2) { flex:1; }.module-tile strong,.module-tile small { display:block; }.module-tile strong { color:#183b56; font-size:.76rem; }.module-tile small { margin-top:.2rem; color:#94a3b8; font-size:.65rem; }.planned-badge { border-radius:999px; background:#f1f5f9; color:#94a3b8; padding:.25rem .45rem; font-size:.6rem; font-weight:700; }
@media (max-width: 900px) { .kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }.dashboard-main-grid { grid-template-columns:1fr; }.module-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width: 640px) { .dashboard-hero { display:block; }.dashboard-hero-meta { margin-top:1rem; }.kpi-grid,.quick-grid,.module-grid { grid-template-columns:1fr; }.dashboard-panel { padding:1rem; } }
</style>
