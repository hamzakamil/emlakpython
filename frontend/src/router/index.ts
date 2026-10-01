/**
 * Vue Router — Türkçe yol adları.
 * Guard: giriş yapılmamışsa /giris'e; konuk sayfasında giriş yapılmışsa panele yönlendirir.
 */
import { createRouter, createWebHistory, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior() {
    requestAnimationFrame(() => {
      document.getElementById('main-content')?.scrollTo({ top: 0, left: 0, behavior: 'auto' })
    })
    return false
  },
  routes: [
    {
      path: '/giris',
      name: 'giris',
      component: () => import('@/views/GirisView.vue'),
      meta: { konuk: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      children: [
        {
          path: '',
          name: 'panel',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'profil',
          name: 'profil',
          component: () => import('@/views/ProfilView.vue'),
        },
        {
          path: 'gayrimenkul/gayrimenkuller',
          name: 'gayrimenkuller',
          component: () => import('@/views/gayrimenkul/GayrimenkullerView.vue'),
        },
        {
          path: 'cari/cariler',
          name: 'cariler',
          component: () => import('@/views/cari/CarilerView.vue'),
        },
        {
          path: 'cari/hareketler',
          name: 'cariHareketler',
          component: () => import('@/views/finans/CariHareketler.vue'),
        },
        {
          path: 'finans/hesaplar',
          name: 'finansHesaplari',
          component: () => import('@/views/finans/FinansHesaplariView.vue'),
        },
        {
          path: 'finans/islemler',
          name: 'finansIslemler',
          component: () => import('@/views/finans/FinansIslemlerView.vue'),
        },
        {
          path: 'finans/faturalar',
          name: 'faturalar',
          component: () => import('@/views/finans/Fatura.vue'),
        },
        {
          path: 'finans/faturalar/:id',
          name: 'fatura-detay',
          component: () => import('@/views/finans/FaturaDetay.vue'),
        },
        {
          path: 'finans/vergi-profilleri',
          name: 'vergiProfilleri',
          component: () => import('@/views/finans/VergiProfilleriView.vue'),
        },
        {
          path: 'finans/stok-hesap-esleme',
          name: 'stokHesapEsleme',
          component: () => import('@/views/satinalma/StokHesapEslemeView.vue'),
        },
        {
          path: 'muhasebe/hesap-plani',
          name: 'hesapPlani',
          component: () => import('@/views/muhasebe/HesapPlaniView.vue'),
        },
        {
          path: 'muhasebe/fisler',
          name: 'muhasebeFisleri',
          component: () => import('@/views/muhasebe/MuhasebeFisleriView.vue'),
        },
        {
          path: 'muhasebe/mizan',
          name: 'mizan',
          component: () => import('@/views/finans/MizanRaporu.vue'),
        },
        {
          path: 'finans/raporlar',
          name: 'raporlar',
          component: () => import('@/views/finans/RaporlarView.vue'),
        },
        {
          path: 'finans/ayarlar',
          name: 'ayarlar',
          component: () => import('@/views/finans/AyarlarView.vue'),
        },
        {
          path: 'yonetim/veritabani',
          name: 'databaseAdmin',
          component: () => import('@/views/DatabaseAdminView.vue'),
          meta: { superAdmin: true },
        },
        {
          path: 'yonetim/firmalar',
          name: 'firmalar',
          component: () => import('@/views/yonetim/FirmalarView.vue'),
          meta: { superAdmin: true },
        },
        {
          path: 'yonetim/kullanicilar',
          name: 'kullanicilar',
          component: () => import('@/views/yonetim/KullanicilarView.vue'),
          meta: { superAdmin: true },
        },
        {
          path: 'insaat/poz-gruplari',
          name: 'pozGruplari',
          component: () => import('@/views/insaat/PozGruplariView.vue'),
        },
        {
          path: 'insaat/pozlar',
          name: 'pozlar',
          component: () => import('@/views/insaat/PozlarView.vue'),
        },
        {
          path: 'insaat/yapi-sinifi',
          name: 'yapiSinifi',
          component: () => import('@/views/insaat/YapiSinifiView.vue'),
        },
        {
          path: 'insaat/malzemeler',
          name: 'malzemeler',
          component: () => import('@/views/insaat/MalzemelerView.vue'),
        },
        {
          path: 'insaat/poz-planlari',
          name: 'pozPlanlari',
          component: () => import('@/views/insaat/PozPlanlariView.vue'),
        },
        {
          path: 'insaat/yfk',
          name: 'yfk',
          component: RouterView,
          children: [
            {
              path: 'yillik-poz-guncelle',
              name: 'yfkYillikPozGuncelle',
              component: () => import('@/views/insaat/yfk/YillikPozGuncelle.vue'),
            },
            {
              path: 'aylik-fiyat-guncelle',
              name: 'yfkAylikFiyatGuncelle',
              component: () => import('@/views/insaat/yfk/AylikFiyatGuncelle.vue'),
            },
            {
              path: 'rayic-guncelle',
              name: 'yfkRayicGuncelle',
              component: () => import('@/views/insaat/yfk/RayicGuncelle.vue'),
            },
            {
              path: 'analiz-guncelle',
              name: 'yfkAnalizGuncelle',
              component: () => import('@/views/insaat/yfk/AnalizGuncelle.vue'),
            },
            {
              path: 'degisen-pozlar',
              name: 'yfkDegisenPozlar',
              component: () => import('@/views/insaat/yfk/DegisenPozlar.vue'),
            },
            {
              path: 'guncelleme-gecmisi',
              name: 'yfkGuncellemeGecmisi',
              component: () => import('@/views/insaat/yfk/GuncellemeGecmisi.vue'),
            },
          ],
        },
        {
          path: 'insaat/mahaller',
          name: 'mahaller',
          component: () => import('@/views/insaat/MahalListesiView.vue'),
        },
        {
          path: 'insaat/hatirlatma-kurallari',
          name: 'hatirlatmaKurallari',
          component: () => import('@/views/insaat/HatirlatmaKurallariView.vue'),
        },
        {
          path: 'insaat/metraj-kesif',
          name: 'metrajKesif',
          component: () => import('@/views/insaat/MetrajKesifView.vue'),
        },
        {
          path: 'insaat/maliyet-hesabi',
          name: 'maliyetHesabi',
          component: () => import('@/views/insaat/MaliyetHesabiView.vue'),
        },
        {
          path: 'insaat/genel-bakis',
          name: 'genelBakis',
          component: () => import('@/views/insaat/GenelBakisView.vue'),
        },
        {
          path: 'insaat/raporlar',
          name: 'insaatRaporlar',
          component: () => import('@/views/insaat/RaporlarView.vue'),
        },
        {
          path: 'insaat/ayarlar',
          name: 'insaatAyarlar',
          component: () => import('@/views/insaat/AyarlarView.vue'),
        },
        {
          path: 'insaat/analiz-kitabi',
          name: 'analizKitabi',
          component: () => import('@/views/insaat/AnalizKitabiView.vue'),
          meta: { title: 'Analiz Kitabı' },
        },
        {
          path: 'insaat/yaklasik-maliyet',
          name: 'yaklasikMaliyet',
          component: () => import('@/views/insaat/YaklasikMaliyetView.vue'),
          meta: { title: 'Yaklaşık Maliyet' },
        },
        {
          path: 'insaat/ifc-import',
          name: 'ifcImport',
          component: () => import('@/views/insaat/IFCImportView.vue'),
          meta: { title: 'IFC Miktar Taslakları' },
        },
{
          path: 'insaat/gantt',
          name: 'gantt',
          component: () => import('@/views/insaat/GanttView.vue'),
        },
        {
          path: 'insaat/rayicler',
          name: 'rayicler',
          component: () => import('@/views/insaat/RayiclerView.vue'),
          meta: { title: 'YFK Rayıç (Katsayı) Listesi' },
        },
        {
          path: 'insaat/projeler',
          name: 'projeler',
          component: () => import('@/views/insaat/ProjelerView.vue'),
        },
        {
          path: 'insaat/hakedisler',
          name: 'hakedisler',
          component: () => import('@/views/insaat/HakedislerView.vue'),
        },
        {
          path: 'insaat/taseron-hakedisleri',
          name: 'taseronHakedisleri',
          component: () => import('@/views/insaat/HakedislerView.vue'),
        },
        {
          path: 'insaat/taseron-sozlesmeleri',
          name: 'taseronSozlesmeleri',
          component: () => import('@/views/construction/TaseronSozlesi.vue'),
        },
        {
          path: 'insaat/santiye-gunlukleri',
          name: 'santiyeGunlukleri',
          component: () => import('@/views/insaat/SantiyeGunlukleriView.vue'),
        },
        {
          path: 'insaat/saha-hareketleri',
          name: 'sahaHareketleri',
          component: () => import('@/views/insaat/SahaHareketleriView.vue'),
        },
        {
          path: 'insaat/poz-fiyatlari',
          name: 'pozFiyatlari',
          component: () => import('@/views/insaat/PozFiyatlariView.vue'),
        },
        {
          path: 'insaat/poz-analizleri',
          name: 'pozAnalizleri',
          component: () => import('@/views/insaat/PozAnalizleriView.vue'),
        },
        {
          path: 'insaat/malzeme-tedarik',
          name: 'malzemeTedarik',
          component: () => import('@/views/insaat/MalzemeTedarikPlaniView.vue'),
        },
        {
          path: 'insaat/tedarikci-teklifleri',
          name: 'tedarikciTeklifleri',
          component: () => import('@/views/insaat/TedarikciTeklifleriView.vue'),
          meta: { title: 'Tedarikçi Teklifleri' },
        },
        {
          path: 'satinalma/talepler',
          name: 'talepler',
          component: () => import('@/views/satinalma/TaleplerView.vue'),
          meta: { title: 'Satın Alma Talepleri' },
        },
        {
          path: 'satinalma/talepler/:id',
          name: 'talep-detay',
          component: () => import('@/views/satinalma/TalepDetay.vue'),
          meta: { title: 'Talep Detayı' },
        },
        {
          path: 'satinalma/siparisler',
          name: 'siparisler',
          component: () => import('@/views/satinalma/SiparislerView.vue'),
          meta: { title: 'Satın Alma Siparişleri' },
        },
        {
          path: 'satinalma/siparisler/:id',
          name: 'siparis-detay',
          component: () => import('@/views/satinalma/SiparisDetay.vue'),
          meta: { title: 'Sipariş Detayı' },
        },
        {
          path: 'satinalma/mal-kabuller',
          name: 'malKabuller',
          component: () => import('@/views/satinalma/MalKabullerView.vue'),
          meta: { title: 'Mal Kabuller' },
        },
        {
          path: 'satinalma/stok-hareketleri',
          name: 'stokHareketleri',
          component: () => import('@/views/satinalma/StokHareketleriView.vue'),
          meta: { title: 'Stok Hareketleri' },
        },
        {
          path: 'satinalma/stok-durumu',
          name: 'stokDurumu',
          component: () => import('@/views/satinalma/StokDurumuView.vue'),
          meta: { title: 'Stok Durumu' },
        },
        {
          path: 'satinalma/depolar',
          name: 'depolar',
          component: () => import('@/views/satinalma/DepolarView.vue'),
          meta: { title: 'Depolar' },
        },
        {
          path: 'insaat/proje-malzemeler',
          name: 'projeMalzemeler',
          component: () => import('@/views/insaat/ProjeMalzemeView.vue'),
          meta: { title: 'Proje Malzemeleri' },
        },
        {
          path: 'insaat/proje-malzeme-fiyatlari',
          name: 'projeMalzemeFiyatlari',
          component: () => import('@/views/insaat/ProjeMalzemeFiyatView.vue'),
          meta: { title: 'Proje Malzeme Fiyatları' },
        },
        {
          path: 'insaat/proje-poz-malzemeler',
          name: 'projePozMalzemeler',
          component: () => import('@/views/insaat/ProjePozMalzemeView.vue'),
          meta: { title: 'Proje Poz Malzemeleri' },
        },
        {
          path: 'insaat/kalite-kontrolleri',
          name: 'kaliteKontrolleri',
          component: () => import('@/views/insaat/KaliteKontrolleriView.vue'),
        },
        {
          path: 'insaat/sozlesme-sablonlari',
          name: 'sozlesmeSablonlari',
          component: () => import('@/views/insaat/ContractTemplatesView.vue'),
        },
        {
          path: 'insaat/riskli-yapi',
          name: 'riskliYapi',
          component: () => import('@/views/insaat/RiskStructuresView.vue'),
        },
        {
          path: 'insaat/kira-yardimi',
          name: 'kiraYardimi',
          component: () => import('@/views/insaat/LeaseAssistanceView.vue'),
        },
        {
          path: 'insaat/ekb',
          name: 'ekb',
          component: () => import('@/views/insaat/EKBView.vue'),
          meta: { title: 'EKB Süreç Takibi' },
        },
        {
          path: 'insaat/nakit-akisi',
          name: 'nakitAkisi',
          component: () => import('@/views/insaat/NakitAkisiView.vue'),
        },
        {
          path: 'insaat/kar-zarar',
          name: 'karZarar',
          component: () => import('@/views/insaat/KarZararView.vue'),
        },
        {
          path: 'insaat/portfoy-karsilastirma',
          name: 'portfoyKarsilastirma',
          component: () => import('@/views/insaat/PortfoyKarsilastirmaView.vue'),
        },
        {
          path: 'insaat/teknik-sartname',
          name: 'teknikSartname',
          component: () => import('@/views/insaat/TeknikSartnameView.vue'),
        },
        {
          path: 'finans/cek-senetler',
          name: 'cekSenetler',
          component: () => import('@/views/finans/CekSenetlerView.vue'),
        },
        {
          path: 'gayrimenkul/ada-parsel',
          name: 'adaParsel',
          component: () => import('@/views/gayrimenkul/AdaParselView.vue'),
        },
        {
          path: 'gayrimenkul/malik-mutabakati',
          name: 'malikMutabakati',
          component: () => import('@/views/gayrimenkul/MalikMutabakatiView.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'bulunamadi',
      component: () => import('@/views/BulunamadiView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.konuk) {
    return auth.girisYapilmis ? { name: 'panel' } : true
  }
  if (!auth.girisYapilmis) {
    return { name: 'giris' }
  }
  if (to.meta.superAdmin && auth.kullanici?.role !== 'super_admin') {
    return { name: 'panel' }
  }
  return true
})

export default router
