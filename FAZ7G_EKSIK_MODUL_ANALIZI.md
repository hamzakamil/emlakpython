# FAZ 7G — EKSİK MODÜL ANALİZİ

**Tarih:** 2026-09-23 · **MOD:** analiz (kod YOK, migration YOK)

## Mekanik (neden böyle görünüyor)

- `AppLayout.vue`: `hazir:false` öğeler tıklanamaz "Yakında" span'i (5 İNŞAAT MALİYET
  maddesi bu yüzden güvenli — route'a gidilemez).
- İstisna: `Kütüphane.children` koşulsuz `RouterLink` render eder (`child.to || '#'`,
  `hazir` bakılmaz) → `Malzemeler` (`hazir:false`) tıklanabilir link üretir →
  router'da kayıt yok → catch-all `BulunamadiView` (404).
- Yan bulgu: bildirim linkleri `to:'/dashboard'` (`AppLayout.vue:83`) ama `/dashboard`
  route'u yok → ölü link (2. 404 kaynağı).

## 404 kök nedeni (`/insaat/malzemeler`)

- Vue route: YOK · component (`MalzemelerView.vue`): HİÇ OLUŞTURULMAMIŞ ·
  guard/import sorunu YOK (kayıt olmadığı için) · API 404 DEĞİL:
  `GET /api/v1/construction/malzemeler/` → 401 (auth kapısı = endpoint yaşıyor).
- Backend TAMAM: `Malzeme` model + `MalzemeViewSet` (CRUD) + migration.
- Yani: yalnızca frontend liste ekranı eksik.

## 5 "Yakında" analizi

| Sayfa | Nitelik | Backend karşılığı |
|---|---|---|
| Genel Bakış | bilinçli placeholder (tıklanamaz) | yok (Panel + Portföy/Nakit/KarZarar ayrı) |
| Metraj & Keşif | bilinçli placeholder; işlev dağınık mevcut | `Metraj` model + `/metrajlar/` + Mahal/IFC/AnalizKitabi ekranları |
| Maliyet Hesabı | bilinçli placeholder; işlev dağınık mevcut | maliyet motoru + YaklaşıkMaliyet + S-eğrisi/Gantt |
| Raporlar | bilinçli placeholder | NakitAkisi/KarZarar/Portföy/TeknikSartname ekranları ayrı |
| Ayarlar | bilinçli placeholder; HİÇ YAPILMAMIŞ | model/API yok (ürün kararı gerekir) |

## Sonuç tablosu (odak; geri kalan 29 link TAMAM)

| Menü | Route | Frontend | Backend | Durum | Eksik |
|---|---|---|---|---|---|
| Genel Bakış | /insaat/genel-bakis | yok | yok | PLACEHOLDER | şemsiye ekran |
| Metraj & Keşif | /insaat/metraj-kesif | yok | VAR (dağınık) | PLACEHOLDER | şemsiye ekran |
| Maliyet Hesabı | /insaat/maliyet-hesabi | yok | VAR (dağınık) | PLACEHOLDER | şemsiye ekran |
| Raporlar | /insaat/raporlar | yok | VAR (dağınık) | PLACEHOLDER | şemsiye ekran |
| Ayarlar | /insaat/ayarlar | yok | YOK | PLACEHOLDER | her şey (karar lazım) |
| Yapı Sınıfları | /insaat/yapi-sinifi | VAR | VAR | TAMAM | — |
| Pozlar | /insaat/pozlar | VAR | VAR | TAMAM | — |
| **Malzemeler** | /insaat/malzemeler | **YOK** | VAR | **404** | route + liste ekranı |
| Mahaller | /insaat/mahaller | VAR | VAR | TAMAM | — |
| (bildirim linki) | /dashboard | — | — | 404 (ölü link) | `to:'/'` olmalı |

Sayılar: toplam 38 menü linki → TAMAM 32 · PLACEHOLDER 5 · 404 1 (+1 ölü bildirim
linki). KISMEN: `ProjeMalzemeView` içindeki 2 "yakında" alert-butonu
(teklif-seçimi, tedarikçi-atama).

## FAZ ilişkisi

Roadmap Faz 1 malzeme kartı ☑ = backend; genel Malzeme liste ekranı hiçbir fazda
ayrı madde değil. 5 şemsiye ekran hiçbir faz/memory-bank kaydında taahhüt değil;
işlevleri 6A–6F'de farklı route'larla teslim edildi. Yani: yarım implementasyon
değil, menü-seviyesi bilinçli placeholder + 1 sehven tıklanabilir link.

## Öncelik

- **A (mutlaka):** `Malzemeler` 404 → 1 route + mevcut `MalzemeViewSet`'i kullanan
  liste ekranı (migration yok, backend hazır); bildirim `/dashboard` → `/`
  (1 satır).
- **B (sonraki):** Metraj & Keşif / Maliyet Hesabı şemsiye ekranları (mevcut
  parçaları toplayan görünüm), Genel Bakış (mevcut endpoint agregasyonu).
- **C (bırakılabilir):** Raporlar şemsiyesi, Ayarlar (önce ürün kararı + backend).

## Önerilen implementasyon sırası

Malzemeler ekranı → /dashboard linki → (B şemsiyeler) → (C karar sonrası).

## SON KARAR

**LOCAL RELEASE FREEZE KALDIRILMALI** — sınırlı kapsamla: yalnızca A maddesi
(ölü navigasyon kullanıcıya 404 gösteriyor). B/C freeze dışında planlanır.
Kod değişikliği bu fazda yapılmadı.
