/**
 * Kimlik servisi — POST /api/v1/auth/token/ (simplejwt, tenant claim'li) +
 * GET /auth/me + GET /tenants/ (yalnızca süper admin, seçici listesi).
 */
import { get, post } from './apiClient'
import type { Kullanici, Sayfali, TenantSecim, TokenCevap } from '@/types/api'

export async function girisYap(username: string, password: string): Promise<TokenCevap> {
  return await post<TokenCevap>('/auth/token/', { username, password })
}

export async function beniGetir(): Promise<Kullanici> {
  return await get<Kullanici>('/auth/me/')
}

export async function sifreDegistir(veri: { mevcut_sifre: string; yeni_sifre: string; yeni_sifre_tekrar: string }): Promise<{ detail: string }> {
  return await post<{ detail: string }>('/auth/password/change/', veri)
}

export async function tenantListesiniGetir(): Promise<TenantSecim[]> {
  const sayfa = await get<Sayfali<TenantSecim>>('/tenants/')
  return sayfa.results
}

