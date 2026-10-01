# İlham Alınabilecek Genel SaaS Özellikleri

> Kaynak: **Tamamen farklı bir proje** — bir İK/personel yönetim SaaS'ının
> (Node.js/Express tabanlı) ilerleme kayıtları. Emlak/muhasebe alanıyla
> doğrudan ilgisi yoktur; burada sadece **genel multi-tenant SaaS pattern'leri**
> olarak, ileride değerlendirilmek üzere referans amacıyla listelenmiştir.
> Bu dosyadaki hiçbir madde proje kapsamına otomatik dahil değildir.

---

## 1. Kayıt / Onboarding Akışları

- **Bayi/Firma Self-Registration:** Firma kendi kendine kayıt olabiliyor
  (`register-dealer` benzeri endpoint) → firma + kullanıcı + kayıt talebi
  tek işlemde, hata halinde rollback ile oluşturuluyordu.
- **Onboarding Wizard:** Yeni kayıt olan admin kullanıcıyı adım adım
  (kart tabanlı hub + step bileşeni) temel kurulum adımlarından geçiren
  bir sihirbaz; tamamlanmadan bazı sayfalara "kuruluma dön" banner'ı
  ile yönlendirme yapılıyordu.
- **Kayıt Talebi Onay Akışı:** Admin panelinden gelen kayıt taleplerinin
  (tip bazlı: firma/bayi) onaylanması veya reddedilmesi, onaylanınca
  ilgili kayıtların otomatik aktive edilmesi.

**Emlak projesi için olası karşılığı:** Yeni tenant/firma kaydı sırasında
benzer bir self-service kayıt + onay akışı ve ilk kurulum sihirbazı
(hesap planı seçimi, ilk gayrimenkul/tenant ayarları) düşünülebilir.

---

## 2. Bildirim ve Gerçek Zamanlı İletişim

- Uygulama içi bildirim merkezi (tip bazlı: talep, onay, hatırlatma vb.)
- Gerçek zamanlı bildirim için WebSocket (Socket.IO) entegrasyonu
- Push notification (FCM) entegrasyonu (mobil/tarayıcı)
- Kullanıcı bildirim tercihleri (hangi bildirimi almak istediğini seçebilme)

**Emlak projesi için olası karşılığı:** `03-IS-AKISLARI.md` Bölüm 4'te
tanımlanan hatırlatıcı akışı, ileri fazda Django Channels + web push ile
gerçek zamanlı hale getirilebilir.

---

## 3. Denetim, Güvenlik ve Uyumluluk

- **Audit Log modeli:** İşlem tipi, TTL (örn. 2 yıl saklama), KVKK/GDPR
  uyumluluğu için anonimleştirme mekanizması, admin panelinde audit log
  görüntüleme sayfası.
- Login denetimi (audit trail).

**Emlak projesi için olası karşılığı:** `01-GELİŞTİRME-KURALLARI.md` Bölüm 5'te
tanımlanan audit log zaten zorunlu; buradaki **TTL + KVKK anonimleştirme**
detayı doğrudan alınabilir — özellikle T.C. Kimlik/IBAN gibi hassas
alanların belirli bir süre sonra anonimleştirilmesi.

---

## 4. Altyapı ve DevOps

- Docker multi-stage build (backend + frontend ayrı servisler)
- CI/CD pipeline: lint → test → build → deploy (GitHub Actions benzeri)
- Otomatik yedekleme scripti: gzip, disk kontrolü, günlük/aylık retention,
  hata durumunda webhook bildirimi
- Restore scripti: interaktif, pre-restore güvenlik yedeği, doğrulama adımı
- Performans: response compression, frontend bundle'ı vendor bazlı
  chunk'lara ayırma (vendor-vue/vendor-utils vb.), lazy loading

**Emlak projesi için olası karşılığı:** Nihai stack'te zaten Docker +
GitHub Actions + Nginx var (`00-TEKNOLOJI-STACK.md`); buradaki **backup/
restore script deseni** ve **CI pipeline adımları** doğrudan örnek alınabilir.

---

## 5. Kod Kalitesi Altyapısı

- Standart API response formatı + merkezi response helper utility
- Global error handler middleware + custom error sınıfları
  (`NotFoundError`, `ForbiddenError` vb.)
- Async handler wrapper (try/catch tekrarını önlemek için)
- Şema bazlı validation middleware (Joi benzeri; Django'da DRF
  serializer + `django-rest-framework` validators karşılığı)
- Test altyapısı: unit + integration + E2E (backend: Pytest,
  frontend: Vitest, E2E: Playwright)

**Emlak projesi için olası karşılığı:** Bu madde zaten
`01-GELİŞTİRME-KURALLARI.md` Bölüm 6-7'de ve `00-TEKNOLOJI-STACK.md`'de
(Pytest, Vitest) karşılanıyor; ek olarak **Playwright ile E2E test**
eklenmesi değerlendirilebilir.

---

## Özet

Bu dosyadaki maddeler **doğrudan bir gereksinim değil, esin kaynağıdır.**
Proje MVP'sinde önceliklendirme yapılırken `01-GELİŞTİRME-KURALLARI.md`
Bölüm 11'deki karar önceliği (veri güvenliği → finansal doğruluk → tenant
izolasyonu → ... → kod estetiği) esas alınmalı, buradaki "hoş olur"
özellikler ancak çekirdek emlak + muhasebe + finans modülleri stabil
olduktan sonra değerlendirilmelidir.
