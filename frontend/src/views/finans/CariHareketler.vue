<script setup lang="ts">
/**
 * Cari Hareketler.vue - Vue 3 Component for Cari Hareket Management
 * 
 * This component provides a complete CRUD interface for managing cari hareketleri
 * (financial transactions) with the following features:
 * 
 * - List view with pagination, search, and filtering
 * - Create new cari hareketleri via modal form
 * - Edit existing cari hareketleri via modal form
 * - Cancel/delete cari hareketleri (with confirmation)
 * - View details of specific cari's hareketleri when accessed via route parameter
 * 
 * Technologies Used:
 * - Vue 3 with Composition API (<script setup>)
 * - TypeScript
 * - Tailwind CSS for styling
 * - Pinia for state management (auth store)
 * - Custom composables (useKayitListesi, useKayitFormu)
 * - Reusable components (VeriTablosu, KayitModal, Sayfalama, VeriKaynakRozeti)
 * 
 * API Endpoints Used:
 * - GET /api/v1/cari/hareketler/ - List all cari hareketleri (with pagination/filtering)
 * - GET /api/v1/cari/cariler/{id}/hareketler/ - List hareketleri for a specific cari
 * - POST /api/v1/cari/hareketler/ - Create new cari hareket
 * - PATCH /api/v1/cari/hareketler/{id}/ - Update existing cari hareket
 * - DELETE /api/v1/cari/hareketler/{id}/iptal/ - Cancel cari hareket (creates reverse record)
 * - GET /api/v1/cari/cariler/{id}/ - Get cari details (for display in header)
 * - GET /api/v1/cari/cariler/ - List all cari (for dropdown in form)
 * 
 * Features:
 * - Responsive design
 * - Loading states
 * - Error handling
 * - Form validation
 * - Permission-based controls (only users with write access can create/edit/delete)
 * - Turkish locale and formatting
 * - Decimal precision for financial amounts
 * - Confirmation dialogs for destructive operations
 */
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import KayitModal from '@/components/KayitModal.vue'
import Sayfalama from '@/components/Sayfalama.vue'
import VeriTablosu from '@/components/VeriTablosu.vue'
import VeriKaynakRozeti from '@/components/VeriKaynakRozeti.vue'
import { cariApi } from '@/services/cariApi'
import { useKayitFormu } from '@/hooks/useKayitFormu'
import { useKayitListesi } from '@/hooks/useKayitListesi'
import { useAuthStore } from '@/stores/auth'
import type { CariHareket, Cari } from '@/types/cari'
import { yazabilirMi } from '@/utils/yetki'
import { post, hataMesaji } from '@/services/apiClient'

const auth = useAuthStore()
const route = useRoute()
const yazabilir = computed(() => yazabilirMi(auth.kullanici?.role))

const cariId = computed(() => route.params.cariId ? Number(route.params.cariId) : null)
const seciliCari = ref<Cari | null>(null)

const L = useKayitListesi<CariHareket>(
  cariId.value ? `/cari/cariler/${cariId.value}/hareketler/` : '/cari/cari-hareketler/',
)

// Cari listesi dropdown için
const cariListesiYukleniyor = ref(false)
const cariListesi = ref<Cari[]>([])

async function cariListesiniYukle(): Promise<void> {
  cariListesiYukleniyor.value = true
  try {
    const veri = await cariApi.cariler.liste({ page_size: 1000, is_active: true })
    cariListesi.value = veri.results
  } catch {
    cariListesi.value = []
  } finally {
    cariListesiYukleniyor.value = false
  }
}

type Form = {
  cari: number | ''
  yon: 'borc' | 'alacak'
  tutar: string
  aciklama: string
  islem_tarihi: string
}

const Fm = useKayitFormu<CariHareket, Form>(
  {
    olustur: (veri) => cariApi.cariler.hareketEkle(veri as Record<string, unknown>),
    guncelle: (id, veri) => cariApi.cariler.hareketGuncelle(id, veri as Record<string, unknown>),
  },
  () => ({
    cari: cariId.value || '',
    yon: 'borc',
    tutar: '',
    aciklama: '',
    islem_tarihi: new Date().toISOString().split('T')[0],
  }),
  (h) => ({
    cari: h.cari,
    yon: h.yon,
    tutar: h.tutar,
    aciklama: h.aciklama || '',
    islem_tarihi: h.islem_tarihi,
  }),
  (f) => ({
    ...f,
    cari: Number(f.cari),
    tutar: f.tutar.trim(),
    aciklama: f.aciklama.trim(),
    islem_tarihi: f.islem_tarihi,
  }),
  (f) => {
    if (!f.cari) return 'Cari seçimi zorunludur.'
    if (!f.tutar || Number(f.tutar) <= 0) return 'Tutar 0\'dan büyük olmalıdır.'
    if (!f.aciklama.trim()) return 'Açıklama zorunludur.'
    if (!f.islem_tarihi) return 'İşlem tarihi zorunludur.'
    return ''
  },
)

