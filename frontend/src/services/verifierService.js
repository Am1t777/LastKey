// Import the pre-configured axios instance (handles JWT headers + CSRF header automatically)
import api from './api'

// getVerifier fetches the current user's trusted verifier record (name, email, has_confirmed, has_denied)
// Returns 404 if no verifier has been set
export const getVerifier = () => api.get('/api/verifier').then(r => r.data)

// setVerifier creates or replaces the trusted verifier for the current user (upsert)
// data: { name, email }
export const setVerifier = (data) => api.post('/api/verifier', data).then(r => r.data)

// deleteVerifier removes the trusted verifier — without one the dead man's switch cannot escalate
export const deleteVerifier = () => api.delete('/api/verifier').then(r => r.data)
