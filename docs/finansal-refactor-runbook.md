# Finansal Bütünlük Refactor Runbook

Bu runbook bakım modu ile yürütülen kademeli geçiş içindir. Eski kayıtlar
otomatik olarak değiştirilmez.

## Bakım modu öncesi

1. Uygulamayı yazma trafiğine kapatın veya finansal endpoint'leri devre dışı
   bırakın.
2. PostgreSQL yedeğini alın ve geri dönüş testini doğrulayın.
3. `finansal_mutabakat --format json` çıktısını saklayın.
4. `manage.py check` ve hedef testleri çalıştırın.
5. Mevzuat danışmanından iptal/iade faturası akışını yazılı olarak onaylatın.

## Faz 0 ve baseline

```powershell
C:\proje\emlakpython\.venv\Scripts\python.exe manage.py finansal_mutabakat --format json > baseline.json
```

Komut read-only'dir. Fatura, cari hareket, finansal işlem veya muhasebe fişi
oluşturmaz.

## Shadow muhasebeleştirme

Eski faturalar yalnızca kullanıcı tarafından açıkça tetiklenir:

```http
POST /api/v1/finance/faturalar/{id}/shadow-muhasebelestir/
Idempotency-Key: fatura-{id}-shadow-1
```

Bu endpoint gerçek `MuhasebeFisi` oluşturmaz; `FinansalOlay` ve satırlarını
oluşturur. Aynı anahtar tekrar kullanılırsa aynı sonuç döner.

## Durum geçişi

```http
POST /api/v1/finance/faturalar/{id}/durum-gecis/
Idempotency-Key: fatura-{id}-aktif-1
{
  "durum": "aktif"
}
```

Geçiş matrisi:

```text
taslak -> aktif, iptal
aktif  -> odendi, iptal
odendi -> iptal
iptal  -> geçiş yok
```

## Outbox

Outbox olayları transaction içinde yazılır. Worker/cron çalıştırıcısı
`process_outbox_events()` fonksiyonunu kullanmalı; handler bulunmayan olaylar
retry sonrasında dead-letter olarak bırakılmalıdır. Dead-letter kayıtları
silinmez, manuel inceleme kuyruğunda tutulur.

## Faz 6 eski veri uyarlaması

1. Baseline ve yeni raporları karşılaştırın.
2. Her fatura için cari/muhasebe eşleşmesini manuel onaylayın.
3. Belirsiz kayıtları ayrı kuyruğa alın.
4. Kullanıcı onayı olmadan backfill çalıştırmayın.
5. Düzeltmeyi fiziksel silme yerine ters kayıtla yapın.

## Geri dönüş

- Yeni migration'ları geri almak için önce uygulamayı yazma trafiğine kapatın.
- Outbox ve finansal olay kayıtlarını silmeyin; önce raporlayın.
- Geri dönüş kararı DBA ve mali sorumlu tarafından birlikte alınmalıdır.
