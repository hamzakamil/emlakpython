<script setup lang="ts">
/**
 * Kayıt iletişim kutusu — oluşturma/düzenleme formları için modal iskelet.
 * Kalıcı paneller form durumunu korur; Escape yalnızca geçici modalı kapatır.
 */
import { computed, inject, onMounted, onUnmounted, ref } from 'vue'

const props = withDefaults(defineProps<{
  baslik: string
  disTiklamaKapat?: boolean
  kalici?: boolean
  buyuk?: boolean
  kucuk?: boolean
  tasinabilir?: boolean
  kontrollu?: boolean
  kirli?: boolean
  genisIcerik?: boolean
}>(), {
  disTiklamaKapat: true,
  kalici: true,
  buyuk: false,
  kucuk: false,
  tasinabilir: true,
  kontrollu: false,
  kirli: false,
  genisIcerik: false,
})

const minimizeModal = inject<(payload: { id: string; title: string }) => void>('minimizeModal')
const emit = defineEmits<{
  (e: 'kapat'): void
  (e: 'kucult'): void
  (e: 'buyut'): void
  (e: 'taslakKaydet'): void
}>()

const panel = ref<HTMLElement | null>(null)
const yerelBuyuk = ref(false)
const yerelKucuk = ref(false)
const tasiniyor = ref(false)
const konumBelirlendi = ref(false)
const panelKonumu = ref({ left: 0, top: 0 })
const boyutBelirlendi = ref(false)
const panelBoyutu = ref({ width: 1200, height: 780 })
const osTipi = ref<'windows' | 'mac' | 'linux'>('windows')
// OS detection on mount
onMounted(() => {
  const ua = navigator.userAgent
  if (/Macintosh|Mac OS X/.test(ua)) {
    osTipi.value = 'mac'
  } else if (/Windows NT/.test(ua)) {
    osTipi.value = 'windows'
  } else {
    osTipi.value = 'linux'
  }
})
const kapatmaUyarisiAcik = ref(false)
const panelTransitionAktif = ref(false)
let surukleme = { x: 0, y: 0, left: 0, top: 0 }
let boyutlandirma = { x: 0, y: 0, width: 0, height: 0, left: 0, top: 0, kenar: '' }
let ghostOutline: HTMLDivElement | null = null
let ghostBoyutu = { width: 0, height: 0 }
let animasyonKare = 0
let sonPointerOlayi: PointerEvent | null = null
let hareketModu: 'surukleme' | 'boyutlandirma' | '' = ''

const panelAnahtari = computed(() => {
  const ad = props.baslik.toLocaleLowerCase('tr-TR').replace(/[^a-z0-9çğıöşü]+/gi, '-').replace(/^-|-$/g, '')
  return `emlak_erp_workspace_${ad || 'kayit'}`
})
const PANEL_BOYUT_ANAHTARI = computed(() => `${panelAnahtari.value}_boyut_v1`)
const PANEL_KONUM_ANAHTARI = computed(() => `${panelAnahtari.value}_konum_v1`)
const etkinBuyuk = computed(() => props.kontrollu ? props.buyuk : yerelBuyuk.value)
const etkinKucuk = computed(() => props.kontrollu ? props.kucuk : yerelKucuk.value)
const etkinKalici = computed(() => props.kalici)
const etkinTasinabilir = computed(() => props.tasinabilir)

