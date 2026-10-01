<script setup lang="ts">
import { computed, ref } from 'vue'
import ilIlceVerisi from '@/data/turkiyeIlIlce.json'

const props = defineProps<{
  il: string
  ilce: string
}>()

const emit = defineEmits<{
  'update:il': [value: string]
  'update:ilce': [value: string]
}>()

function baslikBiçimi(value: string): string {
  return value
    .toLocaleLowerCase('tr-TR')
    .split(' ')
    .map((parça) => parça ? parça[0].toLocaleUpperCase('tr-TR') + parça.slice(1) : parça)
    .join(' ')
}

const iller = Object.keys(ilIlceVerisi).map(baslikBiçimi)
const ilHaritasi = new Map(Object.keys(ilIlceVerisi).map((il) => [normalize(il), il]))

const ilceSecenekleri = computed(() => {
  const kaynakIl = ilHaritasi.get(normalize(props.il))
  return kaynakIl ? ilIlceVerisi[kaynakIl as keyof typeof ilIlceVerisi] : []
})

const ilAramaAcik = ref(false)
const ilceAramaAcik = ref(false)

const filtreliIller = computed(() => {
  const arama = normalize(props.il)
  if (!arama) return iller
  return iller.filter((sehir) => normalize(sehir).includes(arama)).slice(0, 8)
})

const filtreliIlceler = computed(() => {
  const arama = normalize(props.ilce)
  return ilceSecenekleri.value
    .filter((ilce) => !arama || normalize(ilce).includes(arama))
    .slice(0, 8)
})

function normalize(value: string): string {
  return value.toLocaleUpperCase('tr-TR').trim()
}

function ilDegisti(value: string): void {
  emit('update:il', value)
  if (!ilceSecenekleri.value.some((ilce) => normalize(ilce) === normalize(props.ilce))) emit('update:ilce', '')
}

function ilSec(value: string): void {
  emit('update:il', value)
  emit('update:ilce', '')
  ilAramaAcik.value = false
}

function ilceSec(value: string): void {
  emit('update:ilce', baslikBiçimi(value))
  ilceAramaAcik.value = false
}

function kapatIlAramayi(): void {
  window.setTimeout(() => { ilAramaAcik.value = false }, 120)
}

function kapatIlceAramayi(): void {
  window.setTimeout(() => { ilceAramaAcik.value = false }, 120)
}
</script>

<template>
  <div class="il-ilce-secimi">
    <label class="etiket">
      İl
      <input
        :value="il"
        class="alan"
        maxlength="100"
        autocomplete="address-level1"
        placeholder="İl yazın veya seçin"
        @focus="ilAramaAcik = true"
        @blur="kapatIlAramayi"
        @input="ilDegisti(($event.target as HTMLInputElement).value); ilAramaAcik = true"
      />
      <div v-if="ilAramaAcik && filtreliIller.length" class="autocomplete-list" role="listbox" aria-label="İl önerileri">
        <button v-for="sehir in filtreliIller" :key="sehir" type="button" class="autocomplete-option" @mousedown.prevent="ilSec(sehir)">{{ sehir }}</button>
      </div>
    </label>
    <label class="etiket">
      İlçe
      <input
        :value="ilce"
        class="alan"
        maxlength="100"
        autocomplete="address-level2"
        :disabled="!il"
        placeholder="İlçe yazın veya seçin"
        @focus="ilceAramaAcik = true"
        @blur="kapatIlceAramayi"
        @input="emit('update:ilce', ($event.target as HTMLInputElement).value); ilceAramaAcik = true"
      />
      <div v-if="ilceAramaAcik && filtreliIlceler.length" class="autocomplete-list" role="listbox" aria-label="İlçe önerileri">
        <button v-for="ilceAdi in filtreliIlceler" :key="ilceAdi" type="button" class="autocomplete-option" @mousedown.prevent="ilceSec(ilceAdi)">{{ baslikBiçimi(ilceAdi) }}</button>
      </div>
    </label>
  </div>
</template>

<style scoped>
.il-ilce-secimi {
  display: contents;
}

.etiket {
  position: relative;
}

.autocomplete-list {
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

.autocomplete-option {
  display: block;
  width: 100%;
  padding: .48rem .65rem;
  color: #334155;
  font-size: .75rem;
  text-align: left;
}

.autocomplete-option:hover,
.autocomplete-option:focus-visible {
  background: #e8f4f4;
  color: #0f6973;
  outline: none;
}
</style>
