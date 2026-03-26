// createContext creates a React context object that stores and shares auth state
// useContext lets child components consume the context without prop drilling
// useEffect runs side effects (token validation) after the component mounts
// useState stores the current user object and the loading flag
import { createContext, useContext, useEffect, useState } from 'react'
// getMe calls GET /api/auth/me to fetch the current user from the server
// logout (aliased as logoutApi) calls POST /api/auth/logout to invalidate the session server-side
import { getMe, logout as logoutApi } from '../services/authService'

// Create an empty context — child components access it via the useAuth hook below
const AuthContext = createContext(null)

// AuthProvider wraps the app and makes auth state available to all descendant components
export function AuthProvider({ children }) {
  // user stores the authenticated user object (null if not logged in)
  const [user, setUser] = useState(null)
  // isLoading is true while we're validating the stored token on app startup
  const [isLoading, setIsLoading] = useState(true)

  // Run once on mount to check whether a valid token is already stored in localStorage
  useEffect(() => {
    // Look for a JWT that was saved during a previous login session
    const token = localStorage.getItem('lastkey_token')
    // If no token found, skip validation and mark loading as complete
    if (!token) { setIsLoading(false); return }
    // Token found — validate it by fetching the current user profile from the API
    getMe()
      // If the API call succeeds, store the user object in state
      .then(setUser)
      // If the token is invalid/expired, clean it up so we don't retry on the next mount
      .catch(() => localStorage.removeItem('lastkey_token'))
      // Always clear the loading flag when the check finishes (success or failure)
      .finally(() => setIsLoading(false))
  }, []) // Empty dependency array — runs once on mount only

  // login is called after a successful register or login API call
  // It saves the token to localStorage and stores the user data in state
  const login = (token, userData) => {
    // Persist the JWT so it survives page refreshes
    localStorage.setItem('lastkey_token', token)
    // Update the auth state — this triggers a re-render for any consumer of this context
    setUser(userData)
  }

  // logout is called when the user clicks "Sign Out"
  const logout = async () => {
    try { await logoutApi() } catch {} // Call the backend logout endpoint; ignore errors (e.g., network failure)
    // Remove the JWT from localStorage — the axios interceptor will no longer attach it
    localStorage.removeItem('lastkey_token')
    // Clear the user from state — all protected routes will now redirect to /login
    setUser(null)
  }

  return (
    // Provide all auth values and helpers to the component tree
    <AuthContext.Provider value={{
      user,                        // The authenticated user object (or null)
      isLoading,                   // True while the initial token check is in progress
      isAuthenticated: !!user,     // Convenience boolean derived from user
      login,                       // Function to log in with a token + user data
      logout,                      // Function to log out
      setUser,                     // Direct setter for updating the user object (used after profile changes)
    }}>
      {children}
    </AuthContext.Provider>
  )
}

// useAuth is a custom hook that gives any component access to the auth context
// Usage: const { user, isAuthenticated, login, logout } = useAuth()
export const useAuth = () => useContext(AuthContext)
