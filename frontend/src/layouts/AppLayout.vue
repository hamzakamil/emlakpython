<script setup lang="ts">
/**
 * Uygulama düzeni — sol sabit sidebar (280px, site-spec) + üst topbar (64px).
 * Hazır modüller RouterLink; diğerleri "Yakında".
 * Topbar: normal kullanıcıda /auth/me'den gelen gerçek firma adı; süper
 * admin'de tenant seçici dropdown (X-Tenant-Id kapsamı).
 */
import { computed, onMounted, onUnmounted, provide, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import {
  BarChart3,
  Building2,
  ClipboardList,
  Database,
  FileText,
  HardHat,
  Home,
  Landmark,
  Layers,
  LogOut,
  Menu,
  Bell,
  Search,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Folder,
  Receipt,
  Ruler,
  Settings,
  Users,
  BookOpen,
  Calculator,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { ROL_ETIKETLERI } from '@/utils/roller'
import type { Rol } from '@/types/api'
import { notificationsApi } from '@/services/notificationsApi'
import type { Hatirlatma, HatirlatmaPayload } from '@/types/notifications'
import HatirlatmaEkleButonu from '@/components/HatirlatmaEkleButonu.vue'
import HatirlatmaOnerisi from '@/components/HatirlatmaOnerisi.vue'
import { menuHelp } from '@/config/menuHelp'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const sidebarAcik = ref(false)
const sidebarDar = ref(false)
function menuGruplariniOku(): Record<string, boolean> {
  try {
    const kayit = JSON.parse(localStorage.getItem('emlak_erp_acik_menu_gruplari') || '{"Genel":true}')
    return kayit && typeof kayit === 'object' && !Array.isArray(kayit) ? kayit : { Genel: true }
  } catch {
    localStorage.removeItem('emlak_erp_acik_menu_gruplari')
    return { Genel: true }
  }
}
const acikGruplar = ref<Record<string, boolean>>(menuGruplariniOku())
const bildirimlerAcik = ref(false)
const merkeziHatirlatmalar = ref<Hatirlatma[]>([])
const hatirlatmaOnerisi = ref<{ tarih: string; baslik: string; payload: Partial<HatirlatmaPayload> } | null>(null)
const okunanBildirimler = ref<string[]>(JSON.parse(localStorage.getItem('emlak_erp_okunan_bildirimler') || '[]'))
const faturaTaslagiVar = ref(Boolean(localStorage.getItem('emlak_erp_acik_fatura_taslagi')))

const kullaniciAdi = computed(() => auth.kullanici?.username || 'Kullanıcı')
const rolEtiketi = computed(() => {
  const rol: Rol | undefined = auth.kullanici?.role
  return rol ? ROL_ETIKETLERI[rol] : 'Oturum'
})
const tenantGosterimi = computed(() => {
  if (auth.seciciGosterilsinMi) {
    const secili = auth.tenantlar.find((t) => t.id === auth.seciliTenantId)
    return secili ? secili.name : 'Tüm Tenantlar'
  }
  return auth.kullanici?.tenant_ad || 'Tenant seçilmedi'
})
const sayfaBasligi = computed(() => String(route.meta.title || route.name || 'Panel'))
const bildirimler = computed(() => {
  const merkezi = merkeziHatirlatmalar.value.map((hatirlatma) => ({
    id: `hatirlatma-${hatirlatma.id}`,
    baslik: hatirlatma.baslik,
    aciklama: hatirlatma.aciklama,
    to: '/',
  }))
  const liste = []
  if (auth.seciciGosterilsinMi && !auth.seciliTenantId) {
    liste.push({ id: 'firma-secimi', baslik: 'Firma kapsamı seçilmedi', aciklama: 'Cari, fatura ve inşaat kaydı oluşturmak için üst menüden bir firma seçin.', to: '/yonetim/firmalar' })
  }
  liste.push(...merkezi)
  return liste
})
const okunmamisBildirimSayisi = computed(() => bildirimler.value.filter((b) => !okunanBildirimler.value.includes(b.id)).length)

// Minimized modals bar
const minimizeModals = ref<{id:string; title:string}[]>([])
function handleModalMinimized(payload: {id:string; title:string}) {
  if (!minimizeModals.value.some(m => m.id === payload.id)) {
    minimizeModals.value.push(payload)
  }
}
const restoreModal = (id: string) => {
  minimizeModals.value = minimizeModals.value.filter(m => m.id !== id)
  window.dispatchEvent(new CustomEvent('erp:restore-modal', { detail: { id } }))
}
provide('restoreModal', restoreModal)
provide('minimizeModal', handleModalMinimized)

type LucideIkon = typeof Home

interface NavMadde {
  ad: string
  to?: string
  ikon: LucideIkon
  hazir: boolean
  helpKey?: keyof typeof menuHelp
  children?: NavMadde[]
}
interface NavGrup {
  baslik: string
  maddeler: NavMadde[]
}

/** Menüde yer almayan ama yardımı olan ekranlar (Ayarlar hub'ından erişilir). */
const yolYardimEsleme: Record<string, { ad: string; helpKey: keyof typeof menuHelp }> = {
  '/profil': { ad: 'Profil ve Güvenlik', helpKey: 'profil' },
  '/finans/vergi-profilleri': { ad: 'Vergi Profilleri', helpKey: 'vergiProfilleri' },
  '/finans/stok-hesap-esleme': { ad: 'Stok Hesap Eşleme', helpKey: 'stokHesapEsleme' },
  '/insaat/hatirlatma-kurallari': { ad: 'Hatırlatma Kuralları', helpKey: 'hatirlatmaKurallari' },
  '/insaat/yapi-sinifi': { ad: 'Yapı Sınıfları', helpKey: 'yapiSinifi' },
  '/insaat/pozlar': { ad: 'Pozlar', helpKey: 'pozlar' },
  '/insaat/malzemeler': { ad: 'Malzemeler', helpKey: 'malzemeler' },
  '/insaat/mahaller': { ad: 'Mahaller', helpKey: 'mahalListesi' },
}

const navGruplari: NavGrup[] = [
  {
    baslik: 'Genel',
    maddeler: [{ ad: 'Panel', to: '/', ikon: Home, hazir: true, helpKey: 'panel' }],
  },
  {
    baslik: 'Gayrimenkul',
    maddeler: [
      { ad: 'Gayrimenkuller', to: '/gayrimenkul/gayrimenkuller', ikon: Building2, hazir: true, helpKey: 'gayrimenkuller' },
      { ad: 'Ada / Parsel ve İmar', to: '/gayrimenkul/ada-parsel', ikon: Ruler, hazir: true, helpKey: 'adaParsel' },
      { ad: 'Malik Mutabakatı', to: '/gayrimenkul/malik-mutabakati', ikon: Users, hazir: true, helpKey: 'malikMutabakati' },
    ],
  },
      {
    baslik: 'İNŞAAT MALİYET',
    maddeler: [
      { ad: 'Genel Bakış', to: '/insaat/genel-bakis', ikon: BarChart3, hazir: true, helpKey: 'genelBakis' },
      {
        ad: 'Kütüphane',
        ikon: BookOpen,
        hazir: true,
        children: [
          { ad: 'Yapı Sınıfları', to: '/insaat/yapi-sinifi', ikon: Ruler, hazir: true, helpKey: 'yapiSinifi' },
          { ad: 'Pozlar', to: '/insaat/pozlar', ikon: Layers, hazir: true, helpKey: 'pozlar' },
          { ad: 'Malzemeler', to: '/insaat/malzemeler', ikon: Database, hazir: true, helpKey: 'malzemeler' },
          { ad: 'Mahaller', to: '/insaat/mahaller', ikon: ClipboardList, hazir: true, helpKey: 'mahalListesi' },
        ]
      },
      { ad: 'Projeler', to: '/insaat/projeler', ikon: HardHat, hazir: true, helpKey: 'projeler' },
      { ad: 'Şantiye Günlükleri', to: '/insaat/santiye-gunlukleri', ikon: ClipboardList, hazir: true, helpKey: 'santiyeGunlukleri' },
      { ad: 'Metraj & Keşif', to: '/insaat/metraj-kesif', ikon: Ruler, hazir: true, helpKey: 'metrajKesif' },
      { ad: 'Maliyet Hesabı', to: '/insaat/maliyet-hesabi', ikon: Calculator, hazir: true, helpKey: 'maliyetHesabi' },
      { ad: 'Raporlar', to: '/insaat/raporlar', ikon: FileText, hazir: true, helpKey: 'insaatRaporlar' },
      { ad: 'Ayarlar', to: '/insaat/ayarlar', ikon: Settings, hazir: true, helpKey: 'insaatAyarlar' },
    ],
  },
  {
    baslik: 'KENTSEL DÖNÜŞÜM',
    maddeler: [
      { ad: 'Riskli Yapı Süreci', to: '/insaat/riskli-yapi', ikon: ClipboardList, hazir: true, helpKey: 'riskliYapiSureci' },
      { ad: 'EKB Süreç Takibi', to: '/insaat/ekb', ikon: FileText, hazir: true, helpKey: 'ekbSurecTakibi' },
      { ad: 'Kira Yardımı / Tahliye', to: '/insaat/kira-yardimi', ikon: Receipt, hazir: true, helpKey: 'kiraYardimiTahliye' },
    ],
  },
  {
    baslik: 'SATIN ALMA',
    maddeler: [
      { ad: 'Talepler', to: '/satinalma/talepler', ikon: ClipboardList, hazir: true, helpKey: 'satinAlmaTalepleri' },
      { ad: 'Siparişler', to: '/satinalma/siparisler', ikon: FileText, hazir: true, helpKey: 'satinAlmaSiparisleri' },
      { ad: 'Mal Kabuller', to: '/satinalma/mal-kabuller', ikon: ClipboardList, hazir: true, helpKey: 'malKabuller' },
      { ad: 'Stok Hareketleri', to: '/satinalma/stok-hareketleri', ikon: FileText, hazir: true, helpKey: 'stokHareketleri' },
      { ad: 'Stok Durumu', to: '/satinalma/stok-durumu', ikon: ClipboardList, hazir: true, helpKey: 'stokDurumu' },
      { ad: 'Depolar', to: '/satinalma/depolar', ikon: FileText, hazir: true, helpKey: 'depolar' },
    ],
  },
  {
    baslik: 'Finans',
    maddeler: [
      { ad: 'Cari Kartlar', to: '/cari/cariler', ikon: Users, hazir: true, helpKey: 'cariKartlar' },
      { ad: 'Cari Hareketler', to: '/cari/hareketler', ikon: ClipboardList, hazir: true, helpKey: 'cariHareketler' },
      { ad: 'Finans Hesapları', to: '/finans/hesaplar', ikon: Landmark, hazir: true, helpKey: 'finansalHesaplar' },
      { ad: 'Finansal İşlemler', to: '/finans/islemler', ikon: Receipt, hazir: true, helpKey: 'finansalIslemler' },
      { ad: 'Çek / Senetler', to: '/finans/cek-senetler', ikon: Receipt, hazir: true, helpKey: 'cekSenetler' },
      { ad: 'Hesap Planı', to: '/muhasebe/hesap-plani', ikon: Landmark, hazir: true, helpKey: 'hesapPlani' },
      { ad: 'Fişler ve Mizan', to: '/muhasebe/fisler', ikon: Landmark, hazir: true, helpKey: 'fislerMizan' },
      { ad: 'Mizan Raporu', to: '/muhasebe/mizan', ikon: BarChart3, hazir: true, helpKey: 'mizanRaporu' },
      { ad: 'Faturalar', to: '/finans/faturalar', ikon: Receipt, hazir: true, helpKey: 'faturalar' },
      { ad: 'Raporlar', to: '/finans/raporlar', ikon: BarChart3, hazir: true, helpKey: 'raporlar' },
      { ad: 'Ayarlar', to: '/finans/ayarlar', ikon: Settings, hazir: true, helpKey: 'ayarlar' },
    ],
  },
  {
    baslik: 'Yönetim',
    maddeler: [
      { ad: 'Firmalar', to: '/yonetim/firmalar', ikon: Building2, hazir: true, helpKey: 'firmalar' },
      { ad: 'Kullanıcılar', to: '/yonetim/kullanicilar', ikon: Users, hazir: true, helpKey: 'kullanicilar' },
      { ad: 'Veritabanı Yönetimi', to: '/yonetim/veritabani', ikon: Database, hazir: true, helpKey: 'veritabaniYonetimi' },
    ],
  },
]

const seciliMenuYardimi = computed(() => {
  for (const grup of navGruplari) {
    const madde = grup.maddeler.find((item) => item.to && (route.path === item.to || route.path.startsWith(`${item.to}/`)))
    if (madde?.helpKey && madde.to) {
      return { madde, detay: menuHelp[madde.helpKey] }
    }
  }
  const ozel = yolYardimEsleme[route.path]
  if (ozel) {
    return { madde: { ad: ozel.ad }, detay: menuHelp[ozel.helpKey] }
  }
  return null
})

/** Yardım paneli görünürlüğü — ilk kullanımda açık, tercih kullanıcı bazlı saklanır. */
const yardimAnahtari = computed(
  () => `emlak_erp_yardim_paneli_${auth.kullanici?.username || 'anonim'}`,
)
const yardimAcik = ref(true)
watch(yardimAnahtari, (anahtar) => {
  yardimAcik.value = localStorage.getItem(anahtar) !== '0'
}, { immediate: true })
function yardimDegistir(acik: boolean): void {
  yardimAcik.value = acik
  try {
    localStorage.setItem(yardimAnahtari.value, acik ? '1' : '0')
  } catch {
    /* depolama yoksa tercih hatırlanmaz; panel yine çalışır */
  }
}

const gorunenNavGruplari = computed(() =>
  navGruplari.map((grup) => ({
    ...grup,
    maddeler: grup.maddeler.filter(() => grup.baslik !== 'Yönetim' || auth.seciciGosterilsinMi),
  })).filter((grup) => grup.maddeler.length > 0),
)

function grupAcikMi(grup: NavGrup): boolean {
  return Boolean(acikGruplar.value[grup.baslik])
}

function grupAcikliginiDegistir(grup: NavGrup): void {
  acikGruplar.value = {
    ...acikGruplar.value,
    [grup.baslik]: !grupAcikMi(grup),
  }

  localStorage.setItem('emlak_erp_acik_menu_gruplari', JSON.stringify(acikGruplar.value))
}

onMounted(() => {
  // Sayfa yenilenmede gerçek rol/tenant bilgisi /auth/me'den tazelenir (sessiz).
  auth.oturumuTazele()
  void hatirlatmalariYukle()
  const aktifGrup = gorunenNavGruplari.value.find((grup) =>
    grup.maddeler.some((madde) => madde.to === route.path),
  )
  if (aktifGrup && !grupAcikMi(aktifGrup)) {
    acikGruplar.value = { ...acikGruplar.value, [aktifGrup.baslik]: true }
    localStorage.setItem('emlak_erp_acik_menu_gruplari', JSON.stringify(acikGruplar.value))
  }
  window.addEventListener('fatura-taslagi-degisti', faturaTaslagiGuncelle)
  window.addEventListener('hatirlatmalar-degisti', hatirlatmalariYukle)
  window.addEventListener('hatirlatma-onerisi', hatirlatmaOnerisiGoster)
})
onUnmounted(() => {
  window.removeEventListener('fatura-taslagi-degisti', faturaTaslagiGuncelle)
  window.removeEventListener('hatirlatmalar-degisti', hatirlatmalariYukle)
  window.removeEventListener('hatirlatma-onerisi', hatirlatmaOnerisiGoster)
})

function hatirlatmaOnerisiGoster(event: Event): void {
  const detay = (event as CustomEvent<{ tarih?: string; baslik?: string; payload?: Partial<HatirlatmaPayload> }>).detail
  if (detay?.tarih) {
    hatirlatmaOnerisi.value = {
      tarih: detay.tarih,
      baslik: detay.baslik || 'Bu tarihe hatırlatma kurmak ister misiniz?',
      payload: detay.payload || {},
    }
  }
}

async function hatirlatmalariYukle(): Promise<void> {
  try {
    merkeziHatirlatmalar.value = await notificationsApi.gunluk()
  } catch {
    merkeziHatirlatmalar.value = []
  }
}

function faturaTaslagiGuncelle(): void {
  faturaTaslagiVar.value = Boolean(localStorage.getItem('emlak_erp_acik_fatura_taslagi'))
}
function faturaTaslaginaDon(): void {
  router.push('/finans/faturalar')
}

function cikisYap(): void {
  auth.cikis()
  router.push({ name: 'giris' })
}

/** Süper admin kapsam değişimi — liste ekranları yeni kapsamla tazelenir. */
function kapsamDegistir(deger: string): void {
  auth.tenantSec(deger === '' ? null : Number(deger))
  router.go(0)
}
function bildirimleriAc(): void {
  bildirimlerAcik.value = !bildirimlerAcik.value
}
function bildirimiOku(id: string, to: string): void {
  if (!okunanBildirimler.value.includes(id)) {
    okunanBildirimler.value = [...okunanBildirimler.value, id]
    localStorage.setItem('emlak_erp_okunan_bildirimler', JSON.stringify(okunanBildirimler.value))
  }
  bildirimlerAcik.value = false
  router.push(to)
}
</script>

<template>
  <div class="app-shell flex h-dvh overflow-hidden" :class="{ 'sidebar-is-collapsed': sidebarDar }">
    <div v-if="sidebarAcik" class="sidebar-backdrop" @click="sidebarAcik = false"></div>
    <!-- Sidebar (site-spec: 280px, bg-surface, border-r) -->
    <aside class="app-sidebar flex w-[280px] shrink-0 flex-col border-r border-surface-200 bg-surface-50" :class="{ 'sidebar-collapsed': sidebarDar, 'sidebar-mobile-open': sidebarAcik }">
      <div class="flex items-center gap-3 border-b border-surface-200 px-5 py-5">
        <span
          class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-800 font-heading text-sm font-bold text-white"
          >E</span
        >
        <span class="font-heading text-base font-bold tracking-tight text-surface-900"
          >Emlak ERP</span
        >
        <button class="ml-auto hidden rounded-lg p-1 text-surface-500 hover:bg-surface-100 lg:block" title="Menüyü daralt" @click="sidebarDar = !sidebarDar"><ChevronLeft v-if="!sidebarDar" class="h-4 w-4" /><ChevronRight v-else class="h-4 w-4" /></button>
      </div>

      <nav class="min-h-0 flex-1 overflow-y-auto overscroll-contain p-3">
        <template v-for="grup in gorunenNavGruplari" :key="grup.baslik">
          <button
            type="button"
            class="menu-grup-basligi flex w-full items-center gap-2 rounded-lg px-4 py-3 text-left text-[11px] font-bold uppercase tracking-[0.14em] text-surface-500 transition-colors hover:bg-surface-100 hover:text-primary-800"
            :aria-expanded="grupAcikMi(grup)"
            :title="grupAcikMi(grup) ? `${grup.baslik} menüsünü gizle` : `${grup.baslik} menüsünü aç`"
            @click="grupAcikliginiDegistir(grup)"
          >
            <Folder class="h-4 w-4 shrink-0 text-primary-600" />
            <span class="min-w-0 flex-1 truncate">{{ grup.baslik }}</span>
            <ChevronDown v-if="grupAcikMi(grup)" class="h-4 w-4 shrink-0" />
            <ChevronRight v-else class="h-4 w-4 shrink-0" />
          </button>

          <div v-if="grupAcikMi(grup)" class="menu-grup-icerigi">
          <template v-for="madde in grup.maddeler" :key="madde.ad">
            <div class="relative">
              <RouterLink
                v-if="madde.hazir && madde.to && !madde.children"
                :to="madde.to"
                class="nav-item flex items-center gap-3 rounded-lg px-4 py-3 pr-10 text-sm font-medium text-primary-800 transition-all hover:bg-primary-50"
                active-class="bg-primary-100/70 text-primary-800"
              >
                <component :is="madde.ikon" class="h-4 w-4" />
                {{ madde.ad }}
              </RouterLink>
              <template v-else-if="madde.hazir && madde.children">
                <div class="nav-item flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-semibold text-primary-800">
                  <component :is="madde.ikon" class="h-4 w-4" />
                  {{ madde.ad }}
                </div>
                <div class="ml-4 border-l border-primary-100 pl-2">
                  <RouterLink
                    v-for="child in madde.children"
                    :key="child.ad"
                    :to="child.to || '#'"
                    class="nav-item flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-primary-700 transition-all hover:bg-primary-50"
                    active-class="bg-primary-100/70 font-semibold text-primary-800"
                  >
                    <component :is="child.ikon" class="h-3.5 w-3.5" />
                    {{ child.ad }}
                  </RouterLink>
                </div>
              </template>
              <span
                v-else-if="!madde.children"
                class="flex cursor-default items-center justify-between rounded-lg px-4 py-3 pr-10 text-sm text-surface-500 transition-all hover:bg-primary-50/50"
                :title="'Sonraki fazlarda etkinleşecek'"
              >
                <span class="flex items-center gap-3">
                  <component :is="madde.ikon" class="h-4 w-4" />
                  {{ madde.ad }}
                </span>
                <span class="rounded bg-surface-200 px-1.5 py-0.5 text-xs text-surface-500">Yakında</span>
              </span>
            </div>
          </template>
          </div>

        </template>
      </nav>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col">
      <!-- Topbar (site-spec: 64px) -->
      <header
        class="app-header"
      >
        <div
          class="flex h-16 items-center justify-between border-b border-surface-200 bg-surface-50/80 px-6 backdrop-blur-md"
        >
        <div class="flex items-center gap-3">
          <button class="mobile-menu-button rounded-lg p-2 text-surface-600 hover:bg-surface-100" title="Menüyü aç" @click="sidebarAcik = true"><Menu class="h-5 w-5" /></button>
          <div class="hidden text-sm text-surface-500 sm:block">
            <span class="font-semibold text-surface-900">{{ sayfaBasligi }}</span>
            <span class="mx-2 text-surface-300">/</span>
            <span class="font-medium text-surface-700">{{ tenantGosterimi }}</span>
            <template v-if="auth.seciciGosterilsinMi">
              <span class="mx-2 text-surface-300">|</span>
              <select
                :value="auth.seciliTenantId ?? ''"
                class="rounded-lg border border-surface-200 bg-white px-2 py-1 text-sm text-surface-700 outline-none focus:border-primary-600"
                title="İşlem yapılacak firmayı seçin"
                @change="kapsamDegistir(($event.target as HTMLSelectElement).value)"
              >
                <option value="">Tüm Firmalar (kayıt oluşturulamaz)</option>
                <option v-for="t in auth.tenantlar" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
            </template>
          </div>
          <div class="topbar-search hidden md:flex"><Search class="h-4 w-4" /><span>Menüde ara...</span><kbd>⌘ K</kbd></div>
        </div>
        <div class="flex items-center gap-2">
          <HatirlatmaEkleButonu />
          <div class="relative">
            <button class="notification-button" title="Hatırlatmalar" :aria-expanded="bildirimlerAcik" @click="bildirimleriAc">
              <Bell class="h-4 w-4" />
              <i v-if="okunmamisBildirimSayisi"></i>
              <span v-if="okunmamisBildirimSayisi" class="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-error-600 px-1 text-[10px] font-bold text-white">{{ okunmamisBildirimSayisi }}</span>
            </button>
            <div v-if="bildirimlerAcik" class="absolute right-0 top-11 z-50 w-80 rounded-xl border border-surface-200 bg-white p-2 shadow-xl">
              <div class="border-b border-surface-100 px-3 py-2"><p class="text-sm font-semibold text-surface-900">Hatırlatmalar</p><p class="text-xs text-surface-500">İş akışınız için önemli notlar</p></div>
              <button v-for="b in bildirimler" :key="b.id" type="button" class="block w-full rounded-lg px-3 py-3 text-left hover:bg-primary-50" @click="bildirimiOku(b.id, b.to)">
                <p class="text-sm font-semibold text-surface-800">{{ b.baslik }}</p><p class="mt-1 text-xs text-surface-500">{{ b.aciklama }}</p>
              </button>
            </div>
          </div>
          <div class="text-sm text-surface-500 md:hidden">
          <span class="font-medium text-surface-700">{{ tenantGosterimi }}</span>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <button
            v-if="auth.seciciGosterilsinMi"
            type="button"
            class="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-semibold transition-all"
            :class="auth.gelistiriciModu ? 'border-amber-400 bg-amber-50 text-amber-800' : 'border-surface-200 text-surface-600 hover:bg-surface-100'"
            :title="auth.gelistiriciModu ? 'Geliştirici modunu kapat' : 'Geliştirici modunu aç'"
            @click="auth.gelistiriciModunuDegistir"
          >
            <Database class="h-4 w-4" />
            {{ auth.gelistiriciModu ? 'Dev: Açık' : 'Dev' }}
          </button>
          <div class="text-right">
            <p class="text-sm font-medium text-surface-900">{{ kullaniciAdi }}</p>
            <p class="text-xs text-surface-500">{{ rolEtiketi }}</p>
          </div>
          <div v-if="minimizeModals.length" class="modal-gorev-cubugu" aria-label="Küçültülmüş çalışma panelleri">
            <button
              v-for="modal in minimizeModals"
              :key="modal.id"
              type="button"
              class="modal-gorev-sekmesi"
              :title="`${modal.title} panelini geri aç`"
              @click="restoreModal(modal.id)"
            >
              <span class="modal-gorev-ikon" aria-hidden="true">□</span>
              <span class="truncate">{{ modal.title }}</span>
            </button>
          </div>
          <button
            type="button"
            class="flex items-center gap-2 rounded-lg border border-surface-200 px-3 py-2 text-sm text-surface-700 transition-all hover:bg-error-50 hover:text-error-700"
            @click="cikisYap"
          >
            <LogOut class="h-4 w-4" />
            Çıkış
          </button>
        </div>
        </div>
      </header>

      <main id="main-content" class="app-main min-h-0 overflow-y-auto overscroll-contain bg-surface-50 p-6">
        <HatirlatmaOnerisi
          v-if="hatirlatmaOnerisi"
          class="fixed right-6 top-20 z-40 w-[min(32rem,calc(100vw-3rem))]"
          :tarih="hatirlatmaOnerisi.tarih"
          :baslik="hatirlatmaOnerisi.baslik"
          :payload="hatirlatmaOnerisi.payload"
          @kapat="hatirlatmaOnerisi = null"
          @kaydedildi="hatirlatmalariYukle"
        />
        <RouterView />
        <div
          v-if="seciliMenuYardimi && !yardimAcik"
          class="mx-auto mt-6 flex max-w-6xl justify-end"
        >
          <button
            type="button"
            class="ikincil-dugme !px-3 !py-1.5 !text-xs"
            title="Yardım panelini aç"
            @click="yardimDegistir(true)"
          >
            Yardım
          </button>
        </div>
        <section
          v-if="seciliMenuYardimi && yardimAcik"
          class="menu-yardim-panel mx-auto mt-6 max-w-6xl"
          role="region"
          :aria-label="`${seciliMenuYardimi.madde.ad} yardım bilgisi`"
        >
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-[11px] font-bold uppercase tracking-[0.16em] text-primary-700">Menü Yardımı</p>
              <h2 class="mt-1 text-lg font-bold text-surface-900">{{ seciliMenuYardimi.madde.ad }}</h2>
              <p class="mt-2 max-w-3xl text-sm leading-6 text-surface-600">{{ seciliMenuYardimi.detay.amac }}</p>
            </div>
            <button
              type="button"
              class="ikincil-dugme !px-3 !py-1.5 !text-xs"
              title="Yardım panelini kapat"
              aria-label="Yardım panelini kapat"
              @click="yardimDegistir(false)"
            >
              Kapat
            </button>
          </div>
          <div class="mt-5 grid gap-5 border-t border-surface-200 pt-4 md:grid-cols-[1fr_1fr]">
            <div>
              <h3 class="text-xs font-bold uppercase tracking-[0.12em] text-surface-500">Yapılabilecekler</h3>
              <ul class="mt-2 grid gap-2 text-sm text-surface-700 sm:grid-cols-2">
                <li v-for="islem in seciliMenuYardimi.detay.yapilabilir" :key="islem" class="flex gap-2">
                  <span class="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-600" aria-hidden="true"></span>
                  <span>{{ islem }}</span>
                </li>
              </ul>
            </div>
            <div class="rounded-xl border border-primary-100 bg-primary-50/70 p-4">
              <h3 class="text-xs font-bold uppercase tracking-[0.12em] text-primary-700">Kullanım ipucu</h3>
              <p class="mt-2 text-sm leading-6 text-primary-900">{{ seciliMenuYardimi.detay.ipucu }}</p>
            </div>
          </div>
        </section>
      </main>
    </div>
    <button
      v-if="faturaTaslagiVar && route.path !== '/finans/faturalar'"
      type="button"
      class="fixed bottom-5 right-6 z-[80] flex items-center gap-3 rounded-2xl border border-primary-200 bg-white px-4 py-3 text-left shadow-xl transition hover:-translate-y-0.5 hover:border-primary-400"
      @click="faturaTaslaginaDon"
    >
      <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-800 text-white">₺</span>
      <span><span class="block text-xs font-semibold uppercase tracking-wider text-primary-700">Açık çalışma</span><span class="block text-sm font-semibold text-surface-900">Fatura taslağına dön</span></span>
      <span class="ml-2 text-lg text-surface-400">↗</span>
    </button>
  </div>
</template>

<style scoped>
.app-shell { --erp-sidebar-width: 280px; --erp-header-height: 4rem; background: #f8fafc; }
.sidebar-is-collapsed { --erp-sidebar-width: 78px; }
.app-sidebar { transition: width .22s ease, transform .22s ease; }
.app-header { position: fixed; z-index: 60; top: 0; right: 0; left: var(--erp-sidebar-width); height: var(--erp-header-height); }
.app-main { position: fixed; z-index: 0; top: var(--erp-header-height); right: 0; bottom: 0; left: var(--erp-sidebar-width); }
.app-sidebar { position: fixed; z-index: 50; inset: 0 auto 0 0; }
.sidebar-collapsed { width: 78px; }
.sidebar-collapsed .font-heading,
.sidebar-collapsed .menu-grup-basligi span,
.sidebar-collapsed .menu-grup-basligi svg:not(:first-child),
.sidebar-collapsed .nav-item { font-size: 0; }
.sidebar-collapsed .menu-grup-basligi { justify-content: center; padding-left: .7rem; padding-right: .7rem; }
.sidebar-collapsed .menu-grup-basligi svg { margin: 0; }
.sidebar-collapsed .nav-item { justify-content: center; padding-left: .7rem; padding-right: .7rem; }
.sidebar-collapsed .nav-item svg { margin: 0; }
.topbar-search { align-items:center; gap:.45rem; width:210px; margin-left:1rem; border:1px solid #e2e8f0; border-radius:.65rem; background:#fff; color:#94a3b8; padding:.48rem .7rem; font-size:.7rem; }
.topbar-search kbd { margin-left:auto; border:1px solid #e2e8f0; border-radius:.3rem; background:#f8fafc; padding:.1rem .3rem; color:#94a3b8; font-size:.6rem; }
.notification-button { position:relative; display:flex; align-items:center; justify-content:center; width:2.25rem; height:2.25rem; border:1px solid #e2e8f0; border-radius:.65rem; background:#fff; color:#476176; }
.notification-button i { position:absolute; top:5px; right:5px; width:5px; height:5px; border-radius:50%; background:#d4a843; }
.modal-gorev-cubugu { position:fixed; z-index:70; right:1rem; bottom:1rem; left:calc(var(--erp-sidebar-width) + 1rem); display:flex; align-items:center; gap:.5rem; overflow-x:auto; pointer-events:none; }
.modal-gorev-sekmesi { pointer-events:auto; display:flex; min-width:0; max-width:18rem; align-items:center; gap:.5rem; border:1px solid #cbd5e1; border-radius:.65rem; background:#fff; padding:.55rem .75rem; color:#334155; font-size:.72rem; font-weight:700; box-shadow:0 8px 24px rgb(15 23 42 / 12%); transition:transform .15s ease, border-color .15s ease; }
.modal-gorev-sekmesi:hover { transform:translateY(-2px); border-color:#0f6973; color:#0f6973; }
.modal-gorev-ikon { display:inline-flex; width:1rem; height:1rem; align-items:center; justify-content:center; border:1px solid #94a3b8; border-radius:.2rem; color:#0f6973; font-size:.7rem; }
.mobile-menu-button { display:none; }
.menu-yardim-panel {
  border: 1px solid rgb(191 219 218);
  border-radius: 1rem;
  background: linear-gradient(135deg, rgb(240 253 250 / 92%), rgb(255 255 255 / 98%));
  padding: 1.25rem 1.5rem;
  box-shadow: 0 12px 30px rgb(15 23 42 / 8%);
}
.sidebar-help-label { font-size: .65rem; line-height: 1; }
.sidebar-collapsed .sidebar-help-label { display: none; }
.sidebar-backdrop { display:none; }
@media (max-width: 1023px) {
  .app-shell { --erp-sidebar-width: 0px; }
  .mobile-menu-button { display:inline-flex; }
  .app-header { left: 0; }
  .app-main { left: 0; }
  .sidebar-is-collapsed .app-header,
  .sidebar-is-collapsed .app-main { left: 0; }
  .app-sidebar { transform:translateX(-102%); box-shadow:10px 0 30px rgba(15,36,64,.15); }
  .app-sidebar.sidebar-mobile-open { transform:translateX(0); }
  .sidebar-backdrop { display:block; position:fixed; z-index:40; inset:0; background:rgba(15,36,64,.28); backdrop-filter:blur(2px); }
}
@media (max-width: 1023px) {
  .modal-gorev-cubugu { right:.75rem; left:.75rem; bottom:.75rem; }
}
</style>
