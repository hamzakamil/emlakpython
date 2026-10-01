/**
 * Kayıt formu composable'ı — liste ekranlarındaki oluşturma/düzenleme
 * modal akışını tekleştirir (modal aç/kapat, kaydet, hata).
 */
import { ref } from 'vue'
import { hataMesaji } from '@/services/apiClient'

interface CrudKaynak<T> {
  olustur: (veri: Record<string, unknown>) => Promise<T>
  guncelle: (id: number, veri: Record<string, unknown>) => Promise<T>
}

export function useKayitFormu<TKayit extends { id: number }, TForm extends object>(
  kaynak: CrudKaynak<TKayit>,
  bosForm: () => TForm,
  formaDoldur: (kayit: TKayit) => TForm,
  formaVeri: (form: TForm) => Record<string, unknown>,
  dogrula: (form: TForm) => string,
) {
  const modalAcik = ref(false)
  const duzenlenen = ref<TKayit | null>(null)
  const form = ref<TForm>(bosForm())
  const formHata = ref('')
  const kaydediliyor = ref(false)

  function yeniAc(): void {
    duzenlenen.value = null
    form.value = bosForm()
    formHata.value = ''
    modalAcik.value = true
  }

  function duzenleAc(kayit: TKayit): void {
    duzenlenen.value = kayit
    form.value = formaDoldur(kayit)
    formHata.value = ''
    modalAcik.value = true
  }

  async function kaydet(yenile: () => Promise<void>): Promise<void> {
    formHata.value = dogrula(form.value)
    if (formHata.value) return
    kaydediliyor.value = true
    try {
      const veri = formaVeri(form.value)
      if (duzenlenen.value) await kaynak.guncelle(duzenlenen.value.id, veri)
      else await kaynak.olustur(veri)
      modalAcik.value = false
      await yenile()
    } catch (bilinmeyen) {
      formHata.value = hataMesaji(bilinmeyen)
    } finally {
      kaydediliyor.value = false
    }
  }

  return { modalAcik, duzenlenen, form, formHata, kaydediliyor, yeniAc, duzenleAc, kaydet }
}
