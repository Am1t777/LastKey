// Import the pre-configured axios instance (handles JWT headers + CSRF header automatically)
import api from './api'

// listSecrets fetches a paginated list of the current user's secrets (metadata only, no content)
// page: which page of results to fetch; limit: how many per page
export const listSecrets = (page = 1, limit = 20) => api.get('/api/secrets', { params: { page, limit } }).then(r => r.data)

// getSecret fetches a single secret by ID including its encrypted fields (needed for decryption)
export const getSecret = (id) => api.get(`/api/secrets/${id}`).then(r => r.data)

// createSecret sends the encrypted secret data to the server for storage
// data includes: title, content (plaintext — encrypted client-side by the service layer), type, password, beneficiary_ids
export const createSecret = (data) => api.post('/api/secrets', data).then(r => r.data)

// updateSecret sends updated fields for an existing secret (PATCH semantics — only provided fields change)
export const updateSecret = (id, data) => api.patch(`/api/secrets/${id}`, data).then(r => r.data)

// deleteSecret permanently removes a secret and all its beneficiary assignments
export const deleteSecret = (id) => api.delete(`/api/secrets/${id}`).then(r => r.data)

// assignSecret creates a new SecretAssignment — requires the owner's password to decrypt and re-encrypt the AES key
export const assignSecret = (id, data) => api.post(`/api/secrets/${id}/assign`, data).then(r => r.data)
