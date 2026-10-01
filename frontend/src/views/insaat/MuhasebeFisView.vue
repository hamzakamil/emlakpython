<template>
  <div class="container mt-4">
    <h2 class="mb-4">Genel Muhasebe Fişleri</h2>
    <p class="lead text-muted">Tüm finansal işlemlerin kaynağıdır. Borç toplamı, Alacak toplamına eşit olmalıdır. Fişler, fiziksel olarak silinmez; sadece 'iptal' edilir.</p>

    <!-- Yeni Fiş Ekle Butonu -->
    <button @click="openModal(true)" class="btn btn-primary mb-4">
      Yeni Muhasebe Fişi Oluştur
    </button>

    <!-- Fiş Listesi -->
    <div class="card shadow-sm">
      <div class="card-header bg-light">
        Muhasebe Fişleri Listesi (Toplam: {{ fisler.length }})
      </div>
      <div class="card-body table-responsive">
        <table class="table table-hover table-bordered">
          <thead class="table-light">
            <tr v-pre>
              <th class="col-sm-1">ID</th>
              <th class="col-sm-2">Tarih</th>
              <th class="col-sm-3">Açıklama</th>
              <th class="col-sm-2">Borç Toplam</th>
              <th class="col-sm-2">Alacak Toplam</th>
              <th class="col-sm-2">İşlemler</th>
            </tr>
          </thead>
          <tbody v-if="fisler.length > 0">
            <tr v-for="item in fisler" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ formatDate(item.olusturma_tarihi) }}</td>
              <td>{{ item.aciklama }}</td>
              <td class="text-danger">{{ formatCurrency(item.borc_toplam) }}</td>
              <td class="text-success">{{ formatCurrency(item.alacak_toplam) }}</td>
              <td>
                <button @click="openModal(false, item)" class="btn btn-sm btn-info me-2">Düzenle</button>
                <button @click="deleteItem(item.id)" class="btn btn-sm btn-danger">İptal Et</button>
              </td>
            </tr>
          </tbody>
          <tbody v-else>
            <tr class="text-center">
              <td colspan="6" class="text-muted p-3">Henüz muhasebe fişi bulunmamaktadır.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Component (Fiş Oluşturma/Düzenleme) -->
    <div v-if="isModalOpen" class="modal fade show" style="display: block" tabindex="-1" aria-labelledby="muhasebeFisModalLabel" aria-modal="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="muhasebeFisModalLabel">{{ isEditing ? 'Muhasebe Fişini Düzenle' : 'Yeni Muhasebe Fişi Oluştur' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitFis">
              <!-- Ana Fiş Bilgileri -->
              <div class="row mb-4">
                <div class="col-md-6 mb-3">
                  <label for="fis_tarihi" class="form-label">Tarih</label>
                  <input type="date" class="form-control" id="fis_tarihi" v-model="form.tarih" required />
                </div>
                <div class="col-md-6 mb-3">
                  <label for="aciklama" class="form-label">Açıklama</label>
                  <textarea class="form-control" id="aciklama" v-model="form.aciklama" rows="2" required></textarea>
                </div>
              </div>
              
              <hr>
              <h5 class="mb-3">Hesap Satırları (Detay)</h5>
              <div class="border p-3 mb-4">
                <!-- Satır Ekleme Alanı -->
                <div class="row mb-3">
                  <div class="col-md-4">
                    <label for="hesap_id" class="form-label">Hesap Planı</label>
                    <select class="form-select" v-model="form.satirlar[0].hesap_id" required></select>
                  </div>
                  <div class="col-md-2">
                    <label for="borc_tutar_satir" class="form-label">Borç (TL)</label>
                    <input type="number" step="0.01" v-model.number="form.satirlar[0].borc_tutar" class="form-control" required />
                  </div>
                  <div class="col-md-2">
                    <label for="alacak_tutar_satir" class="form-label">Alacak (TL)</label>
                    <input type="number" step="0.01" v-model.number="form.satirlar[0].alacak_tutar" class="form-control" required />
                  </div>
                  <div class="col-md-4">
                    <button type="button" @click="addRow" class="btn btn-sm btn-outline-primary me-2">
                      + Satır Ekle
                    </button>
                  </div>
                </div>
                
                <!-- Satır Listesi -->
                <div v-for="(satir, index) in form.satirlar" :key="index" class="row mb-3 p-2 border rounded bg-light">
                    <div class="col-md-4">
                        <select class="form-select" v-model="satir.hesap_id" required>
                            <option value="" disabled>Hesap Seçiniz</option>
                            <!-- Options loaded from API -->
                        </select>
                    </div>
                    <div class="col-md-2">
                        <input type="number" step="0.01" v-model.number="satir.borc_tutar" class="form-control" required />
                    </div>
                    <div class="col-md-2">
                        <input type="number" step="0.01" v-model.number="satir.alacak_tutar" class="form-control" required />
                    </div>
                    <div class="col-md-2">
                        <button type="button" @click="removeRow(index)" class="btn btn-sm btn-warning">
                          - Sil
                        </button>
                    </div>
                </div>
              </div>

              <div class="text-end">
                <p>Toplam Borç: <span class="text-danger fw-bold">{{ formatCurrency(totalBorc) }}</span> | Toplam Alacak: <span class="text-success fw-bold">{{ formatCurrency(totalAlacak) }}</span></p>
                <button type="submit" :disabled="Math.abs(totalBorc - totalAlacak) > 0.01" class="btn btn-success" :class="{ 'disabled': Math.abs(totalBorc - totalAlacak) > 0.01 }">
                  Kaydet (Borç = Alacak)
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MuhasebeFisView',
  data() {
    return {
      isModalOpen: false,
      isEditing: false,
      form: {
        tarih: new Date().toISOString().substring(0, 10),
        aciklama: '',
        satirlar: [{
          hesap_id: '',
          borc_tutar: 0.00,
          alacak_tutar: 0.00
        }]
      }
    };
  },
  computed: {
    // Hesap Planı seçeneklerini API'den çekmeli.
    // ...
    totalBorc() {
      return this.form.satirlar.reduce((sum, satir) => sum + satir.borc_tutar, 0);
    },
    totalAlacak() {
      return this.form.satirlar.reduce((sum, satir) => sum + satir.alacak_tutar, 0);
    }
  },
  methods: {
    openModal(isCreate, item = null) {
      // Logic to populate form based on item or reset for new
      this.isEditing = !isCreate;
      // Reset form data structure
      this.form.satirlar = [{ hesap_id: '', borc_tutar: 0.00, alacak_tutar: 0.00 }];
      this.isModalOpen = true;
    },
    closeModal() {
      this.isModalOpen = false;
    },
    addRow() {
      this.form.satirlar.push({
        hesap_id: '',
        borc_tutar: 0.00,
        alacak_tutar: 0.00
      });
    },
    removeRow(index) {
      if (this.form.satirlar.length > 1) {
        this.form.satirlar.splice(index, 1);
      } else {
        alert('En az bir muhasebe satırı olmalıdır.');
      }
    },
    async submitFis() {
      // 1. Borç = Alacak kontrolü (UI'da zaten yapılmış)
      if (Math.abs(this.totalBorc - this.totalAlacak) > 0.01) {
        alert('Hata: Muhasebe fişi dengesiz. Toplam Borç, Toplam Alacak\'a eşit olmalıdır.');
        return;
      }
      // 2. API Çağrısı
      try {
        // TODO: API call for /api/v1/accounting/fisler/
        await this.$api.post('/api/v1/accounting/fisler/', {
          tarih: this.form.tarih,
          aciklama: this.form.aciklama,
          satirlar: this.form.satirlar
        });
        alert('Muhasebe fişi başarıyla oluşturuldu.');
        this.closeModal();
        this.$emit('refresh-list');
      } catch (error) {
        alert('İşlem başarısız oldu. Lütfen hata mesajını kontrol edin.');
      }
    }
  },
  mounted() {
    // Simulate initial data loading
    this.$emit('show-modal');
  }
}
</script>
<style scoped>
/* Component specific styles */
</style>