<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Database, Download, FileArchive, RefreshCw, Save, ShieldCheck, Upload } from 'lucide-vue-next'
import KayitModal from '@/components/KayitModal.vue'
import { hataMesaji } from '@/services/apiClient'
import { databaseApi } from '@/services/databaseApi'
import { useAuthStore } from '@/stores/auth'
import type { DatabaseBackup, DatabaseColumn, DatabaseOverview, DatabaseRows, DatabaseTable } from '@/types/database'

const overview = ref<DatabaseOverview | null>(null)
const auth = useAuthStore()
const rows = ref<DatabaseRows | null>(null)
const backups = ref<DatabaseBackup[]>([])
const selectedTable = ref('')
const search = ref('')
const page = ref(1)
const loading = ref(false)
const error = ref('')
const notice = ref('')
const backupRunning = ref(false)
const restoreRunning = ref(false)
const restoreFile = ref<File | null>(null)
const restoreConfirmation = ref('')
const editRow = ref<Record<string, string> | null>(null)
const editTable = ref<DatabaseTable | null>(null)
const editSaving = ref(false)
const selectedTables = ref<string[]>([])
const selectedFields = ref<Record<string, string[]>>({})
const excelFile = ref<File | null>(null)
const excelRunning = ref(false)
const excelDryRun = ref(true)
const targetTenant = ref<number | null>(auth.seciliTenantId)

const groups = computed(() => {
  const grouped = new Map<string, DatabaseTable[]>()
  for (const table of overview.value?.tables || []) {
    const [prefix] = table.name.split('_')
    const label = prefix === 'construction' ? 'İnşaat' : prefix === 'real' ? 'Gayrimenkul' : prefix === 'accounting' ? 'Muhasebe' : prefix === 'finance' ? 'Finans' : prefix === 'cari' ? 'Cari' : prefix === 'users' ? 'Kullanıcılar' : prefix === 'tenants' ? 'Tenant' : 'Sistem'
    if (!grouped.has(label)) grouped.set(label, [])
    grouped.get(label)?.push(table)
  }
  return [...grouped.entries()].sort(([a], [b]) => a.localeCompare(b, 'tr'))
})

const visibleRows = computed(() => rows.value?.rows || [])
const totalPages = computed(() => Math.max(1, Math.ceil((rows.value?.count || 0) / (rows.value?.page_size || 25))))

function tableLabel(table: DatabaseTable): string {
  return table.name.split('_').slice(1).join(' ').replace(/_/g, ' ') || table.label
}
function formatBytes(bytes: number): string { return `${(bytes / 1024 / 1024).toFixed(2)} MB` }
function display(value: unknown): string { return value === null || value === undefined ? 'NULL' : String(value) }
function editableColumns(table: DatabaseTable): DatabaseColumn[] { return table.columns.filter((column) => column.editable && !column.sensitive) }
function toggleTable(tableName: string): void {
  selectedTables.value = selectedTables.value.includes(tableName)
    ? selectedTables.value.filter((name) => name !== tableName)
    : [...selectedTables.value, tableName]
  if (selectedTables.value.includes(tableName) && !selectedFields.value[tableName]) {
    const table = overview.value?.tables.find((item) => item.name === tableName)
    selectedFields.value[tableName] = table?.columns.filter((column) => column.editable && !column.sensitive).map((column) => column.name) || []
  }
}
function selectAllTables(): void {
  selectedTables.value = overview.value?.tables.map((table) => table.name) || []
  for (const table of overview.value?.tables || []) {
    selectedFields.value[table.name] = table.columns.filter((column) => column.editable && !column.sensitive).map((column) => column.name)
  }
}
function toggleField(tableName: string, fieldName: string): void {
  const fields = selectedFields.value[tableName] || []
  selectedFields.value[tableName] = fields.includes(fieldName) ? fields.filter((field) => field !== fieldName) : [...fields, fieldName]
}
function chooseExcel(event: Event): void { excelFile.value = (event.target as HTMLInputElement).files?.[0] || null }

