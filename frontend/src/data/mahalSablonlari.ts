import type { MahalElemaniTipi } from '@/types/insaat'

export interface MahalSablonu {
  ad: string
  mahal_tipi: string
  elemanlar: Array<{ eleman_tipi: MahalElemaniTipi; malzeme_aciklama: string }>
}

export const MAHAL_SABLONLARI: MahalSablonu[] = [
  {
    ad: 'Standart Yatak Odası',
    mahal_tipi: 'oda',
    elemanlar: [
      { eleman_tipi: 'doseme', malzeme_aciklama: 'Laminat parke' },
      { eleman_tipi: 'duvar', malzeme_aciklama: 'Saten alçı ve iç cephe boyası' },
      { eleman_tipi: 'tavan', malzeme_aciklama: 'Plastik boya' },
      { eleman_tipi: 'supurgelik', malzeme_aciklama: 'MDF süpürgelik' },
    ],
  },
  {
    ad: 'Standart Banyo',
    mahal_tipi: 'banyo',
    elemanlar: [
      { eleman_tipi: 'doseme', malzeme_aciklama: 'Seramik döşeme' },
      { eleman_tipi: 'duvar', malzeme_aciklama: 'Seramik duvar kaplaması' },
      { eleman_tipi: 'tavan', malzeme_aciklama: 'Neme dayanıklı boya' },
      { eleman_tipi: 'kapi', malzeme_aciklama: 'Ahşap iç kapı' },
    ],
  },
]
