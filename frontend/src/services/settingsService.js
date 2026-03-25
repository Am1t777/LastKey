// Import the pre-configured axios instance (handles JWT headers + CSRF header automatically)
import api from './api'

// updateInterval changes how many days the user has between required check-ins
// days: the new check-in interval in days (e.g., 7 for weekly, 30 for monthly)
// Returns { message } on success
export const updateInterval = (days) => api.patch('/api/settings/interval', { days }).then(r => r.data)