function baslatSurukleme(olay: PointerEvent): void {
  if (!etkinTasinabilir.value || etkinBuyuk.value || etkinKucuk.value || !panel.value) return
  olay.preventDefault()
  olay.stopPropagation()
  const rect = panel.value.getBoundingClientRect()
  tasiniyor.value = true
  konumBelirlendi.value = true
  surukleme = { x: olay.clientX, y: olay.clientY, left: rect.left, top: rect.top }
  panelKonumu.value = { left: rect.left, top: rect.top }
  hareketModu = 'surukleme'
  ghostOlustur(rect)
  panel.value.style.opacity = '0.4'
  panel.value.style.userSelect = 'none'
  window.addEventListener('pointermove', surukle)
  window.addEventListener('pointerup', bitirSurukleme, { once: true })
}
function surukle(olay: PointerEvent): void {
  if (!tasiniyor.value || !ghostOutline) return
  sonPointerOlayi = olay
  karePlanla()
}
function bitirSurukleme(): void {
  if (sonPointerOlayi) {
    cancelAnimationFrame(animasyonKare)
    suruklemeGhostGuncelle(sonPointerOlayi)
  }
  const sonKonum = sonPointerOlayi ? suruklemeKonumuHesapla(sonPointerOlayi) : panelKonumu.value
  tasiniyor.value = false
  panelKonumu.value = sonKonum
  hareketiTemizle()
  panelTransitionAktif.value = true
  localStorage.setItem(PANEL_KONUM_ANAHTARI.value, JSON.stringify(panelKonumu.value))
  window.removeEventListener('pointermove', surukle)
  window.setTimeout(() => { panelTransitionAktif.value = false }, 150)
}