async function loadOverview(): Promise<void> {
  error.value = ''
  try {
    overview.value = await databaseApi.overview()
  } catch (e) {
    error.value = `Veritabanı şeması yüklenemedi: ${hataMesaji(e)}`
    return
  }
  try {
    await auth.tenantlariYukle()
  } catch (e) {
    error.value = `Tenant listesi yüklenemedi: ${hataMesaji(e)}`
  }
  await loadBackups()
  if (!selectedTable.value && overview.value.tables[0]) await selectTable(overview.value.tables[0])
}
async function downloadExcelTemplate(): Promise<void> {
  if (!selectedTables.value.length) { error.value = 'Şablon için en az bir tablo seçin.'; return }
  try {
    const response = await databaseApi.excelTemplate(selectedTables.value, selectedFields.value)
    const url = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = 'emlak_erp_veri_sablonu.xlsx'
    link.click()
    URL.revokeObjectURL(url)
    notice.value = `${selectedTables.value.length} tablo için Excel şablonu indirildi.`
  } catch (e) { error.value = hataMesaji(e) }
}
async function exportExcel(): Promise<void> {
  if (!selectedTables.value.length) { error.value = 'Dışa aktarmak için en az bir tablo seçin.'; return }
  try {
    const response = await databaseApi.excelExport(selectedTables.value, selectedFields.value)
    const url = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = 'emlak_erp_veri_export.xlsx'
    link.click()
    URL.revokeObjectURL(url)
    notice.value = `${selectedTables.value.length} tablonun mevcut verileri Excel'e aktarıldı.`
  } catch (e) { error.value = hataMesaji(e) }
}
async function importExcel(): Promise<void> {
  if (!excelFile.value) { error.value = 'Önce bir Excel dosyası seçin.'; return }
  excelRunning.value = true; error.value = ''; notice.value = ''
  try {
    const result = await databaseApi.excelImport(excelFile.value, targetTenant.value, excelDryRun.value)
    const report = (result.data.data || result.data) as { dry_run?: boolean; total_rows?: number; inserted?: number }
    notice.value = report.dry_run ? `${report.total_rows || 0} satır doğrulandı. Henüz veritabanına yazılmadı.` : `${report.inserted || 0} satır veritabanına yüklendi.`
    if (!report.dry_run) { excelFile.value = null; await loadOverview() }
  } catch (e) { error.value = hataMesaji(e) }
  finally { excelRunning.value = false }
}
async function loadBackups(): Promise<void> {
  try { backups.value = await databaseApi.backups() }
  catch (e) { error.value = `Yedek listesi yüklenemedi: ${hataMesaji(e)}` }
}
async function selectTable(table: DatabaseTable): Promise<void> {
  selectedTable.value = table.name; page.value = 1; await loadRows()
}
async function loadRows(): Promise<void> {
  if (!selectedTable.value) return
  loading.value = true; error.value = ''
  try { rows.value = await databaseApi.rows(selectedTable.value, { page: page.value, page_size: 25, search: search.value }) }
  catch (e) { error.value = hataMesaji(e) }
  finally { loading.value = false }
}
function searchRows(): void { page.value = 1; void loadRows() }
function openEdit(row: Record<string, unknown>): void { editRow.value = Object.fromEntries(Object.entries(row).map(([key, value]) => [key, value === null || value === undefined ? '' : String(value)])); editTable.value = rows.value?.table || null }
async function saveEdit(): Promise<void> {
  if (!editRow.value || !editTable.value?.primary_key) return
  const id = Number(editRow.value[editTable.value.primary_key])
  const values: Record<string, unknown> = {}
  for (const column of editableColumns(editTable.value)) values[column.name] = editRow.value[column.name]
  editSaving.value = true
  try { await databaseApi.updateRow(editTable.value.name, id, values); editRow.value = null; notice.value = 'Kayıt güncellendi.'; await loadRows() }
  catch (e) { error.value = hataMesaji(e) }
  finally { editSaving.value = false }
}
async function createBackup(): Promise<void> {
  backupRunning.value = true; error.value = ''; notice.value = ''
  try { await databaseApi.createBackup(); notice.value = 'Yedek başarıyla oluşturuldu.'; await loadBackups(); if (overview.value) overview.value.backup_count += 1 }
  catch (e) { error.value = hataMesaji(e) }
  finally { backupRunning.value = false }
}
async function downloadBackup(backup: DatabaseBackup): Promise<void> {
  try { const response = await import('@/services/apiClient').then(({ http }) => http.get(databaseApi.downloadUrl(backup.name), { responseType: 'blob' })); const url = URL.createObjectURL(response.data); const link = document.createElement('a'); link.href = url; link.download = backup.name; link.click(); URL.revokeObjectURL(url) }
  catch (e) { error.value = hataMesaji(e) }
}
function fileSelected(event: Event): void { restoreFile.value = (event.target as HTMLInputElement).files?.[0] || null }
async function restoreBackup(): Promise<void> {
  if (!restoreFile.value || restoreConfirmation.value !== 'RESTORE DATABASE') return
  restoreRunning.value = true; error.value = ''; notice.value = ''
  try { const result = await databaseApi.restore(restoreFile.value, restoreConfirmation.value); const payload = result.data.data || result.data; notice.value = `Geri yükleme tamamlandı. Güvenlik yedeği: ${payload.safety_backup || 'oluşturuldu'}`; restoreFile.value = null; restoreConfirmation.value = ''; await loadOverview() }
  catch (e) { error.value = hataMesaji(e) }
  finally { restoreRunning.value = false }
}

