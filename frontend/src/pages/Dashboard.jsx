import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { API } from '../context/AuthContext'
import { useAuth } from '../context/AuthContext'

function StatusBadge({ status }) {
  const s = (status || '').toLowerCase().replace(' ', '_')
  return <span className={`badge badge-${s}`}>{status?.replace('_', ' ')}</span>
}

function StatCard({ label, value, sub, color }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${color || ''}`}>{value ?? '—'}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [flights, setFlights]     = useState([])
  const [fStats,  setFStats]      = useState(null)
  const [cStats,  setCStats]      = useState(null)
  const [mStats,  setMStats]      = useState(null)
  const [aog,     setAog]         = useState([])
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    let mounted = true
    Promise.all([
      API('/api/flights/?limit=12').then(r => r.json()),
      API('/api/flights/stats/summary').then(r => r.json()),
      API('/api/crew/stats/summary').then(r => r.json()),
      API('/api/maintenance/stats/summary').then(r => r.json()),
      API('/api/maintenance/aog').then(r => r.json()),
    ]).then(([fl, fs, cs, ms, aogData]) => {
      if (!mounted) return
      setFlights(fl.flights || [])
      setFStats(fs)
      setCStats(cs)
      setMStats(ms)
      setAog(aogData.aog_records || [])
      setLoading(false)
    }).catch(() => setLoading(false))
    return () => { mounted = false }
  }, [])

  const fmtTime = (iso) => {
    if (!iso) return '—'
    const d = new Date(iso)
    return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }) + 'Z'
  }

  if (loading) return (
    <div className="loading-center">
      <div className="loading-ring" style={{ width: 32, height: 32 }} />
      <span>Loading operations data…</span>
    </div>
  )

  return (
    <div>
      <div className="page-title">Good {greeting()}, {user?.full_name?.split(' ')[1] || user?.full_name}</div>
      <div className="page-subtitle">Cairo International Airport · CAI/HECA · All times UTC</div>

      {/* AOG Alerts */}
      {aog.length > 0 && aog.map(a => (
        <div key={a.id} className="aog-banner" onClick={() => navigate('/maintenance')} style={{ cursor: 'pointer' }}>
          <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <strong>AOG — {a.aircraft_reg}</strong>
          <span style={{ fontWeight: 400 }}>: {a.fault_description?.slice(0, 80)}{a.fault_description?.length > 80 ? '…' : ''}</span>
          <span style={{ marginLeft: 'auto', fontSize: 11, opacity: 0.7 }}>ETA: {a.estimated_tat || 'TBD'}</span>
        </div>
      ))}

      {/* Stats */}
      <div className="stats-grid">
        <StatCard label="Total Flights"     value={fStats?.total}     sub="Today's schedule" />
        <StatCard label="Delayed"           value={fStats?.delayed}   color={fStats?.delayed > 0 ? 'yellow' : 'green'} sub="Awaiting update" />
        <StatCard label="Cancelled"         value={fStats?.cancelled} color={fStats?.cancelled > 0 ? 'red' : ''} sub="Today" />
        <StatCard label="Crew on Duty"      value={cStats?.on_duty}   color="accent" sub={`${cStats?.available || 0} available`} />
        <StatCard label="Aircraft AOG"      value={mStats?.aog_count} color={mStats?.aog_count > 0 ? 'red' : 'green'} sub="Grounded" />
        <StatCard label="Open MEL Items"    value={mStats?.open_mel_items} sub="Active deferrals" />
      </div>

      {/* Flight Board */}
      <div className="card">
        <div className="card-header">
          <div>
            <div className="card-title">Live Flight Board</div>
            <div className="card-sub">Most recent / upcoming operations</div>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/flights')}>
            View all →
          </button>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Flight</th>
                <th>Route</th>
                <th>Aircraft</th>
                <th>STD</th>
                <th>STA</th>
                <th>Gate</th>
                <th>Status</th>
                <th>Delay</th>
              </tr>
            </thead>
            <tbody>
              {flights.length === 0 && (
                <tr><td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No flights loaded</td></tr>
              )}
              {flights.map(f => (
                <tr key={f.id} onClick={() => navigate('/flights')}>
                  <td><span className="td-flight-num">{f.flight_number}</span></td>
                  <td>
                    <span className="td-mono">{f.origin_iata}</span>
                    <span style={{ color: 'var(--text-muted)', margin: '0 4px' }}>→</span>
                    <span className="td-mono">{f.dest_iata}</span>
                  </td>
                  <td><span className="td-mono">{f.aircraft_reg}</span></td>
                  <td><span className="td-mono">{fmtTime(f.scheduled_dep)}</span></td>
                  <td><span className="td-mono">{fmtTime(f.scheduled_arr)}</span></td>
                  <td><span className="td-mono">{f.gate || '—'}</span></td>
                  <td><StatusBadge status={f.status} /></td>
                  <td>
                    {f.delay_minutes > 0
                      ? <span style={{ color: 'var(--status-yellow)', fontFamily: 'var(--font-data)', fontSize: 12 }}>+{f.delay_minutes}m</span>
                      : <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>—</span>
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bottom row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginTop: 16 }}>
        {/* Crew summary */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Crew Status</div>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate('/crew')}>View →</button>
          </div>
          {cStats && Object.entries(cStats.by_status || {}).map(([status, count]) => (
            <div key={status} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid var(--border)' }}>
              <StatusBadge status={status} />
              <span style={{ fontFamily: 'var(--font-data)', fontSize: 14, fontWeight: 600 }}>{count}</span>
            </div>
          ))}
        </div>

        {/* Maintenance summary */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Maintenance Status</div>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate('/maintenance')}>View →</button>
          </div>
          {[
            { label: 'Aircraft Fleet',        value: mStats?.total_aircraft,     color: '' },
            { label: 'Aircraft AOG',           value: mStats?.aog_count,          color: mStats?.aog_count > 0 ? 'var(--status-red)' : 'var(--status-green)' },
            { label: 'Tasks In Progress',      value: mStats?.tasks_in_progress,  color: 'var(--accent)' },
            { label: 'Open MEL Items',         value: mStats?.open_mel_items,     color: 'var(--status-yellow)' },
            { label: 'AOG Priority Tasks',     value: mStats?.aog_priority_tasks, color: 'var(--status-red)' },
          ].map(row => (
            <div key={row.label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{row.label}</span>
              <span style={{ fontFamily: 'var(--font-data)', fontSize: 14, fontWeight: 600, color: row.color || 'var(--text-primary)' }}>{row.value ?? '—'}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function greeting() {
  const h = new Date().getUTCHours()
  if (h < 12) return 'morning'
  if (h < 18) return 'afternoon'
  return 'evening'
}
