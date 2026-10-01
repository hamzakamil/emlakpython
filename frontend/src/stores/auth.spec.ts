import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from './auth'

vi.mock('@/services/authApi', () => ({
  girisYap: vi.fn(async (_username: string, _password: string) => ({
    access: 'access-token',
    refresh: 'refresh-token',
  })),
  beniGetir: vi.fn(async () => ({
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    role: 'kullanici',
    tenant: 7,
    tenant_ad: 'Demo Firma A.Ş.',
  })),
  tenantListesiniGetir: vi.fn(async () => [
    { id: 7, name: 'Demo Firma A.Ş.', slug: 'demo', is_active: true },
  ]),
}))

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('emlak_erp_beni_hatirla', '1')
    setActivePinia(createPinia())
  })

  it('giriş sonrası tokenlar yazılır ve oturum geçerli sayılır', async () => {
    const auth = useAuthStore()

    await auth.giris('admin', 'sifre123', true)

    expect(auth.girisYapilmis).toBe(true)
    expect(localStorage.getItem('emlak_erp_access')).toBe('access-token')
    expect(localStorage.getItem('emlak_erp_refresh')).toBe('refresh-token')
    expect(auth.kullanici?.username).toBe('admin')
  })

  it('çıkışta tokenlar ve kullanıcı bilgisi temizlenir', async () => {
    const auth = useAuthStore()
    await auth.giris('admin', 'sifre123', true)

    auth.cikis()

    expect(auth.girisYapilmis).toBe(false)
    expect(auth.kullanici).toBeNull()
    expect(localStorage.getItem('emlak_erp_access')).toBeNull()
    expect(localStorage.getItem('emlak_erp_kullanici')).toBeNull()
  })

  it('sayfa yenilenince kullanıcı bilgisi localStorage\'dan okunur', async () => {
    const auth = useAuthStore()
    await auth.giris('admin', 'sifre123', true)

    // Yeni pinia örneği = uygulamanın yeniden başlaması
    setActivePinia(createPinia())
    const yeniden = useAuthStore()

    expect(yeniden.kullanici?.username).toBe('admin')
    expect(yeniden.kullanici?.tenant_ad).toBe('Demo Firma A.Ş.')
    expect(yeniden.girisYapilmis).toBe(true)
  })

  it('normal kullanıcıda seçici gizlenir; süper adminde görünür', async () => {
    const auth = useAuthStore()
    await auth.giris('admin', 'sifre123', true)
    expect(auth.seciciGosterilsinMi).toBe(false)

    auth.kullanici = { ...auth.kullanici!, role: 'super_admin', tenant: null, tenant_ad: null }
    expect(auth.seciciGosterilsinMi).toBe(true)
  })

  it('tenant seçimi saklanır ve çıkışta temizlenir', async () => {
    const auth = useAuthStore()
    await auth.giris('admin', 'sifre123', true)

    auth.tenantSec(7)
    expect(auth.seciliTenantId).toBe(7)
    expect(localStorage.getItem('emlak_erp_tenant_secimi')).toBe('7')

    auth.tenantSec(null)
    expect(auth.seciliTenantId).toBeNull()
    expect(localStorage.getItem('emlak_erp_tenant_secimi')).toBeNull()

    auth.tenantSec(7)
    auth.cikis()
    expect(localStorage.getItem('emlak_erp_tenant_secimi')).toBeNull()
  })
})
