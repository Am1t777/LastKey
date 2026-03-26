// Import the pre-configured axios instance (handles JWT headers + CSRF header automatically)
import api from './api'

// listBeneficiaries returns all beneficiaries added by the current user
export const listBeneficiaries = () => api.get('/api/beneficiaries').then(r => r.data)

// getBeneficiary fetches a single beneficiary by ID including their has_key status
export const getBeneficiary = (id) => api.get(`/api/beneficiaries/${id}`).then(r => r.data)

// createBeneficiary adds a new beneficiary with name and email (no key yet)
export const createBeneficiary = (data) => api.post('/api/beneficiaries', data).then(r => r.data)

// updateBeneficiary changes a beneficiary's name and/or email (PATCH semantics)
export const updateBeneficiary = (id, data) => api.patch(`/api/beneficiaries/${id}`, data).then(r => r.data)

// deleteBeneficiary removes the beneficiary and all their secret assignments
export const deleteBeneficiary = (id) => api.delete(`/api/beneficiaries/${id}`).then(r => r.data)

// generateKey triggers RSA-2048 key pair generation for the beneficiary on the server
// Returns { private_key_pem } — the private key is shown once and never stored server-side
export const generateKey = (id) => api.post(`/api/beneficiaries/${id}/generate-key`).then(r => r.data)

// listBeneficiarySecrets returns all secrets currently assigned to a specific beneficiary
export const listBeneficiarySecrets = (id) => api.get(`/api/beneficiaries/${id}/secrets`).then(r => r.data)
