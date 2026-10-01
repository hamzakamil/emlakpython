# SON HAL — BROWSER E2E RAPORU

**Tarih:** 2026-09-23 · **MOD:** çalıştır + test (kod değişikliği YOK)
**KARAR: GO** (tek kozmetik not: favicon 404)

## Ortam

- Backend: `python manage.py runserver 127.0.0.1:8000` → `/api/v1/health/` true.
- Frontend: proje yöntemi npm (`package-lock.json`), `vite` dev server :3000.
  Not: Vite bu makinede yalnızca IPv6 `::1` dinledi (`127.0.0.1` reddedildi) —
  testler `http://localhost:3000` üzerinden koştu. Proxy `/api → localhost:8000`
  sorunsuz çalıştı (tüm API 200).
- Browser: sistem Chrome + Temp dizininde `playwright-core` (repo'ya kurulmadı).
  Kullanıcı: `smoke-finans` (tenant 175 "Smoke Finans", rol finans).
- Kanıtlar: `.../Temp/opencode/e2e/sonuc.json` + `shots/` (26 ekran görüntüsü).

## Test edilen ekranlar (13 + login, 2 viewport)

`/giris`, `/`, `/cari/cariler`, `/cari/hareketler`, `/finans/faturalar`,
`/finans/faturalar/1`, `/satinalma/talepler`, `/satinalma/siparisler`,
`/satinalma/mal-kabuller`, `/satinalma/stok-hareketleri`, `/satinalma/stok-durumu`,
`/muhasebe/hesap-plani`, `/muhasebe/fisler`, `/muhasebe/mizan`.

## Başarılı akışlar

- Login → `/` yönlenmesi; reload sonrası oturum korundu (tekrar login gerekmedi).
- Tenant bağlamı tüm ekranlarda ("Smoke Finans"); fatura detayı gerçek kayıt
  (SMOKE-FAT-001, onarılan kolonlar dahil) ile render oldu.
- Kritik akışlar 6/6: login, cari, fatura, satınalma, mal kabul, stok görüntüleme.
- API URL'leri relative `/api/v1` (koda uygun); CORS sorunu yok (same-origin).

## Console / Network / Auth

- `console.error`: 1 adet — `/favicon.ico` 404 (projede favicon yok; kozmetik).
- Uncaught exception: 0. Failed request: 0. 4xx/5xx (otantikli akış): 0.
- Yetkisiz `GET /api/v1/cari/cariler/` → **401** (kapı çalışıyor).
- Token: "beni hatırla" kapalı olduğundan sessionStorage'da tutuldu
  (localStorage boş olması normal); 401'de tek-seferlik refresh interceptor
  kodda mevcut (`apiClient.ts`), akışta tetiklenmedi (access geçerliydi).
- 403: akışta karşılaşılmadı (okuma rollerine uygun menü); satın alma SoD
  backend testleriyle kapsamlı (71 test).

## Responsive

1920x1080 ve 1366x768: 13/13 ekranda yatay taşma YOK (ölçüldü:
`scrollWidth == innerWidth`). Ekran görüntüleri incelendi, kırılma yok.

## Kritik bulgular

1. favicon 404 (kozmetik; kod değişikliği yapılmadı, raporlandı).
2. Vite IPv6-only dinleme bu makinede (ortam notu; prod build'i etkilemez).
3. Hata görülmediğinden kod değişikliği yapılmadı (talimata uygun).

## GO / NO-GO: GO
