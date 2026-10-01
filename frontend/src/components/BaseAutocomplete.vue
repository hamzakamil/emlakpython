<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { Combobox } from '@headlessui/vue'
import { XMarkIcon, ChevronUpDownIcon } from '@heroicons/vue/24/outline'
void XMarkIcon; void ChevronUpDownIcon

interface Option<T = unknown> {
  value: T
  label: string
  disabled?: boolean
  [key: string]: unknown
}

interface Props<T = unknown> {
  modelValue: T | null
  options?: Option<T>[]
  fetchFn?: (query: string) => Promise<Option<T>[]>
  placeholder?: string
  label?: string
  clearable?: boolean
  noDataText?: string
  disabled?: boolean
  error?: string
  debounceMs?: number
  minChars?: number
  getOptionLabel?: (option: Option<T>) => string
  getOptionValue?: (option: Option<T>) => T
  class?: string
  required?: boolean
  name?: string
  hint?: string
  multiple?: boolean
}

interface Emits<T = unknown> {
  (e: 'update:modelValue', value: T | null): void
  (e: 'change', value: T | null): void
  (e: 'search', query: string): void
  (e: 'focus'): void
  (e: 'blur'): void
}

const props = withDefaults(defineProps<Props>(), {
  options: () => [],
  placeholder: 'Seçin veya yazın...',
  clearable: true,
  noDataText: 'Eşleşen kayıt bulunamadı',
  disabled: false,
  debounceMs: 300,
  minChars: 0,
  getOptionLabel: (opt: Option<unknown>) => opt.label,
  getOptionValue: (opt: Option<unknown>) => opt.value,
  multiple: false,
})

const emit = defineEmits<Emits>()

const searchQuery = ref('')
const isOpen = ref(false)
const highlightedIndex = ref(-1)
const debouncedFetch = ref<ReturnType<typeof setTimeout> | null>(null)
const fetchedOptions = ref<Option[]>([])
const isLoading = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

const allOptions = computed(() => {
  const staticOpts = props.options || []
  const dynamicOpts = fetchedOptions.value
  const seen = new Set<unknown>()
  const merged: Option[] = []
  ;[...staticOpts, ...dynamicOpts].forEach(opt => {
    const val = props.getOptionValue(opt)
    if (!seen.has(val)) {
      seen.add(val)
      merged.push(opt)
    }
  })
  return merged
})

const filteredOptions = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return allOptions.value

  return allOptions.value.filter(opt => {
    const label = props.getOptionLabel(opt).toLowerCase()
    return label.includes(query) ||
           label.localeCompare(query, 'tr', { sensitivity: 'base', usage: 'search' }) === 0
  })
})

const selectedLabel = computed(() => {
  if (props.modelValue === null || props.modelValue === undefined) return ''
  const opt = allOptions.value.find(o => props.getOptionValue(o) === props.modelValue)
  return opt ? props.getOptionLabel(opt) : ''
})
﻿
watch(() => searchQuery.value, async (query) => {
  emit('search', query)

  if (props.fetchFn) {
    if (debouncedFetch.value) clearTimeout(debouncedFetch.value)
    debouncedFetch.value = setTimeout(async () => {
      if (query.length < (props.minChars || 0)) {
        fetchedOptions.value = []
        return
      }
      isLoading.value = true
      try {
        if (!props.fetchFn) return
        const results = await props.fetchFn(query)
        fetchedOptions.value = results
      } catch {
        fetchedOptions.value = []
      } finally {
        isLoading.value = false
      }
    }, props.debounceMs)
  }
})

watch(() => props.disabled, (val) => {
  if (val) isOpen.value = false
})

