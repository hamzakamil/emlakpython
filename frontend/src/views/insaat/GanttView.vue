<template>
  <div class="gantt-view">
    <div class="mb-4">
      <h2 class="text-xl font-bold">İş Zaman Çizelgesi (Gantt)</h2>
      <p class="text-sm text-gray-500">
        Proje ve yıl seçerek işlemelerin planlanan tarihlerine göre zaman çizelgesini görüntüleyin.
      </p>
    </div>

    <div class="bg-white rounded-lg shadow p-4 mb-6">
      <form @submit.prevent="fetchGantt" class="grid gap-4 sm:grid-cols-3 items-end">
        <div>
          <label class="block text-sm font-medium mb-1">Proje *</label>
          <select
            v-model="selectedProjeId"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Proje seçin</option>
            <option
              v-for="proje in projeler"
              :key="proje.id"
              :value="proje.id"
            >
              {{ proje.proje_kodu }} - {{ proje.ad }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Yıl</label>
          <select
            v-model="selectedYil"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Tüm yıllar</option>
            <option
              v-for="yil in yilAraligi"
              :key="yil"
              :value="yil"
            >
              {{ yil }}
            </option>
          </select>
        </div>

        <div>
          <button
            type="submit"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            :disabled="!selectedProjeId || loading"
          >
            {{ loading ? 'Yükleniyor...' : 'Görüntüle' }}
          </button>
        </div>
      </form>
    </div>

    <div v-if="error" class="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
      <p class="text-red-700">{{ error }}</p>
    </div>

    <div v-if="ganttData">
      <div v-if="ganttData.cubuklar.length === 0 && ganttData.tarihsiz_sayi === 0" class="text-center py-8 text-gray-500">
        Gösterilecek veri bulunamadı.
      </div>

      <template v-else>
        <div class="mb-4">
          <h3 class="text-lg font-semibold mb-2">Zaman Çizelgesi Özeti</h3>
          <div class="grid gap-2 sm:grid-cols-4 text-sm">
            <div>
              <span class="block text-gray-500">Proje</span>
              <span class="block font-medium">{{ ganttData.proje_kodu }} - {{ ganttData.proje_ad }}</span>
            </div>
            <div v-if="ganttData.yil !== null">
              <span class="block text-gray-500">Yıl</span>
              <span class="block font-medium">{{ ganttData.yil }}</span>
            </div>
            <div>
              <span class="block text-gray-500">Tarih Aralığı</span>
              <span class="block font-medium">
                {{ ganttData.en_erken ? ganttData.en_erken : 'Tanımsız' }} –
                {{ ganttData.en_gec ? ganttData.en_gec : 'Tanımsız' }}
              </span>
            </div>
            <div>
              <span class="block text-gray-500">Tarih Belirtilmemiş İşler</span>
              <span class="block font-medium">{{ ganttData.tarihsiz_sayi }}</span>
            </div>
          </div>
        </div>

        <div v-if="ganttData.en_erken && ganttData.en_gec" class="mb-6">
          <div class="relative h-20 bg-gray-100 rounded">
            <!-- Timeline axis -->
            <div class="absolute inset-0 flex items-center">
              <div class="w-px bg-gray-300" :style="{ left: '0%' }"></div>
              <div class="w-px bg-gray-300" :style="{ left: '100%' }"></div>
              <!-- Date labels -->
              <div class="absolute left-0 -mt-2 text-xs text-gray-500 whitespace-nowrap">
                {{ formatDate(ganttData.en_erken) }}
              </div>
              <div class="absolute right-0 -mt-2 text-xs text-gray-500 whitespace-nowrap">
                {{ formatDate(ganttData.en_gec) }}
              </div>
            </div>

            <!-- Bars -->
            <div
              class="absolute inset-0"
              :style="{ '--overall-start': ganttData.en_erken, '--overall-end': ganttData.en_gec }"
            >
              <template v-for="(cubuk, index) in ganttData.cubuklar" :key="cubuk.id">
                <div
                  v-if="cubuk.tarih_atandi"
                  class="absolute left-0 right-0"
                  :style="{ top: index * 28 + 'px', height: '20px' }"
                >
                  <div
                    class="relative h-full"
                    :title="cubukTooltip(cubuk)"
                  >
                    <!-- Background track -->
                    <div class="absolute inset-0 bg-gray-200 rounded"></div>
                    <!-- Progress bar -->
                    <div
                      class="absolute inset-0 bg-blue-500 rounded"
                      :style="barStyle(cubuk)"
                    ></div>
                    <!-- Label -->
                    <div class="absolute left-0 -mt-6 w-32 text-xs text-gray-700 font-medium truncate"
                      :title="cubuk.poz_no + ': ' + cubuk.poz_ad"
                    >
                      {{ cubuk.poz_no }}
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>

        <div v-if="ganttData.tarihsiz_sayi > 0" class="mt-6 pt-4 border-t">
          <h3 class="text-lg font-semibold mb-2">Tarih Belirtilmemiş İşler</h3>
          <ul class="divide-y">
            <template v-for="cubuk in ganttData.cubuklar" :key="cubuk.id">
              <li v-if="!cubuk.tarih_atandi" class="px-4 py-3">
                <div class="flex justify-between items-start">
                  <div>
                    <div class="font-medium">{{ cubuk.poz_no }}: {{ cubuk.poz_ad }}</div>
                    <div class="text-sm text-gray-500">
                      Yıl: {{ cubuk.yil }},
                      Planlanan: {{ cubuk.planlanan_miktar }},
                      Gerçekleşen: {{ cubuk.gercek_miktar }},
                      İlerleme: {{ cubuk.ilerleme_yuzde }}
                    </div>
                  </div>
                  <div class="text-xs text-gray-400">Tarih tanımlanmamış</div>
                </div>
              </li>
            </template>
          </ul>
        </div>
      </template>
    </div>

    <div v-else class="text-center py-8 text-gray-500">
      Proje seçip "Görüntüle" butonuna tıklayarak zaman çizelgesini görüntüleyin.
    </div>
  </div>
</template>
<script lang="ts" setup>
import { reactive, toRefs } from 'vue';
import { insaatApi } from '@/services/insaatApi';
import type { GanttRaporu, GanttCubugu } from '@/types/insaat';

const state = reactive({
  loading: false,
  error: null as string | null,
  ganttData: null as GanttRaporu | null,
  selectedProjeId: null as number | null,
  selectedYil: null as number | null,
  projeler: [] as Array<{ id: number; proje_kodu: string; ad: string }>,
  yilAraligi: [] as number[],
});

// Expose state properties for template
const { loading, error, ganttData, selectedProjeId, selectedYil, projeler, yilAraligi } = toRefs(state);

// Toast fallback if vue-toastification not available
const showError = (msg: string) => {
  alert(msg);
};

const fetchProjeler = async () => {
  try {
    const response = await insaatApi.projeler.liste({ sayfa_boyutu: 100 });
    projeler.value = response.results.map((p: any) => ({
      id: p.id,
      proje_kodu: p.proje_kodu,
      ad: p.ad,
    }));
  } catch (e: any) {
    showError('Projeler yüklenemedi: ' + (e.response?.data?.message ?? e.message));
  }
};

const fetchGantt = async () => {
  if (!selectedProjeId.value) {
    showError('Lütfen bir proje seçin.');
    return;
  }

  loading.value = true;
  error.value = null;
  try {
    const data = await insaatApi.gantt(selectedProjeId.value, selectedYil.value ?? undefined);
    ganttData.value = data;
    // Update year range for the selector based on available data
    const years = [...new Set(data.cubuklar.map((c: GanttCubugu) => c.yil))].sort();
    yilAraligi.value = years;
  } catch (e: any) {
    error.value = 'Veri yüklenemedi: ' + (e.response?.data?.detail ?? e.message);
    showError(error.value);
    ganttData.value = null;
  } finally {
    loading.value = false;
  }
};

const formatDate = (dateString: string | null): string => {
  if (!dateString) return '';
  const d = new Date(dateString);
  return d.toLocaleDateString('tr-TR', { year: 'numeric', month: 'short', day: 'numeric' });
};

const barStyle = (cubuk: GanttCubugu) => {
  // İlerleme yüzdesine göre ilerleme çubuğu genişliği (0-100 arası sınırlı).
  const yuzde = Math.min(100, Math.max(0, Number(cubuk.ilerleme_yuzde) || 0))
  return { width: yuzde + '%' }
};

const cubukTooltip = (cubuk: GanttCubugu): string => {
  return `
Poz: ${cubuk.poz_no} - ${cubuk.poz_ad}
Yıl: ${cubuk.yil}
Başlangıç: ${cubuk.baslangic ? formatDate(cubuk.baslangic) : 'Tanımsız'}
Bitiş: ${cubuk.bitis ? formatDate(cubuk.bitis) : 'Tanımsız'}
Planlanan Miktar: ${cubuk.planlanan_miktar}
Gerçekleşen Miktar: ${cubuk.gercek_miktar}
İlerleme: ${cubuk.ilerleme_yuzde}
Plan Değeri: ${cubuk.plan_deger}
Gerçek Değer: ${cubuk.gercek_deger}
  `.trim();
};

// Initialize
fetchProjeler();
</script>

<style scoped>
.gantt-view {
  max-width: 1200px;
  margin: 0 auto;
}

/* Timeline container */
.relative.h-20.bg-gray-100.rounded {
  overflow: visible;
}

/* Bar label */
.absolute.left-0.-mt-6.w-32.text-xs.text-gray-700.font-medium.truncate {
  text-align: right;
  padding-right: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Tooltip styling via title attribute is fine for now */
</style>