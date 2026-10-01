# Emlak ERP - Başlatma Scriptleri

Bu klasörde projeyi hızlıca başlatmak için hazır scriptler bulunmaktadır.

## 📁 Dosyalar

| Dosya | Açıklama | Platform |
|-------|----------|----------|
| `baslat.bat` | Gelişmiş Batch scripti (menülü, loglama, bağımlılık kontrolü) | Windows |
| `baslat.ps1` | Modern PowerShell scripti (renkli, background job, graceful shutdown) | Windows |
| `baslat2.bat` | Eski basit batch scripti | Windows |

## 🚀 Hızlı Başlangıç

### Seçenek 1: PowerShell (Önerilen - En özellikli)
```powershell
# İzin ver (ilk kez)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Çalıştır
.\baslat.ps1
```

### Seçenek 2: Batch (Basit)
```cmd
baslat.bat
```

### Seçenek 3: Parametreli çalıştırma (PowerShell)
```powershell
# Aynı pencerede (varsayılan)
.\baslat.ps1 -Mode BothSame

# Ayrı pencerelerde
.\baslat.ps1 -Mode BothSeparate

# Sadece Backend
.\baslat.ps1 -Mode BackendOnly

# Sadece Frontend
.\baslat.ps1 -Mode FrontendOnly

# Portları temizle
.\baslat.ps1 -Mode CleanPorts

# Bağımlılıkları kontrol et
.\baslat.ps1 -Mode CheckDeps

# Farklı portlar
.\baslat.ps1 -BackendPort 8001 -FrontendPort 3001
```

## 🎯 Modlar

| Mod | Açıklama | Kullanım Alanı |
|-----|----------|----------------|
| **BothSame** | Her iki servis aynı pencerede (background job + foreground) | Geliştirme, logları takip etmek için |
| **BothSeparate** | Her servis ayrı pencerede | Üretim benzeri test, çoklu monitör |
| **BackendOnly** | Sadece Django API | API geliştirme, test |
| **FrontendOnly** | Sadece Vite | UI geliştirme, hot reload |
| **CleanPorts** | 8000, 3000-3002 portlarını temizle | Port çakışması olursa |
| **CheckDeps** | Python/Node/venv/npm bağımlılıklarını kontrol et/kur | İlk kurulum, CI/CD |

## 📋 Özellikler (baslat.ps1)

- ✅ **Bağımlılık kontrolü**: Python, Node.js, venv, pip, npm
- ✅ **Otomatik kurulum**: Eksik bağımlılıkları kurar
- ✅ **Port temizleme**: Eski süreçleri otomatik öldürür
- ✅ **Loglama**: `logs/backend.log`, `logs/frontend.log`
- ✅ **Graceful shutdown**: `Ctrl+C` ile her iki servis de düzgün kapanır
- ✅ **Renkli çıktı**: PowerShell'de renkli loglar
- ✅ **Parametreli**: CI/CD ve otomasyon için uygun

## 🌐 Erişim Adresleri (Varsayılan)

| Servis | URL |
|--------|-----|
| Backend API | http://localhost:8000 |
| Django Admin | http://localhost:8000/admin/ |
| API Docs (Swagger) | http://localhost:8000/api/schema/swagger-ui/ |
| Frontend | http://localhost:3000 |

## 🔧 Sorun Giderme

### "Running scripts is disabled" hatası (PowerShell)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
# veya
powershell -ExecutionPolicy Bypass -File .\baslat.ps1
```

### Port zaten kullanımda
```powershell
.\baslat.ps1 -Mode CleanPorts
# veya
baslat.bat -> Seçenek 5
```

### Bağımlılık hataları
```powershell
.\baslat.ps1 -Mode CheckDeps
# veya
baslat.bat -> Seçenek 6
```

### Sanal ortam sorunları
```cmd
# Manuel temizleme
rmdir /s .venv
# Sonra baslat.bat/baslat.ps1 tekrar çalıştır (yeniden oluşturur)
```

## 📝 Log Dosyaları

- `logs/backend.log` - Django sunucu logları
- `logs/frontend.log` - Vite sunucu logları

Canlı izleme:
```powershell
Get-Content logs\backend.log -Wait
Get-Content logs\frontend.log -Wait
```

## 🛠️ Geliştirme İpuçları

1. **Hot Reload**: Her iki sunucuda da kod değişikliklerinde otomatik yenileme var
2. **Debug**: Backend için VS Code launch.json kullanın, Frontend için Vue DevTools
3. **Database**: `python manage.py migrate` ve `python manage.py createsuperuser` unutmayın
4. **Static Files**: `python manage.py collectstatic` (production için)

## 📦 Gereksinimler

- **Python** 3.10+
- **Node.js** 18+
- **PostgreSQL** (docker-compose.yml ile: `docker compose up -d db`)
- **Redis** (opsiyonel, cache/celery için)

---

**Not**: İlk çalıştırmada bağımlılıkların indirilmesi birkaç dakika sürebilir.