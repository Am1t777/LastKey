// axios is an HTTP client library that simplifies making API requests from the browser
import axios from 'axios'

// Create a pre-configured axios instance so all API calls share the same base URL and options
const api = axios.create({
  // Base URL is read from the Vite environment variable; falls back to localhost for development
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  // withCredentials: true sends cookies (e.g., session cookies) on cross-origin requests
  withCredentials: true,
})

// REQUEST INTERCEPTOR — runs before every outgoing API call
api.interceptors.request.use((config) => {
  // Read the JWT access token from localStorage (set during login/register)
  const token = localStorage.getItem('lastkey_token')
  // If a token exists, attach it as a Bearer token in the Authorization header
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  // Add the CSRF header that the backend CSRFMiddleware requires on all state-changing requests
  // Browsers cannot set custom headers on cross-origin requests without a preflight,
  // so this effectively proves the request originated from our own JavaScript
  config.headers['X-Requested-With'] = 'XMLHttpRequest'
  // Return the modified config so the request proceeds with the added headers
  return config
})

// RESPONSE INTERCEPTOR — runs after every response (or error) comes back from the server
api.interceptors.response.use(
  // For successful responses, pass them through unchanged
  (res) => res,
  // For error responses, check whether it's a 401 Unauthorized
  (err) => {
    if (err.response?.status === 401) {
      // JWT is invalid or expired — remove the stale token from storage
      localStorage.removeItem('lastkey_token')
      // Redirect the user to the login page so they can re-authenticate
      window.location.href = '/login'
    }
    // Re-throw the error so the calling code (React Query hooks) can still handle it
    return Promise.reject(err)
  },
)

// Export the configured axios instance — all service files import this instead of raw axios
export default api
