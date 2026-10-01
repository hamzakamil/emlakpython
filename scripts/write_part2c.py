import os
views_dir = r"c:\proje\emlakpython\frontend\src\views\insaat\yfk"
f = open(os.path.join(views_dir, "YillikPozGuncelle.vue"), "a", encoding="utf-8")
f.write("          <div v-if=\"selectedPoz.fiyatlar && selectedPoz.fiyatlar.length\" class=\"mb-4\"><h4 class=\"font-medium mb-2\">Fiyat Geçmişi</h4><table class=\"table w-full text-sm\"><thead><tr><th>Yıl</th><th>Dönem</th><th>Birim Fiyat</th><th>Kaynak</th><th>Yayın Tarihi</th><th>Geçerlilik</th></tr></thead><tbody><tr v-for=\"f in selectedPoz.fiyatlar\" :key=\"f.id\"><td>{{ f.yil }}</td><td>{{ f.donem || 'Yıllık' }}</td><td class=\"font-mono\">{{ formatCurrency(f.birim_fiyat) }}</td><td>{{ f.kaynak }}</td><td>{{ f.yayin_tarihi || '-' }}</td><td>{{ f.gecerlilik_tarihi || '-' }}</td></tr></tbody></table></div>\n")
f.write("          <div v-if=\"selectedPoz.rayiclar && selectedPoz.rayiclar.length\" class=\"mb-4\"><h4 class=\"font-medium mb-2\">Rayıçlar</h4><table class=\"table w-full text-sm\"><thead><tr><th>Tip</th><th>Malzeme Kodu</th><th>Malzeme Adı</th><th>Birim</th><th>Katsayı</th></tr></thead><tbody><tr v-for=\"r in selectedPoz.rayiclar\" :key=\"r.id\"><td>{{ r.malzeme_tipi }}</td><td>{{ r.malzeme_kodu }}</td><td>{{ r.malzeme_adi }}</td><td>{{ r.birim }}</td><td class=\"font-mono\">{{ r.katsayi }}</td></tr></tbody></table></div>\n")
f.write("          <div v-if=\"selectedPoz.analizler && selectedPoz.analizler.length\" class=\"mb-4\"><h4 class=\"font-medium mb-2\">Analiz Detayları</h4><table class=\"table w-full text-sm\"><thead><tr><th>Tip</th><th>Sıra</th><th>Malzeme Kodu</th><th>Malzeme Adı</th><th>Birim</th><th>Miktar</th><th>Birim Fiyat</th><th>Toplam</th></tr></thead><tbody><tr v-for=\"a in selectedPoz.analizler\" :key=\"a.id\"><td>{{ a.malzeme_tipi }}</td><td>{{ a.sira_no }}</td><td>{{ a.malzeme_kodu }}</td><td>{{ a.malzeme_adi }}</td><td>{{ a.birim }}</td><td class=\"font-mono\">{{ a.miktar }}</td><td class=\"font-mono\">{{ formatCurrency(a.birim_fiyat) }}</td><td class=\"font-mono\">{{ formatCurrency(a.toplam_tutar) }}</td></tr></tbody></table></div>\n")
f.write("        </div>\n")
f.write("      </div>\n")
f.write("    </div>\n")
f.write("  </div>\n")
f.write("</template>\n")
f.close()
print("Part 2c done")