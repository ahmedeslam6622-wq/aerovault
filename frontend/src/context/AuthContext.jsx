import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AuthContext = createContext(null)

const API = (path, opts = {}) => {
  const token = localStorage.getItem('aerovault_token')
  return fetch(path, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}),
    },
  })
}

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // Rehydrate session from localStorage on boot
  useEffect(() => {
    const token = localStorage.getItem('aerovault_token')
    if (!token) { setLoading(false); return }
    API('/api/auth/me')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setUser(data) })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (username, password) => {
    const form = new URLSearchParams({ username, password, grant_type: 'password' })
    const res  = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Login failed')
    if (data.requires_totp) return { requiresTotp: true, username }
    localStorage.setItem('aerovault_token', data.access_token)
    setUser(data)
    return { success: true }
  }, [])

  const loginSuperuser = useCallback(async (username, password, totpCode) => {
    const res  = await fetch('/api/auth/login/superuser', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, totp_code: totpCode }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Authentication failed')
    localStorage.setItem('aerovault_token', data.access_token)
    setUser(data)
    return { success: true }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('aerovault_token')
    setUser(null)
  }, [])

  const can = useCallback((action) => {
    if (!user) return false
    const role = user.role
    const map = {
      edit_flights:     ['flight_manager', 'admin', 'superuser'],
      edit_maintenance: ['maintenance_chief', 'admin', 'superuser'],
      manage_users:     ['admin', 'superuser'],
      superuser_only:   ['superuser'],
      view_all:         ['viewer', 'flight_manager', 'maintenance_chief', 'admin', 'superuser'],
    }
    return (map[action] || []).includes(role)
  }, [user])

  return (
    <AuthContext.Provider value={{ user, loading, login, loginSuperuser, logout, can, API }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
export { API }
