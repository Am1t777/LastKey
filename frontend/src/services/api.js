import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('lastkey_token')
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  config.headers['X-Requested-With'] = 'XMLHttpRequest'
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('lastkey_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export default api
