<script setup lang="ts">
import { RouterLink } from 'vue-router'

interface RaporKarti {
  ad: string
  aciklama: string
  to: string
}

const raporlar: RaporKarti[] = [
  { ad: 'Portföy Özeti', aciklama: 'Tüm projelerde bütçe, gerçekleşme, sapma ve net sonuç karşılaştırması.', to: '/insaat/portfoy-karsilastirma' },
  { ad: 'Nakit Akışı', aciklama: 'Proje bazında planlanan gider, gerçekleşen hakediş ve aylık net akış.', to: '/insaat/nakit-akisi' },
  { ad: 'Kâr / Zarar', aciklama: 'Bütçelenen maliyet, gerçekleşme, sapma ve net sonuç analizi.', to: '/insaat/kar-zarar' },
  { ad: 'S-Eğrisi', aciklama: 'Poz bazında planlanan/gerçekleşen maliyet ve sapma yüzdeleri.', to: '/insaat/poz-planlari' },
  { ad: 'Gantt', aciklama: 'İş kalemleri zaman çizelgesi, ilerleme ve tarihsiz kayıt takibi.', to: '/insaat/gantt' },
  { ad: 'Metraj Kontrolü', aciklama: 'Metraj eşik kontrolleri ve açıklanabilir aksiyon önerileri.', to: '/insaat/poz-planlari' },
  { ad: 'Fiyat Anomalileri', aciklama: 'Snapshot fiyat ile önceki yıl aktif fiyat karşılaştırması.', to: '/insaat/poz-fiyatlari' },
  { ad: 'Mizan', aciklama: 'Muhasebe hesaplarında borç/alacak bakiyeleri ve mizan tablosu.', to: '/muhasebe/mizan' },
  { ad: 'Teknik Şartname', aciklama: 'Poz, malzeme ve TS referanslarından yazdırılabilir şartname taslağı.', to: '/insaat/teknik-sartname' },
]
</script>

<template>
  <div class="mx-auto max-w-7xl">
    <div class="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-sm font-medium text-primary-700">İnşaat / Maliyet</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">Raporlar</h1>
        <p class="mt-1 text-sm text-surface-500">Tüm raporlara tek ekrandan erişin; hesaplama ve detay mevcut ekranlardadır.</p>
      </div>
    </div>
    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <div v-for="x in raporlar" :key="x.ad" class="flex flex-col rounded-xl border border-surface-200 bg-surface-50 p-5 shadow-card">
        <p class="font-heading text-base font-bold text-surface-900">{{ x.ad }}</p>
        <p class="mt-1 flex-1 text-sm text-surface-600">{{ x.aciklama }}</p>
        <div class="mt-4"><RouterLink :to="x.to" class="ikincil-dugme">Raporu aç →</RouterLink></div>
      </div>
    </div>
  </div>
</template>
