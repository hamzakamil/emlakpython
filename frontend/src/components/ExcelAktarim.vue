<script setup lang="ts">
import { ref } from 'vue'
import * as XLSX from 'xlsx'

export interface ExcelSutun {
  key: string
  label: string
  required?: boolean
  templateValue?: unknown
}

const props = withDefaults(defineProps<{
  rows: Record<string, unknown>[]
  columns: ExcelSutun[]
  filename?: string
  title?: string
}>(), { filename: 'kayitlar', title: 'Excel işlemleri' })

const emit = defineEmits<{
  (event: 'imported', rows: Record<string, unknown>[]): void
  (event: 'error', message: string): void
}>()

const input = ref<HTMLInputElement>()
const busy = ref(false)
const message = ref('')

function notifyError(error: unknown): void {
  message.value = error instanceof Error ? error.message : 'Excel dosyası işlenemedi.'
  emit('error', message.value)
}

function indir(data: Record<string, unknown>[], suffix: string): void {
  const sheet = XLSX.utils.json_to_sheet(data, { header: props.columns.map((column) => column.label) })
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, sheet, 'Veriler')
  XLSX.writeFile(workbook, `${props.filename}-${suffix}.xlsx`)
}

function exportRows(): void {
  if (!props.rows.length) {
    notifyError(new Error('Dışa aktarılacak kayıt bulunamadı.'))
    return
  }
  const data = props.rows.map((row) => Object.fromEntries(props.columns.map((column) => [column.label, row[column.key] ?? ''])))
  indir(data, 'export')
}

function downloadTemplate(): void {
  const template = [Object.fromEntries(props.columns.map((column) => [column.label, column.templateValue ?? '']))]
  indir(template, 'sablon')
}

function openPicker(): void {
  message.value = ''
  input.value?.click()
}

function normaliseHeader(value: unknown): string {
  return String(value ?? '').trim().toLocaleLowerCase('tr-TR')
}

async function importWorkbook(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  busy.value = true
  message.value = ''
  try {
    const workbook = XLSX.read(await file.arrayBuffer(), { type: 'array', cellDates: true })
    const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
    if (!firstSheet) throw new Error('Çalışma sayfası bulunamadı.')
    const matrix = XLSX.utils.sheet_to_json<unknown[]>(firstSheet, { header: 1, defval: '' })
    const header = (matrix.shift() || []).map(normaliseHeader)
    const indexes = props.columns.map((column) => header.indexOf(normaliseHeader(column.label)))
    const missing = props.columns.filter((column, index) => column.required && indexes[index] < 0).map((column) => column.label)
    if (missing.length) throw new Error(`Zorunlu sütunlar eksik: ${missing.join(', ')}`)
    const imported = matrix.filter((row) => row.some((value) => value !== '')).map((row) => {
      const result: Record<string, unknown> = {}
      props.columns.forEach((column, index) => {
        const position = indexes[index]
        result[column.key] = position >= 0 ? row[position] ?? '' : column.templateValue ?? ''
      })
      return result
    })
    if (!imported.length) throw new Error('Dosyada içe aktarılacak satır bulunamadı.')
    emit('imported', imported)
    message.value = `${imported.length} satır hazırlandı.`
  } catch (error) {
    notifyError(error)
  } finally {
    busy.value = false
    if (input.value) input.value.value = ''
  }
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2" :aria-label="title">
    <input ref="input" type="file" accept=".xlsx,.xls,.csv" class="hidden" @change="importWorkbook" />
    <button type="button" class="ikincil-dugme" :disabled="busy" @click="exportRows">Excel'e aktar</button>
    <button type="button" class="ikincil-dugme" :disabled="busy" @click="downloadTemplate">Şablon indir</button>
    <button type="button" class="ikincil-dugme" :disabled="busy" @click="openPicker">{{ busy ? 'Okunuyor…' : 'Excel içe aktar' }}</button>
    <span v-if="message" class="text-xs text-surface-500" role="status">{{ message }}</span>
  </div>
</template>
