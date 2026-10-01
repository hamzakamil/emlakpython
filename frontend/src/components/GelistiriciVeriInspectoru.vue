<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

interface Kaynak {
  tablo: string
  sutun: string
  alan: string
  tip: string
  api: string
  ekran: string
}

const auth = useAuthStore()
const route = useRoute()
const kaynak = ref<Kaynak | null>(null)
const imlec = ref({ x: 0, y: 0 })
const hedef = ref<HTMLElement | null>(null)
const aktif = computed(() => auth.gelistiriciModu && auth.kullanici?.role === 'super_admin')

const endpointEslemeleri: Array<[RegExp, string, string]> = [
  [/^\/cari\/cariler/, 'cari_cari', 'Cari'],
  [/^\/finans\/hesaplar/, 'finance_kasabankahesabi', 'KasaBankaHesabi'],
  [/^\/finans\/islemler/, 'finance_finansalislem', 'FinansalIslem'],
  [/^\/insaat\/pozlar/, 'construction_poz', 'Poz'],
  [/^\/insaat\/yapi-sinifi/, 'construction_yapisinifibirimmaliyet', 'YapiSinifiBirimMaliyet'],
  [/^\/insaat\/projeler/, 'construction_proje', 'Proje'],
  [/^\/insaat\/poz-planlari/, 'construction_pozplan', 'PozPlan'],
  [/^\/insaat\/hakedisler/, 'construction_hakedis', 'Hakedis'],
  [/^\/gayrimenkul\/gayrimenkuller/, 'real_estate_gayrimenkul', 'Gayrimenkul'],
  [/^\/yonetim\/veritabani/, 'database_admin', 'Database'],
]

function tabloBilgisi(): [string, string] {
  const esleme = endpointEslemeleri.find(([desen]) => desen.test(route.path))
  return esleme ? [esleme[1], esleme[2]] : ['uygulama', 'Uygulama']
}

function alanAdi(element: HTMLElement): string {
  if (element.closest('.dev-kaynak-noktasi')) return 'rozet'
  const acikAlan = element.closest('[data-db-field]')?.getAttribute('data-db-field')
  if (acikAlan) return acikAlan
  const td = element.closest('td')
  const th = element.closest('table')?.querySelectorAll('thead th')
  if (th && td) return th[Array.from(td.parentElement?.children || []).indexOf(td)]?.textContent?.trim() || 'deger'
  const label = element.closest('label')?.textContent?.trim()
  return label || element.getAttribute('name') || element.getAttribute('placeholder') || 'deger'
}

function alanNormalleştir(deger: string): string {
  return deger.toLocaleLowerCase('tr-TR').replace(/[^a-z0-9]+/gi, '_').replace(/^_|_$/g, '') || 'deger'
}

function kaynakOlustur(element: HTMLElement): Kaynak {
  const [tablo, model] = tabloBilgisi()
  const sutun = element.getAttribute('data-db-column') || alanNormalleştir(alanAdi(element))
  return {
    tablo,
    sutun,
    alan: `${model}.${sutun}`,
    tip: element.getAttribute('type') || element.tagName.toLocaleLowerCase(),
    api: `GET/POST ${route.path}`,
    ekran: route.path,
  }
}

function uygunHedef(element: HTMLElement | null): HTMLElement | null {
  if (element?.closest('.dev-kaynak-noktasi')) return null
  return element?.closest('td, th, input, textarea, select, [data-db-field]') as HTMLElement | null
}

function ustuneGel(event: MouseEvent): void {
  if (!aktif.value) return
  const yeniHedef = uygunHedef(event.target as HTMLElement)
  if (!yeniHedef) return
  hedef.value = yeniHedef
  kaynak.value = kaynakOlustur(yeniHedef)
  imlec.value = { x: event.clientX + 14, y: event.clientY + 14 }
}

function fareHareket(event: MouseEvent): void {
  if (hedef.value) imlec.value = { x: event.clientX + 14, y: event.clientY + 14 }
}

function odaklan(event: FocusEvent): void {
  if (!aktif.value) return
  const yeniHedef = uygunHedef(event.target as HTMLElement)
  if (!yeniHedef) return
  hedef.value = yeniHedef
  kaynak.value = kaynakOlustur(yeniHedef)
}

function ayril(event: MouseEvent): void {
  if (!(event.relatedTarget as Node | null)?.parentElement) {
    hedef.value = null
    kaynak.value = null
  }
}

onMounted(() => {
  document.addEventListener('mouseover', ustuneGel)
  document.addEventListener('mousemove', fareHareket)
  document.addEventListener('focusin', odaklan)
  document.addEventListener('mouseout', ayril)
})

onBeforeUnmount(() => {
  document.removeEventListener('mouseover', ustuneGel)
  document.removeEventListener('mousemove', fareHareket)
  document.removeEventListener('focusin', odaklan)
  document.removeEventListener('mouseout', ayril)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="aktif && kaynak" class="dev-inspector-popup" :style="{ left: `${imlec.x}px`, top: `${imlec.y}px` }" role="tooltip">
      <strong>Veri kaynağı</strong>
      <span><b>Tablo:</b> {{ kaynak.tablo }}</span>
      <span><b>Sütun:</b> {{ kaynak.sutun }}</span>
      <span><b>Model alanı:</b> {{ kaynak.alan }}</span>
      <span><b>Tip:</b> {{ kaynak.tip }}</span>
      <span><b>API:</b> {{ kaynak.api }}</span>
      <span><b>Ekran:</b> {{ kaynak.ekran }}</span>
    </div>
  </Teleport>
</template>