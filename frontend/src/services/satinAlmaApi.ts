/**
 * FAZ 3A — Satın alma API istemcisi.
 * Desen: insaatApi crudFactory + aksiyon post'ları (hakedisOnayla benzeri).
 * Backend: /api/v1/purchase-requests/, /api/v1/purchase-orders/.
 */
import { del, get, patch, post } from '@/services/apiClient'
import type { Sayfali } from '@/types/api'
import type {
  Depo,
  MalKabul,
  MalKabulKalemi,
  SatinAlmaSiparisi,
  SatinAlmaTalebi,
  SiparisKalemi,
  StokHareketi,
  StokHesapEsleme,
  TalepKalemi,
} from '@/types/satinAlma'

function crudFactory<T>(kaynak: string) {
  return {
    liste: (params?: Record<string, unknown>) => get<Sayfali<T>>(kaynak, params),
    tek: (id: number) => get<T>(`${kaynak}${id}/`),
    olustur: (veri: Record<string, unknown>) => post<T>(kaynak, veri),
    guncelle: (id: number, veri: Record<string, unknown>) => patch<T>(`${kaynak}${id}/`, veri),
    sil: (id: number) => del<T>(`${kaynak}${id}/`),
  }
}

export const satinAlmaApi = {
  talepler: {
    ...crudFactory<SatinAlmaTalebi>('/purchase-requests/'),
    onayaGonder: (id: number) => post<SatinAlmaTalebi>(`/purchase-requests/${id}/onaya-gonder/`),
    onayla: (id: number) => post<SatinAlmaTalebi>(`/purchase-requests/${id}/onayla/`),
    reddet: (id: number) => post<SatinAlmaTalebi>(`/purchase-requests/${id}/reddet/`),
    iptalEt: (id: number) => post<SatinAlmaTalebi>(`/purchase-requests/${id}/iptal-et/`),
    taleptenSiparisOlustur: (id: number, veri: Record<string, unknown>) =>
      post<SatinAlmaSiparisi>(`/purchase-requests/${id}/talepten-siparis-olustur/`, veri),
  },
  talepKalemleri: crudFactory<TalepKalemi>('/purchase-request-items/'),
  siparisler: {
    ...crudFactory<SatinAlmaSiparisi>('/purchase-orders/'),
    onayaGonder: (id: number) => post<SatinAlmaSiparisi>(`/purchase-orders/${id}/onaya-gonder/`),
    onayla: (id: number) => post<SatinAlmaSiparisi>(`/purchase-orders/${id}/onayla/`),
    iptalEt: (id: number) => post<SatinAlmaSiparisi>(`/purchase-orders/${id}/iptal-et/`),
  },
  siparisKalemleri: crudFactory<SiparisKalemi>('/purchase-order-items/'),
  depolar: crudFactory<Depo>('/purchase-depolar/'),
  malKabuller: {
    ...crudFactory<MalKabul>('/purchase-mal-kabul/'),
    onayla: (id: number) => post<MalKabul>(`/purchase-mal-kabul/${id}/onayla/`),
    iptalEt: (id: number) => post<MalKabul>(`/purchase-mal-kabul/${id}/iptal-et/`),
  },
  malKabulKalemleri: crudFactory<MalKabulKalemi>('/purchase-mal-kabul-items/'),
  stokHareketleri: {
    liste: (params?: Record<string, unknown>) =>
      get<Sayfali<StokHareketi>>('/purchase-stok-hareketleri/', params),
    bakiye: (depo: number, malzeme?: number) =>
      get<{ depo: number; malzeme?: number; bakiye?: string; kalemler?: { malzeme_id: number; bakiye: string }[] }>(
        '/purchase-stok-hareketleri/stok-bakiye/', { depo, ...(malzeme ? { malzeme } : {}) },
      ),
    transferOlustur: (veri: Record<string, unknown>) =>
      post<{ cikis: StokHareketi; giris: StokHareketi }>('/purchase-stok-hareketleri/transfer-olustur/', veri),
    tuketimOlustur: (veri: Record<string, unknown>) =>
      post<StokHareketi>('/purchase-stok-hareketleri/tuketim-olustur/', veri),
    iadeOlustur: (veri: Record<string, unknown>) =>
      post<StokHareketi & { iade_fatura_no?: string | null; iade_fis_no?: string | null }>('/purchase-stok-hareketleri/iade-olustur/', veri),
  },
  stokHesapEsleme: crudFactory<StokHesapEsleme>('/purchase-stok-hesap-esleme/'),
}
