<template>
  <div class="container mt-4">
    <h2 class="mb-4">Kasa & Banka Hareketleri</h2>
    <p class="lead text-muted">Şirketin tüm nakit akışlarını (gelir, gider, transfer) yönetir. Her işlem bir kaynağa (Kasa/Banka) ve bir amaca (Gider/Gelir) bağlanır. Tüm işlemler iptal edilemez, sadece ters kayıt (muhasebe yoluyla) oluşturulur.</p>

    <!-- Yeni İşlem Ekle Butonu -->
    <button @click="openModal(true)" class="btn btn-primary mb-4">
      Yeni Finansal İşlem Kaydı Ekle
    </button>

    <!-- İşlem Listesi -->
    <div class="card shadow-sm">
      <div class="card-header bg-light">
        Son Finansal İşlemler
      </div>
      <div class="card-body table-responsive">
        <table class="table table-hover table-bordered">
          <thead class="table-light">
            <tr v-pre>
              <th class="col-sm-1">ID</th>
              <th class="col-sm-2">Tarih</th>
              <th class="col-sm-3">Açıklama</th>
              <th class="col-sm-2">Kaynak</th>
              <th class="col-sm-2">Borç (TL)</th>
              <th class="col-sm-2">Alacak (TL)</th>
              <th class="col-sm-2">İşlemler</th>
            </tr>
          </thead>
          <tbody v-if="finansIslemler.length > 0">
            <tr v-for="item in finansIslemler" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ formatDate(item.tarih) }}</td>
              <td>{{ item.aciklama }}</td>
              <td>{{ item.kaynak_tip }} ({{ item.kaynak_ad }})</td>
              <td class="text-danger">{{ formatCurrency(item.borc_tutar) }}</td>
              <td class="text-success">{{ formatCurrency(item.alacak_tutar) }}</td>
              <td>
                <button @click="openModal(false, item)" class="btn btn-sm btn-info me-2">Düzenle</button>
                <button @click="deleteItem(item.id)" class="btn btn-sm btn-danger">İptal Et</button>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr class="text-center">
              <td colspan="7" class="text-muted p-3">Henüz finansal işlem kaydedilmemiştir.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Component (İşlem Oluşturma/Düzenleme) -->
    <div v-if="isModalOpen" class="modal fade show" style="display: block" tabindex="-1" aria-labelledby="finansIslemModalLabel" aria-modal="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="finansIslemModalLabel">{{ isEditing ? 'İşlemi Düzenle' : 'Yeni Finansal İşlem Kaydı Oluştur' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitIslem">
              <!-- Temel Bilgiler -->
              <div class="mb-3">
                <label for="tarih" class="form-label">İşlem Tarihi</label>
                <input type="date" class="form-control" id="tarih" v-model="form.tarih" required />
              </div>
              <div class="mb-3">
                <label for="aciklama" class="form-label">Açıklama</label>
                <textarea class="form-control" id="aciklama" v-model="form.aciklama" rows="2" required></textarea>
              </div>

              <hr>
              <h5 class="mb-3">İşlem Detayı (Borç/Alacak)</h5>
              <div class="row mb-3">
                <div class="col-md-6 mb-3">
                  <label for="kaynak_tip" class="form-label">İşlem Kaynağı</label>
                  <select class="form-select" id="kaynak_tip" v-model="form.kaynak_tip" required>
                    <option value="kasa">Şirket Kasası</option>
                    <option value="banka">Banka Hesapları</option>
                    <!-- TODO: Diğer hesaplar eklenecek -->
                  </select>
                </div>
                <div class="col-md-3 mb-3">
                  <label for="kaynak_ad" class="form-label">Kaynak/Hesap</label>
                  <select class="form-select" id="kaynak_ad" v-model="form.kaynak_ad" required></select>
                </div>
              </div>

              <div class="row mb-3">
                <div class="col-md-4">
                  <label for="borc_tutar" class="form-label">Borç Tutar (TL)</label>
                  <input type="number" step="0.01" class="form-control" id="borc_tutar" v-model.number="form.borc_tutar" required />
                </div>
                <div class="col-md-4">
                  <label for="alacak_tutar" class="form-label">Alacak Tutar (TL)</label>
                  <input type="number" step="0.01" class="form-control" id="alacak_tutar" v-model.number="form.alacak_tutar" required />
                </div>
              </div>

              <div class="text-end">
                <p>Toplam Borç: <span class="text-danger fw-bold">{{ formatCurrency(totalBorc) }}</span> | Toplam Alacak: <span class="text-success fw-bold">{{ formatCurrency(totalAlacak) }}</span></p>
                <button type="submit" :disabled="Math.abs(totalBorc - totalAlacak) > 0.01" class="btn btn-success" :class="{ 'disabled': Math.abs(totalBorc - totalAlacak) > 0.01 }">
                  Kaydet
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div >
</template>

<script>
export default {
  name: 'FinansalIslemView',
  data() {
    return {
      isModalOpen: false,
      isEditing: false,
      form: {
        tarih: new Date().toISOString().substring(0, 10),
        aciklama: '',
        kaynak_tip: 'kasa',
        kaynak_ad: 'Ana Kasa',
        borc_tutar: 0.00,
        alacak_tutar: 0.00
      }
    };
  },
  computed: {
    ...mapGetters(['finansIslemler']),
    totalBorc() {
      return this.form.borc_tutar;
    },
    totalAlacak() {
      return this.form.alacak_tutar;
    }
  },
  methods: {
    openModal(isCreate, item = null) {
      this.isEditing = !isCreate;
      if (item) {
        this.form = {
          tarih: item.tarih,
          aciklama: item.aciklama,
          kaynak_tip: item.kaynak_tip,
          kaynak_ad: item.kaynak_ad,
          borc_tutar: item.borc_tutar,
          alacak_tutar: item.alacak_tutar
        };
      } else {
        // Reset for new entry
        this.form = {
          tarih: new Date().toISOString().substring(0, 10),
          aciklama: '',
          kaynak_tip: 'kasa',
          kaynak_ad: 'Ana Kasa',
          borc_tutar: 0.00,
          alacak_tutar: 0.00
        };
      }
      this.isModalOpen = true;
    },
    closeModal() {
      this.isModalOpen = false;
    },
    async submitIslem() {
      if (Math.abs(this.totalBorc - this.totalAlacak) > 0.01) {
        alert('Hata: Finansal işlem borç ve alacak toplamları birbirine eşit olmalıdır.');
        return;
      }
      // TODO: API call for /api/v1/finance/islemler/
      try {
        await this.$api.post('/api/v1/finance/islemler/', this.form);
        alert('İşlem başarıyla kaydedildi.');
        this.closeModal();
        this.$emit('refresh-list');
      } catch (error) {
        alert('İşlem başarısız oldu. API hatasını kontrol edin.');
      }
    }
  }
}
</script>
<style scoped>
/* Component specific styles */
</style>