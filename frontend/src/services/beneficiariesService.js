import api from './api'
export const listBeneficiaries = () => api.get('/api/beneficiaries').then(r => r.data)
export const getBeneficiary = (id) => api.get(`/api/beneficiaries/${id}`).then(r => r.data)
export const createBeneficiary = (data) => api.post('/api/beneficiaries', data).then(r => r.data)
export const updateBeneficiary = (id, data) => api.patch(`/api/beneficiaries/${id}`, data).then(r => r.data)
export const deleteBeneficiary = (id) => api.delete(`/api/beneficiaries/${id}`).then(r => r.data)
export const generateKey = (id) => api.post(`/api/beneficiaries/${id}/generate-key`).then(r => r.data)
export const listBeneficiarySecrets = (id) => api.get(`/api/beneficiaries/${id}/secrets`).then(r => r.data)
