import type { Rol } from '@/types/api'

/** Rollerin Türkçe etiketleri — backend UserRole.choices ile senkron. */
export const ROL_ETIKETLERI: Record<Rol, string> = {
  super_admin: 'Süper Admin',
  tenant_admin: 'Tenant Admin',
  firma_admin: 'Firma Admin',
  muhasebe: 'Muhasebe',
  finans: 'Finans',
  proje_yoneticisi: 'Proje Yöneticisi',
  satis: 'Satış',
  santiye_sefi: 'Şantiye Şefi',
  maliyet_muhendisi: 'Maliyet Mühendisi',
  kullanici: 'Kullanıcı',
}