function baslatBoyutlandirma(olay: PointerEvent, kenar: string): void {
  if (!etkinKalici.value || etkinBuyuk.value || etkinKucuk.value || !panel.value) return
  olay.preventDefault()
  olay.stopPropagation()
  const rect = panel.value.getBoundingClientRect()
  boyutlandirma = { x: olay.clientX, y: olay.clientY, width: rect.width, height: rect.height, left: rect.left, top: rect.top, kenar }
  boyutBelirlendi.value = true
  hareketModu = 'boyutlandirma'
  ghostOlustur(rect)
  panel.value.style.opacity = '0.4'
  panel.value.style.userSelect = 'none'
  window.addEventListener('pointermove', boyutlandir)
  window.addEventListener('pointerup', bitirBoyutlandirma, { once: true })
}
function boyutlandir(olay: PointerEvent): void {
  if (!boyutlandirma.kenar || !ghostOutline) return
  sonPointerOlayi = olay
  karePlanla()
}
function bitirBoyutlandirma(): void {
  if (sonPointerOlayi) {
    cancelAnimationFrame(animasyonKare)
    boyutlandirmaGhostGuncelle(sonPointerOlayi)
  }
  const sonBoyut = sonPointerOlayi ? boyutlandirmaHesapla(sonPointerOlayi) : {
    width: boyutlandirma.width,
    height: boyutlandirma.height,
    left: boyutlandirma.left,
    top: boyutlandirma.top,
  }
  panelBoyutu.value = { width: sonBoyut.width, height: sonBoyut.height }
  if (boyutlandirma.kenar.includes('w') || boyutlandirma.kenar.includes('n')) {
    panelKonumu.value = { left: sonBoyut.left, top: sonBoyut.top }
    konumBelirlendi.value = true
  }
  hareketiTemizle()
  panelTransitionAktif.value = true
  localStorage.setItem(PANEL_BOYUT_ANAHTARI.value, JSON.stringify(panelBoyutu.value))
  if (boyutlandirma.kenar.includes('w') || boyutlandirma.kenar.includes('n')) {
    localStorage.setItem(PANEL_KONUM_ANAHTARI.value, JSON.stringify(panelKonumu.value))
  }
  window.setTimeout(() => { panelTransitionAktif.value = false }, 150)
  window.removeEventListener('pointermove', boyutlandir)
}
function ghostOlustur(rect: DOMRect): void {
  ghostOutline?.remove()
  ghostBoyutu = { width: rect.width, height: rect.height }
  ghostOutline = document.createElement('div')
  ghostOutline.style.position = 'fixed'
  ghostOutline.style.pointerEvents = 'none'
  ghostOutline.style.left = `${rect.left}px`
  ghostOutline.style.top = `${rect.top}px`
  ghostOutline.style.width = `${rect.width}px`
  ghostOutline.style.height = `${rect.height}px`
  ghostOutline.style.border = '2px dashed #0f6973'
  ghostOutline.style.background = 'rgba(15,105,115,0.08)'
  ghostOutline.style.borderRadius = getComputedStyle(panel.value as HTMLElement).borderRadius
  ghostOutline.style.willChange = 'transform'
  ghostOutline.style.zIndex = '2147483646'
  document.body.appendChild(ghostOutline)
}
function karePlanla(): void {
  if (animasyonKare) return
  animasyonKare = requestAnimationFrame(() => {
    animasyonKare = 0
    if (!sonPointerOlayi) return
    if (hareketModu === 'surukleme') suruklemeGhostGuncelle(sonPointerOlayi)
    if (hareketModu === 'boyutlandirma') boyutlandirmaGhostGuncelle(sonPointerOlayi)
  })
}
function suruklemeKonumuHesapla(olay: PointerEvent): { left: number; top: number } {
  const margin = 12
  const width = ghostBoyutu.width || 480
  const height = ghostBoyutu.height || 500
  return {
    left: Math.min(Math.max(margin, surukleme.left + olay.clientX - surukleme.x), window.innerWidth - width - margin),
    top: Math.min(Math.max(margin, surukleme.top + olay.clientY - surukleme.y), window.innerHeight - height - margin),
  }
}
function suruklemeGhostGuncelle(olay: PointerEvent): void {
  if (!ghostOutline) return
  const konum = suruklemeKonumuHesapla(olay)
  ghostOutline.style.transform = `translate3d(${konum.left - surukleme.left}px, ${konum.top - surukleme.top}px, 0)`
}
function boyutlandirmaHesapla(olay: PointerEvent): { width: number; height: number; left: number; top: number } {
  const minWidth = Math.min(760, window.innerWidth - 32)
  const minHeight = Math.min(520, window.innerHeight - 32)
  const maxWidth = Math.max(minWidth, window.innerWidth - 32)
  const maxHeight = Math.max(minHeight, window.innerHeight - 32)
  const dx = olay.clientX - boyutlandirma.x
  const dy = olay.clientY - boyutlandirma.y
  let width = boyutlandirma.width
  let height = boyutlandirma.height
  let left = boyutlandirma.left
  let top = boyutlandirma.top
  if (boyutlandirma.kenar.includes('e')) width = Math.min(maxWidth, Math.max(minWidth, boyutlandirma.width + dx))
  if (boyutlandirma.kenar.includes('w')) {
    width = Math.min(maxWidth, Math.max(minWidth, boyutlandirma.width - dx))
    left = boyutlandirma.left + boyutlandirma.width - width
  }
  if (boyutlandirma.kenar.includes('s')) height = Math.min(maxHeight, Math.max(minHeight, boyutlandirma.height + dy))
  if (boyutlandirma.kenar.includes('n')) {
    height = Math.min(maxHeight, Math.max(minHeight, boyutlandirma.height - dy))
    top = boyutlandirma.top + boyutlandirma.height - height
  }
  if (boyutlandirma.kenar.includes('w') || boyutlandirma.kenar.includes('n')) {
    const konum = {
      left: Math.max(12, Math.min(left, window.innerWidth - width - 12)),
      top: Math.max(12, Math.min(top, window.innerHeight - height - 12)),
    }
    left = konum.left
    top = konum.top
  }
  return { width, height, left, top }
}
function boyutlandirmaGhostGuncelle(olay: PointerEvent): void {
  if (!ghostOutline) return
  const boyut = boyutlandirmaHesapla(olay)
  ghostOutline.style.width = `${boyut.width}px`
  ghostOutline.style.height = `${boyut.height}px`
  ghostOutline.style.left = `${boyut.left}px`
  ghostOutline.style.top = `${boyut.top}px`
}
function hareketiTemizle(): void {
  if (animasyonKare) cancelAnimationFrame(animasyonKare)
  animasyonKare = 0
  ghostOutline?.remove()
  ghostOutline = null
  ghostBoyutu = { width: 0, height: 0 }
  sonPointerOlayi = null
  hareketModu = ''
  boyutlandirma.kenar = ''
  if (panel.value) {
    panel.value.style.opacity = ''
    panel.value.style.userSelect = ''
  }
}

