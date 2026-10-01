import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useInsaatStore = defineStore('insaat', () => {
  const loading = ref(false)

  // ===== YFK - Yıllık Poz =====
  async function fetchYfkYillikPozlar(params = {}) {
    loading.value = true
    try {
      const res = await api.get('/api/construction/yfk/poz-versiyonlar/', { params })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchYfkYillikPozDetail(id: number) {
    loading.value = true
    try {
      const res = await api.get(`/api/construction/yfk/poz-versiyonlar/${id}/`)
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function importYfkYillikPoz(formData: FormData) {
    loading.value = true
    try {
      const res = await api.post('/api/construction/yfk/poz-versiyonlar/import/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function downloadYfkYillikTemplate() {
    loading.value = true
    try {
      const res = await api.get('/api/construction/yfk/poz-versiyonlar/template/', {
        responseType: 'blob'
      })
      return res.data
    } finally {
      loading.value = false
    }
  }

  // ===== YFK - Aylık Fiyat =====
  async function fetchYfkFiyatlar(params = {}) {
    loading.value = true
    try {
      const res = await api.get('/api/construction/yfk/fiyatlar/', { params })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function importYfkAylikFiyat(formData: FormData) {
    loading.value = true
    try {
      const res = await api.post('/api/construction/yfk/fiyatlar/import/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function downloadYfkAylikFiyatTemplate() {
    loading.value = true
    try {
      const res = await api.get('/api/construction/yfk/fiyatlar/template/', {
        responseType: 'blob'
      })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchYfkFiyatDetail(id: number) {
    loading.value = true
    try {
      const res = await api.get(`/api/construction/yfk/fiyatlar/${id}/`)
      return res.data
    } finally {
      loading.value = false
    }
  }

  // ===== YFK - Rayıç =====
  async function fetchYfkRayiclar(params = {}) {
    loading.value = true
    try {
      const res = await api.get('/api/construction/yfk/rayiclar/', { params })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function importYfkRayic(formData: FormData) {
    loading.value = true
    try {
      const res = await api.post('/api/construction/yfk/rayiclar/import/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function downloadYfkRayicTemplate() {
    loading.value = true
    try {
      const res = await api.get('/api/construction/yfk/rayiclar/template/', {
        responseType: 'blob'
      })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchYfkRayicDetail(id: number) {
    loading.value = true
    try {
      const res = await api.get(`/api/construction/yfk/rayiclar/${id}/`)
      return res.data
    } finally {
      loading.value = false
    }
  }

  // ===== YFK - Analiz =====
  async function fetchYfkAnalizler(params = {}) {
    loading.value = true
    try {
      const res = await api.get('/api/construction/yfk/analizler/', { params })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function importYfkAnaliz(formData: FormData) {
    loading.value = true
    try {
      const res = await api.post('/api/construction/yfk/analizler/import/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function downloadYfkAnalizTemplate() {
    loading.value = true
    try {
      const res = await api.get('/api/construction/yfk/analizler/template/', {
        responseType: 'blob'
      })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchYfkAnalizDetail(id: number) {
    loading.value = true
    try {
      const res = await api.get(`/api/construction/yfk/analizler/${id}/`)
      return res.data
    } finally {
      loading.value = false
    }
  }

  // ===== YFK - Değişen Pozlar =====
  async function fetchYfkDegisenPozlar(params = {}) {
    loading.value = true
    try {
      const res = await api.get('/api/construction/yfk/degisen-pozlar/', { params })
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchYfkDegisenPozDetail(id: number) {
    loading.value = true
    try {
      const res = await api.get(`/api/construction/yfk/degisen-pozlar/${id}/`)
      return res.data
    } finally {
      loading.value = false
    }
  }

  // ===== YFK - Güncelleme Geçmişi =====
  async function fetchYfkGuncellemeGecmisi(params = {}) {
    loading.value = true
    try {
      const res = await api.get('/api/construction/yfk/guncelleme-gecmisi/', { params })
      return res.data
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    fetchYfkYillikPozlar,
    fetchYfkYillikPozDetail,
    importYfkYillikPoz,
    downloadYfkYillikTemplate,
    fetchYfkFiyatlar,
    fetchYfkFiyatDetail,
    importYfkAylikFiyat,
    downloadYfkAylikFiyatTemplate,
    fetchYfkRayiclar,
    fetchYfkRayicDetail,
    importYfkRayic,
    downloadYfkRayicTemplate,
    fetchYfkAnalizler,
    fetchYfkAnalizDetail,
    importYfkAnaliz,
    downloadYfkAnalizTemplate,
    fetchYfkDegisenPozlar,
    fetchYfkDegisenPozDetail,
    fetchYfkGuncellemeGecmisi,
  }
})