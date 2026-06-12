import { useState, useEffect, useCallback } from 'react'
import { API } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const CATEGORY_ICONS = {
  gate_change: '🚪', delay: '⏱', cancellation: '✕', crew_reassignment: '👤',
  maintenance_alert: '🔧', aog: '⛔', emergency: '🚨', grounding: '⛔',
  critical_maintenance: '⚠', system: 'ℹ',
}

const CATEGORY_COLORS = {
  aog: 'var(--status-red)', emergency: 'var(--status-red)', grounding: 'var(--status-red)',
  delay: 'var(--status-yellow)', maintenance_alert: 'var(--status-yellow)',
  gate_change: 'var(--status-blue)', system: 'var(--text-muted)',
}

export default function NotificationsPage() {
  const { addToast } = useToast()
  const [notifs,     setNotifs]  = useState([])
  const [mode,       setMode]    = useState('')
  const [loading,    setLoading] = useState(true)
  const [unreadOnly, setUnread]  = useState(false)

  const load = useCallback(() => {
    const params = new URLSearchParams()
    if (unreadOnly) params.set('unread_only', 'true')
    API(`/api/notifications/?${params}`).then(r => r.json()).then(d => {
      setNotifs(d.notifications || [])
      setMode(d.mode || '')
      setLoading(false)
    })
  }, [unreadOnly])

  useEffect(() => { load() }, [load])

  const markRead = async (id) => {
    await API(`/api/notifications/${id}/read`, { method: 'PATCH' })
    setNotifs(p => p.map(n => n.id === id ? { ...n, is_read: true } : n))
  }

  const markAll = async () => {
    await API('/api/notifications/read-all', { method: 'PATCH' })
    setNotifs(p => p.map(n => ({ ...n, is_read: true })))
    addToast('All notifications marked as read', 'success')
  }

  const updateMode = async (m) => {
    const res = await API('/api/notifications/settings/mode', {
      method: 'PATCH',
      body: JSON.stringify({ mode: m }),
    })
    if (res.ok) { setMode(m); addToast(`Notification mode: ${m}`, 'success') }
  }

  const fmtTime = (iso) => {
    if (!iso) return ''
    return new Date(iso).toLocaleString('en-GB', {
      day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'UTC',
    }) + 'Z'
  }

  const unreadCount = notifs.filter(n => !n.is_read).length

  return (
    <div>
      <div className="page-title">Notifications</div>
      <div className="page-subtitle">
        {unreadCount} unread · Mode: <strong style={{ textTransform: 'capitalize' }}>{mode}</strong>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)' }}>Mode:</span>
          {['minimal', 'standard', 'work'].map(m => (
            <button key={m} className={`filter-btn ${mode === m ? 'active' : ''}`} onClick={() => updateMode(m)}>
              {m.charAt(0).toUpperCase() + m.slice(1)}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)', fontWeight: 'normal', textTransform: 'none', letterSpacing: 'normal' }}>
            <input type="checkbox" checked={unreadOnly} onChange={e => setUnread(e.target.checked)} />
            Unread only
          </label>
          {unreadCount > 0 && (
            <button className="btn btn-secondary btn-sm" onClick={markAll}>Mark all read</button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="loading-center"><div className="loading-ring" /></div>
      ) : notifs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔔</div>
          <p>No notifications in your current mode.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {notifs.map(n => (
            <div key={n.id} onClick={() => !n.is_read && markRead(n.id)} style={{
              background: n.is_read ? 'var(--bg-card)' : 'var(--bg-hover)',
              border: `1px solid ${n.is_read ? 'var(--border)' : 'var(--border-light)'}`,
              borderLeft: `3px solid ${CATEGORY_COLORS[n.category] || 'var(--accent)'}`,
              borderRadius: 'var(--radius)', padding: '14px 16px',
              cursor: n.is_read ? 'default' : 'pointer', display: 'flex', gap: 12,
            }}>
              <span style={{ fontSize: 20, flexShrink: 0 }}>{CATEGORY_ICONS[n.category] || '🔔'}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: n.is_read ? 500 : 700, fontSize: 14 }}>{n.title}</span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', flexShrink: 0 }}>{fmtTime(n.created_at)}</span>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>{n.body}</div>
                {(n.flight_ref || n.aircraft_ref || !n.is_read) && (
                  <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                    {n.flight_ref && <span style={{ fontSize: 11, fontFamily: 'var(--font-data)', color: 'var(--accent)' }}>{n.flight_ref}</span>}
                    {n.aircraft_ref && <span style={{ fontSize: 11, fontFamily: 'var(--font-data)', color: 'var(--text-muted)' }}>{n.aircraft_ref}</span>}
                    {!n.is_read && <span style={{ fontSize: 11, color: 'var(--accent)', marginLeft: 'auto' }}>tap to mark read</span>}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
