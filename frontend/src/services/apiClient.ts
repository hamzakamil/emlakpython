/**
 * Axios tabanlı API istemcisi.
 * - baseURL /api/v1 (Vite proxy: /api → http://localhost:8000, önek korunur)
 * - İsteklerde Bearer access token (localStorage)
 * - 401'de bir kez refresh token ile yeniler, isteği tekrar dener
 * - Yanıtları zarf açıcıyla (zarfAc) çözüp sadece data döner
 */
import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import { ApiHatasi, zarfAc } from './zarf'
import type { AlanHatalari, Kullanici, Zarf } from '@/types/api'

const ACCESS_ANAHTARI = 'emlak_erp_access'
const REFRESH_ANAHTARI = 'emlak_erp_refresh'
const KULLANICI_ANAHTARI = 'emlak_erp_kullanici'
const SECILI_TENANT_ANAHTARI = 'emlak_erp_tenant_secimi'
const BENI_HATIRLA_ANAHTARI = 'emlak_erp_beni_hatirla'

/** Süper admin kapsam başlığı — backend tenants.api.TENANT_KAPSAM_BASLIGI ile senkron. */
export const TENANT_KAPSAM_BASLIGI = 'X-Tenant-Id'

/**
 * "Beni hatırla" tercihi localStorage'da kalıcı tutulur (tarayıcı kapatılsa da).
 * İşaretliyse oturum verileri localStorage'a, değilse sessionStorage'a yazılır
 * (sekme/tarayıcı kapanınca oturum sona erer).
 */
export function beniHatirlaOku(): boolean {
  return localStorage.getItem(BENI_HATIRLA_ANAHTARI) === '1'
}

export function beniHatirlaYaz(aktif: boolean): void {
  if (aktif) {
    localStorage.setItem(BENI_HATIRLA_ANAHTARI, '1')
  } else {
    localStorage.removeItem(BENI_HATIRLA_ANAHTARI)
  }
}

/** Oturum verileri için depolama: beni hatırla → localStorage, yoksa sessionStorage. */
function oturumDeposu(): Storage {
  return beniHatirlaOku() ? localStorage : sessionStorage
}

export function accessOku(): string | null {
  return oturumDeposu().getItem(ACCESS_ANAHTARI)
}

export function refreshOku(): string | null {
  return oturumDeposu().getItem(REFRESH_ANAHTARI)
}

export function tokenYaz(access: string, refresh: string): void {
  const depo = oturumDeposu()
  depo.setItem(ACCESS_ANAHTARI, access)
  depo.setItem(REFRESH_ANAHTARI, refresh)
}

export function tokenTemizle(): void {
  // Her iki depodan da temizle — hangi modda girildiyse güvenle çıkış yapılsın.
  ;[localStorage, sessionStorage].forEach((depo) => {
    depo.removeItem(ACCESS_ANAHTARI)
    depo.removeItem(REFRESH_ANAHTARI)
    depo.removeItem(KULLANICI_ANAHTARI)
    depo.removeItem(SECILI_TENANT_ANAHTARI)
  })
}

/** Süper admin tenant kapsam seçimi (null = global görünüm). */
export function seciliTenantOku(): number | null {
  const ham = oturumDeposu().getItem(SECILI_TENANT_ANAHTARI)
  if (!ham) return null
  const id = Number(ham)
  return Number.isInteger(id) && id > 0 ? id : null
}

export function seciliTenantYaz(id: number | null): void {
  const depo = oturumDeposu()
  if (id === null) {
    depo.removeItem(SECILI_TENANT_ANAHTARI)
  } else {
    depo.setItem(SECILI_TENANT_ANAHTARI, String(id))
  }
}

/** Görüntü amaçlı kullanıcı bilgisi (login'de bilinen kadarı saklanır). */
export function kullaniciBilgisiYaz(kullanici: Kullanici): void {
  oturumDeposu().setItem(KULLANICI_ANAHTARI, JSON.stringify(kullanici))
}

export function kullaniciBilgisiOku(): Kullanici | null {
  const ham = oturumDeposu().getItem(KULLANICI_ANAHTARI)
  if (!ham) return null
  try {
    return JSON.parse(ham) as Kullanici
  } catch {
    return null
  }
}