const originalYeniAc = Fm.yeniAc
Fm.yeniAc = () => {
  originalYeniAc()
  if (cariListesi.value.length === 0) void cariListesiniYukle()
}

const originalDuzenleAc = Fm.duzenleAc
Fm.duzenleAc = (kayit: CariHareket) => {
  originalDuzenleAc(kayit)
  if (cariListesi.value.length === 0) void cariListesiniYukle()
}

async function yukle(): Promise<void> {
  if (cariId.value) {
    try {
      const cari = await cariApi.cariler.getir(cariId.value)
      seciliCari.value = cari
    } catch {
      // Cari bulunamazsa sessizce devam et
    }
  }
  await L.yukle()
}

async function hareketIptal(id: number): Promise<void> {
  if (!confirm('Bu hareketi iptal etmek istediğinizden emin misiniz? (Ters kayıt oluşturulacak)')) return
  try {
    await post<CariHareket>(`/cari/cari-hareketler/${id}/iptal/`)
    await L.yukle()
  } catch (e) {
    alert(hataMesaji(e))
  }
}

async function hareketMuhasebelestir(id: number): Promise<void> {
  try {
    await post<CariHareket>(`/cari/cari-hareketler/${id}/muhasebelestir/`)
    await L.yukle()
  } catch (e) {
    alert(hataMesaji(e))
  }
}

onMounted(() => {
  void yukle()
})
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-sm font-medium text-primary-700">Finans</p>
        <h1 class="font-heading text-2xl font-bold tracking-tight text-surface-900">
          {{ cariId ? `Cari Hareketleri: ${seciliCari?.ad || 'Yükleniyor...'}` : 'Tüm Cari Hareketleri' }}
        </h1>
      </div>
      <button v-if="yazabilir" type="button" class="birincil-dugme" @click="Fm.yeniAc()">
        + Yeni Hareket
      </button>
    </div>

    <div v-if="cariId && seciliCari" class="mb-4 flex flex-wrap items-center gap-3">
      <div class="flex-1 min-w-0">
        <p class="text-sm text-surface-500">Seçili Cari</p>
        <p class="font-medium text-surface-900 truncate">{{ seciliCari.ad }}</p>
      </div>
      <router-link :to="`/cari/cariler/${cariId}/duzenle`" class="ikincil-dugme whitespace-nowrap">
        Cariyi Düzenle
      </router-link>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="flex flex-1 items-center gap-2" @submit.prevent="L.aramaYap">
        <input
          v-model="L.arama.value"
          type="search"
          placeholder="Açıklama veya cari ad ile ara..."
          class="alan w-full max-w-sm"
        />
        <button type="submit" class="ikincil-dugme">Ara</button>
      </form>
      <select v-model="L.filtreler.value.yon" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tüm yönler</option>
        <option value="borc">Borç</option>
        <option value="alacak">Alacak</option>
      </select>
      <select v-model="L.filtreler.value.is_cancelled" class="alan" @change="L.sayfa.value = 1; L.yukle()">
        <option :value="undefined">Tümü</option>
        <option value="false">Aktif</option>
        <option value="true">İptal Edilmiş</option>
      </select>
    </div>

    <p v-if="L.hata.value" class="hata-kutusu mb-4" role="alert">{{ L.hata.value }}</p>

    <VeriTablosu
      :basliklar="[
        'Tarih',
        'Cari',
        'Yön',
        'Tutar',
        'Açıklama',
        'Durum',
        'Muhasebe',
        yazabilir ? 'İşlem' : ''
      ]"
      :bos-mu="!L.yukleniyor.value && L.kayitlar.value.length === 0"
    >
      <tr
        v-for="h in L.kayitlar.value"
        :key="h.id"
        class="transition-colors hover:bg-surface-100/60"
        :class="{ 'opacity-50': h.is_cancelled }"
      >
        <td class="px-4 py-3 whitespace-nowrap text-surface-700">
          <VeriKaynakRozeti
            :aktif="auth.gelistiriciModu"
            tablo="cari_carihareket"
            sutun="islem_tarihi"
            alan="CariHareket.islem_tarihi"
            tip="date"
            api="GET /api/v1/cari/hareketler/"
            :iliski="`id=${h.id}`"
          >
            {{ new Date(h.islem_tarihi).toLocaleDateString('tr-TR') }}
          </VeriKaynakRozeti>
        </td>
        <td class="px-4 py-3 max-w-xs truncate font-medium">
          <VeriKaynakRozeti
            :aktif="auth.gelistiriciModu"
            tablo="cari_carihareket"
            sutun="cari"
            alan="CariHareket.cari"
            tip="integer"
            :iliski="`cari_id=${h.cari}`"
          >
            {{ h.cari_ad || `Cari #${h.cari}` }}
          </VeriKaynakRozeti>
        </td>
        <td class="px-4 py-3 whitespace-nowrap">
          <span :class="h.yon === 'borc' ? 'durum-borc' : 'durum-alacak'">
            {{ h.yon === 'borc' ? 'Borç' : 'Alacak' }}
          </span>
        </td>
        <td class="px-4 py-3 font-mono tabular-nums text-right">
          <VeriKaynakRozeti
            :aktif="auth.gelistiriciModu"
            tablo="cari_carihareket"
            sutun="tutar"
            alan="CariHareket.tutar"
            tip="numeric(14,2)"
          >
            {{ Number(h.tutar).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }} ₺
          </VeriKaynakRozeti>
        </td>
        <td class="px-4 py-3 max-w-md truncate text-surface-600">
          {{ h.aciklama || '—' }}
        </td>
        <td class="px-4 py-3">
          <span v-if="h.is_cancelled" class="durum-iptal">İptal Edilmiş</span>
          <span v-else class="durum-aktif">Aktif</span>
          <span v-if="h.iptal_nedeni" class="ml-2 text-xs text-surface-400">({{ h.iptal_nedeni }})</span>
        </td>
        <td class="px-4 py-3 whitespace-nowrap">
          <span v-if="h.muhasebelesti" class="durum-aktif">Muhasebeleşti</span>
          <button
            v-else-if="yazabilir && !h.is_cancelled"
            type="button"
            class="text-sm font-medium text-primary-700 hover:underline"
            @click="hareketMuhasebelestir(h.id)"
          >
            Muhasebeleştir
          </button>
          <span v-else class="text-xs text-surface-400">Bekliyor</span>
        </td>
        <td v-if="yazabilir" class="whitespace-nowrap px-4 py-3">
          <div class="flex items-center gap-2">
            <button
              type="button"
              class="text-sm font-medium text-primary-700 hover:underline"
              @click="Fm.duzenleAc(h)"
              :disabled="h.is_cancelled"
            >
              Düzenle
            </button>
            <button
              type="button"
              class="text-sm font-medium text-red-700 hover:underline"
              @click="hareketIptal(h.id)"
              :disabled="h.is_cancelled"
            >
              İptal Et
            </button>
          </div>
        </td>
      </tr>
    </VeriTablosu>

    <Sayfalama
      :sayfa="L.sayfa.value"
      :toplam="L.toplam.value"
      :yukleniyor="L.yukleniyor.value"
      @sayfa-degistir="(s) => { L.sayfa.value = s; L.yukle() }"
    />
