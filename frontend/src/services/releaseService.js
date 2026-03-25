// Import the pre-configured axios instance (handles JWT headers + CSRF header automatically)
import api from './api'

// getRelease fetches the released secrets for a beneficiary using their unique release token
// token: the opaque token from the email link sent when the dead man's switch fires
// Returns { deceased_name, beneficiary_name, released_at, secrets[] }
// Each secret contains the encrypted content + the AES key encrypted with the beneficiary's RSA key
export const getRelease = (token) => api.get(`/api/release/${token}`).then(r => r.data)
