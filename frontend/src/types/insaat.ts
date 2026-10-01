/**
 * İnşaat modülü tipleri — backend serializer'larıyla senkron
 * (construction/serializers.py, fields=__all__).
 */

export interface PozGrubu {
  id: number
  kod: string
  ad: string
  ust_grup: number | null
  is_active: boolean
}

/** Poz.PozTipi choices. */
export type PozTipi = 'yapim' | 'iscilik' | 'nakliye' | 'makine' | 'diger'

export interface Poz {
  id: number
  tenant: number
  poz_no: string
  ad: string
  birim: string
  grup: number
  tip: PozTipi
  is_active: boolean
  created_at: string
  updated_at: string
  /** read-only gösterim alanı (grup.kod) */
  grup_bilgisi: string
}

/** YapiSinifiBirimMaliyet — birim_maliyet JSON'da string olarak gelir (Decimal). */
export interface YapiSinifi {
  id: number
  sinif_kodu: string
  yil: number
  birim_maliyet: string
  is_active: boolean
  created_at: string
}

/** Proje.Durum choices. */
export type ProjeDurumu = 'teklif' | 'planlanan' | 'devam' | 'askida' | 'tamamlandi' | 'iptal'

export interface Proje {
  id: number
  proje_kodu: string
  ad: string
  durum: ProjeDurumu
  yapisinif_maliyet: number | null
  /** read-only gösterim alanı (yapisinif_maliyet.sinif_kodu) */
  yapisinif_kodu: string | null
  baslangic: string | null
  bitis: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

/** Yaklaşık maliyet başlığı — Decimal alanlar API'de string olarak gelir. */
export interface YaklasikMaliyet {
  id: number
  proje: number
  proje_kodu?: string
  yil: number
  ad: string
  aciklama: string
  versiyon: number
  onceki: number | null
  toplam_tutar: string
  is_active: boolean
  satirlar?: YaklasikMaliyetSatiri[]
  created_at?: string
  updated_at?: string
}

/** Yaklaşık maliyet poz satırı ve fiyat snapshot'ı. */
export interface YaklasikMaliyetSatiri {
  id: number
  tenant?: number
  yaklasik_maliyet: number
  poz: number
  poz_no?: string
  mahal: number | null
  miktar: string
  birim_fiyat_snapshot: string
  toplam_tutar: string
  satir_tutari?: string
  aciklama: string
  sira: number
  created_at?: string
  updated_at?: string
}

export interface Hatirlatma {
  id: number
  baslik: string
  aciklama: string
  ilgili_modul: string
  ilgili_kayit_id: number | null
  ilgili_kayit_tipi: string
  hatirlatma_tarihi: string
  seviye: 'kritik' | 'uyari' | 'bilgi'
  durum: 'bekliyor' | 'okundu' | 'tamamlandi' | 'iptal'
  tekrarlama_tipi: 'yok' | 'gunluk' | 'haftalik' | 'aylik'
  tekrarlama_gun: number
}

export interface HatirlatmaKurali {
  id: number
  ilgili_modul: string
  tetikleyici: string
  once_gun_sayisi: number
  seviye: Hatirlatma['seviye']
  aktif_mi: boolean
}

export type MahalTipi = 'oda' | 'salon' | 'mutfak' | 'banyo' | 'wc' | 'balkon' | 'koridor' | 'antre' | 'depo' | 'diger'
export type MahalElemaniTipi = 'doseme' | 'duvar' | 'tavan' | 'supurgelik' | 'kapi' | 'pencere' | 'dograma'
export interface MahalElemani {
  id: number
  mahal: number
  eleman_tipi: MahalElemaniTipi
  poz: number | null
  malzeme_aciklama: string
  sira: number
  aciklama: string
}
export interface Mahal {
  id: number
  proje: number
  blok: string
  kat: string
  mahal_no: string
  mahal_adi: string
  mahal_tipi: MahalTipi
  alan_m2: string
  cevre_m: string
  yukseklik_m: string
  aciklama: string
  is_active: boolean
  elemanlar?: MahalElemani[]
}
export const MAHAL_TIPLERI: Record<MahalTipi, string> = {
  oda: 'Oda', salon: 'Salon', mutfak: 'Mutfak', banyo: 'Banyo', wc: 'WC',
  balkon: 'Balkon', koridor: 'Koridor', antre: 'Antre', depo: 'Depo', diger: 'Diğer',
}
export const MAHAL_ELEMANI_TIPLERI: Record<MahalElemaniTipi, string> = {
  doseme: 'Döşeme', duvar: 'Duvar', tavan: 'Tavan', supurgelik: 'Süpürgelik',
  kapi: 'Kapı', pencere: 'Pencere', dograma: 'Doğrama',
}

export type AnalizTipi = 'malzeme' | 'iscilik' | 'makine' | 'nakliye' | 'diger'
export interface PozAnaliz {
  id: number
  poz: number
  satir_no: number
  malzeme: string
  birim: string
  miktar: string
  birim_fiyat: string
  tutar: string
  analiz_tipi: AnalizTipi
}
export interface NakliyeMesafe {
  id: number
  proje: number
  poz: number
  mesafe_km: string
  k_katsayisi: string
}

export type EKBDurumu = 'taslak' | 'basvuru' | 'inceleme' | 'onaylandi' | 'reddedildi' | 'yenileme'
export type EKBEnerjiSinifi = 'A+' | 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G'
export type EKBGecerlilikDurumu = 'tarih_yok' | 'suresi_doldu' | 'yaklasiyor' | 'gecerli'
export interface EKB {
  id: number
  proje: number
  proje_kodu?: string
  proje_adi?: string
  belge_no: string
  durum: EKBDurumu
  enerji_sinifi: EKBEnerjiSinifi | ''
  duzenlenme_tarihi: string | null
  gecerlilik_tarihi: string | null
  duzenleyen: string
  notlar: string
  dokuman_referansi: string
  is_active: boolean
  gecerlilik_durumu?: EKBGecerlilikDurumu
  kalan_gun?: number | null
  created_at?: string
  updated_at?: string
}
export const EKB_DURUMLARI: Record<EKBDurumu, string> = {
  taslak: 'Taslak', basvuru: 'Başvuru Yapıldı', inceleme: 'İncelemede',
  onaylandi: 'Onaylandı', reddedildi: 'Reddedildi', yenileme: 'Yenileme Gerekli',
}
export const EKB_ENERJI_SINIFLARI: Record<EKBEnerjiSinifi, string> = {
  'A+': 'A+', A: 'A', B: 'B', C: 'C', D: 'D', E: 'E', F: 'F', G: 'G',
}

export const POZ_TIPLERI: Record<PozTipi, string> = {
  yapim: 'Yapım',
  iscilik: 'İşçilik',
  nakliye: 'Nakliye',
  makine: 'Makine',
  diger: 'Diğer',
}

export const PROJE_DURUMLARI: Record<ProjeDurumu, string> = {
  teklif: 'Teklif Aşaması',
  planlanan: 'Planlanan',
  devam: 'İnşaat Devam Ediyor',
  askida: 'Askıda',
  tamamlandi: 'Tamamlandı',
  iptal: 'İptal',
}

/** PozPlan — proje/poz/yıl bazlı planlanan vs gerçekleşen metraj (Faz 2). */
export interface PozPlan {
  id: number
  proje: number
  poz: number
  yil: number
  /** Decimal alanlar JSON'da string olarak gelir (float yasak). */
  planlanan_miktar: string
  gercek_miktar: string
  /** Gantt zaman çizelgesi için planlanan tarihler (opsiyonel, ISO YYYY-MM-DD). */
  planlanan_baslangic: string | null
  planlanan_bitis: string | null
  /** Kayıt anındaki birim fiyat (değişmez; istemciden gönderilmez). */
  birim_fiyat_snapshot: string
  aciklama: string
  is_active: boolean
  created_at: string
  updated_at: string
  /** read-only gösterim alanları */
  poz_no: string
  grup_kodu: string
  plan_deger: string
  gercek_deger: string
}

/** Hesaplanmış metraj kaydı — /construction/metrajlar/. */
export interface Metraj {
  id: number
  ad: string
  metraj_tipi: string
  ifade: string
  sonuc: string
  birim: string
  aciklama: string
  is_active: boolean
  created_at: string
  updated_at: string
}

/** Kayıt oluşturmadan güvenli metraj önizlemesi yanıtı. */
export interface MetrajHesaplamaSonucu {
  sonuc: string
  birim: string
  metraj_tipi: string
  ifade?: string
}

export type IFCImportDurumu = 'queued' | 'processing' | 'completed' | 'failed'
export interface IFCQuantityDraft {
  id: number
  job: number
  project: number
  year: number
  poz: number | null
  poz_no: string | null
  source_name: string
  quantity: string
  unit: string
  mapping_status: 'mapped' | 'unmapped' | 'invalid'
  validation_message: string
}
export interface IFCImportJob {
  id: number
  project: number
  project_code?: string
  year: number
  file_name: string
  file_size: number
  status: IFCImportDurumu
  parser_mode: string
  processing_message: string
  validation_errors: string[]
  draft_rows: IFCQuantityDraft[]
  created_at: string
}

/** S-eğrisi rapor satırı — GET /construction/poz-planlari/s-egrisi/ */
export interface SEkgrisiSatiri {
  poz_no: string
  poz_ad: string
  grup_kodu: string | null
  planlanan_miktar: string
  gercek_miktar: string
  birim: string
  birim_fiyat: string
  plan_deger: string
  gercek_deger: string
  sapma_tutar: string
  sapma_yuzde: string
}

/** Poz bazlı planlanan/gerçekleşen maliyet karşılaştırma raporu (S-eğrisi). */
export interface SEkgrisiRaporu {
  proje_kodu: string
  yil: number
  toplam_plan_miktar: string
  toplam_gercek_miktar: string
  toplam_plan_deger: string
  toplam_gercek_deger: string
  toplam_sapma_tutar: string
  toplam_sapma_yuzde: string
  pozlar: SEkgrisiSatiri[]
}

export interface ProjeNakitAkisiAyi {
  donem: string
  planlanan_gider: string
  gerceklesen_gider: string
  gelir: string
  net: string
  kümülatif_net: string
}

export interface ProjeNakitAkisi {
  proje_kodu: string
  yil: number
  planlanan_gider: string
  gerceklesen_gider: string
  gelir: string
  net: string
  veri_notu: string
  aylar: ProjeNakitAkisiAyi[]
}

export interface ProjeKarZararPoz {
  poz_no: string
  poz_ad: string
  butce: string
  gerceklesen_metraj_degeri: string
  sapma: string
}

export interface ProjeKarZarar {
  proje_kodu: string
  yil: number
  butcelenen_maliyet: string
  gerceklesen_maliyet: string
  maliyet_sapmasi: string
  maliyet_sapmasi_yuzde: string
  gelir: string
  net_sonuc: string
  veri_notu: string
  pozlar: ProjeKarZararPoz[]
}

export interface PortfoyProjeSatiri {
  id: number
  proje_kodu: string
  proje_adi: string
  durum: string
  yapisinif_kodu: string | null
  butce: string
  gerceklesen: string
  sapma: string
  sapma_yuzde: string
  net_sonuc: string
}

export interface PortfoyKarsilastirma {
  yil: number
  proje_sayisi: number
  toplam_butce: string
  toplam_gerceklesen: string
  toplam_sapma: string
  toplam_net_sonuc: string
  veri_notu: string
  projeler: PortfoyProjeSatiri[]
}

export interface TeknikSartnameKalemi {
  poz_no: string
  poz_ad: string
  birim: string
  grup: string
  malzemeler: Array<{ kod: string; ad: string; birim: string; miktar: string; ts_no: string }>
}

export interface TeknikSartnameTaslagi {
  baslik: string
  proje_kodu: string
  proje_adi: string
  yil: number
  uretim_notu: string
  kalem_sayisi: number
  malzeme_sayisi: number
  kalemler: TeknikSartnameKalemi[]
  markdown: string
}

export type MetrajKontrolSeviyesi = 'kritik' | 'uyari' | 'bilgi'
export interface MetrajKontrolOnerisi {
  poz_no: string
  poz_ad: string
  seviye: MetrajKontrolSeviyesi
  kod: string
  mesaj: string
  onerilen_aksiyon: string
}
export interface MetrajKontrolRaporu {
  proje_kodu: string
  yil: number
  kontrol_edilen_poz: number
  kritik: number
  uyari: number
  bilgi: number
  oneriler: MetrajKontrolOnerisi[]
}

export interface FiyatAnomalisi {
  poz_no: string
  poz_ad: string
  yil: number
  seviye: 'kritik' | 'uyari'
  kod: string
  mevcut_fiyat: string
  referans_fiyat: string
  degisim_yuzde: string
  mesaj: string
  onerilen_aksiyon: string
}
export interface FiyatAnomaliRaporu {
  proje_kodu: string
  yil: number
  kontrol_edilen_poz: number
  kritik: number
  uyari: number
  anomaliler: FiyatAnomalisi[]
}

/** HakedisSatiri — poz + miktar + birim fiyat (tutar backend hesaplar). */
export interface HakedisSatiri {
  id?: number
  poz: number
  /** read-only gösterim alanı */
  poz_no?: string
  /** Decimal alanlar JSON'da string olarak gelir (float yasak). */
  miktar: string
  birim_fiyat: string
  /** read-only: miktar × birim_fiyat */
  satir_tutar?: string
}

/** Hakedis.Durum choices. */
export type HakedisDurumu = 'taslak' | 'onaylandi' | 'iptal'

export const HAKEDIS_DURUMLARI: Record<HakedisDurumu, string> = {
  taslak: 'Taslak',
  onaylandi: 'Onaylandı',
  iptal: 'İptal',
}

/** Hakedis — dönemsel hakediş (onay → Cari Hareket + Muhasebe Fişi). */
export interface Hakedis {
  id: number
  tenant: number
  proje: number
  proje_kodu?: string
  donem: string
  cari: number | null
  durum: HakedisDurumu
  aciklama: string
  cari_hareket: number | null
  muhasebe_fisi: number | null
  onaylayan: number | null
  onay_tarihi: string | null
  created_at: string
  updated_at: string
  satirlar: HakedisSatiri[]
  /** read-only: satır tutarları toplamı (string Decimal) */
  toplam_tutar: string
}

/** GanttCubugu — GET /construction/poz-planlari/gantt/ satırı (backend TypedDict). */
export interface GanttCubugu {
  id: number
  poz_no: string
  poz_ad: string
  grup_kodu: string | null
  yil: number
  baslangic: string | null
  bitis: string | null
  tarih_atandi: boolean
  planlanan_miktar: string
  gercek_miktar: string
  ilerleme_yuzde: string
  plan_deger: string
  gercek_deger: string
}

/** GanttRaporu — proje zaman çizelgesi + eksen aralığı. */
export interface GanttRaporu {
  proje_kodu: string
  proje_ad: string
  yil: number | null
  en_erken: string | null
  en_gec: string | null
  tarihsiz_sayi: number
  cubuklar: GanttCubugu[]
}

/** ContractTemplate — sözleşme şablonları (Phase 3). */
export interface ContractTemplate {
  id: number
  name: string
  type: string
  content: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface RiskStructure {
  id: number
  proje?: number | null
  risk_durumu: string
  aciklama: string
  son_durum_tarihi: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

/** LeaseAssistance — kira yardımı kayıtları (Phase 3). */
export interface LeaseAssistance {
  id: number
  proje: number
  proje_kodu?: string
  kira_yardim_id: string
  tahliye_sikligi: string
  aciklama: string
  banka_iban?: string
  banka_adi?: string
  odeme_notu?: string
  created_at: string
  updated_at: string
}

export interface Tedarikci {
  id: number
  firma_adi: string
  firma_kodu: string
  il?: string
  ilce?: string
  telefon?: string
  email?: string
  adres?: string
  is_active: boolean
}

export interface Malzeme {
  id: number
  malzeme_kodu: string
  ad: string
  birim: string
  ts_no?: string
  is_active: boolean
}

export interface MalzemeTedarikciIliskisi {
  id: number
  malzeme: number
  tedarikci: number
  miktar: string
  birim: string
  durum: string
  teslim_tarihi: string | null
  aciklama: string
}

export type TedarikciTeklifiDurumu =
  | 'taslak' | 'istendi' | 'geldi' | 'degerlendiriliyor' | 'kabul' | 'red' | 'iptal'

export interface TedarikciTeklifi {
  id: number
  proje: number
  malzeme: number
  tedarikci: number
  miktar: string
  birim_fiyat: string
  toplam_tutar: string
  durum: TedarikciTeklifiDurumu
  gecerlilik_tarihi: string | null
  notlar: string
  secildi: boolean
  is_active: boolean
  proje_kodu?: string
  proje_adi?: string
  malzeme_adi?: string
  malzeme_birimi?: string
  tedarikci_adi?: string
  created_at: string
  updated_at: string
}

/** PozFiyat — Poz birim fiyatı (yıl/dönem bazlı). */
export interface PozFiyat {
  id: number
  tenant: number
  poz: number
  /** Poz numarası ve adı (read-only, poz relation'dan) */
  poz_bilgisi?: string
  yil: number
  donem: string
  kaynak: string
  birim_fiyat: string
  kaynak_url: string
  yayin_tarihi: string | null
  gecerlilik_tarihi: string | null
  ice_aktarma_tarihi: string
  is_active: boolean
  created_at: string
  updated_at: string
}

/** ProjePozFiyat — Projeye özel poz birim fiyatı. */
export interface ProjePozFiyat {
  id: number
  tenant: number
  proje: number
  poz: number
  /** Poz numarası (read-only, poz relation'dan) */
  poz_no?: string
  /** Proje kodu (read-only, proje relation'dan) */
  proje_kodu?: string
  yil: number
  birim_fiyat: string
  kaynak: string
  kaynak_url: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TaseronSozlesi {
  id: number
  proje: number
  taseron_firma: string
  sosyal_unvan: string
  sicil_no: string
  tarih_baslangic: string
  tarih_bitis: string | null
  tutar: string
  durum: string
  aciklama: string
}

export interface KaliteKabulTeminati {
  id: number
  proje: number
  poz: number | null
  tarih: string
  kriter: string
  sonuc: string
  belge: string | null
  aciklama: string
}

/** FiyatSonucu — malzeme fiyat hesaplama sonucu (FAZ 2). */
export interface FiyatSonucu {
  fiyat: string | null
  kaynak: string
  kaynak_id: number | null
  para_birimi: string
}

/** ProjeMalzeme — proje seviyesinde malzeme tedarik ve teklif bilgisi (FAZ 2). */
export interface ProjeMalzeme {
  id: number
  tenant: number
  proje: number
  proje_kodu?: string
  malzeme: number
  malzeme_kodu?: string
  malzeme_adi?: string
  malzeme_birim?: string
  tedarikci: number | null
  tedarikci_adi?: string
  cari: number | null
  cari_adi?: string
  selected_teklif: number | null
  selected_teklif_id?: number
  selected_teklif_fiyat?: string
  kaynak: string
  kaynak_url: string
  is_active: boolean
  aciklama: string
  created_at: string
  updated_at: string
  /** read-only: etkin fiyat (malzeme_etkin_fiyati servisinden) */
  etkin_fiyat?: string | null
  /** read-only: etkin fiyat kaynağı */
  etkin_fiyat_kaynak?: string
}

/** ProjeMalzemeFiyat — proje bazlı malzeme yıl bazlı fiyatı (FAZ 2). */
export interface ProjeMalzemeFiyat {
  id: number
  tenant: number
  proje: number
  proje_kodu?: string
  malzeme: number
  malzeme_kodu?: string
  malzeme_adi?: string
  malzeme_birim?: string
  yil: number
  birim_fiyat: string
  para_birimi: 'TRY' | 'USD' | 'EUR'
  kaynak: string
  kaynak_url: string
  is_active: boolean
  created_at: string
  updated_at: string
}

/** ProjePozMalzeme — proje-poz seviyesinde malzeme alternatifi (FAZ 2). */
export interface ProjePozMalzeme {
  id: number
  tenant: number
  proje: number
  proje_kodu?: string
  poz: number
  poz_no?: string
  poz_adi?: string
  kaynak_malzeme: number
  kaynak_malzeme_kodu?: string
  kaynak_malzeme_adi?: string
  kaynak_malzeme_birim?: string
  etkin_malzeme: number
  etkin_malzeme_kodu?: string
  etkin_malzeme_adi?: string
  etkin_malzeme_birim?: string
  miktar_override: string | null
  aciklama: string
  is_active: boolean
  created_at: string
  updated_at: string
  /** read-only: etkin malzeme fiyatı */
  etkin_fiyat?: string | null
  /** read-only: etkin fiyat kaynağı */
  etkin_fiyat_kaynak?: string
}

/** MalzemeFiyat — genel tenant bazlı malzeme fiyatı (FAZ 2). */
export interface MalzemeFiyat {
  id: number
  tenant: number
  malzeme: number
  malzeme_kodu?: string
  malzeme_adi?: string
  malzeme_birim?: string
  yil: number
  birim_fiyat: string
  para_birimi: 'TRY' | 'USD' | 'EUR'
  kaynak: string
  kaynak_url: string
  is_active: boolean
  created_at: string
  updated_at: string
}
