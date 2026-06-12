import { useState, useEffect, useCallback } from 'react'
import { API } from '../context/AuthContext'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const STATUSES = ['scheduled','boarding','departed','en_route','approaching','landed','delayed','cancelled','diverted','on_ground']

function Badge({ status }) {
  const s = (status || '').toLowerCase().replace(/ /g, '_')
  return <span className={`badge badge-${s}`}>{(status || '').replace(/_/g, ' ')}</span>
}

function fmtUTC(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }) + 'Z'
}

function fmtDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }) + 'Z'
}

function EditModal({ flight, onClose, onSaved }) {
  const { addToast } = useToast()
  const [form, setForm] = useState({
    status: flight.status || '', gate: flight.gate || '',
    terminal: flight.terminal || '', delay_minutes: flight.delay_minutes || 0,
    delay_reason: flight.delay_reason || '', baggage_belt: flight.baggage_belt || '',
    check_in_desk: flight.check_in_desk || '', remarks: flight.remarks || '',
  })
  const [saving, setSaving] = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      const res = await API(`/api/flights/${flight.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ ...form, delay_minutes: Number(form.delay_minutes) }),
      })
      if (!res.ok) throw new Error((await res.json()).detail)
      addToast(`${flight.flight_number} updated`, 'success')
      onSaved(); onClose()
    } catch (e) { addToast(e.message, 'error') }
    finally { setSaving(false) }
  }

  const f = (k) => (v) => setForm(p => ({ ...p, [k]: v }))

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div>
            <div className="modal-title">Update {flight.flight_number}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              {flight.origin_iata} → {flight.dest_iata} · {flight.aircraft_reg}
            </div>
          </div>
          <button className="icon-btn" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div className="form-group">
              <label>Status</label>
              <select value={form.status} onChange={e => f('status')(e.target.value)}>
                {STATUSES.map(s => <option key={s} value={s}>{s.replace(/_/g,' ')}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Gate</label>
              <input value={form.gate} onChange={e => f('gate')(e.target.value)} placeholder="e.g. G14" />
            </div>
            <div className="form-group">
              <label>Terminal</label>
              <input value={form.terminal} onChange={e => f('terminal')(e.target.value)} placeholder="e.g. T3" />
            </div>
            <div className="form-group">
              <label>Delay (min)</label>
              <input type="number" value={form.delay_minutes} onChange={e => f('delay_minutes')(e.target.value)} min={0} />
            </div>
          </div>
          <div className="form-group">
            <label>Delay Reason</label>
            <input value={form.delay_reason} onChange={e => f('delay_reason')(e.target.value)} placeholder="e.g. Late inbound aircraft" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div className="form-group">
              <label>Check-in</label>
              <input value={form.check_in_desk} onChange={e => f('check_in_desk')(e.target.value)} placeholder="D21-D26" />
            </div>
            <div className="form-group">
              <label>Baggage Belt</label>
              <input value={form.baggage_belt} onChange={e => f('baggage_belt')(e.target.value)} placeholder="Belt 7" />
            </div>
          </div>
          <div className="form-group">
            <label>Remarks</label>
            <textarea value={form.remarks} onChange={e => f('remarks')(e.target.value)} rows={2} />
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button className="btn btn-primary" onClick={save} disabled={saving}>
              {saving ? <span className="loading-ring" /> : 'Save'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function DetailModal({ flight, onClose, onEdit, canEdit }) {
  const row = (label, value, mono) => (
    <div style={{ display:'flex', justifyContent:'space-between', padding:'7px 0', borderBottom:'1px solid var(--border)', gap:12, flexWrap:'wrap' }}>
      <span style={{ fontSize:12, color:'var(--text-muted)', flexShrink:0 }}>{label}</span>
      <span style={{ fontSize:13, fontFamily:mono?'var(--font-data)':undefined, textAlign:'right' }}>{value||'—'}</span>
    </div>
  )
  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <div>
            <div style={{ display:'flex', alignItems:'center', gap:8, flexWrap:'wrap' }}>
              <span style={{ fontFamily:'var(--font-data)', fontSize:18, fontWeight:700, color:'var(--accent)' }}>{flight.flight_number}</span>
              <Badge status={flight.status} />
              {flight.live_tracking && (
                <span style={{ fontSize:11, color:'var(--status-green)', display:'flex', alignItems:'center', gap:4 }}>
                  <span className="live-dot" />LIVE
                </span>
              )}
            </div>
            <div style={{ fontSize:13, color:'var(--text-muted)', marginTop:2 }}>
              EgyptAir · {flight.origin_city} → {flight.dest_city}
            </div>
          </div>
          <div style={{ display:'flex', gap:6 }}>
            {canEdit && <button className="btn btn-primary btn-sm" onClick={onEdit}>Edit</button>}
            <button className="icon-btn" onClick={onClose}>✕</button>
          </div>
        </div>
        <div className="modal-body">
          {row('Route',          `${flight.origin_iata} → ${flight.dest_iata}`, true)}
          {row('Aircraft',       `${flight.aircraft_reg} · ${flight.aircraft_type}`, true)}
          {row('Callsign',       flight.callsign, true)}
          {row('Sched. Dep',     fmtDateTime(flight.scheduled_dep), true)}
          {row('Sched. Arr',     fmtDateTime(flight.scheduled_arr), true)}
          {row('Terminal / Gate',`${flight.terminal||'—'} / ${flight.gate||'—'}`, true)}
          {row('Check-in',       flight.check_in_desk)}
          {row('Baggage Belt',   flight.baggage_belt)}
          {row('Delay',          flight.delay_minutes > 0 ? `+${flight.delay_minutes}m — ${flight.delay_reason||''}` : 'None')}
          {row('Passengers',     flight.total_seats ? `${flight.passengers_booked} / ${flight.total_seats}` : null)}
          {flight.altitude_ft && row('Position', `${flight.altitude_ft?.toLocaleString()} ft · ${flight.speed_kts} kts`, true)}
          {flight.latitude && row('Coordinates', `${flight.latitude?.toFixed(2)}°, ${flight.longitude?.toFixed(2)}°`, true)}
          {flight.remarks && (
            <div style={{ marginTop:10, padding:10, background:'var(--bg-hover)', borderRadius:'var(--radius-sm)', fontSize:12, color:'var(--text-secondary)' }}>
              {flight.remarks}
            </div>
          )}
          {flight.crew?.length > 0 && (
            <div style={{ marginTop:14 }}>
              <div style={{ fontSize:11, fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:8 }}>Assigned Crew</div>
              {flight.crew.map((c,i) => (
                <div key={i} style={{ display:'flex', justifyContent:'space-between', padding:'6px 0', borderBottom:'1px solid var(--border)', fontSize:13 }}>
                  <span>{c.full_name} <span style={{ color:'var(--text-muted)', fontSize:11 }}>({c.employee_id})</span></span>
                  <span style={{ color:'var(--text-muted)', fontSize:11, textTransform:'capitalize' }}>{c.role.replace(/_/g,' ')}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function FlightsPage() {
  const { can } = useAuth()
  const [flights,  setFlights]  = useState([])
  const [total,    setTotal]    = useState(0)
  const [liveData, setLiveData] = useState(false)
  const [loading,  setLoading]  = useState(true)
  const [search,   setSearch]   = useState('')
  const [filter,   setFilter]   = useState('all')
  const [selected, setSelected] = useState(null)
  const [editing,  setEditing]  = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (filter !== 'all') params.set('status', filter)
    params.set('limit', '100')
    API(`/api/flights/?${params}`).then(r => r.json()).then(d => {
      setFlights(d.flights || [])
      setTotal(d.total || 0)
      setLiveData(d.live_data || false)
      setLoading(false)
    })
  }, [search, filter])

  useEffect(() => { load() }, [load])

  const loadDetail = async (f) => {
    const res  = await API(`/api/flights/${f.id}`)
    const data = await res.json()
    setSelected(data)
  }

  const liveCount = flights.filter(f => f.live_tracking).length

  const STATUS_FILTERS = [
    { key:'all', label:'All' }, { key:'scheduled', label:'Scheduled' },
    { key:'boarding', label:'Boarding' }, { key:'departed', label:'Departed' },
    { key:'en_route', label:'En Route' }, { key:'approaching', label:'Approaching' },
    { key:'landed', label:'Landed' }, { key:'delayed', label:'Delayed' },
    { key:'cancelled', label:'Cancelled' },
  ]

  return (
    <div>
      <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', flexWrap:'wrap', gap:8, marginBottom:2 }}>
        <div className="page-title">Flight Operations</div>
        {liveCount > 0 && (
          <span style={{ fontSize:12, color:'var(--status-green)', display:'flex', alignItems:'center', gap:4, marginTop:4 }}>
            <span className="live-dot" />{liveCount} live via OpenSky
          </span>
        )}
      </div>
      <div className="page-subtitle">EgyptAir · Cairo International · {total} flights</div>

      <div style={{ marginBottom:14 }}>
        <div className="search-bar" style={{ marginBottom:10 }}>
          <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search flight, route, aircraft…" />
        </div>
        <div className="filters-row">
          {STATUS_FILTERS.map(f => (
            <button key={f.key} className={`filter-btn ${filter===f.key?'active':''}`} onClick={() => setFilter(f.key)}>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="loading-center"><div className="loading-ring" /></div>
      ) : flights.length === 0 ? (
        <div className="empty-state"><div className="empty-state-icon">✈</div><p>No flights match your filters.</p></div>
      ) : (
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
                <th>Live</th>
              </tr>
            </thead>
            <tbody>
              {flights.map(f => (
                <tr key={f.id} onClick={() => loadDetail(f)}>
                  <td><span className="td-flight-num">{f.flight_number}</span></td>
                  <td>
                    <span className="td-mono">{f.origin_iata}</span>
                    <span style={{ color:'var(--text-muted)', margin:'0 3px' }}>→</span>
                    <span className="td-mono">{f.dest_iata}</span>
                  </td>
                  <td><span className="td-mono">{f.aircraft_reg}</span></td>
                  <td><span className="td-mono">{fmtUTC(f.scheduled_dep)}</span></td>
                  <td><span className="td-mono">{fmtUTC(f.scheduled_arr)}</span></td>
                  <td><span className="td-mono">{f.gate||'—'}</span></td>
                  <td><Badge status={f.status} /></td>
                  <td>
                    {f.delay_minutes > 0
                      ? <span style={{ color:'var(--status-yellow)', fontFamily:'var(--font-data)', fontSize:12, fontWeight:600 }}>+{f.delay_minutes}m</span>
                      : <span style={{ color:'var(--text-muted)', fontSize:12 }}>—</span>}
                  </td>
                  <td>
                    {f.live_tracking
                      ? <span className="live-dot" title="Live OpenSky data" />
                      : <span style={{ color:'var(--text-muted)', fontSize:11 }}>—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selected && !editing && (
        <DetailModal flight={selected} canEdit={can('edit_flights')}
          onEdit={() => setEditing(selected)} onClose={() => setSelected(null)} />
      )}
      {editing && (
        <EditModal flight={editing}
          onClose={() => { setEditing(null); setSelected(null) }} onSaved={load} />
      )}
    </div>
  )
}
