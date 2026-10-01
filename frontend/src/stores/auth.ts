/**
 * Kimlik store'u — JWT access/refresh localStorage'da tutulur (apiClient).
 * Girişten sonra /auth/me çağrısıyla gerçek rol/tenant bilgisi alınır;
 * /auth/me erişilemezse yedek olarak formdaki kullanıcı adı kullanılır.
 *
 * Süper admin için tenant kapsamı: `seciliTenantId` null ise global görünüm,
 * sayı ise o tenant'a daraltılmış görünüm. Seçim `X-Tenant-Id` başlığı olarak
 * her API isteğine eklenir (bkz. apiClient); localStorage'da saklanır.
 */
import { defineStore } from 'pinia'
import { beniGetir, girisYap, tenantListesiniGetir } from '@/services/authApi'
import {
  accessOku,
  beniHatirlaYaz,
  kullaniciBilgisiOku,
  kullaniciBilgisiYaz,
  refreshOku,
  seciliTenantOku,
  seciliTenantYaz,
  tokenTemizle,
  tokenYaz,
} from '@/services/apiClient'
import type { Kullanici, TenantSecim } from '@/types/api'

interface Durum {
  kullanici: Kullanici | null
  tenantlar: TenantSecim[]
  seciliTenantId: number | null
  tenantlarYukleniyor: boolean
  gelistiriciModu: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): Durum => ({
    kullanici: kullaniciBilgisiOku(),
    tenantlar: [],
    seciliTenantId: seciliTenantOku(),
    tenantlarYukleniyor: false,
    gelistiriciModu: localStorage.getItem('emlak_erp_gelistirici_modu') === '1',
  }),

  getters: {
    /** Access+refresh çifti varsa oturum geçerli kabul edilir. */
    girisYapilmis(): boolean {
      return Boolean(this.kullanici && accessOku() && refreshOku())
    },

    /** Tenant seçici yalnızca süper admin'e gösterilir. */
    seciciGosterilsinMi(): boolean {
      return this.kullanici?.role === 'super_admin'
    },
  },

  actions: {
    async giris(username: string, password: string, beniHatirla = false): Promise<void> {
      // "Beni hatırla" tercihi token yazılmadan önce ayarlanmalı — tokenYaz
      // oturum deposunu (localStorage/sessionStorage) bu tercihe göre seçer.
      beniHatirlaYaz(beniHatirla)
      const token = await girisYap(username, password)
      tokenYaz(token.access, token.refresh)

      let kullanici: Kullanici
      try {
        kullanici = await beniGetir()
      } catch {
        // /auth/me ulaşılamazsa yedek: formdaki kullanıcı adı ile devam.
        kullanici = { id: 0, username, email: '', role: 'kullanici', tenant: null }
      }
      kullaniciBilgisiYaz(kullanici)
      this.kullanici = kullanici
      this.seciliTenantId = seciliTenantOku()
      this.tenantlar = []
      if (kullanici.role === 'super_admin') {
        await this.tenantlariYukle()
      }
    },

    /** Sayfa yenilenmede rol/tenant bilgisini /auth/me'den tazeler (sessiz). */
    async oturumuTazele(): Promise<void> {
      if (!accessOku() || !refreshOku()) return
      try {
        const kullanici = await beniGetir()
        kullaniciBilgisiYaz(kullanici)
        this.kullanici = kullanici
        if (kullanici.role === 'super_admin') {
          await this.tenantlariYukle()
        }
      } catch {
        // 401 durumunda apiClient refresh dener; o da başarısızsa sonraki
        // istek zaten giriş sayfasına yönlendirir.
      }
    },

    /** Süper admin tenant listesini yükler (sessiz; yetki yoksa boş kalır). */
    async tenantlariYukle(): Promise<void> {
      if (this.kullanici?.role !== 'super_admin') return
      this.tenantlarYukleniyor = true
      try {
        this.tenantlar = await tenantListesiniGetir()
      } catch {
        this.tenantlar = []
      } finally {
        this.tenantlarYukleniyor = false
      }
    },

    /** Süper admin kapsam seçimi; null = global görünüm. */
    tenantSec(id: number | null): void {
      this.seciliTenantId = id
      seciliTenantYaz(id)
    },

    gelistiriciModunuDegistir(): void {
      if (this.kullanici?.role !== 'super_admin') return
      this.gelistiriciModu = !this.gelistiriciModu
      localStorage.setItem('emlak_erp_gelistirici_modu', this.gelistiriciModu ? '1' : '0')
    },

    cikis(): void {
      tokenTemizle()
      this.kullanici = null
      this.tenantlar = []
      this.seciliTenantId = null
      this.gelistiriciModu = false
      localStorage.removeItem('emlak_erp_gelistirici_modu')
    },
  },
})
