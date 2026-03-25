import api from './api'
export const updateInterval = (days) => api.patch('/api/settings/interval', { days }).then(r => r.data)
