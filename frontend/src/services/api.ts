import axios from 'axios'

/** Legacy YFK store compatibility client. New code should use apiClient.ts. */
const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('emlak_erp_access') || sessionStorage.getItem('emlak_erp_access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api