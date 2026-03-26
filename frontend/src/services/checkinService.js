// Import the pre-configured axios instance (handles JWT headers + CSRF header automatically)
import api from './api'

// checkinByToken performs a password-less check-in using the one-time token from the email link
// token: the URL token extracted from the email's check-in link query parameter
// Returns { message, next_checkin_due } on success
export const checkinByToken = (token) => api.post('/api/checkin', { token }).then(r => r.data)

// checkinAuthenticated performs a check-in for the currently logged-in user (no token needed)
// Used when the user clicks "Check In" directly inside the authenticated dashboard
export const checkinAuthenticated = () => api.post('/api/checkin/auth').then(r => r.data)
