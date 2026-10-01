import os
views_dir = r"c:\proje\emlakpython\frontend\src\views\insaat\yfk"
f = open(os.path.join(views_dir, "GuncellemeGecmisi.vue"), "a", encoding="utf-8")
f.write("        <div class=\"overflow-x-auto\"><table class=\"table w-full\"><thead><tr><th>Tarih</th><th>Islem Turu</th><th>Veri Turu</th><th>Poz No</th><th>Ad</th><th>Eski Deger</th><th>Yeni Deger</th><th>Yil</th><th>Donem</th><th>Kaynak</th><th>Kullanici</th><th>Aciklama</th></tr></thead><tbody>\n")
f.write("          <tr v-for=\"g in filteredGecmisList\" :key=\"g.id\"><td>{{ formatDateTime(g.tarih) }}</td><td><span class=\"badge\" :class=\"islemClass(g.islem_turu)\">{{ g.islem_turu }}</span></td><td>{{ g.veri_turu }}</td><td class=\"font-mono\">{{ g.poz_no }}</td><td>{{ g.ad }}</td><td>{{ g.eski_deger }}</td><td>{{ g.yeni_deger }}</td><td>{{ g.yil }}</td><td>{{ g.donem or '-' }}</td><td>{{ g.kaynak }}</td><td>{{ g.kullanici }}</td><td>{{ g.aciklama }}</td></tr>\n")
f.write("          <tr v-if=\"filteredGecmisList.length === 0\"><td colspan=\"12\" class=\"text-center py-8 text-gray-500\">Kayit bulunamadi</td></tr>\n")
f.write("        </tbody></table></div>\n")
f.write("        <div class=\"p-4 border-t flex justify-between items-center\" v-if=\"pagination.total > 0\"><p class=\"text-sm text-gray-600\"> {{ (pagination.page - 1) * pagination.pageSize + 1 }} - {{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} / {{ pagination.total }} kayit</p><div class=\"flex gap-2\"><button @click=\"pagination.page > 1 and (pagination.page--, loadGecmisList())\" :disabled=\"pagination.page <= 1\" class=\"btn btn-sm btn-ghost\">Onceki</button><button @click=\"pagination.page * pagination.pageSize < pagination.total and (pagination.page++, loadGecmisList())\" :disabled=\"pagination.page * pagination.pageSize >= pagination.total\" class=\"btn btn-sm btn-ghost\">Sonraki</button></div></div>\n")
f.write("      </div>\n")
f.write("    </div>\n")
f.write("  </div>\n")
f.write("</template>\n")
f.close()
print("Part 2 done")