export const http: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use((config) => {
  const access = accessOku()
  if (access) {
    config.headers.Authorization = `Bearer ${access}`
  }
  // Süper admin tenant kapsamı (seçiliyse); normal kullanıcı seçimi
  // backend'de yok sayılır — izolasyon asla gevşetilmez.
  const secili = seciliTenantOku()
  if (secili !== null) {
    config.headers[TENANT_KAPSAM_BASLIGI] = String(secili)
  }
  return config
})

/** Eşzamanlı 401'lerde tek refresh isteği çalışsın diye bekleyen vaat. */
let yenilemeVaat: Promise<string> | null = null

function tokenYenile(): Promise<string> {
  yenilemeVaat = yenilemeVaat ?? (async () => {
    const refresh = refreshOku()
    if (!refresh) {
      throw new ApiHatasi(401, 'Oturum yenilenemedi.', null)
    }
    const { data } = await axios.post<Zarf<{ access: string }>>('/api/v1/auth/token/refresh/', {
      refresh,
    })
    const govde = data as Zarf<{ access: string }>
    if (!govde.success || !govde.data?.access) {
      throw new ApiHatasi(401, govde.message || 'Oturum yenilenemedi.', govde.errors ?? null)
    }
    oturumDeposu().setItem(ACCESS_ANAHTARI, govde.data.access)
    return govde.data.access
  })()

  return yenilemeVaat.finally(() => {
    yenilemeVaat = null
  })
}

type YenidenGonderilebilirConfig = InternalAxiosRequestConfig & { _yeniden?: boolean }

http.interceptors.response.use(
  (yanit) => yanit,
  async (hata: AxiosError) => {
    const durum = hata.response?.status
    const orijinal = hata.config as YenidenGonderilebilirConfig | undefined

    if (durum === 401 && orijinal && !orijinal._yeniden && refreshOku()) {
      orijinal._yeniden = true
      try {
        const access = await tokenYenile()
        orijinal.headers.Authorization = `Bearer ${access}`
        return http(orijinal)
      } catch {
        tokenTemizle()
      }
    }
    return Promise.reject(hata)
  },
)

/* --- Zarf açan istek yardımcıları (bileşenler bunları kullanır) --- */

export async function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const yanit = await http.get<Zarf<T>>(url, { params })
  return zarfAc(yanit.data, yanit.status)
}

export async function post<T>(url: string, veri?: unknown): Promise<T> {
  const yanit = await http.post<Zarf<T>>(url, veri)
  return zarfAc(yanit.data, yanit.status)
}

export async function put<T>(url: string, veri?: unknown): Promise<T> {
  const yanit = await http.put<Zarf<T>>(url, veri)
  return zarfAc(yanit.data, yanit.status)
}

export async function patch<T>(url: string, veri?: unknown): Promise<T> {
  const yanit = await http.patch<Zarf<T>>(url, veri)
  return zarfAc(yanit.data, yanit.status)
}

export async function del<T>(url: string): Promise<T> {
  const yanit = await http.delete<Zarf<T>>(url)
  return zarfAc(yanit.data, yanit.status)
}

/** Kullanıcıya gösterilecek Türkçe hata mesajını çıkarır. */
export function hataMesaji(hata: unknown): string {
  if (hata instanceof ApiHatasi) {
    return hata.message
  }
  if (axios.isAxiosError(hata)) {
    const govde = hata.response?.data as (Zarf<unknown> & { detail?: string; errors?: AlanHatalari }) | undefined
    if (govde && typeof govde === 'object' && typeof govde.message === 'string') {
      return govde.message
    }
    if (govde && typeof govde === 'object' && typeof govde.detail === 'string') {
      return govde.detail
    }
    if (govde && typeof govde === 'object' && govde.errors && typeof govde.errors === 'object') {
      return Object.entries(govde.errors)
        .map(([alan, mesaj]) => `${alan}: ${Array.isArray(mesaj) ? mesaj.join(', ') : String(mesaj)}`)
        .join(' | ')
    }
    if (hata.response?.status === 401) {
      return 'Kullanıcı adı veya şifre hatalı.'
    }
    if (!hata.response) {
      return 'Sunucuya ulaşılamıyor. Backend çalışıyor mu?'
    }
    return hata.message
  }
  return 'Beklenmeyen bir hata oluştu.'
}

export type { AlanHatalari }
