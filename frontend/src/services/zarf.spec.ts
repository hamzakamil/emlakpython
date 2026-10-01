import { describe, expect, it } from 'vitest'
import { ApiHatasi, zarfAc } from './zarf'

describe('zarfAc', () => {
  it('başarılı zarfın data alanını döndürür', () => {
    const sonuc = zarfAc({ success: true, data: { a: 1 }, message: 'İşlem başarılı.' }, 200)
    expect(sonuc).toEqual({ a: 1 })
  })

  it('success=false durumunda ApiHatasi fırlatır ve hataları taşır', () => {
    const govde = {
      success: false,
      data: null,
      message: 'Muhasebe fişinde borç ve alacak eşit olmalıdır.',
      errors: { debit: ['Bu alan gerekli.'] },
    }
    try {
      zarfAc(govde, 400)
      expect.unreachable('ApiHatasi fırlamalıydı')
    } catch (bilinmeyen) {
      expect(bilinmeyen).toBeInstanceOf(ApiHatasi)
      const hata = bilinmeyen as ApiHatasi
      expect(hata.durum).toBe(400)
      expect(hata.message).toBe('Muhasebe fişinde borç ve alacak eşit olmalıdır.')
      expect(hata.hatalar).toEqual({ debit: ['Bu alan gerekli.'] })
    }
  })

  it('zarf dışı yanıt reddedilir', () => {
    expect(() => zarfAc({ mesaj: 'garip' }, 200)).toThrow(/zarf/)
  })
})