<KayitModal
      v-if="Fm.modalAcik.value"
      :baslik="Fm.duzenlenen.value ? 'Hareketi Düzenle' : 'Yeni Cari Hareketi'"
      @kapat="Fm.modalAcik.value = false"
    >
      <form class="flex flex-col gap-4" @submit.prevent="Fm.kaydet(L.yukle)">
        <label class="etiket">
          Cari
          <select v-model="Fm.form.value.cari" class="alan" required>
            <option value="">Cari seçin...</option>
            <option
              v-for="c in cariListesi"
              :key="c.id"
              :value="c.id"
            >
              {{ c.ad }}
            </option>
          </select>
        </label>

        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">
            Yön
            <select v-model="Fm.form.value.yon" class="alan" required>
              <option value="borc">Borç (Alacaklıyız)</option>
              <option value="alacak">Alacak (Borçluyuz)</option>
            </select>
          </label>
          <label class="etiket">
            Tutar (₺)
            <input
              v-model="Fm.form.value.tutar"
              type="number"
              step="0.01"
              min="0.01"
              inputmode="decimal"
              class="alan text-right font-mono tabular-nums"
              required
            />
          </label>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <label class="etiket">
            İşlem Tarihi
            <input
              v-model="Fm.form.value.islem_tarihi"
              type="date"
              class="alan"
              required
            />
          </label>
        </div>

        <label class="etiket">
          Açıklama
          <textarea
            v-model="Fm.form.value.aciklama"
            rows="3"
            class="alan"
            required
            placeholder="Hareket açıklaması (örn: Ocak 2024 kira tahsilatı)"
          />
        </label>

        <p v-if="Fm.formHata.value" class="hata-kutusu" role="alert">{{ Fm.formHata.value }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="ikincil-dugme" @click="Fm.modalAcik.value = false">Vazgeç</button>
          <button type="submit" :disabled="Fm.kaydediliyor.value" class="birincil-dugme">
            {{ Fm.kaydediliyor.value ? 'Kaydediliyor...' : 'Kaydet' }}
          </button>
        </div>
      </form>
    </KayitModal>
  </div>
</template>

<style scoped>
.durum-borc {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800;
}
.durum-alacak {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800;
}
.durum-iptal {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800;
}
.durum-aktif {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800;
}
.durum-pasif {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-100 text-surface-600;
}
</style>