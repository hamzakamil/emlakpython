# Emlak + Muhasebe + Finans Multitenant SaaS — Nihai Teknoloji Stack

> Bu dosya projenin bağlayıcı teknoloji kararlarını içerir. Yeni bir modül veya
> bağımlılık eklenmeden önce burası referans alınmalıdır.

| Katman                 | Nihai seçim                                          | Neden seçiyoruz?                                                      |
| ----------------------- | ----------------------------------------------------- | ------------------------------------------------------------------- |
| **Frontend**           | Vue 3 + TypeScript                                    | Modern, hızlı, öğrenmesi/geliştirmesi kolay, tip güvenliği           |
| **UI / CSS**           | Tailwind CSS                                          | Hızlı arayüz geliştirme, Vue ile çok uyumlu                          |
| **State Management**   | Pinia                                                  | Vue 3 için standart ve sade state yönetimi                           |
| **Backend**            | Python + Django                                       | ERP, muhasebe, kullanıcı, yetki ve multitenant yapı için güçlü       |
| **API**                | Django REST Framework (DRF)                           | Vue ile temiz REST API mimarisi                                      |
| **Veritabanı**         | PostgreSQL                                             | ACID, transaction, ilişkisel veri, JSONB, RLS; muhasebe için ideal   |
| **ORM**                | Django ORM                                             | Django ile tamamen entegre, karmaşık ilişkiler için yeterli          |
| **Şema Yönetimi**      | Elle SQL — `db/schema.sql` (pg_dump)                     | Migration kullanılmaz; şema tek dosyada version-controllu tutulur    |
| **Authentication**     | JWT + Refresh Token                                    | SPA + multitenant yapı için uygun                                    |
| **Yetkilendirme**      | RBAC + Django Permissions                              | Süper Admin → Tenant Admin → Firma Admin → Kullanıcı vb.             |
| **Multitenancy**       | Shared DB + `tenant_id` + PostgreSQL RLS               | Başlangıç/orta ölçek için maliyet ve performans açısından dengeli    |
| **Muhasebe**           | Çift taraflı muhasebe motoru                           | Borç = Alacak kuralını sistem seviyesinde korur                      |
| **Cache**              | Başlangıçta yok → Redis                                | Gereksiz erken karmaşıklıktan kaçınırız                              |
| **Background Jobs**    | Başlangıçta Django → Celery + Redis gerektiğinde       | E-fatura, rapor, bildirim vb. ağır işlemler için                     |
| **Dosya / Fotoğraf**   | S3 uyumlu Object Storage                               | Emlak fotoğrafları, belgeler ve ekler için                           |
| **API Dokümantasyonu** | OpenAPI / Swagger                                      | Frontend ve entegrasyon geliştirmesini kolaylaştırır                 |
| **Test**               | Pytest + Django Test                                   | Backend güvenilirliği                                                |
| **Frontend Test**      | Vitest + Vue Test Utils                                | Vue bileşenlerinin testi                                             |
| **Deployment**         | Docker + Ubuntu VPS                                    | Başlangıç ve orta ölçek için yeterli                                 |
| **Web Server / Proxy** | Nginx                                                  | Reverse proxy, SSL, statik dosyalar                                  |
| **SSL**                | Let's Encrypt                                          | Ücretsiz HTTPS                                                       |
| **Versiyon kontrolü**  | Git + GitHub                                           | Kod yönetimi ve CI/CD                                                |
| **CI/CD**              | GitHub Actions                                         | Otomatik test/deploy                                                 |
| **Loglama**            | Python logging + merkezi log yapısı                    | Hata ve işlem takibi                                                 |
| **Monitoring**         | Başlangıçta basit → Sentry                             | Hataları üretimde takip etmek                                        |
| **Ana veri yaklaşımı** | PostgreSQL merkezli                                    | Muhasebe + ERP + Emlak verilerini tek güvenilir kaynakta tutmak      |

---

## Diğer md dosyalarıyla ilişki

Bu proje **sıfırdan Django + PostgreSQL üzerine** kurulacağı için, referans olarak
incelenen eski/paralel projelerdeki (Node.js + Express tabanlı) kod düzeyindeki
detaylar (Express route dosyaları vb.) buraya taşınmamıştır. Onun yerine o projelerden çıkarılan **kavramsal veri modeli,
iş akışları ve kurallar**, bu stack'e uyarlanmış şekilde aşağıdaki dosyalarda yer alır:

- `01-GELISTIRME-KURALLARI.md`
- `02-VERI-MODELI.md`
- `03-IS-AKISLARI.md`
- `04-API-VE-ROLLER.md`
- `05-RAPORLAMA-VE-AI.md`
- `06-ILHAM-OZELLIKLER.md`