function handleKeydown(e: KeyboardEvent) {
  const opts = filteredOptions.value
  if (!opts.length) return
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      highlightedIndex.value = Math.min(highlightedIndex.value + 1, opts.length - 1)
      break
    case 'ArrowUp':
      e.preventDefault()
      highlightedIndex.value = Math.max(highlightedIndex.value - 1, -1)
      break
    case 'Enter':
      if (highlightedIndex.value >= 0) {
        e.preventDefault()
        selectOption(opts[highlightedIndex.value])
      }
      break
    case 'Escape':
      isOpen.value = false
      highlightedIndex.value = -1
      searchQuery.value = ''
      break
    case 'Tab':
      isOpen.value = false
      highlightedIndex.value = -1
      break
  }
}

function selectOption(option: Option) {
  const value = props.getOptionValue(option)
  emit('update:modelValue', value)
  emit('change', value)
  searchQuery.value = props.getOptionLabel(option)
  isOpen.value = false
  highlightedIndex.value = -1
  nextTick(() => { (document.activeElement as HTMLElement)?.blur() })
}

// @ts-ignore - used in template
function clearSelection() {
  emit('update:modelValue', null)
  emit('change', null)
  searchQuery.value = ''
  isOpen.value = false
  highlightedIndex.value = -1
}

function handleFocus() { isOpen.value = true; highlightedIndex.value = -1; emit('focus') }

function handleBlur(e: FocusEvent) {
  if (e.relatedTarget === null || (e.relatedTarget as HTMLElement)?.closest('.autocomplete-container') === null) {
    setTimeout(() => {
      isOpen.value = false
      highlightedIndex.value = -1
      if (!props.multiple && props.modelValue !== null) searchQuery.value = selectedLabel.value
      else if (!props.multiple) searchQuery.value = ''
    }, 100)
  }
  emit('blur')
}

function handleInputClick() { if (!props.disabled) isOpen.value = true }

function handleOptionClick(option: Option) { selectOption(option) }

function handleOptionMouseEnter(index: number) { highlightedIndex.value = index }

defineExpose({
  focus: () => { inputRef.value?.focus() },
  open: () => { isOpen.value = true },
  close: () => { isOpen.value = false },
})
</script>
<template>
  <div class="autocomplete-container w-full" :class="{ 'autocomplete-disabled': props.disabled }">
    <label v-if="props.label" class="block text-sm font-medium text-surface-700 mb-1.5">
      {{ props.label }}
      <span class="text-red-500 ml-1" v-if="props.required">*</span>
    </label>
    <Combobox v-slot="{ open }" class="w-full" :disabled="props.disabled">
      <div class="relative" @click="handleInputClick">
        <div
          class="autocomplete-input-wrapper relative"
          :class="[
            'flex items-center border rounded-lg bg-white transition-colors duration-150',
            'hover:border-primary-400 focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-500/20',
            props.error ? 'border-red-400 bg-red-50' : 'border-surface-300',
            props.disabled ? 'bg-surface-100 cursor-not-allowed opacity-70' : ''
          ]"
          @keydown="handleKeydown"
          @focusin="handleFocus"
          @focusout="handleBlur"
          role="combobox"
          :aria-expanded="open"
          aria-haspopup="listbox"
          :aria-label="props.label"
          :aria-invalid="!!props.error"
        >
          <input
            ref="inputRef"
            type="text"
            class="autocomplete-input flex-1 appearance-none bg-transparent border-none outline-none text-sm px-3 py-2.5 text-surface-900 placeholder:text-surface-400"
            :placeholder="props.placeholder"
            :value="searchQuery"