onMounted(() => { void loadOverview() })
</script>

<template>
  <div class="mx-auto max-w-[1500px] space-y-5">
    <header class="db-hero">
      <div><div class="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300"><ShieldCheck class="h-4 w-4" /> Süper admin alanı</div><h1 class="font-heading text-3xl font-bold text-white">Veritabanı Yönetimi</h1><p class="mt-2 max-w-2xl text-sm leading-6 text-slate-300">Şemanı keşfet, kayıtları kontrollü biçimde düzelt ve geri dönüş noktalarını tek merkezden yönet.</p></div>
      <div class="db-hero-stats"><div><span>Veritabanı</span><strong>{{ overview?.database || '...' }}</strong></div><div><span>Tablo</span><strong>{{ overview?.table_count || 0 }}</strong></div><div><span>Yedek</span><strong>{{ overview?.backup_count || backups.length }}</strong></div></div>
    </header>

    <p v-if="error" class="hata-kutusu" role="alert">{{ error }} <button class="ml-3 underline" @click="error = ''">Kapat</button></p><p v-if="notice" class="db-notice" role="status">{{ notice }}</p>
    <div class="grid gap-5 xl:grid-cols-[280px_minmax(0,1fr)_300px]">
      <aside class="db-panel db-tree-panel"><div class="db-panel-title"><span>Veri haritası</span><div class="flex items-center gap-2"><button class="text-xs text-cyan-700" @click="selectAllTables">Tümü</button><button title="Yenile" @click="loadOverview"><RefreshCw class="h-4 w-4" /></button></div></div><p class="mb-4 text-xs leading-5 text-slate-500">Tabloyu ve şablona girecek alanları seçin.</p><div v-for="([group, tables]) in groups" :key="group" class="mb-4"><div class="db-group-title">{{ group }} <span>{{ tables.length }}</span></div><div v-for="table in tables" :key="table.name" class="db-table-choice"><div class="db-tree-row"><input type="checkbox" :checked="selectedTables.includes(table.name)" :aria-label="`${tableLabel(table)} tablosunu Excel'e dahil et`" @click="toggleTable(table.name)" /><button class="db-tree-item" :class="selectedTable === table.name ? 'db-tree-active' : ''" @click="selectTable(table)"><Database class="h-4 w-4 shrink-0" /><span class="min-w-0 flex-1 truncate">{{ tableLabel(table) }}</span><small>{{ table.row_count }}</small></button></div><div v-if="selectedTables.includes(table.name)" class="db-fields"><label v-for="column in table.columns.filter((item) => item.editable && !item.sensitive)" :key="column.name"><input type="checkbox" :checked="selectedFields[table.name]?.includes(column.name)" @change="toggleField(table.name, column.name)" />{{ column.name }}</label></div></div></div></aside>
      <section class="db-panel min-w-0"><div class="db-panel-title"><div><span>{{ rows?.table ? tableLabel(rows.table) : 'Tablo seçin' }}</span><small v-if="rows" class="ml-2 text-slate-500">{{ rows.count }} kayıt</small></div><div class="flex items-center gap-2"><form v-if="rows" class="flex gap-2" @submit.prevent="searchRows"><input v-model="search" class="db-search" placeholder="Kayıtlarda ara..." /><button class="db-icon-button" title="Ara"><RefreshCw class="h-4 w-4" /></button></form></div></div><div v-if="loading" class="db-empty">Kayıtlar yükleniyor...</div><div v-else-if="!rows" class="db-empty"><Database class="mx-auto mb-3 h-10 w-10 text-cyan-500" />Sol menüden bir tablo seçin.</div><div v-else class="overflow-x-auto"><table class="db-table"><thead><tr><th v-for="column in rows.columns" :key="column.name">{{ column.name }}<small>{{ column.sensitive ? 'gizli' : column.type }}</small></th><th>İşlem</th></tr></thead><tbody><tr v-for="row in visibleRows" :key="String(row[rows.table.primary_key || rows.columns[0].name])"><td v-for="column in rows.columns" :key="column.name" :class="column.primary_key ? 'font-mono text-cyan-700' : ''"><span v-if="column.sensitive" class="text-slate-400">Gizli</span><span v-else class="db-cell">{{ display(row[column.name]) }}</span></td><td><button class="db-edit-button" :disabled="!rows.table.primary_key" @click="openEdit(row)">Düzenle</button></td></tr></tbody></table><div v-if="!visibleRows.length" class="db-empty">Bu tabloda kayıt bulunamadı.</div></div><div v-if="rows" class="db-pager"><span>Sayfa {{ page }} / {{ totalPages }}</span><div><button :disabled="page <= 1" @click="page -= 1; loadRows">Önceki</button><button :disabled="page >= totalPages" @click="page += 1; loadRows">Sonraki</button></div></div></section>
      <aside class="space-y-5"><section class="db-panel db-excel"><div class="db-panel-title"><span>Excel veri aktarımı</span><Download class="h-4 w-4 text-cyan-600" /></div><p class="mt-3 text-xs leading-5 text-slate-600">{{ selectedTables.length }} tablo seçili. Alan seçimleriyle şablon ve mevcut veri dışa aktarımı yapabilirsiniz.</p><button class="db-primary-button mt-3 w-full" @click="downloadExcelTemplate"><Download class="h-4 w-4" />Boş Excel şablonu indir</button><button class="db-export-button mt-2 w-full" @click="exportExcel"><Database class="h-4 w-4" />Mevcut verileri Excel'e aktar</button><select v-model="targetTenant" class="db-confirm mt-3 w-full"><option :value="null">Tenant seçin</option><option v-for="tenant in auth.tenantlar" :key="tenant.id" :value="tenant.id">{{ tenant.name }}</option></select><label class="db-file-input mt-3"><Upload class="h-4 w-4" />{{ excelFile?.name || 'Doldurulmuş Excel seç' }}<input type="file" accept=".xlsx,.xlsm" @change="chooseExcel" /></label><label class="mt-3 flex items-center gap-2 text-xs text-slate-600"><input v-model="excelDryRun" type="checkbox" /> Önce sadece doğrula</label><button class="db-restore-button mt-3 w-full" :disabled="excelRunning || !excelFile" @click="importExcel">{{ excelRunning ? 'Excel işleniyor...' : 'Excel verilerini yükle' }}</button></section><section class="db-panel"><div class="db-panel-title"><span>Yedekler</span><FileArchive class="h-4 w-4 text-cyan-600" /></div><button class="db-primary-button mt-3 w-full" :disabled="backupRunning" @click="createBackup"><FileArchive class="h-4 w-4" />{{ backupRunning ? 'Yedek alınıyor...' : 'Yeni yedek oluştur' }}</button><div class="mt-4 space-y-2"><div v-for="backup in backups.slice(0, 5)" :key="backup.name" class="db-backup-item"><div class="min-w-0"><strong>{{ backup.name }}</strong><small>{{ formatBytes(backup.size) }}</small></div><button title="İndir" @click="downloadBackup(backup)"><Download class="h-4 w-4" /></button></div><p v-if="!backups.length" class="text-xs text-slate-500">Henüz yedek yok.</p></div></section><section class="db-panel db-warning"><div class="db-panel-title"><span>Geri yükleme</span><Upload class="h-4 w-4 text-amber-600" /></div><p class="mt-3 text-xs leading-5 text-amber-800">Mevcut veritabanı değişir. İşlemden önce otomatik güvenlik yedeği alınır.</p><label class="db-file-input mt-3"><Upload class="h-4 w-4" />{{ restoreFile?.name || 'SQL yedeği seç' }}<input type="file" accept=".sql" @change="fileSelected" /></label><input v-model="restoreConfirmation" class="db-confirm mt-3" placeholder="RESTORE DATABASE yazın" /><button class="db-restore-button mt-3 w-full" :disabled="restoreRunning || !restoreFile || restoreConfirmation !== 'RESTORE DATABASE'" @click="restoreBackup">{{ restoreRunning ? 'Geri yükleniyor...' : 'Geri yüklemeyi başlat' }}</button></section></aside>
    </div>

    <KayitModal v-if="editRow && editTable" baslik="Kayıt düzenle" @kapat="editRow = null"><div class="space-y-4"><p class="text-xs leading-5 text-slate-500">Salt-okunur alanlar ve gizli değerler korunur. Kaydetmeden önce değişiklikleri kontrol edin.</p><label v-for="column in editableColumns(editTable)" :key="column.name" class="etiket">{{ column.name }}<textarea v-model="editRow[column.name]" class="alan min-h-10" rows="1" /></label><div class="flex justify-end gap-2"><button class="ikincil-dugme" @click="editRow = null">Vazgeç</button><button class="birincil-dugme" :disabled="editSaving" @click="saveEdit"><Save class="h-4 w-4" />{{ editSaving ? 'Kaydediliyor...' : 'Kaydet' }}</button></div></div></KayitModal>
  </div>