function tuslaKapat(olay: KeyboardEvent): void {
  if (olay.key !== 'Escape') return
  if (etkinBuyuk.value) {
    olay.preventDefault()
    buyutPanel()
    return
  }
  if (!etkinKalici.value && props.disTiklamaKapat) kapatPanel()
}
function kucultPanel(): void {
  if (!props.kontrollu) yerelKucuk.value = !yerelKucuk.value
  const payload = { id: panelAnahtari.value, title: props.baslik }
  minimizeModal?.(payload)
  emit('kucult')
}
function geriAcPanel(): void {
  if (props.kontrollu) {
    emit('kucult')
  } else {
    yerelKucuk.value = false
  }
}
function buyutPanel(): void {
  if (!props.kontrollu) yerelBuyuk.value = !yerelBuyuk.value
  emit('buyut')
}
function kapatPanel(): void {
  if (props.kirli) {
    kapatmaUyarisiAcik.value = true
    return
  }
  emit('kapat')
}
function taslagiKaydetVeKapat(): void {
  kapatmaUyarisiAcik.value = false
  emit('taslakKaydet')
  emit('kapat')
}
function kapatmadanDevam(): void {
  kapatmaUyarisiAcik.value = false
  emit('kapat')
}
function osTespit(): 'windows' | 'mac' | 'linux' {
  if (typeof window === 'undefined') return 'windows'
  const navigatorRef = window.navigator as Navigator & {
    userAgentData?: { platform?: string }
  }
  const uaData = navigatorRef.userAgentData
  if (uaData?.platform) {
    const platform = uaData.platform.toLowerCase()
    if (platform.includes('win')) return 'windows'
    if (platform.includes('mac')) return 'mac'
    if (platform.includes('linux')) return 'linux'
  }
  const platform = navigatorRef.platform || ''
  const userAgent = navigatorRef.userAgent || ''
  if (/Win/i.test(platform) || /Windows/i.test(userAgent)) return 'windows'
  if (/Mac/i.test(platform) || /Macintosh/i.test(userAgent)) return 'mac'
  if (/Linux/i.test(platform) || /Linux/i.test(userAgent)) return 'linux'
  return 'windows'
}

let oncekiBodyOverflow = ''

onMounted(() => {
  osTipi.value = osTespit()
  window.addEventListener('erp:restore-modal', panelGeriAc)
  oncekiBodyOverflow = document.body.style.overflow
  if (!etkinKalici.value) document.body.style.overflow = 'hidden'
  window.addEventListener('keydown', tuslaKapat)
  if (etkinTasinabilir.value) {
    try {
      const kayitliKonum = JSON.parse(localStorage.getItem(PANEL_KONUM_ANAHTARI.value) || 'null') as { left?: number; top?: number } | null
      if (kayitliKonum?.left !== undefined && kayitliKonum.top !== undefined) {
        panelKonumu.value = { left: kayitliKonum.left, top: kayitliKonum.top }
        konumBelirlendi.value = true
      }
    } catch {
      localStorage.removeItem(PANEL_KONUM_ANAHTARI.value)
    }
    try {
      const kayitliBoyut = JSON.parse(localStorage.getItem(PANEL_BOYUT_ANAHTARI.value) || 'null') as { width?: number; height?: number } | null
      if (kayitliBoyut?.width && kayitliBoyut?.height) {
        const shell = getComputedStyle(document.querySelector('.app-shell') || document.documentElement)
        const sidebar = Number.parseFloat(shell.getPropertyValue('--erp-sidebar-width')) || 0
        const header = Number.parseFloat(shell.getPropertyValue('--erp-header-height')) || 64
        const maxWidth = Math.max(760, window.innerWidth - sidebar - 24)
        const maxHeight = Math.max(520, window.innerHeight - header - 24)
        panelBoyutu.value = {
          width: Math.min(Math.max(760, kayitliBoyut.width), maxWidth),
          height: Math.min(Math.max(520, kayitliBoyut.height), maxHeight),
        }
        boyutBelirlendi.value = true
      }
    } catch {
      localStorage.removeItem(PANEL_BOYUT_ANAHTARI.value)
    }
  }
})

function panelGeriAc(olay: Event): void {
  const detay = (olay as CustomEvent<{ id?: string }>).detail
  if (detay?.id !== panelAnahtari.value) return
  geriAcPanel()
}

