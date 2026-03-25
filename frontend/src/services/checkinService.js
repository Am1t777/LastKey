import api from './api'
export const checkinByToken = (token) => api.post('/api/checkin', { token }).then(r => r.data)
export const checkinAuthenticated = () => api.post('/api/checkin/auth').then(r => r.data)
