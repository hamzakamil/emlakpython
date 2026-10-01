/**
 * İnşaat modülü API servisi — /api/v1/construction/ kaynakları.
 * Tüm yanıtlar apiClient tarafından zarf açılarak döner.
 */
import { del, get, patch, post } from './apiClient'
import type { Sayfali } from '@/types/api'
import type {
  GanttRaporu,
  Hakedis,
  ContractTemplate,
  LeaseAssistance,
  RiskStructure,
  KaliteKabulTeminati,
  MalzemeTedarikciIliskisi,
  Malzeme,
  MalzemeFiyat,
  Poz,
  PozGrubu,
  PozPlan,
  PozFiyat,
  ProjePozFiyat,
  Proje,
  ProjeMalzeme,
  ProjeMalzemeFiyat,
  ProjePozMalzeme,
  ProjeNakitAkisi,
  MetrajKontrolRaporu,
  Metraj,
  MetrajHesaplamaSonucu,
  FiyatAnomaliRaporu,
  ProjeKarZarar,
  PortfoyKarsilastirma,
  TeknikSartnameTaslagi,
  SEkgrisiRaporu,
  TaseronSozlesi,
  Tedarikci,
  TedarikciTeklifi,
  YapiSinifi,
  EKB,
  PozAnaliz,
  NakliyeMesafe,
  Mahal,
  MahalElemani,
  YaklasikMaliyet,
  YaklasikMaliyetSatiri,
  Hatirlatma,
  HatirlatmaKurali,
} from '@/types/insaat'
import type { KaliteKontrol } from '@/types/saha'

/** Sayfalı kaynağı sayfa sayfa gezerek tüm kayıtları toplar (select listeleri için). */
export async function tumunuGetir<T>(
  liste: (params?: Record<string, unknown>) => Promise<Sayfali<T>>,
  baslangicParametreleri: Record<string, unknown> = {},
): Promise<T[]> {
  const hepsi: T[] = []
  let sayfa = 1
  // Güvenlik üst sınırı: 20 sayfa (500 kayıt) — tekilleştirme listeleri için yeterli.
  for (;;) {
    const veri = await liste({ ...baslangicParametreleri, page: sayfa })
    hepsi.push(...veri.results)
    if (!veri.next || sayfa >= 20) break
    sayfa += 1
  }
  return hepsi
}

function crudFactory<T>(kaynak: string) {
  return {
    liste: (params?: Record<string, unknown>) => get<Sayfali<T>>(kaynak, params),
    tek: (id: number) => get<T>(`${kaynak}${id}/`),
    olustur: (veri: Record<string, unknown>) => post<T>(kaynak, veri),
    guncelle: (id: number, veri: Record<string, unknown>) => patch<T>(`${kaynak}${id}/`, veri),
    sil: (id: number) => del<T>(`${kaynak}${id}/`),
  }
}