onUnmounted(() => {
  hareketiTemizle()
  if (!etkinKalici.value) document.body.style.overflow = oncekiBodyOverflow
  window.removeEventListener('keydown', tuslaKapat)
  window.removeEventListener('pointermove', surukle)
  window.removeEventListener('pointermove', boyutlandir)
  window.removeEventListener('erp:restore-modal', panelGeriAc)
})
</script>

<template>
  <div
    class="fixed inset-0 z-70 flex items-end justify-end"
    :class="etkinKalici ? 'pointer-events-none' : 'bg-surface-900/50 p-4'"
    @click.self="props.disTiklamaKapat && emit('kapat')"
  >
    <div
      class="kayit-modal pointer-events-auto flex flex-col border border-surface-200 bg-surface-50 shadow-modal"
      :class="[
        `os-${osTipi}`,
        { 'kapatma-uyarisi-acik': kapatmaUyarisiAcik },
        etkinKucuk
          ? 'mb-4 mr-4 w-[min(92vw,25rem)] rounded-2xl'
          : etkinBuyuk
            ? 'erp-panel-buyuk fixed h-[calc(100dvh-var(--erp-header-height)-1.5rem)] max-h-none w-[calc(100vw-var(--erp-sidebar-width)-1.5rem)] rounded-2xl'
            : 'erp-panel-docked rounded-2xl',
      ]"
      ref="panel"
      :style="etkinTasinabilir && !etkinBuyuk && !etkinKucuk && (boyutBelirlendi || konumBelirlendi) ? {
        ...(boyutBelirlendi ? { width: `${panelBoyutu.width}px`, height: `${panelBoyutu.height}px` } : {}),
        position: 'fixed',
        transition: panelTransitionAktif ? 'left 150ms ease-out, top 150ms ease-out, width 150ms ease-out, height 150ms ease-out' : 'none',
        ...(konumBelirlendi ? { left: `${panelKonumu.left}px`, top: `${panelKonumu.top}px`, right: 'auto', bottom: 'auto' } : {}),
      } : undefined"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="`kayit-modal-baslik-${panelAnahtari}`"
    >
      <div class="kayit-modal-baslik flex shrink-0 select-none items-center justify-between border-b border-surface-200 bg-white px-5 py-3" :class="{ 'cursor-move': etkinTasinabilir && !etkinBuyuk && !etkinKucuk, 'cursor-grabbing': tasiniyor }" @pointerdown="baslatSurukleme">
        <div class="kayit-modal-baslik-metni">
          <p v-if="etkinKalici" class="text-[10px] font-semibold uppercase tracking-[0.18em] text-primary-700">Çalışma paneli</p>
          <h2 :id="`kayit-modal-baslik-${panelAnahtari}`" class="font-heading text-base font-semibold text-surface-900">{{ baslik }}</h2>
        </div>
        <div class="kayit-modal-kontroller flex items-center gap-1" :class="{ 'kayit-modal-kontroller-mac': osTipi === 'mac' }">
          <button v-if="etkinKalici && !etkinKucuk" type="button" class="pencere-kontrol pencere-minimize" aria-label="Alta al" title="Alta al" @pointerdown.stop @click.stop="kucultPanel">
            <svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1 5h8" /></svg>
          </button>
          <button v-if="etkinKalici && !etkinKucuk" type="button" class="pencere-kontrol pencere-maximize" :aria-label="etkinBuyuk ? 'Normale dön' : 'Büyüt'" :title="etkinBuyuk ? 'Normale dön' : 'Büyüt'" @pointerdown.stop @click.stop="buyutPanel">
            <svg v-if="!etkinBuyuk" viewBox="0 0 10 10" aria-hidden="true"><rect x="1.5" y="1.5" width="7" height="7" /></svg>
            <svg v-else viewBox="0 0 10 10" aria-hidden="true"><path d="M3 1.5h5.5V7M7 3H1.5v5.5H7V3Z" /></svg>
          </button>
          <button v-if="etkinKalici && etkinKucuk" type="button" class="pencere-kontrol pencere-restore" aria-label="Geri aç" title="Geri aç" @pointerdown.stop @click.stop="geriAcPanel">
            <svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 3.5h5v5h-5zM3.5 1.5h5v5" /></svg>
          </button>
          <button type="button" class="pencere-kontrol pencere-close" aria-label="Kapat" title="Taslağı kapat" @pointerdown.stop @click.stop="kapatPanel">
            <svg viewBox="0 0 10 10" aria-hidden="true"><path d="m2 2 6 6M8 2 2 8" /></svg>
          </button>
        </div>
      </div>
      <div v-if="!etkinKucuk" class="kayit-modal-icerik min-h-0 flex-1 overflow-y-auto p-4" :class="{ 'kayit-modal-icerik-genis': props.genisIcerik }">
        <slot />
      </div>
      <div v-else class="flex items-center justify-between px-4 py-3 text-xs text-surface-500">
        <span>Çalışma paneli açık</span><button type="button" class="font-semibold text-primary-700" @click="geriAcPanel">Geri aç</button>
      </div>
      <template v-if="etkinKalici && !etkinBuyuk && !etkinKucuk">
        <span class="erp-resize-handle erp-resize-n" @pointerdown="baslatBoyutlandirma($event, 'n')" />
        <span class="erp-resize-handle erp-resize-e" @pointerdown="baslatBoyutlandirma($event, 'e')" />
        <span class="erp-resize-handle erp-resize-s" @pointerdown="baslatBoyutlandirma($event, 's')" />
        <span class="erp-resize-handle erp-resize-w" @pointerdown="baslatBoyutlandirma($event, 'w')" />
        <span class="erp-resize-handle erp-resize-se" @pointerdown="baslatBoyutlandirma($event, 'se')" />
        <span class="erp-resize-handle erp-resize-sw" @pointerdown="baslatBoyutlandirma($event, 'sw')" />
        <span class="erp-resize-handle erp-resize-ne" @pointerdown="baslatBoyutlandirma($event, 'ne')" />
        <span class="erp-resize-handle erp-resize-nw" @pointerdown="baslatBoyutlandirma($event, 'nw')" />
      </template>
    </div>
    <div v-if="kapatmaUyarisiAcik" class="kapatma-uyarisi pointer-events-auto" role="alertdialog" aria-modal="true" aria-labelledby="kapatma-uyarisi-baslik" @click.stop>
      <h3 id="kapatma-uyarisi-baslik">Kaydedilmemiş değişiklikler var</h3>
      <p>Taslağı kapatmadan önce nasıl devam etmek istersiniz?</p>
      <div class="kapatma-uyarisi-eylemler">
        <button type="button" class="birincil-dugme" @click="taslagiKaydetVeKapat">Taslağı Kaydet</button>
        <button type="button" class="ikincil-dugme" @click="kapatmadanDevam">Kaydetmeden Kapat</button>
        <button type="button" class="metin-dugme" @click="kapatmaUyarisiAcik = false">Vazgeç</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.erp-panel-docked {
  position: fixed;
  top: calc(var(--erp-header-height) + .75rem);
  right: .75rem;
  bottom: .75rem;
  left: calc(var(--erp-sidebar-width) + .75rem);
  min-width: min(760px, calc(100vw - 1.5rem));
  min-height: min(520px, calc(100dvh - var(--erp-header-height) - 1.5rem));
  max-width: calc(100vw - var(--erp-sidebar-width) - 1.5rem);
  max-height: calc(100dvh - var(--erp-header-height) - 1.5rem);
}

