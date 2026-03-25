import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/layout/ProtectedRoute'
import AppShell from './components/layout/AppShell'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import CheckinPage from './pages/CheckinPage'
import VerifyConfirmPage from './pages/VerifyConfirmPage'
import VerifyDenyPage from './pages/VerifyDenyPage'
import ReleasePage from './pages/ReleasePage'
import DashboardPage from './pages/DashboardPage'
import SecretsPage from './pages/SecretsPage'
import NewSecretPage from './pages/NewSecretPage'
import SecretDetailPage from './pages/SecretDetailPage'
import BeneficiariesPage from './pages/BeneficiariesPage'
import BeneficiaryDetailPage from './pages/BeneficiaryDetailPage'
import VerifierPage from './pages/VerifierPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/checkin" element={<CheckinPage />} />
          <Route path="/verify/:token/confirm" element={<VerifyConfirmPage />} />
          <Route path="/verify/:token/deny" element={<VerifyDenyPage />} />
          <Route path="/release/:token" element={<ReleasePage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/secrets" element={<SecretsPage />} />
              <Route path="/secrets/new" element={<NewSecretPage />} />
              <Route path="/secrets/:id" element={<SecretDetailPage />} />
              <Route path="/beneficiaries" element={<BeneficiariesPage />} />
              <Route path="/beneficiaries/:id" element={<BeneficiaryDetailPage />} />
              <Route path="/verifier" element={<VerifierPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