export const insaatApi = {
  pozGruplari: crudFactory<PozGrubu>('/construction/poz-gruplari/'),
  pozlar: crudFactory<Poz>('/construction/pozlar/'),
  pozFiyatlari: crudFactory<PozFiyat>('/construction/poz-fiyatlari/'),
  projePozFiyatlari: crudFactory<ProjePozFiyat>('/construction/proje-poz-fiyatlari/'),
  yapiSinifi: crudFactory<YapiSinifi>('/construction/yapi-sinifi-birim-maliyetleri/'),
  projeler: crudFactory<Proje>('/construction/projeler/'),
  pozPlanlari: crudFactory<PozPlan>('/construction/poz-planlari/'),
  metrajlar: {
    ...crudFactory<Metraj>('/construction/metrajlar/'),
    hesapla: (veri: Record<string, unknown>) =>
      post<MetrajHesaplamaSonucu>('/construction/metrajlar/hesapla/', veri),
  },
  pozAnalizleri: {
    ...crudFactory<PozAnaliz>('/construction/poz-analizleri/'),
    toplam: (poz: number) => get<{ poz: number; toplam: string }>('/construction/poz-analizleri/poz-toplam/', { poz }),
  },
  nakliyeMesafeleri: crudFactory<NakliyeMesafe>('/construction/nakliye-mesafeleri/'),
  hakedisler: crudFactory<Hakedis>('/construction/hakedisler/'),
  mahaller: {
    ...crudFactory<Mahal>('/construction/mahaller/'),
    elemanlar: (id: number) => get<MahalElemani[]>(`/construction/mahaller/${id}/elemanlar/`),
    elemanOlustur: (id: number, veri: Record<string, unknown>) =>
      post<MahalElemani>(`/construction/mahaller/${id}/elemanlar/`, veri),
    elemanSil: (mahalId: number, elemanId: number) =>
      del<MahalElemani>(`/construction/mahaller/${mahalId}/elemanlar/${elemanId}/`),
  },
  yaklasikMaliyetler: {
    ...crudFactory<YaklasikMaliyet>('/construction/yaklasik-maliyetler/'),
    hesapla: (id: number) => post<YaklasikMaliyet>(`/construction/yaklasik-maliyetler/${id}/hesapla/`),
    revize: (id: number, veri: { ad?: string; aciklama?: string }) =>
      post<YaklasikMaliyet>(`/construction/yaklasik-maliyetler/${id}/revize/`, veri),
    mahalListesindenOlustur: (id: number) =>
      post<YaklasikMaliyet>(`/construction/yaklasik-maliyetler/${id}/mahal-listesinden-olustur/`),
  },
  yaklasikMaliyetSatirlari: crudFactory<YaklasikMaliyetSatiri>('/construction/yaklasik-maliyet-satirlari/'),
  hatirlatmalar: {
    ...crudFactory<Hatirlatma>('/construction/hatirlatmalar/'),
    gunluk: () => get<Hatirlatma[]>('/construction/hatirlatmalar/gunluk/'),
    uret: () => post<{ uretilen: number }>('/construction/hatirlatmalar/uret/'),
  },
  hatirlatmaKurallari: crudFactory<HatirlatmaKurali>('/construction/hatirlatma-kurallari/'),
  mahalSablondanOlustur: (projeId: number, veri: Record<string, unknown>) =>
    post<{ mahal: Mahal; elemanlar: MahalElemani[] }>(`/construction/projeler/${projeId}/mahal-sablondan-olustur/`, veri),
  tedarikciler: crudFactory<Tedarikci>('/construction/tedarikciler/'),
  malzemeler: crudFactory<Malzeme>('/construction/malzemeler/'),
  malzemeTedarikciIliskileri: crudFactory<MalzemeTedarikciIliskisi>('/construction/malzeme-tedarikci-iliskileri/'),
  tedarikciTeklifleri: {
    ...crudFactory<TedarikciTeklifi>('/construction/tedarikci-teklifleri/'),
    kazananSec: (id: number) =>
      post<TedarikciTeklifi>(`/construction/tedarikci-teklifleri/${id}/kazanan-sec/`),
  },

  // FAZ 2 — Projeye Özel Malzeme Sistemi
  projeMalzemeler: {
    ...crudFactory<ProjeMalzeme>('/construction/proje-malzemeler/'),
    teklifSec: (id: number, teklifId: number) =>
      post<ProjeMalzeme>(`/construction/proje-malzemeler/${id}/teklif-sec/`, { teklif_id: teklifId }),
    tedarikciAta: (id: number, tedarikciId: number) =>
      post<ProjeMalzeme>(`/construction/proje-malzemeler/${id}/tedarikci-ata/`, { tedarikci_id: tedarikciId }),
  },
  projeMalzemeFiyatlari: crudFactory<ProjeMalzemeFiyat>('/construction/proje-malzeme-fiyatlari/'),
  projePozMalzemeler: crudFactory<ProjePozMalzeme>('/construction/proje-poz-malzemeler/'),
  malzemeFiyatlari: crudFactory<MalzemeFiyat>('/construction/malzeme-fiyatlari/'),
  taseronSozlesi: crudFactory<TaseronSozlesi>('/construction/taseron-sozlesmeleri/'),
  kaliteKabulTeminati: crudFactory<KaliteKabulTeminati>('/construction/kalite-kabul-teminatlari/'),
  kaliteKontrolleri: crudFactory<KaliteKontrol>('/construction/kalite-kontrolleri/'),
  contractTemplates: crudFactory<ContractTemplate>('/construction/contract-templates/'),
  riskStructures: crudFactory<RiskStructure>('/construction/risk-structures/'),
  leaseAssistances: crudFactory<LeaseAssistance>('/construction/lease-assistances/'),
  ekb: {
    ...crudFactory<EKB>('/construction/ekb/'),
    arsivdenCikar: (id: number) => post<EKB>(`/construction/ekb/${id}/arsivden-cikar/`),
    ozet: (params?: Record<string, unknown>) =>
      get<{ toplam: number; onayli: number; suresi_dolan: number; otuz_gun_icinde: number }>(
        '/construction/ekb/ozet/', params,
      ),
  },

  /** Poz bazlı planlanan/gerçekleşen maliyet karşılaştırma (S-eğrisi) raporu. */
  sEgrisi: (projeId: number, yil: number) =>
    get<SEkgrisiRaporu>('/construction/poz-planlari/s-egrisi/', { proje: projeId, yil }),

  /** İş kalemi (poz) bazlı zaman çizelgesi — yıl verilmezse tüm yıllar gelir. */
  gantt: (projeId: number, yil?: number) =>
    get<GanttRaporu>('/construction/poz-planlari/gantt/', {
      proje: projeId,
      ...(yil ? { yil } : {}),
    }),
  nakitAkisi: (projeId: number, yil: number) =>
    get<ProjeNakitAkisi>('/construction/poz-planlari/nakit-akisi/', { proje: projeId, yil }),
  karZarar: (projeId: number, yil: number) =>
    get<ProjeKarZarar>('/construction/poz-planlari/kar-zarar/', { proje: projeId, yil }),
  metrajKontrolu: (projeId: number, yil: number) =>
    get<MetrajKontrolRaporu>('/construction/poz-planlari/metraj-kontrolu/', { proje: projeId, yil }),
  fiyatAnomalileri: (projeId: number, yil: number) =>
    get<FiyatAnomaliRaporu>('/construction/poz-planlari/fiyat-anomalileri/', { proje: projeId, yil }),
  portfoyOzeti: (params: { yil: number; arama?: string; durum?: string; sinif?: string }) =>
    get<PortfoyKarsilastirma>('/construction/projeler/portfoy-ozeti/', params),
  teknikSartname: (projeId: number, yil: number) =>
    get<TeknikSartnameTaslagi>('/construction/projeler/teknik-sartname/', { proje: projeId, yil }),

  /** Taslak hakedişe, poz planlarındaki gerçekleşen metrajdan satır üretir. */
  hakedisSatirlariUret: (id: number) =>
    post<{ eklenen_satir: number; hakedis: Hakedis }>(
      `/construction/hakedisler/${id}/satirlari-olustur/`,
    ),

  /** Taslak hakedişi onaylar → Cari Hareket + Muhasebe Fişi üretir (backend). */
  hakedisOnayla: (id: number) => post<Hakedis>(`/construction/hakedisler/${id}/onayla/`),

  /** Fiziksel silme yok — taslak hakediş iptale çekilir (backend destroy). */
  hakedisIptal: (id: number) => del<Hakedis>(`/construction/hakedisler/${id}/`),
}