.erp-resize-handle {
  position: absolute;
  z-index: 5;
}
.erp-resize-n, .erp-resize-s { left: 12px; right: 12px; height: 8px; cursor: ns-resize; }
.erp-resize-n { top: -4px; }
.erp-resize-s { bottom: -4px; }
.erp-resize-e, .erp-resize-w { top: 12px; bottom: 12px; width: 8px; cursor: ew-resize; }
.erp-resize-e { right: -4px; }
.erp-resize-w { left: -4px; }
.erp-resize-se, .erp-resize-sw, .erp-resize-ne, .erp-resize-nw { width: 14px; height: 14px; }
.erp-resize-se {
  right: -5px;
  bottom: -5px;
  cursor: nwse-resize;
  border-radius: 0 0 1rem 0;
  background: linear-gradient(135deg, transparent 48%, rgba(100, 116, 139, .4) 49%, rgba(100, 116, 139, .4) 58%, transparent 59%), linear-gradient(135deg, transparent 62%, rgba(100, 116, 139, .4) 63%, rgba(100, 116, 139, .4) 72%, transparent 73%);
}
.erp-resize-sw { left: -5px; bottom: -5px; cursor: nesw-resize; }
.erp-resize-ne { right: -5px; top: -5px; cursor: nesw-resize; }
.erp-resize-nw { left: -5px; top: -5px; cursor: nwse-resize; }

