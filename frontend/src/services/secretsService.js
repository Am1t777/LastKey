import api from './api'
export const listSecrets = (page = 1, limit = 20) => api.get('/api/secrets', { params: { page, limit } }).then(r => r.data)
export const getSecret = (id) => api.get(`/api/secrets/${id}`).then(r => r.data)
export const createSecret = (data) => api.post('/api/secrets', data).then(r => r.data)
export const updateSecret = (id, data) => api.patch(`/api/secrets/${id}`, data).then(r => r.data)
export const deleteSecret = (id) => api.delete(`/api/secrets/${id}`).then(r => r.data)
export const assignSecret = (id, data) => api.post(`/api/secrets/${id}/assign`, data).then(r => r.data)
