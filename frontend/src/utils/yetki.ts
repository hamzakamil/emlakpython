import type { Rol } from '@/types/api'

/**
 * Yazma yetkisi — backend construction/permissions.py EDITOR_ROLES ile senkron.
 * Şantiye şefi + satış + kullanıcı salt okur; diğer roller yazar.
 * (muhasebe/finans: finans ve cari modüllerinde yazar.)
 */
const YAZAR_ROLLER: Rol[] = [
  'super_admin',
  'tenant_admin',
  'firma_admin',
  'maliyet_muhendisi',
  'proje_yoneticisi',
  'muhasebe',
  'finans',
]

/**
 * Satın alma yazma yetkisi — backend purchasing/permissions.py EDITOR_ROLES
 * ile senkron (FAZ 6C SoD: finans/muhasebe satın almada yazamaz/onaylayamaz).
 */
const SATINALMA_YAZAR_ROLLER: Rol[] = [
  'super_admin',
  'tenant_admin',
  'firma_admin',
  'maliyet_muhendisi',
  'proje_yoneticisi',
]

export function yazabilirMi(rol: Rol | undefined | null): boolean {
  if (!rol) return false
  return YAZAR_ROLLER.includes(rol)
}

export function satinAlmaYazabilirMi(rol: Rol | undefined | null): boolean {
  if (!rol) return false
  return SATINALMA_YAZAR_ROLLER.includes(rol)
}
