import { useState, useEffect, useCallback } from 'react'
import { API } from '../context/AuthContext'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const ROLES = ['viewer','flight_manager','maintenance_chief','admin','superuser']
const ROLE_LABELS = {
  viewer: 'Viewer', flight_manager: 'Flight Manager',
  maintenance_chief: 'Maint. Chief', admin: 'Admin', superuser: 'Superuser',
}

const ROLE_COLORS = {
  viewer: 'var(--text-muted)', flight_manager: 'var(--status-blue)',
  maintenance_chief: 'var(--status-yellow)', admin: 'var(--accent)',
  superuser: 'var(--status-red)',
}

function RoleBadge({ role }) {
  return (
    <span style={{
      display: 'inline-block', fontSize: 11, fontWeight: 700, padding: '2px 8px',
      borderRadius: 4, background: 'var(--bg-hover)', color: ROLE_COLORS[role] || 'var(--text-muted)',
      fontFamily: 'var(--font-data)', textTransform: 'uppercase', letterSpacing: '0.05em',
    }}>
      {ROLE_LABELS[role] || role}
    </span>
  )
}

export default function AdminPage() {
  const { user: self } = useAuth()
  const { addToast }   = useToast()
  const [users,   setUsers]   = useState([])
  const [stats,   setStats]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null)   // { userId, field }
  const [newRole, setNewRole] = useState('')

  const load = useCallback(() => {
    Promise.all([
      API('/api/admin/users').then(r => r.json()),
      API('/api/admin/stats/summary').then(r => r.json()),
    ]).then(([u, s]) => { setUsers(u.users || []); setStats(s); setLoading(false) })
  }, [])

  useEffect(() => { load() }, [load])

  const startEdit = (user) => {
    setEditing(user.id)
    setNewRole(user.role)
  }

  const saveRole = async (userId) => {
    const res = await API(`/api/admin/users/${userId}/role`, {
      method: 'PATCH',
      body: JSON.stringify({ role: newRole }),
    })
    const data = await res.json()
    if (!res.ok) { addToast(data.detail, 'error'); return }
    addToast(data.message, 'success')
    setEditing(null)
    load()
  }

  const toggleUser = async (userId, name) => {
    const res  = await API(`/api/admin/users/${userId}/toggle`, { method: 'PATCH' })
    const data = await res.json()
    if (!res.ok) { addToast(data.detail, 'error'); return }
    addToast(data.message, 'success')
    load()
  }

  const fmtDate = (iso) => {
    if (!iso) return 'Never'
    return new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: '2-digit', hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }) + 'Z'
  }

  return (
    <div>
      <div className="page-title">Admin Panel</div>
      <div className="page-subtitle">User management and system overview</div>

      {/* System stats */}
      {stats && (
        <div className="stats-grid">
          {[
            { label: 'Total Users',    value: stats.total_users    },
            { label: 'Active Users',   value: stats.active_users,  color: 'green' },
            { label: 'Total Flights',  value: stats.total_flights  },
            { label: 'Total Crew',     value: stats.total_crew     },
            { label: 'Fleet Size',     value: stats.total_aircraft },
            { label: 'Aircraft AOG',   value: stats.aog_aircraft,  color: stats.aog_aircraft > 0 ? 'red' : '' },
          ].map(s => (
            <div className="stat-card" key={s.label}>
              <div className="stat-label">{s.label}</div>
              <div className={`stat-value ${s.color || ''}`}>{s.value ?? '—'}</div>
            </div>
          ))}
        </div>
      )}

      {/* Users table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">User Accounts ({users.length})</div>
        </div>

        {loading ? (
          <div className="loading-center"><div className="loading-ring" /></div>
        ) : (
          <div className="table-wrap" style={{ border: 'none', borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Employee ID</th>
                  <th>Name</th>
                  <th>Username</th>
                  <th>Department</th>
                  <th>Role</th>
                  <th>Notif Mode</th>
                  <th>Status</th>
                  <th>Last Login</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} style={{ opacity: u.is_active ? 1 : 0.5 }}>
                    <td><span className="td-mono">{u.employee_id}</span></td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{
                          width: 28, height: 28, borderRadius: 6, background: 'var(--bg-hover)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 10, fontWeight: 700, fontFamily: 'var(--font-data)',
                          color: ROLE_COLORS[u.role] || 'var(--text-muted)', flexShrink: 0,
                        }}>
                          {u.avatar_initials}
                        </div>
                        <span style={{ fontSize: 13, fontWeight: 500 }}>{u.full_name}</span>
                        {u.id === self?.id && <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>(you)</span>}
                      </div>
                    </td>
                    <td><span className="td-mono">{u.username}</span></td>
                    <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{u.department || '—'}</td>
                    <td>
                      {editing === u.id ? (
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          <select value={newRole} onChange={e => setNewRole(e.target.value)} style={{ fontSize: 12, padding: '4px 8px' }}>
                            {ROLES.map(r => (
                              <option key={r} value={r} disabled={r === 'superuser' && self?.role !== 'superuser'}>
                                {ROLE_LABELS[r]}
                              </option>
                            ))}
                          </select>
                          <button className="btn btn-primary btn-sm" onClick={() => saveRole(u.id)}>✓</button>
                          <button className="btn btn-secondary btn-sm" onClick={() => setEditing(null)}>✕</button>
                        </div>
                      ) : (
                        <RoleBadge role={u.role} />
                      )}
                    </td>
                    <td>
                      <span style={{ fontSize: 11, textTransform: 'capitalize', color: 'var(--text-secondary)' }}>
                        {u.notification_mode}
                      </span>
                    </td>
                    <td>
                      <span style={{
                        display: 'inline-block', fontSize: 11, fontWeight: 600, padding: '2px 8px',
                        borderRadius: 4, fontFamily: 'var(--font-data)',
                        background: u.is_active ? 'rgba(34,197,94,0.12)' : 'rgba(107,114,128,0.12)',
                        color: u.is_active ? 'var(--status-green)' : 'var(--status-grey)',
                      }}>
                        {u.is_active ? 'ACTIVE' : 'DISABLED'}
                      </span>
                    </td>
                    <td><span className="td-mono" style={{ fontSize: 11 }}>{fmtDate(u.last_login)}</span></td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        {editing !== u.id && u.id !== self?.id && (
                          <button className="btn btn-secondary btn-sm" onClick={() => startEdit(u)}>
                            Edit Role
                          </button>
                        )}
                        {u.id !== self?.id && u.role !== 'superuser' && (
                          <button
                            className={`btn btn-sm ${u.is_active ? 'btn-danger' : 'btn-secondary'}`}
                            onClick={() => toggleUser(u.id, u.full_name)}
                          >
                            {u.is_active ? 'Disable' : 'Enable'}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Role reference */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-title" style={{ marginBottom: 12 }}>Role Permissions Reference</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10 }}>
          {[
            { role: 'viewer',            perms: ['View flights', 'View crew', 'View maintenance'] },
            { role: 'flight_manager',    perms: ['All Viewer perms', 'Edit flight status', 'Assign crew', 'Update gates'] },
            { role: 'maintenance_chief', perms: ['All Viewer perms', 'Update maintenance tasks', 'Manage MEL items'] },
            { role: 'admin',             perms: ['All above', 'Manage users', 'Change roles', 'View system stats'] },
            { role: 'superuser',         perms: ['Full system access', 'Assign Superuser role', 'Cannot be disabled'] },
          ].map(({ role, perms }) => (
            <div key={role} style={{ padding: 12, background: 'var(--bg-hover)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
              <RoleBadge role={role} />
              <ul style={{ marginTop: 8, paddingLeft: 0, listStyle: 'none' }}>
                {perms.map(p => (
                  <li key={p} style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '2px 0' }}>
                    <span style={{ color: 'var(--status-green)', marginRight: 6 }}>✓</span>{p}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
