<template>
  <div class="container mt-4">
    <h2>Malzeme-Tedarikçi İlişkileri</h2>
    <p class="text-muted">Bu alanda, hangi malzemelerin hangi tedarikçilerden temin edildiği ve bu ilişkinin durum takibi yapılır. Tüm veriler multi-tenant ve ilişki, malzeme/tedarikçi bazında izlenir.</p>

    <div class="row">
      <!-- Create/Add Button -->
      <div class="col-12 mt-4">
        <button @click="openModal(true)" class="btn btn-primary" @click.prevent="$emit('show-modal')">
          Yeni İlişki Ekle
        </button>
      </div>
    </div>

    <div class="card mt-4 shadow-sm">
      <div class="card-header">
        İlişki Listesi
      </div>
      <div class="card-body table-responsive">
        <table class="table table-hover table-bordered">
          <thead class="table-light">
            <tr v-pre>
              <th class="col-sm-2">Malzeme Adı</th>
              <th class="col-sm-3">Tedarikçi Firma Adı</th>
              <th class="col-sm-3">İlişki Açıklaması</th>
              <th class="col-sm-2">Durum</th>
              <th class="col-sm-2">İşlemler</th>
            </tr>
          </thead>
          <tbody v-if="materialSupplierRelations.length > 0">
            <tr v-for="item in materialSupplierRelations" :key="item.id">
              <td>{{ item.malzeme_adi }}</td>
              <td>{{ item.tedarikci_adi }}</td>
              <td>{{ item.aciklama || '-' }}</td>
              <td><span :class="getStatusClass(item.durum)">{{ item.durum }}</span></td>
              <td>
                <button @click="openModal(false, item)" class="btn btn-sm btn-info me-2">Düzenle</button>
                <button @click="deleteItem(item.id)" class="btn btn-sm btn-danger">Sil</button>
              </td>
            </tr>
          <th v-else colspan="5">
            <div class="text-center text-muted p-3">Kayıt bulunmamaktadır.</div>
          </th>
        </table>
      </div>
    </div>

    <!-- Modal Component -->
    <div v-if="isModalOpen" class="modal fade show" style="display: block" tabindex="-1" aria-labelledby="materialSupplierRelationModalLabel" aria-modal="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="materialSupplierRelationModalLabel">{{ isEditing ? 'İlişkiyi Düzenle' : 'Yeni İlişki Ekle' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitRelation">
              <div class="mb-3">
                <label for="malzeme_adi" class="form-label">Malzeme Adı</label>
                <input type="text" class="form-control" id="malzeme_adi" v-model="form.malzeme_adi" required />
              </div>
              <div class="mb-3">
                <label for="tedarikci_adi" class="form-label">Tedarikçi Firma Adı</label>
                <input type="text" class="form-control" id="tedarikci_adi" v-model="form.tedarikci_adi" required />
              </div>
              <div class="mb-3">
                <label for="aciklama" class="form-label">Açıklama</label>
                <textarea class="form-control" id="aciklama" v-model="form.aciklama" rows="3"></textarea>
              </div>
              <div class="mb-3">
                <label for="durum" class="form-label">İlişki Durumu</label>
                <select class="form-select" id="durum" v-model="form.durum" required>
                    <option value="Planlandı">Planlandı</option>
                    <option value="Sipariş Verildi">Sipariş Verildi</option>
                    <option value="Teslim Edildi">Teslim Edildi</option>
                    <option value="İptal Edildi">İptal Edildi</option>
                </select>
              </div>
              <button type="submit" class="btn btn-success mt-3">{{ isEditing ? 'Güncelle' : 'Kaydet' }}</button>
            </form>
          </div>
        </div>
      </div>
    </div >
</template>

<script>
import { mapGetters } from 'vuex';
// Varsayım: useApi, formatters ve Vuex store yapısı mevcut.

export default {
  name: 'MalzemeTedarikciIliskisiView',
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
        malzeme_adi: '',
        tedarikci_adi: '',
        aciklama: '',
        durum: 'Planlandı'
      }
    };
  },
  computed: {
    ...mapGetters(['materialSupplierRelations']),
  },
  methods: {
    openModal(isCreate, item = null) {
      this.isEditing = !isCreate;
      this.form = {
        malzeme_adi: isCreate ? '' : item.malzeme_adi,
        tedarikci_adi: isCreate ? '' : item.tedarikci_adi,
        aciklama: isCreate ? '' : item.aciklama,
        durum: isCreate ? 'Planlandı' : item.durum
      };
      this.isModalOpen = true;
    },
    closeModal() {
      this.isModalOpen = false;
    },
    getStatusClass(durum) {
      switch (durum) {
        case 'Teslim Edildi':
          return 'text-success fw-bold';
        case 'Sipariş Verildi':
          return 'text-warning fw-bold';
        case 'İptal Edildi':
          return 'text-danger';
        case 'Planlandı':
        default:
          return 'text-secondary';
      }
    },
    async submitRelation() {
      if (!this.form.malzeme_adi || !this.form.tedarikci_adi) {
        alert('Lütfen tüm alanları doldurunuz.');
        return;
      }
      // TODO: API call logic here, checking if item ID exists for update vs new creation.
      alert('Veri Gönderimi Simüle Edildi!');
      this.closeModal();
      this.$emit('refresh-list'); 
    },
    async deleteItem(id) {
      if (!confirm('Bu kaydı silmek istediğinizden emin misiniz?')) return;
      // Manually remove from local data for immediate UI feedback
      this.materialSupplierRelations = this.materialSupplierRelations.filter(item => item.id !== id);
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