// BrowserRouter provides HTML5 history-based routing (URL changes without page reloads)
// Routes is the container for all route definitions
// Route defines a single URL-to-component mapping
// Navigate performs a programmatic redirect (used here as a catch-all redirect)
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
// AuthProvider wraps the app with authentication state (JWT, user object, login/logout)
import { AuthProvider } from './context/AuthContext'
// ProtectedRoute is a wrapper component that redirects unauthenticated users to /login
import ProtectedRoute from './components/layout/ProtectedRoute'
// AppShell provides the persistent layout shell (sidebar + main content area) for authenticated pages
import AppShell from './components/layout/AppShell'
// All page components — each corresponds to a distinct URL in the app
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import CheckinPage from './pages/CheckinPage'           // Token-based check-in from email link
import VerifyConfirmPage from './pages/VerifyConfirmPage' // Verifier confirms incapacitation
import VerifyDenyPage from './pages/VerifyDenyPage'       // Verifier denies — user is alive
import ReleasePage from './pages/ReleasePage'             // Beneficiary views released secrets
import DashboardPage from './pages/DashboardPage'
import SecretsPage from './pages/SecretsPage'
import NewSecretPage from './pages/NewSecretPage'
import SecretDetailPage from './pages/SecretDetailPage'
import BeneficiariesPage from './pages/BeneficiariesPage'
import BeneficiaryDetailPage from './pages/BeneficiaryDetailPage'
import VerifierPage from './pages/VerifierPage'
import SettingsPage from './pages/SettingsPage'

// App is the root component — it sets up routing and the auth context
export default function App() {
  return (
    // BrowserRouter enables client-side routing throughout the component tree
    <BrowserRouter>
      {/* AuthProvider makes auth state (user, login, logout) available to all pages */}
      <AuthProvider>
        <Routes>
          {/* Public routes — accessible without authentication */}
          {/* /login — email + password login form */}
          <Route path="/login" element={<LoginPage />} />
          {/* /register — new account creation form */}
          <Route path="/register" element={<RegisterPage />} />
          {/* /checkin — password-less check-in via email token (?token=...) */}
          <Route path="/checkin" element={<CheckinPage />} />
          {/* /verify/:token/confirm — verifier confirms the user is incapacitated */}
          <Route path="/verify/:token/confirm" element={<VerifyConfirmPage />} />
          {/* /verify/:token/deny — verifier confirms the user is alive */}
          <Route path="/verify/:token/deny" element={<VerifyDenyPage />} />
          {/* /release/:token — beneficiary accesses their inherited secrets */}
          <Route path="/release/:token" element={<ReleasePage />} />

          {/* Protected routes — ProtectedRoute redirects to /login if not authenticated */}
          <Route element={<ProtectedRoute />}>
            {/* AppShell renders the sidebar and wraps all authenticated pages */}
            <Route element={<AppShell />}>
              {/* /dashboard — home screen with switch status and next check-in date */}
              <Route path="/dashboard" element={<DashboardPage />} />
              {/* /secrets — paginated list of all the user's encrypted secrets */}
              <Route path="/secrets" element={<SecretsPage />} />
              {/* /secrets/new — form to create a new encrypted secret */}
              <Route path="/secrets/new" element={<NewSecretPage />} />
              {/* /secrets/:id — view/decrypt/assign a single secret */}
              <Route path="/secrets/:id" element={<SecretDetailPage />} />
              {/* /beneficiaries — list all beneficiaries */}
              <Route path="/beneficiaries" element={<BeneficiariesPage />} />
              {/* /beneficiaries/:id — view/manage a single beneficiary and their assigned secrets */}
              <Route path="/beneficiaries/:id" element={<BeneficiaryDetailPage />} />
              {/* /verifier — set/update/remove the trusted verifier */}
              <Route path="/verifier" element={<VerifierPage />} />
              {/* /settings — configure the check-in interval */}
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Route>

          {/* Catch-all: any unknown URL redirects to /dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
