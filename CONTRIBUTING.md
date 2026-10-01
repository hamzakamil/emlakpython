# Contribution Guide (Katkıda Bulunma Rehberi)

Bu proje, multi-tenant, modüler bir ERP/SaaS yapısını temsil etmektedir. Yeni özellikler eklerken veya bug fix yaparken aşağıdaki kurallar ve adımlar takip edilmelidir.

## 🛠️ Geliştirme Ortamı Kurulumu (Setup)
1. **Bağımlılıklar:** Öncelikle sanal ortamı aktive edin ve tüm bağımlılıkları kurun.
   ```bash
   source .venv/bin/activate # Linux/macOS
   .venv\Scripts\activate    # Windows
   pip install -r requirements.txt
   ```
2. **Veritabanı Migrasyonu:** Uygulama şemasını güncelleyin. (Not: Bu aşama, temel Django Auth şemalarının da çalışır durumda olmasını gerektirir.)
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
3. **Frontend:** Vue/Vuex state'leri için gerekli tüm modüllerin tanımlandığından emin olun.

## 🚀 Yeni Özellik Ekleme (Feature Development)
1. **Domain Model:** Yeni iş kurallarını `construction/models.py` dosyasına yansıtın. Her model, `TenantAwareModel` miras almalıdır.
2. **Validation/Business Logic:** Model bazında iş kuralları (constraint'ler, custom clean methods) **önce** tanımlanmalıdır.
3. **Serializer:** Yeni model için `construction/serializers.py`'de bir serializer oluşturun.
4. **ViewSet:** Yeni iş akışını yönetecek bir `TenantScopedViewSet` oluşturun ve gerekli `search_fields`/`filterset_fields`'leri ekleyin.
5. **URL Routing:** `construction/urls.py` dosyasına yeni bir `router.register` çağrısı ekleyin.
6. **Frontend View:** İlgili modül için Vue bileşenini (`.vue`):
    *   **State Management:** Vuex/Pinia store'da ilgili state/action'ları tanımlayın.
    *   **Components:** CRUD operasyonlarını yöneten View bileşenini (`.vue`) oluşturun.
    *   **Router:** `frontend/src/router/index.ts` dosyasına yeni yolu ve bileşen referansını ekleyin.

## 🐛 Bug Fix ve Refactoring
*   **Test Önceliği:** Bir şeyi değiştirmeden önce, ilgili modül için bir test yazın (Unit/Integration). Test geçmiyorsa, kodunuzun sorunu çözün.
*   **Code Review:** Değişiklikleriniz bir Pull Request (PR) olarak açılmadan önce, bir meslektaşınızdan kontrol geçmesini talep edin.

## ⚠️ Kritik Kurallar
*   **UTF-8 Zorunluluğu:** Tüm verilerde (kullanıcı girişi, açıklama, dosya içeriği) Türkçe karakterler ve UTF-8 kullanılmalıdır.
*   **Multi-Tenancy:** Tüm CRUD operasyonları `tenant_id` üzerinden izole edilmelidir.
*   **Kod Kalitesi:** Tüm viewset'ler `TenantScopedViewSet` yapısını korumalıdır.