<transition
          enter="transition ease-out duration-100"
          enter-from="opacity-0 scale-y-95"
          enter-to="opacity-100 scale-y-100"
          leave="transition ease-in duration-75"
          leave-from="opacity-100 scale-y-100"
          leave-to="opacity-0 scale-y-95"
        >
          <div
            v-if="open"
            class="absolute z-50 w-full mt-1 max-h-60 overflow-auto rounded-lg bg-white border border-surface-200 shadow-lg ring-1 ring-black/5 focus:outline-none"
            role="listbox"
            :id="props.name ? props.name + '-listbox' : undefined"
            aria-multiselectable="false"
          >
            <div v-if="filteredOptions.length > 0" class="py-1">
              <button
                v-for="(option, index) in filteredOptions"
                :key="String(props.getOptionValue(option))"
                type="button"
                role="option"
                :aria-selected="highlightedIndex === index"
                :aria-disabled="option.disabled"
                class="autocomplete-option w-full px-3 py-2 text-left text-sm transition-colors"
                :class="[
                  'hover:bg-primary-50 hover:text-primary-700',
                  highlightedIndex === index ? 'bg-primary-50 text-primary-700' : 'text-surface-700',
                  option.disabled ? 'opacity-50 cursor-not-allowed' : ''
                ]"
                @click.stop="handleOptionClick(option)"
                @mouseenter="handleOptionMouseEnter(index)"
                @mousedown.prevent
              >
                {{ props.getOptionLabel(option) }}
              </button>
            </div>
            <div v-else-if="!isLoading" class="px-3 py-3 text-center text-sm text-surface-500" role="status" aria-live="polite">
              {{ props.noDataText }}
            </div>
            <div v-else class="px-3 py-3 text-center text-sm text-surface-500">
              <div class="flex items-center justify-center gap-2">
                <svg class="animate-spin h-4 w-4 text-primary-600" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Yükleniyor...
              </div>
            </div>
          </div>
        </transition>
      </div>
    </Combobox>
    <p v-if="props.error" class="mt-1.5 text-sm text-red-600" role="alert">
      {{ props.error }}
    </p>
    <p v-else-if="props.hint" class="mt-1.5 text-sm text-surface-500">
      {{ props.hint }}
    </p>
  </div>
</template>

<style scoped>
.autocomplete-container :deep(.autocomplete-input-wrapper) { min-height: 42px; }
.autocomplete-container :deep(.autocomplete-input) { width: 100%; }
.autocomplete-container :deep(.autocomplete-option) { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.autocomplete-disabled :deep(.autocomplete-input-wrapper) { background-color: #f3f4f6; cursor: not-allowed; }
.autocomplete-container :deep(.autocomplete-input-wrapper:focus-within) { box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
.dark .autocomplete-container :deep(.autocomplete-input-wrapper) { background-color: #1f2937; border-color: #4b5563; color: #f9fafb; }
.dark .autocomplete-container :deep(.autocomplete-input-wrapper:hover) { border-color: #60a5fa; }
.dark .autocomplete-container :deep(.autocomplete-option:hover),
.dark .autocomplete-container :deep(.autocomplete-option[aria-selected="true"]) { background-color: #1e3a5f; color: #93c5fd; }
.dark .autocomplete-container :deep(.autocomplete-option) { color: #e5e7eb; }
.dark .autocomplete-container :deep([role="listbox"]) { background-color: #1f2937; border-color: #374151; }
</style>
            @input="searchQuery = ($event.target as HTMLInputElement).value"
            @click.stop
            :disabled="props.disabled"
            aria-autocomplete="list"
            :aria-controls="props.name ? props.name + '-listbox' : undefined"
            :name="props.name"
            autocomplete="off"
          />
          <div v-if="isLoading" class="flex items-center px-2 text-primary-600">
            <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
          <button
            v-if="props.clearable && props.modelValue !== null && props.modelValue !== undefined && !props.disabled"
            type="button"
            class="flex items-center justify-center p-1.5 text-surface-400 hover:text-surface-600 hover:bg-surface-100 rounded-r-lg transition-colors"
            @click.stop="clearSelection"
            @mousedown.prevent
            aria-label="Seçimi temizle"
          >
            <XMarkIcon class="h-4 w-4" />
          </button>
          <ChevronUpDownIcon
            v-if="!props.clearable || props.modelValue === null || props.modelValue === undefined || props.disabled"
            class="flex items-center justify-center p-1.5 text-surface-400 pointer-events-none"
            :class="{ 'rotate-180': open }"
          />
        </div>