@media (max-width: 900px) {
  .erp-panel-docked {
    min-width: calc(100vw - 1.5rem);
    width: calc(100vw - 1.5rem) !important;
    top: calc(var(--erp-header-height) + .5rem);
    right: .75rem;
    bottom: .5rem;
    left: .75rem;
  }
}

.erp-panel-buyuk {
  top: var(--erp-header-height);
  right: 1.5rem;
  bottom: 1.5rem;
  left: var(--erp-sidebar-width);
}

.kayit-modal {
  --win-close-bg: #e81123;
  --mac-close: #ff5f56;
  --mac-minimize: #ffbd2e;
  --mac-maximize: #27c93f;
}

.kayit-modal-baslik {
  min-height: 3.25rem;
  gap: 1rem;
}

.kayit-modal-baslik-metni {
  min-width: 0;
}

.kayit-modal-icerik {
  --kayit-form-max-width: 58rem;
  --kayit-field-height: 2.15rem;
  --kayit-field-padding-x: .6rem;
  --kayit-field-padding-y: .42rem;
}

.kayit-modal-icerik :deep(form) {
  width: min(100%, var(--kayit-form-max-width));
  margin: 0 auto;
  gap: .75rem;
}

.kayit-modal-icerik :deep(form > .grid) {
  gap: .6rem .75rem;
}

.kayit-modal-icerik :deep(.etiket) {
  gap: .25rem;
  font-size: .72rem;
  line-height: 1.2;
}

.kayit-modal-icerik :deep(.etiket > input),
.kayit-modal-icerik :deep(.etiket > select),
.kayit-modal-icerik :deep(.etiket > textarea),
.kayit-modal-icerik :deep(.alan) {
  min-height: var(--kayit-field-height);
  max-width: 100%;
  border-radius: .45rem;
  padding: var(--kayit-field-padding-y) var(--kayit-field-padding-x);
  font-size: .78rem;
}

.kayit-modal-icerik :deep(.etiket > textarea),
.kayit-modal-icerik :deep(textarea.alan) {
  min-height: 4.25rem;
}

.kayit-modal-icerik :deep(.etiket-baslik) {
  display: block;
  min-height: 1rem;
  line-height: 1rem;
}

.kayit-modal-icerik :deep(fieldset) {
  min-width: 0;
}

.kayit-modal-icerik :deep(button.birincil-dugme),
.kayit-modal-icerik :deep(button.ikincil-dugme) {
  min-height: 2.15rem;
  padding: .42rem .7rem;
  font-size: .78rem;
}

.kayit-modal-icerik-genis {
  --kayit-form-max-width: none;
}

.kayit-modal-icerik-genis :deep(form) {
  width: 100%;
  max-width: none;
}

.kayit-modal-icerik-genis :deep(.kayit-genis-bolum) {
  width: 100%;
  min-width: 0;
}

.kayit-modal-kontroller {
  flex: 0 0 auto;
  align-self: stretch;
  margin: -.75rem -1.25rem -.75rem 0;
  gap: 0;
}

.pencere-kontrol {
  display: inline-flex;
  width: 46px;
  height: 52px;
  align-items: center;
  justify-content: center;
  border: 0;
  background: transparent;
  color: #475569;
  cursor: pointer;
  transition: background-color .15s ease, color .15s ease;
}

.pencere-kontrol svg {
  width: 10px;
  height: 10px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.1;
}

