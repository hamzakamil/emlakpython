<template>
  <div class="container mt-4">
    <h2 class="mb-4">Bilanço ve Mizan Raporu</h2>
    <p class="lead text-muted">Finansal hareketlerin dönemsel özetini ve muhasebe defterindeki tüm hesapların dengesini gösterir. Bu rapor, tüm temel finansal işlemlerin (Fişler, Hareketler) nihai çıktısıdır.</p>

    <div class="row mb-4">
      <div class="col-md-4">
        <label for="rapor_tarihi" class="form-label">Rapor Tarihi</label>
        <input type="date" class="form-control" id="rapor_tarihi" v-model="form.rapor_tarihi" required />
      </div>
      <div class="col-md-4">
        <label for="rapor_tipi" class="form-label">Rapor Tipi</label>
        <select class="form-select" id="rapor_tipi" v-model="form.rapor_tipi" required>
          <option value="mizan">Mizan (Hesap Bazlı Özet)</option>
          <option value="bilanco">Bilanço (Varlık/Kaynak Özet)</option>
        </select>
      </div>
      <div class="col-md-4">
        <button @click="generateReport" class="btn btn-success" :disabled="!form.rapor_tarihi">
          Raporu Oluştur / Yenile
        </button>
      </div>
    </div>

    <div class="card shadow-sm mt-4">
      <div class="card-header bg-light">
        Rapor Sonuçları
      </div>
      <div class="card-body table-responsive">
        <table class="table table-bordered">
          <thead>
            <tr>
              <th>Hesap Kodu</th>
              <th>Hesap Adı</th>
              <th>Borç Toplam (TL)</th>
              <th>Alacak Toplam (TL)</th>
              <th>Dönemsel Bakiye (TL)</th>
            </tr>
          </thead>
          <tbody>
            <!-- Rapor verileri buraya eklenecek -->
            <tr v-if="raporVeri.length === 0">
              <td colspan="5" class="text-center text-muted p-3">Rapor verileri yüklenmedi. Lütfen tarih giriniz.</td>
            </tr>
            <tr v-else-for="item in raporVeri" :key="item.hesap_kodu">
              <td>{{ item.hesap_kodu }}</td>
              <td>{{ item.hesap_adi }}</td>
              <td class="text-danger">{{ formatCurrency(item.borc_toplam) }}</td>
              <td class="text-success">{{ formatCurrency(item.alacak_toplam) }}</td>
              <td class="fw-bold">{{ formatCurrency(item.bakiye) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MizanView',
  data() {
    return {
      form: {
        rapor_tarihi: new Date().toISOString().substring(0, 10),
        rapor_tipi: 'mizan'
      },
      raporVeri: [],
    };
  },
  computed: {
    // Raporun ana mantığı buraya gelecek.
  },
  methods: {
    async generateReport() {
      if (!this.form.rapor_tarihi) {
        alert('Lütfen rapor tarihi seçiniz.');
        return;
      }
      // *** API CALL SIMULATION ***
      try {
        // TODO: API call for /api/v1/accounting/mizan/
        const response = await this.$api.get('/api/v1/accounting/mizan/', {
          params: {
            tarih: this.form.rapor_tarihi,
            tip: this.form.rapor_tipi
          }
        });
        this.raporVeri = response.data;
      } catch (error) {
        alert('Rapor oluşturulamadı. Lütfen tarihi kontrol edin.');
      }
    }
  }
}
</script>
<style scoped>
/* Component specific styles */
</style>