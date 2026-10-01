<template>
  <div class="container mt-4">
    <h2>Cari Hareket Kayıtları</h2>
    <p class="text-muted">Bu alanda, bir cari hesabın (müşteri/tedarikçi) zaman içindeki tüm borç ve alacak hareketleri izlenir. Her hareket, bir fatura, ödeme veya avans ile ilişkilidir.</p>

    <div class="row">
      <div class="col-12 mt-4">
        <button @click="openModal(true)" class="btn btn-primary" @click.prevent="$emit('show-modal')">
          Yeni Hareket Kaydı Ekle
        </button>
      </div>
    </div>

    <div class="card mt-4 shadow-sm">
      <div class="card-header">
        Hareket Listesi
      </div>
      <div class="card-body table-responsive">
        <table class="table table-hover table-bordered">
          <thead class="table-light">
            <tr v-pre>
              <th class="col-sm-2">Hareket ID</th>
              <th class="col-sm-3">Tarih</th>
              <th class="col-sm-3">Açıklama</th>
              <th class="col-sm-2">Borç (TL)</th>
              <th class="col-sm-2">Alacak (TL)</th>
              <th class="col-sm-2">İşlemler</th>
            </tr>
          </thead>
          <tbody v-if="cariHareketler.length > 0">
            <tr v-for="item in cariHareketler" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ formatDate(item.olusturma_tarihi) }}</td>
              <td>{{ item.aciklama }}</td>
              <td class="text-danger">{{ formatCurrency(item.borc_tutar) }}</td>
              <td class="text-success">{{ formatCurrency(item.alacak_tutar) }}</td>
              <td>
                <button @click="openModal(false, item)" class="btn btn-sm btn-info me-2">Düzenle</button>
                <button @click="deleteItem(item.id)" class="btn btn-sm btn-danger">Sil</button>
              </td>
            </tr>
          <tbody v-else>
            <tr class="text-center">
              <td colspan="6" class="text-muted p-3">Kayıt bulunmamaktadır.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Component -->
    <div v-if="isModalOpen" class="modal fade show" style="display: block" tabindex="-1" aria-labelledby="cariHareketModalLabel" aria-modal="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="cariHareketModalLabel">{{ isEditing ? 'Hareket Kaydını Düzenle' : 'Yeni Hareket Kaydı Ekle' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitRelation">
              <div class="mb-3">
                <label for="cari_id" class="form-label">Cari Hesap</label>
                <select class="form-select" id="cari_id" v-model="form.cari_id" required></select>
              </div>
              <div class="mb-3">
                <label for="aciklama" class="form-label">Açıklama</label>
                <textarea class="form-control" id="aciklama" v-model="form.aciklama" rows="3" required></textarea>
              </div>
              <div class="mb-3">
                <label for="borc_tutar" class="form-label">Borç Tutarı (TL)</label>
                <input type="number" step="0.01" class="form-control" id="borc_tutar" v-model.number="form.borc_tutar" required />
              </div>
              <div class="mb-3">
                <label for="alacak_tutar" class="form-label">Alacak Tutarı (TL)</label>
                <input type="number" step="0.01" class="form-control" id="alacak_tutar" v-model.number="form.alacak_tutar" required />
              </div>
              <button type="submit" class="btn btn-success mt-3">{{ isEditing ? 'Güncelle' : 'Kaydet' }}</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div >
</template>

<script>
import { mapGetters } from 'vuex';
// Varsayım: useApi, formatters ve Vuex store yapısı mevcut.
export default {
  name: 'CariHareketView',
  props: {
    showModal: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isModalOpen: this.showModal,
      isEditing: false,
      form: {
        cari_id: '',
        aciklama: '',
        borc_tutar: 0.00,
        alacak_tutar: 0.00
      }
    };
  },
  computed: {
    ...mapGetters(['cariHareketler']),
  },
  methods: {
    openModal(isCreate, item = null) {
      this.isEditing = !isCreate;
      this.form = {
        cari_id: isCreate ? '' : item.cari_id,
        aciklama: isCreate ? '' : item.aciklama,
        borc_tutar: isCreate ? 0.00 : item.borc_tutar,
        alacak_tutar: isCreate ? 0.00 : item.alacak_tutar
      };
      this.isModalOpen = true;
    },
    closeModal() {
      this.isModalOpen = false;
    },
    getStatusClass(durum) {
      // Bu modül için kullanmıyorum, ama yapıyı koruyalım.
    },
    async submitRelation() {
      if (!this.form.cari_id || !this.form.aciklama || this.form.borc_tutar < 0 || this.form.alacak_tutar < 0) {
        alert('Lütfen cari ID, açıklama ve pozitif tutarlar giriniz.');
        return;
      }
      // *** API CALL SIMULATION ***
      try {
        // TODO: API call for /api/v1/cari/hareketler/
        await this.$api.post('/api/v1/cari/hareketler/', this.form);
        
        alert('Hareket kaydı başarıyla eklendi/güncellendi!');
        this.closeModal();
        this.$emit('refresh-list'); 
      } catch (error) {
        alert('İşlem başarısız oldu. Cari borç ve alacak toplamının dengeli olduğundan emin olun.');
      }
    },
    async deleteItem(id) {
      if (!confirm('Bu hareket kaydını silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.')) return;
      // *** API CALL SIMULATION ***
      try {
        await this.$api.delete(`/api/v1/cari/hareketler/${id}/`);
        alert('Kayıt silindi.');
        this.cariHareketler = this.cariHareketler.filter(item => item.id !== id);
      } catch (error) {
        alert('Silme işlemi başarısız oldu.');
      }
    }
  },
  mounted() {
    this.$emit('show-modal');
  }
}
</script>
<style scoped>
/* Component specific styles */
</style>