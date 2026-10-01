import { describe, expect, it } from 'vitest'
import { satinAlmaYazabilirMi, yazabilirMi } from './yetki'

describe('yazabilirMi', () => {
  it('editor roller yazabilir', () => {
    expect(yazabilirMi('maliyet_muhendisi')).toBe(true)
    expect(yazabilirMi('proje_yoneticisi')).toBe(true)
    expect(yazabilirMi('tenant_admin')).toBe(true)
    expect(yazabilirMi('super_admin')).toBe(true)
    expect(yazabilirMi('firma_admin')).toBe(true)
  })

  it('saha ve salt-okur roller yazamaz; finans rolleri yazabilir', () => {
    expect(yazabilirMi('santiye_sefi')).toBe(false)
    expect(yazabilirMi('satis')).toBe(false)
    expect(yazabilirMi('kullanici')).toBe(false)
    expect(yazabilirMi('muhasebe')).toBe(true)
    expect(yazabilirMi('finans')).toBe(true)
  })

  it('bos rol yazamaz', () => {
    expect(yazabilirMi(undefined)).toBe(false)
    expect(yazabilirMi(null)).toBe(false)
  })
})

describe('satinAlmaYazabilirMi', () => {
  it('satinalma editor rolleri yazabilir', () => {
    expect(satinAlmaYazabilirMi('maliyet_muhendisi')).toBe(true)
    expect(satinAlmaYazabilirMi('proje_yoneticisi')).toBe(true)
    expect(satinAlmaYazabilirMi('tenant_admin')).toBe(true)
    expect(satinAlmaYazabilirMi('super_admin')).toBe(true)
    expect(satinAlmaYazabilirMi('firma_admin')).toBe(true)
  })

  it('finans/muhasebe satinalmada yazamaz (FAZ 6C SoD)', () => {
    expect(satinAlmaYazabilirMi('muhasebe')).toBe(false)
    expect(satinAlmaYazabilirMi('finans')).toBe(false)
    expect(satinAlmaYazabilirMi('santiye_sefi')).toBe(false)
    expect(satinAlmaYazabilirMi('satis')).toBe(false)
    expect(satinAlmaYazabilirMi('kullanici')).toBe(false)
    expect(satinAlmaYazabilirMi(undefined)).toBe(false)
    expect(satinAlmaYazabilirMi(null)).toBe(false)
  })
})
