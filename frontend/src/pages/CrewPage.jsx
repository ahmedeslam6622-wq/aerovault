import { useState, useEffect, useCallback } from 'react'
import { API } from '../context/AuthContext'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const ROLE_LABELS = {
  captain: 'Captain', first_officer: 'First Officer', second_officer: '2nd Officer',
  purser: 'Purser', senior_cabin_crew: 'Senior Cabin', cabin_crew: 'Cabin Crew',
  ground_agent: 'Ground Agent', flight_dispatcher: 'Dispatcher', load_controller: 'Load Controller',
}

function Badge({ status }) {
  const s = (status || '').toLowerCase().replace(/ /g, '_')
  return <span className={`badge badge-${s}`}>{(status || '').replace(/_/g, ' ')}</span>
}

function HoursBar({ used, max, label }) {
  const pct = Math.min(100, Math.round((used / max) * 100))
  const color = pct > 90 ? 'var(--status-red)' : pct > 75 ? 'var(--status-yellow)' : 'var(--status-green)'
  return (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
        <span>{label}</span>
        <span style={{ fontFamily: 'var(--font-data)', color: 'var(--text-secondary)' }}>{used}h / {max}h ({pct}%)</span>
      </div>
      <div style={{ height: 5, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.4s' }} />
      </div>
    </div>
  )
}

function CrewDetailModal({ crew, onClose, canEdit, onStatusChanged }) {
  const { addToast } = useToast()
  const [newStatus, setNewStatus] = useState(crew.status)
  const [saving, setSaving] = useState(false)

  const STATUSES = ['available','on_duty','resting','standby','sick','grounded','on_leave','off_roster']

  const saveStatus = async () => {
    if (newStatus === crew.status) return
    setSaving(true)
    try {
      const res = await API(`/api/crew/${crew.id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      })
      if (!res.ok) throw new Error((await res.json()).detail)
      addToast(`${crew.full_name} — status updated`, 'success')
      onStatusChanged()
      onClose()
    } catch(e) {
      addToast(e.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const row = (label, val, mono) => (
    <div style={{ display:'flex', justifyContent:'space-between', padding:'7px 0', borderBottom:'1px solid var(--border)', gap:12 }}>
      <span style={{ fontSize:12, color:'var(--text-muted)', flexShrink:0 }}>{label}</span>
      <span style={{ fontSize:13, fontFamily: mono?'var(--font-data)':undefined, textAlign:'right' }}>{val||'—'}</span>
    </div>
  )

  return (
    <div className="modal-overlay" onClick={e => e.target===e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div>
            <div style={{ fontSize:18, fontWeight:700 }}>{crew.full_name}</div>
            <div style={{ fontSize:13, color:'var(--text-muted)', marginTop:2 }}>
              {crew.employee_id} · {ROLE_LABELS[crew.role] || crew.role}
            </div>
          </div>
          <div style={{ display:'flex', gap:6, alignItems:'center' }}>
            <Badge status={crew.status} />
            <button className="icon-btn" onClick={onClose}>✕</button>
          </div>
        </div>
        <div className="modal-body">
          {row('Base Airport',    crew.base_airport, true)}
          {row('Current Airport', crew.current_airport, true)}
          {row('License',         `${crew.license_type||''} ${crew.license_number||''}`.trim(), true)}
          {row('License Expiry',  crew.license_expiry, true)}
          {row('Medical Class',   crew.medical_class)}
          {row('Medical Expiry',  crew.medical_expiry, true)}
          {row('Type Ratings',    (crew.type_ratings||[]).join(', '), true)}
          {row('Languages',       (crew.languages||[]).join(', '))}
          {row('Total Hours',     crew.flight_hours_total?.toLocaleString() + ' hrs', true)}

          <div style={{ marginTop:14, marginBottom:4 }}>
            <div style={{ fontSize:12, fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:10 }}>Hours Utilisation</div>
            <HoursBar used={crew.flight_hours_month} max={crew.max_hours_month} label="This Month" />
            <HoursBar used={crew.flight_hours_year}  max={crew.max_hours_year}  label="This Year"  />
          </div>

          {crew.assignments?.length > 0 && (
            <div style={{ marginTop:14 }}>
              <div style={{ fontSize:12, fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:8 }}>Flight Assignments</div>
              {crew.assignments.map((a, i) => (
                <div key={i} style={{ display:'flex', justifyContent:'space-between', padding:'6px 0', borderBottom:'1px solid var(--border)', fontSize:13 }}>
                  <div>
                    <span className="td-flight-num" style={{ fontSize:13 }}>{a.flight_number}</span>
                    <span style={{ color:'var(--text-muted)', marginLeft:8 }}>{a.route}</span>
                  </div>
                  <div style={{ display:'flex', gap:8, alignItems:'center' }}>
                    <span style={{ fontSize:11, color:'var(--text-muted)' }}>{a.role_on_flight?.replace(/_/g,' ')}</span>
                    <Badge status={a.status} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {crew.notes && (
            <div style={{ marginTop:12, padding:10, background:'var(--bg-hover)', borderRadius:'var(--radius-sm)', fontSize:12, color:'var(--text-secondary)' }}>
              📝 {crew.notes}
            </div>
          )}

          {canEdit && (
            <div style={{ marginTop:16 }}>
              <div className="divider" />
              <div style={{ fontSize:12, fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:8 }}>Update Status</div>
              <div style={{ display:'flex', gap:8 }}>
                <select value={newStatus} onChange={e => setNewStatus(e.target.value)} style={{ flex:1 }}>
                  {STATUSES.map(s => <option key={s} value={s}>{s.replace(/_/g,' ')}</option>)}
                </select>
                <button className="btn btn-primary btn-sm" onClick={saveStatus} disabled={saving || newStatus===crew.status}>
                  {saving ? <span className="loading-ring" /> : 'Update'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function CrewPage() {
  const { can } = useAuth()
  const [crew,     setCrew]    = useState([])
  const [stats,    setStats]   = useState(null)
  const [loading,  setLoading] = useState(true)
  const [search,   setSearch]  = useState('')
  const [filter,   setFilter]  = useState('all')
  const [roleFilter, setRoleFilter] = useState('all')
  const [selected, setSelected] = useState(null)

  const load = useCallback(() => {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (filter !== 'all') params.set('status', filter)
    if (roleFilter !== 'all') params.set('role', roleFilter)
    Promise.all([
      API(`/api/crew/?${params}`).then(r => r.json()),
      API('/api/crew/stats/summary').then(r => r.json()),
    ]).then(([c, s]) => { setCrew(c.crew || []); setStats(s); setLoading(false) })
  }, [search, filter, roleFilter])

  useEffect(() => { load() }, [load])

  const loadDetail = async (c) => {
    const res = await API(`/api/crew/${c.id}`)
    const data = await res.json()
    setSelected(data)
  }

  const STATUS_FILTERS = ['all','available','on_duty','resting','standby','sick','grounded']
  const ROLE_FILTERS = [
    { key:'all', label:'All Roles' },
    { key:'captain', label:'Captains' },
    { key:'first_officer', label:'First Officers' },
    { key:'purser', label:'Pursers' },
    { key:'cabin_crew', label:'Cabin Crew' },
    { key:'flight_dispatcher', label:'Dispatchers' },
    { key:'ground_agent', label:'Ground' },
  ]

  return (
    <div>
      <div className="page-title">Crew Management</div>
      <div className="page-subtitle">{crew.length} crew members · All stations</div>

      {/* Stats strip */}
      {stats && (
        <div className="stats-grid" style={{ marginBottom:20 }}>
          {[
            { label:'Total Crew',  value: stats.total,     color:'' },
            { label:'On Duty',     value: stats.on_duty,   color:'accent' },
            { label:'Available',   value: stats.available, color:'green' },
            { label:'Standby',     value: stats.standby,   color:'yellow' },
          ].map(s => (
            <div className="stat-card" key={s.label}>
              <div className="stat-label">{s.label}</div>
              <div className={`stat-value ${s.color}`}>{s.value ?? '—'}</div>
            </div>
          ))}
        </div>
      )}

      {/* Search */}
      <div className="search-bar" style={{ marginBottom:12 }}>
        <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search name or employee ID…" />
      </div>

      <div className="filters-row">
        {STATUS_FILTERS.map(f => (
          <button key={f} className={`filter-btn ${filter===f?'active':''}`} onClick={() => setFilter(f)}>
            {f === 'all' ? 'All Status' : f.replace(/_/g,' ')}
          </button>
        ))}
      </div>
      <div className="filters-row" style={{ marginTop:4 }}>
        {ROLE_FILTERS.map(f => (
          <button key={f.key} className={`filter-btn ${roleFilter===f.key?'active':''}`} onClick={() => setRoleFilter(f.key)}>
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-center"><div className="loading-ring" /></div>
      ) : crew.length === 0 ? (
        <div className="empty-state"><div className="empty-state-icon">👤</div><p>No crew match your filters.</p></div>
      ) : (
        <div className="table-wrap" style={{ marginTop:12 }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Role</th>
                <th>Status</th>
                <th>Base</th>
                <th>Location</th>
                <th>Type Ratings</th>
                <th>Month Hrs</th>
                <th>Year Hrs</th>
                <th>License</th>
              </tr>
            </thead>
            <tbody>
              {crew.map(c => {
                const monthPct = Math.round((c.flight_hours_month / c.max_hours_month) * 100)
                return (
                  <tr key={c.id} onClick={() => loadDetail(c)}>
                    <td><span className="td-mono">{c.employee_id}</span></td>
                    <td style={{ fontWeight:500 }}>{c.full_name}</td>
                    <td style={{ fontSize:12 }}>{ROLE_LABELS[c.role] || c.role}</td>
                    <td><Badge status={c.status} /></td>
                    <td><span className="td-mono">{c.base_airport}</span></td>
                    <td><span className="td-mono">{c.current_airport || '—'}</span></td>
                    <td>
                      <span style={{ fontFamily:'var(--font-data)', fontSize:11, color:'var(--text-secondary)' }}>
                        {(c.type_ratings||[]).join(' · ')||'—'}
                      </span>
                    </td>
                    <td>
                      <span style={{
                        fontFamily:'var(--font-data)', fontSize:12,
                        color: monthPct > 90 ? 'var(--status-red)' : monthPct > 75 ? 'var(--status-yellow)' : 'var(--text-primary)'
                      }}>
                        {c.flight_hours_month}h
                      </span>
                    </td>
                    <td><span className="td-mono">{c.flight_hours_year}h</span></td>
                    <td><span className="td-mono" style={{ fontSize:11 }}>{c.license_type || '—'}</span></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {selected && (
        <CrewDetailModal
          crew={selected}
          canEdit={can('edit_flights')}
          onClose={() => setSelected(null)}
          onStatusChanged={load}
        />
      )}
    </div>
  )
}
