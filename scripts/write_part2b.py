import os
views_dir = r"c:\proje\emlakpython\frontend\src\views\insaat\yfk"
f = open(os.path.join(views_dir, "YillikPozGuncelle.vue"), "a", encoding="utf-8")
f.write("        <div class=\"p-4 border-t flex justify-between items-center\" v-if=\"pagination.total > 0\"><p class=\"text-sm text-gray-600\"> {{ (pagination.page - 1) * pagination.pageSize + 1 }} - {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} / {{ pagination.total }} kayıt</p><div class=\"flex gap-2\"><button @click=\"pagination.page > 1 && (pagination.page--, loadPozList())\" :disabled=\"pagination.page <= 1\" class=\"btn btn-sm btn-ghost\">Önceki</button><button @click=\"pagination.page * pagination.pageSize < pagination.total && (pagination.page++, loadPozList())\" :disabled=\"pagination.page * pagination.pageSize >= pagination.total\" class=\"btn btn-sm btn-ghost\">Sonraki</button></div></div>\n")
f.write("      </div>\n")
f.write("    </div>\n\n")
f.write("    <div v-if=\"selectedPoz\" class=\"fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4\">\n")
f.write("      <div class=\"bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden\">\n")
f.write("        <div class=\"p-4 border-b flex justify-between items-center\"><h3 class=\"text-lg font-bold\">{{ selectedPoz.poz_no }} - {{ selectedPoz.ad }} (v{{ selectedPoz.versiyon }})</h3><button @click=\"selectedPoz = null\" class=\"text-gray-500 hover:text-gray-700\">✕</button></div>\n")
f.write("        <div class=\"p-4 overflow-y-auto max-h-[70vh]\">\n")
f.write("          <div class=\"grid grid-cols-1 md:grid-cols-2 gap-4 mb-4\"><div><strong>Poz No:</strong> {{ selectedPoz.poz_no }}</div><div><strong>Ad:</strong> {{ selectedPoz.ad }}</div><div><strong>Birim:</strong> {{ selectedPoz.birim }}</div><div><strong>Grup:</strong> {{ selectedPoz.grup_kodu }} - {{ selectedPoz.grup_adi }}</div><div><strong>Versiyon:</strong> {{ selectedPoz.versiyon }}</div><div><strong>Değişiklik Türü:</strong> {{ selectedPoz.degisiklik_turu }}</div><div><strong>Yayın Tarihi:</strong> {{ selectedPoz.yayin_tarihi || '-' }}</div><div><strong>Geçerlilik:</strong> {{ selectedPoz.gecerlilik_baslangic || '-' }} - {{ selectedPoz.gecerlilik_bitis || '-' }}</div></div>\n")
f.close()
print("Part 2b done")