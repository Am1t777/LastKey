import { createContext, useContext, useEffect, useState } from 'react'
import { getMe, logout as logoutApi } from '../services/authService'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('lastkey_token')
    if (!token) { setIsLoading(false); return }
    getMe()
      .then(setUser)
      .catch(() => localStorage.removeItem('lastkey_token'))
      .finally(() => setIsLoading(false))
  }, [])

  const login = (token, userData) => {
    localStorage.setItem('lastkey_token', token)
    setUser(userData)
  }

  const logout = async () => {
    try { await logoutApi() } catch {}
    localStorage.removeItem('lastkey_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, isAuthenticated: !!user, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
