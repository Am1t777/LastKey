import api from './api'
export const getRelease = (token) => api.get(`/api/release/${token}`).then(r => r.data)
