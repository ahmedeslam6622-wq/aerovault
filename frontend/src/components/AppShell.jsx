import { useState, useEffect } from 'react'
import { useLocation, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const ROLE_LABELS = {
  viewer: 'Viewer', flight_manager: 'Flight Manager',
  maintenance_chief: 'Maint. Chief', admin: 'Administrator', superuser: 'Superuser',
}

const Icons = {
  dashboard:     <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>,
  flights:       <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24"><path d="M22 16.5L12 2 2 16.5l4-1.5 6 4 6-4 4 1.5z"/></svg>,
  crew:          <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24"><circle cx="9" cy="7" r="4"/><path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/><path d="M16 11a4 4 0 0 1 0-8"/><path d="M21 21v-2a4 4 0 0 0-3-3.87"/></svg>,
  maintenance:   <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>,
  notifications: <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>,
  admin:         <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>,
  logout:        <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>,
  sun:           <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>,
  moon:          <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.75" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>,
  menu:          <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>,
  close:         <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
}

const NAV = [
  { path: '/dashboard',     label: 'Dashboard',    icon: 'dashboard' },
  { path: '/flights',       label: 'Flights',       icon: 'flights' },
  { path: '/crew',          label: 'Crew',          icon: 'crew' },
  { path: '/maintenance',   label: 'Maintenance',   icon: 'maintenance' },
  { path: '/notifications', label: 'Notifications', icon: 'notifications' },
]

const PAGE_TITLES = {
  '/dashboard': 'Dashboard', '/flights': 'Flight Operations',
  '/crew': 'Crew Management', '/maintenance': 'Maintenance',
  '/notifications': 'Notifications', '/admin': 'Admin Panel',
}

export default function AppShell({ children }) {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem('av_theme') || 'dark')

  // Close sidebar on navigation
  useEffect(() => setOpen(false), [location.pathname])

  // Lock body scroll when sidebar open on mobile
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    localStorage.setItem('av_theme', next)
    document.documentElement.setAttribute('data-theme', next)
  }

  return (
    <div className="app-shell">
      {/* Overlay — blocks interaction with content when sidebar open on mobile */}
      <div
        className={`sidebar-overlay ${open ? 'open' : ''}`}
        onClick={() => setOpen(false)}
      />

      {/* Sidebar */}
      <nav className={`sidebar ${open ? 'open' : ''}`}>
        <div className="sidebar-logo">
          <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="var(--accent)" strokeWidth="1.75">
            <path d="M22 16.5L12 2 2 16.5l4-1.5 6 4 6-4 4 1.5z"/>
          </svg>
          <div>
            <div className="logo-name">AeroVault</div>
            <div className="logo-sub">CAI · EgyptAir Ops</div>
          </div>
        </div>

        <div className="sidebar-nav">
          <div className="nav-section-label">Operations</div>
          {NAV.map(item => (
            <Link key={item.path} to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}>
              {Icons[item.icon]}
              {item.label}
            </Link>
          ))}
          {(user?.role === 'admin' || user?.role === 'superuser') && (
            <>
              <div className="nav-section-label" style={{ marginTop: 8 }}>System</div>
              <Link to="/admin" className={`nav-item ${location.pathname === '/admin' ? 'active' : ''}`}>
                {Icons.admin} Admin Panel
              </Link>
            </>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="user-pill">
            <div className="user-avatar">
              {user?.avatar_initials || user?.username?.slice(0, 2).toUpperCase()}
            </div>
            <div style={{ minWidth: 0 }}>
              <div className="user-name">{user?.full_name}</div>
              <div className="user-role">{ROLE_LABELS[user?.role] || user?.role}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
            <button className="btn btn-secondary btn-sm" style={{ flex: 1 }} onClick={toggleTheme}>
              {theme === 'dark' ? Icons.sun : Icons.moon}
              {theme === 'dark' ? 'Light' : 'Dark'}
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => { logout(); navigate('/login') }}>
              {Icons.logout}
            </button>
          </div>
        </div>
      </nav>

      {/* Main content — full width on mobile, offset on desktop */}
      <div className="main-content">
        <header className="page-header">
          <button className="menu-toggle" onClick={() => setOpen(o => !o)} aria-label="Menu">
            {open ? Icons.close : Icons.menu}
          </button>
          <h1 className="page-header-title">
            {PAGE_TITLES[location.pathname] || 'AeroVault'}
          </h1>
          <div className="header-actions">
            <Link to="/notifications" className="icon-btn" title="Notifications">
              {Icons.notifications}
              <span className="notif-dot" />
            </Link>
          </div>
        </header>
        <div className="page-body">
          {children}
        </div>
      </div>
    </div>
  )
}