.pencere-kontrol:hover,
.pencere-kontrol:focus-visible {
  background: rgba(0, 0, 0, .05);
  outline: none;
  color: #0f172a;
}

.pencere-close:hover,
.pencere-close:focus-visible {
  background: var(--win-close-bg);
  color: #fff;
}

.kayit-modal-kontroller-mac {
  order: -1;
  margin: -.75rem 0 -.75rem -1.25rem;
  padding-left: 12px;
}

.kayit-modal-kontroller-mac .pencere-kontrol {
  width: 12px;
  height: 12px;
  margin-right: 8px;
  border-radius: 999px;
  background: #94a3b8;
  position: relative;
}

.kayit-modal-kontroller-mac .pencere-close { background: var(--mac-close); }
.kayit-modal-kontroller-mac .pencere-minimize { background: var(--mac-minimize); }
.kayit-modal-kontroller-mac .pencere-maximize { background: var(--mac-maximize); }
.kayit-modal-kontroller-mac .pencere-restore { background: var(--mac-maximize); }
.kayit-modal-kontroller-mac .pencere-close { order: 1; }
.kayit-modal-kontroller-mac .pencere-minimize { order: 2; }
.kayit-modal-kontroller-mac .pencere-maximize,
.kayit-modal-kontroller-mac .pencere-restore { order: 3; }

.kayit-modal-kontroller-mac .pencere-kontrol svg {
  width: 8px;
  height: 8px;
  opacity: 0;
  stroke: #592f2b;
  stroke-width: 1.2;
  transition: opacity .12s ease;
}

.kayit-modal-kontroller-mac:hover .pencere-kontrol svg,
.kayit-modal-kontroller-mac:focus-within .pencere-kontrol svg {
  opacity: 1;
}

.kayit-modal-kontroller-mac .pencere-close svg {
  stroke: #6f2622;
}

.kapatma-uyarisi {
  position: fixed;
  top: 50%;
  left: 50%;
  z-index: 80;
  width: min(92vw, 28rem);
  transform: translate(-50%, -50%);
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  background: #fff;
  box-shadow: 0 24px 70px rgba(15, 23, 42, .24);
  padding: 1.25rem;
}

.kapatma-uyarisi h3 { margin: 0; color: #0f172a; font-size: 1rem; font-weight: 700; }
.kapatma-uyarisi p { margin: .5rem 0 1rem; color: #64748b; font-size: .875rem; }
.kapatma-uyarisi-eylemler { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: .5rem; }
.kapatma-uyarisi-eylemler button { min-height: 2.25rem; border-radius: .5rem; padding: .5rem .75rem; font-size: .75rem; font-weight: 700; }
.kapatma-uyarisi .birincil-dugme { background: #0f766e; color: #fff; }
.kapatma-uyarisi .ikincil-dugme { border: 1px solid #fecaca; color: #b91c1c; }
.kapatma-uyarisi .metin-dugme { color: #475569; }

@media (max-width: 767px) {
  .kayit-modal:not(.os-mac) .pencere-kontrol,
  .kayit-modal.os-mac .pencere-kontrol {
    width: 44px;
    height: 44px;
    border-radius: 0;
    margin: 0;
  }
  .kayit-modal-kontroller-mac {
    order: initial;
    margin: -.75rem -1.25rem -.75rem 0;
    padding-left: 0;
  }
  .kayit-modal-kontroller-mac .pencere-kontrol {
    width: 44px;
    height: 44px;
    margin: 0;
    border-radius: 0;
    background: transparent;
  }
  .kayit-modal-kontroller-mac .pencere-kontrol::before {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: currentColor;
    content: '';
  }
  .kayit-modal-kontroller-mac .pencere-close { color: var(--mac-close); }
  .kayit-modal-kontroller-mac .pencere-minimize { color: var(--mac-minimize); }
  .kayit-modal-kontroller-mac .pencere-maximize,
  .kayit-modal-kontroller-mac .pencere-restore { color: var(--mac-maximize); }
  .kayit-modal-kontroller-mac .pencere-kontrol svg { display: none; }
}
</style>
