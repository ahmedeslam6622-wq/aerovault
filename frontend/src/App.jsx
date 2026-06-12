import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import AppShell from './components/AppShell'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import FlightsPage from './pages/FlightsPage'
import CrewPage from './pages/CrewPage'
import MaintenancePage from './pages/MaintenancePage'
import NotificationsPage from './pages/NotificationsPage'

import AdminPage from './pages/AdminPage'

function AuthGuard({ children }) {
  const { user, loading } = useAuth()
  if (loading) return (
    <div style={{ minHeight: '100dvh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div className="loading-ring" style={{ width: 32, height: 32 }} />
    </div>
  )
  if (!user) return <Navigate to="/login" replace />
  return children
}

function AppRoutes() {
  const { user } = useAuth()
  if (!user) return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )

  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/flights" element={<FlightsPage />} />
        <Route path="/crew" element={<CrewPage />} />
        <Route path="/maintenance" element={<MaintenancePage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        {(user.role === 'admin' || user.role === 'superuser') && (
          <Route path="/admin" element={<AdminPage />} />
        )}
        <Route path="/login" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AppShell>
  )
}

export default function App() {
  // Persist theme preference
  const [theme, setTheme] = useState(() => localStorage.getItem('av_theme') || 'dark')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('av_theme', theme)
  }, [theme])

  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  )
}
