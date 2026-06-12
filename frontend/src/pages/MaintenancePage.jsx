import { useState, useEffect, useCallback } from 'react'
import { API } from '../context/AuthContext'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

function Badge({ val, type = 'status' }) {
  const s = (val || '').toLowerCase().replace(/ /g, '_')
  return <span className={`badge badge-${s}`}>{(val || '').replace(/_/g, ' ')}</span>
}

function PriorityDot({ priority }) {
  const colors = { aog: 'var(--status-red)', urgent: 'var(--status-yellow)', routine: 'var(--status-green)' }
  return <span style={{ display:'inline-block', width:8, height:8, borderRadius:'50%', background: colors[priority] || 'var(--text-muted)', marginRight:6 }} />
}

function TaskDetailModal({ task, onClose, canEdit, onUpdate }) {
  const { addToast } = useToast()
  const [form, setForm] = useState({
    status: task.status || '',
    findings: task.findings || '',
    corrective_action: task.corrective_action || '',
    man_hours_actual: task.man_hours_actual || '',
    approved_by: task.approved_by || '',
  })
  const [saving, setSaving] = useState(false)

  const save = async () => {
    setSaving(true)
    try {
      const res = await API(`/api/maintenance/tasks/${task.id}`, {
        method:'PATCH',
        body: JSON.stringify({ ...form, man_hours_actual: form.man_hours_actual ? Number(form.man_hours_actual) : undefined }),
      })
      if (!res.ok) throw new Error((await res.json()).detail)
      addToast(`Task ${task.task_number} updated`, 'success')
      onUpdate(); onClose()
    } catch(e) { addToast(e.message, 'error') }
    finally { setSaving(false) }
  }

  const fmtDT = (iso) => {
    if (!iso) return '—'
    return new Date(iso).toLocaleString('en-GB', { day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit', timeZone:'UTC' }) + 'Z'
  }

  const row = (label, val, mono) => (
    <div style={{ display:'flex', justifyContent:'space-between', padding:'7px 0', borderBottom:'1px solid var(--border)', gap:12, flexWrap:'wrap' }}>
      <span style={{ fontSize:12, color:'var(--text-muted)', flexShrink:0 }}>{label}</span>
      <span style={{ fontSize:13, fontFamily:mono?'var(--font-data)':undefined, textAlign:'right', wordBreak:'break-word' }}>{val||'—'}</span>
    </div>
  )

  const TASK_STATUSES = ['scheduled','in_progress','on_hold','completed','deferred','cancelled']

  return (
    <div className="modal-overlay" onClick={e => e.target===e.currentTarget && onClose()}>
      <div className="modal" style={{ maxWidth:600 }}>
        <div className="modal-header">
          <div>
            <div style={{ display:'flex', alignItems:'center', gap:8, flexWrap:'wrap' }}>
              <span style={{ fontFamily:'var(--font-data)', fontSize:14, color:'var(--accent)' }}>{task.task_number}</span>
              <Badge val={task.status} />
              <Badge val={task.priority} />
            </div>
            <div style={{ fontSize:15, fontWeight:700, marginTop:4 }}>{task.title}</div>
            <div style={{ fontSize:12, color:'var(--text-muted)' }}>{task.aircraft_reg} · {task.ata_chapter} — {task.ata_description}</div>
          </div>
          <button className="icon-btn" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          {row('Scheduled Start',  fmtDT(task.scheduled_start))}
          {row('Scheduled End',    fmtDT(task.scheduled_end))}
          {row('Actual Start',     fmtDT(task.actual_start))}
          {row('Actual End',       fmtDT(task.actual_end))}
          {row('Lead Technician',  task.lead_technician)}
          {row('Hangar / Bay',     task.hangar_bay)}
          {row('Man-Hours Est.',   task.man_hours_est ? `${task.man_hours_est}h` : null)}
          {row('Work Order',       task.work_order_ref, true)}
          {task.ad_number && row('AD / SB',   task.ad_number, true)}
          {row('Parts Cost',       task.parts_cost_usd ? `USD ${task.parts_cost_usd?.toLocaleString()}` : null)}
          {row('Labor Cost',       task.labor_cost_usd  ? `USD ${task.labor_cost_usd?.toLocaleString()}`  : null)}

          {task.description && (
            <div style={{ margin:'12px 0', padding:12, background:'var(--bg-hover)', borderRadius:'var(--radius-sm)', fontSize:13, color:'var(--text-secondary)', lineHeight:1.6 }}>
              {task.description}
            </div>
          )}

          {task.findings && row('Findings', task.findings)}

          {canEdit && (
            <>
              <div className="divider" />
              <div style={{ fontSize:12, fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.06em', marginBottom:12 }}>Update Task</div>
              <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
                <div className="form-group">
                  <label>Status</label>
                  <select value={form.status} onChange={e => setForm(p=>({...p, status:e.target.value}))}>
                    {TASK_STATUSES.map(s => <option key={s} value={s}>{s.replace(/_/g,' ')}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Findings</label>
                  <textarea value={form.findings} onChange={e => setForm(p=>({...p,findings:e.target.value}))} rows={2} placeholder="What was found during inspection…" />
                </div>
                <div className="form-group">
                  <label>Corrective Action</label>
                  <textarea value={form.corrective_action} onChange={e => setForm(p=>({...p,corrective_action:e.target.value}))} rows={2} placeholder="Action taken…" />
                </div>
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
                  <div className="form-group">
                    <label>Actual Hours</label>
                    <input type="number" value={form.man_hours_actual} onChange={e => setForm(p=>({...p,man_hours_actual:e.target.value}))} min={0} step={0.5} />
                  </div>
                  <div className="form-group">
                    <label>Approved By</label>
                    <input value={form.approved_by} onChange={e => setForm(p=>({...p,approved_by:e.target.value}))} placeholder="Licensed AME name" />
                  </div>
                </div>
                <div style={{ display:'flex', gap:8, justifyContent:'flex-end' }}>
                  <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
                  <button className="btn btn-primary" onClick={save} disabled={saving}>
                    {saving ? <span className="loading-ring" /> : 'Save Update'}
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function MaintenancePage() {
  const { can } = useAuth()
  const [tab,      setTab]     = useState('tasks')
  const [tasks,    setTasks]   = useState([])
  const [aircraft, setAircraft] = useState([])
  const [mel,      setMel]     = useState([])
  const [aog,      setAog]     = useState([])
  const [stats,    setStats]   = useState(null)
  const [loading,  setLoading] = useState(true)
  const [filter,   setFilter]  = useState('all')
  const [selected, setSelected] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    const params = new URLSearchParams()
    if (filter !== 'all') params.set('priority', filter)
    Promise.all([
      API(`/api/maintenance/tasks?${params}`).then(r => r.json()),
      API('/api/maintenance/aircraft').then(r => r.json()),
      API('/api/maintenance/mel').then(r => r.json()),
      API('/api/maintenance/aog').then(r => r.json()),
      API('/api/maintenance/stats/summary').then(r => r.json()),
    ]).then(([t, a, m, g, s]) => {
      setTasks(t.tasks || [])
      setAircraft(a.aircraft || [])
      setMel(m.mel_items || [])
      setAog(g.aog_records || [])
      setStats(s)
      setLoading(false)
    })
  }, [filter])

  useEffect(() => { load() }, [load])

  const loadTask = async (t) => {
    const res = await API(`/api/maintenance/tasks/${t.id}`)
    const data = await res.json()
    setSelected({ ...data, _type: 'task' })
  }

  const fmtDate = (iso) => {
    if (!iso) return '—'
    if (!iso.includes('T')) return iso  // Already a date string
    return new Date(iso).toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'2-digit' })
  }

  const PRIORITY_FILTERS = [
    { key:'all', label:'All Priority' },
    { key:'aog', label:'AOG' },
    { key:'urgent', label:'Urgent' },
    { key:'routine', label:'Routine' },
  ]

  return (
    <div>
      <div className="page-title">Maintenance Operations</div>
      <div className="page-subtitle">Fleet status, tasks, MEL items, and AOG management</div>

      {/* Stats */}
      {stats && (
        <div className="stats-grid">
          {[
            { label:'Fleet Size',       value: stats.total_aircraft,    color:'' },
            { label:'Aircraft AOG',     value: stats.aog_count,         color: stats.aog_count>0?'red':'' },
            { label:'Tasks Active',     value: stats.tasks_in_progress, color:'accent' },
            { label:'Open MEL',         value: stats.open_mel_items,    color: stats.open_mel_items>0?'yellow':'' },
            { label:'AOG Priority',     value: stats.aog_priority_tasks, color: stats.aog_priority_tasks>0?'red':'' },
          ].map(s => (
            <div className="stat-card" key={s.label}>
              <div className="stat-label">{s.label}</div>
              <div className={`stat-value ${s.color}`}>{s.value??'—'}</div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display:'flex', gap:4, marginBottom:16, borderBottom:'1px solid var(--border)', paddingBottom:0 }}>
        {[
          { key:'tasks',    label:`Tasks (${tasks.length})` },
          { key:'aircraft', label:`Fleet (${aircraft.length})` },
          { key:'mel',      label:`MEL (${mel.length})` },
          { key:'aog',      label:`AOG (${aog.length})` },
        ].map(t => (
          <button key={t.key} onClick={() => setTab(t.key)} style={{
            padding:'8px 16px', background:'none', border:'none', cursor:'pointer',
            fontSize:14, fontWeight:600, color: tab===t.key ? 'var(--accent)' : 'var(--text-secondary)',
            borderBottom: tab===t.key ? '2px solid var(--accent)' : '2px solid transparent',
            marginBottom:-1, transition:'all 0.15s', fontFamily:'var(--font-ui)',
          }}>{t.label}</button>
        ))}
      </div>

      {/* Filters (tasks only) */}
      {tab === 'tasks' && (
        <div className="filters-row">
          {PRIORITY_FILTERS.map(f => (
            <button key={f.key} className={`filter-btn ${filter===f.key?'active':''}`} onClick={() => setFilter(f.key)}>
              {f.label}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="loading-center"><div className="loading-ring" /></div>
      ) : (
        <>
          {/* TASKS TAB */}
          {tab === 'tasks' && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Priority</th>
                    <th>Task No.</th>
                    <th>Aircraft</th>
                    <th>Type</th>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Scheduled</th>
                    <th>Lead Tech</th>
                    <th>WO Ref</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map(t => (
                    <tr key={t.id} onClick={() => loadTask(t)}>
                      <td><PriorityDot priority={t.priority} /><Badge val={t.priority} /></td>
                      <td><span className="td-mono" style={{ fontSize:11 }}>{t.task_number}</span></td>
                      <td><span className="td-mono">{t.aircraft_reg}</span></td>
                      <td style={{ fontSize:12 }}>{t.check_type?.replace(/_/g,' ')}</td>
                      <td style={{ maxWidth:200 }}><span className="truncate" style={{ display:'block', fontSize:13 }}>{t.title}</span></td>
                      <td><Badge val={t.status} /></td>
                      <td><span className="td-mono">{fmtDate(t.scheduled_start)}</span></td>
                      <td style={{ fontSize:12 }}>{t.lead_technician?.split(' ').slice(0,2).join(' ') || '—'}</td>
                      <td><span className="td-mono" style={{ fontSize:11 }}>{t.work_order_ref || '—'}</span></td>
                    </tr>
                  ))}
                  {tasks.length === 0 && (
                    <tr><td colSpan={9} style={{ textAlign:'center', color:'var(--text-muted)', padding:32 }}>No tasks match filters</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* FLEET TAB */}
          {tab === 'aircraft' && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Registration</th>
                    <th>Type</th>
                    <th>Airline</th>
                    <th>Location</th>
                    <th>Total Hours</th>
                    <th>Cycles</th>
                    <th>Last A-Check</th>
                    <th>Next C-Check</th>
                    <th>Open MEL</th>
                    <th>AOG</th>
                  </tr>
                </thead>
                <tbody>
                  {aircraft.map(a => (
                    <tr key={a.id} style={{ opacity: a.is_aog ? 0.7 : 1 }}>
                      <td>
                        <span className="td-mono" style={{ fontWeight:700 }}>{a.registration}</span>
                        {a.is_aog && <span className="badge badge-aog" style={{ marginLeft:6, fontSize:10 }}>AOG</span>}
                      </td>
                      <td style={{ fontSize:12 }}>{a.aircraft_type}</td>
                      <td style={{ fontSize:12 }}>{a.airline_name}</td>
                      <td><span className="td-mono">{a.current_airport || '—'}</span></td>
                      <td><span className="td-mono">{a.total_flight_hours?.toLocaleString()}h</span></td>
                      <td><span className="td-mono">{a.total_cycles?.toLocaleString()}</span></td>
                      <td><span className="td-mono" style={{ fontSize:11 }}>{a.hours_since_last_a}h ago</span></td>
                      <td>
                        <span className="td-mono" style={{ fontSize:11, color: a.next_c_check_due < '2025-01-01' ? 'var(--status-yellow)' : undefined }}>
                          {a.next_c_check_due || '—'}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontFamily:'var(--font-data)', color: a.open_mel_items>0 ? 'var(--status-yellow)' : 'var(--text-muted)' }}>
                          {a.open_mel_items}
                        </span>
                      </td>
                      <td>
                        <span style={{ color: a.active_aog>0 ? 'var(--status-red)' : 'var(--text-muted)', fontFamily:'var(--font-data)' }}>
                          {a.active_aog > 0 ? '● Active' : '—'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* MEL TAB */}
          {tab === 'mel' && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>MEL Number</th>
                    <th>Aircraft</th>
                    <th>ATA</th>
                    <th>Description</th>
                    <th>Category</th>
                    <th>Raised</th>
                    <th>Expires</th>
                    <th>Raised By</th>
                  </tr>
                </thead>
                <tbody>
                  {mel.map(m => (
                    <tr key={m.id}>
                      <td><span className="td-mono">{m.mel_number}</span></td>
                      <td>
                        {aircraft.find(a => a.id === m.aircraft_id)?.registration
                          ? <span className="td-mono">{aircraft.find(a => a.id === m.aircraft_id)?.registration}</span>
                          : '—'}
                      </td>
                      <td><span className="td-mono" style={{ fontSize:11 }}>{m.ata_chapter || '—'}</span></td>
                      <td style={{ maxWidth:250 }}><span className="truncate" style={{ display:'block', fontSize:13 }}>{m.description}</span></td>
                      <td>
                        <span className="badge" style={{
                          background: m.category==='A' ? 'rgba(239,68,68,0.12)' : m.category==='B' ? 'rgba(245,158,11,0.12)' : 'rgba(59,130,246,0.12)',
                          color: m.category==='A' ? 'var(--status-red)' : m.category==='B' ? 'var(--status-yellow)' : 'var(--status-blue)',
                        }}>Cat-{m.category}</span>
                      </td>
                      <td><span className="td-mono">{m.raised_date}</span></td>
                      <td><span className="td-mono" style={{ color: m.expiry_date < new Date().toISOString().slice(0,10) ? 'var(--status-red)' : undefined }}>{m.expiry_date}</span></td>
                      <td style={{ fontSize:12 }}>{m.raised_by}</td>
                    </tr>
                  ))}
                  {mel.length === 0 && <tr><td colSpan={8} style={{ textAlign:'center', color:'var(--text-muted)', padding:32 }}>No active MEL items</td></tr>}
                </tbody>
              </table>
            </div>
          )}

          {/* AOG TAB */}
          {tab === 'aog' && (
            aog.length === 0 ? (
              <div className="empty-state"><div className="empty-state-icon" style={{ color:'var(--status-green)' }}>✓</div><p>No active AOG events. All aircraft operational.</p></div>
            ) : (
              aog.map(g => (
                <div key={g.id} className="card" style={{ marginBottom:16, borderColor:'rgba(239,68,68,0.25)' }}>
                  <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:12, flexWrap:'wrap' }}>
                    <div>
                      <div style={{ display:'flex', alignItems:'center', gap:10, flexWrap:'wrap' }}>
                        <span style={{ fontFamily:'var(--font-data)', fontSize:16, fontWeight:700, color:'var(--status-red)' }}>{g.aircraft_reg}</span>
                        <span className="td-mono" style={{ fontSize:13 }}>{g.aog_ref}</span>
                        <Badge val={g.status} />
                      </div>
                      <div style={{ marginTop:6, fontSize:13, color:'var(--text-secondary)', lineHeight:1.6 }}>{g.fault_description}</div>
                    </div>
                    <div style={{ textAlign:'right', flexShrink:0 }}>
                      <div style={{ fontSize:11, color:'var(--text-muted)' }}>Location</div>
                      <div style={{ fontFamily:'var(--font-data)', fontSize:18, fontWeight:700 }}>{g.location}</div>
                    </div>
                  </div>
                  <div style={{ marginTop:12, display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(200px, 1fr))', gap:10 }}>
                    <div>
                      <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:4 }}>ATA Chapter</div>
                      <div style={{ fontFamily:'var(--font-data)', fontSize:13 }}>{g.ata_chapter || '—'}</div>
                    </div>
                    <div>
                      <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:4 }}>Estimated TAT</div>
                      <div style={{ fontSize:13, fontWeight:600 }}>{g.estimated_tat || 'TBD'}</div>
                    </div>
                    <div>
                      <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:4 }}>Affected Flights</div>
                      <div style={{ fontSize:12 }}>{(g.affected_flights||[]).join(', ') || 'None'}</div>
                    </div>
                    <div>
                      <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:4 }}>Parts on Order</div>
                      <div style={{ fontSize:12, color:'var(--status-yellow)' }}>{(g.parts_on_order||[]).join(', ') || 'None'}</div>
                    </div>
                  </div>
                  {g.notes && (
                    <div style={{ marginTop:10, padding:'8px 12px', background:'var(--bg-hover)', borderRadius:'var(--radius-sm)', fontSize:12, color:'var(--text-secondary)' }}>
                      📋 {g.notes}
                    </div>
                  )}
                </div>
              ))
            )
          )}
        </>
      )}

      {selected?._type === 'task' && (
        <TaskDetailModal
          task={selected}
          canEdit={can('edit_maintenance')}
          onClose={() => setSelected(null)}
          onUpdate={load}
        />
      )}
    </div>
  )
}