</template>

<style scoped>
.db-hero { display:flex; justify-content:space-between; gap:2rem; padding:2rem; border-radius:1.25rem; background:linear-gradient(120deg,#102a43,#0f4c5c 55%,#116466); box-shadow:0 16px 35px rgba(15,76,92,.16); }
.db-hero-stats { display:flex; gap:1.5rem; align-items:flex-end; }
.db-hero-stats div { min-width:90px; border-left:1px solid rgba(255,255,255,.2); padding-left:1rem; }
.db-hero-stats span,.db-hero-stats strong { display:block; }
.db-hero-stats span { color:#9ccfd5; font-size:.7rem; text-transform:uppercase; letter-spacing:.12em; }
.db-hero-stats strong { color:white; font-size:1.15rem; margin-top:.4rem; }
.db-panel { border:1px solid #dbe5ea; border-radius:1rem; background:#fff; box-shadow:0 8px 24px rgba(15,42,67,.06); padding:1rem; }
.db-tree-panel { background:#f7fafb; }
.db-panel-title { display:flex; align-items:center; justify-content:space-between; font-weight:700; color:#102a43; }
.db-group-title { display:flex; justify-content:space-between; color:#6b7c88; font-size:.68rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin:.9rem .5rem .35rem; }
.db-group-title span { color:#9aaab2; }
.db-tree-item { display:flex; width:100%; gap:.6rem; align-items:center; padding:.58rem .65rem; border-radius:.65rem; color:#3d5968; font-size:.82rem; text-align:left; transition:.18s; }
.db-tree-row { display:flex; align-items:center; gap:.2rem; }
.db-table-choice { margin-bottom:.2rem; }
.db-tree-row > input { accent-color:#0f6973; margin-left:.35rem; }
.db-tree-row .db-tree-item { flex:1; }
.db-fields { display:grid; grid-template-columns:1fr 1fr; gap:.25rem .5rem; margin:.25rem .4rem .5rem 2rem; padding:.45rem; border-left:2px solid #c7e4e5; }
.db-fields label { display:flex; align-items:center; gap:.3rem; color:#58717b; font-size:.68rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.db-fields input { accent-color:#0f6973; }
.db-tree-item:hover { background:#e7f3f4; color:#0f6670; }
.db-tree-item small { color:#8ca0aa; font-variant-numeric:tabular-nums; }
.db-tree-active { background:#d7eef0; color:#0d5963; font-weight:700; box-shadow:inset 3px 0 #1b8790; }
.db-search,.db-confirm { border:1px solid #d4e0e5; border-radius:.55rem; padding:.48rem .7rem; font-size:.8rem; outline:none; }
.db-search:focus,.db-confirm:focus { border-color:#2296a0; box-shadow:0 0 0 3px rgba(34,150,160,.12); }
.db-icon-button { border:1px solid #d4e0e5; border-radius:.55rem; padding:.55rem; color:#14717a; }
.db-primary-button,.db-restore-button { display:flex; justify-content:center; align-items:center; gap:.5rem; border-radius:.6rem; padding:.65rem .8rem; font-size:.78rem; font-weight:700; }
.db-primary-button { background:#0f6973; color:white; }.db-primary-button:hover { background:#0a4d56; }.db-primary-button:disabled,.db-restore-button:disabled { opacity:.5; cursor:not-allowed; }
.db-export-button { display:flex; justify-content:center; align-items:center; gap:.5rem; border:1px solid #0f6973; border-radius:.6rem; padding:.58rem .8rem; color:#0f6973; font-size:.78rem; font-weight:700; }
.db-export-button:hover { background:#e4f4f3; }
.db-restore-button { background:#a95524; color:#fff; }.db-restore-button:hover { background:#873f1b; }
.db-warning { background:#fffaf3; border-color:#f2d8ad; }
.db-excel { background:#f2fbfa; border-color:#b8e1df; }
.db-file-input { display:flex; align-items:center; gap:.5rem; border:1px dashed #d9a45b; border-radius:.6rem; padding:.65rem; color:#9a5b20; font-size:.75rem; cursor:pointer; }.db-file-input input { display:none; }
.db-backup-item { display:flex; align-items:center; justify-content:space-between; gap:.5rem; border-bottom:1px solid #edf1f2; padding:.6rem 0; }.db-backup-item strong,.db-backup-item small { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }.db-backup-item strong { max-width:220px; font-size:.72rem; color:#244554; }.db-backup-item small { color:#8a9ca4; font-size:.68rem; margin-top:.2rem; }.db-backup-item button { color:#0d7780; padding:.35rem; }
.db-table { width:100%; border-collapse:collapse; font-size:.76rem; }.db-table th { background:#f3f7f8; color:#59707b; font-size:.66rem; letter-spacing:.05em; text-align:left; text-transform:uppercase; }.db-table th,.db-table td { border-bottom:1px solid #eaf0f2; padding:.7rem .65rem; vertical-align:top; }.db-table th small { display:block; font-weight:400; text-transform:none; color:#9aabb2; margin-top:.25rem; }.db-cell { display:block; max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }.db-edit-button { color:#0d7780; font-size:.72rem; font-weight:700; white-space:nowrap; }.db-pager { display:flex; justify-content:space-between; align-items:center; color:#71858e; font-size:.75rem; padding-top:1rem; }.db-pager button { margin-left:.4rem; border:1px solid #d4e0e5; border-radius:.45rem; padding:.4rem .6rem; }.db-pager button:disabled { opacity:.4; }.db-empty { padding:4rem 1rem; text-align:center; color:#81939b; font-size:.82rem; }.db-notice { border:1px solid #b7dfc5; border-radius:.65rem; background:#effaf2; color:#24683a; padding:.75rem 1rem; font-size:.8rem; }
@media (max-width: 900px) { .db-hero { flex-direction:column; }.db-hero-stats { align-items:stretch; }.db-hero-stats div { flex:1; }.db-table { min-width:900px; } }
</style>
