// Import the pre-configured axios instance (handles JWT headers + CSRF header automatically)
import api from './api'

// register sends the user's name, email, and password to create a new account
// Returns { access_token } on success — the token is immediately stored by AuthContext
export const register = (data) => api.post('/api/auth/register', data).then(r => r.data)

// login verifies email + password credentials and returns a JWT access token
// Returns { access_token } on success
export const login = (data) => api.post('/api/auth/login', data).then(r => r.data)

// logout calls the server to log the audit event, then AuthContext clears the stored token
export const logout = () => api.post('/api/auth/logout').then(r => r.data)

// getMe fetches the currently authenticated user's profile using the stored JWT
// Used on app startup to validate a previously stored token and restore the user session
export const getMe = () => api.get('/api/auth/me').then(r => r.data)
