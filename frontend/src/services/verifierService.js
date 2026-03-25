import api from './api'
export const getVerifier = () => api.get('/api/verifier').then(r => r.data)
export const setVerifier = (data) => api.post('/api/verifier', data).then(r => r.data)
export const deleteVerifier = () => api.delete('/api/verifier').then(r => r.data)
