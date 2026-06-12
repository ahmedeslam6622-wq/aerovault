import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login, loginSuperuser } = useAuth()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [totpCode, setTotpCode] = useState('')
  const [step, setStep]         = useState('credentials') // 'credentials' | 'totp'
  const [suUsername, setSuUsername] = useState('')
  const [suPassword, setSuPassword] = useState('')
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')

  const handleLogin = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const res = await login(username, password)
      if (res.requiresTotp) {
        setSuUsername(res.username); setSuPassword(password)
        setStep('totp')
      } else {
        navigate('/dashboard')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleTotp = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      await loginSuperuser(suUsername, suPassword, totpCode)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
      setTotpCode('')
    } finally {
      setLoading(false)
    }
  }

  const PlaneIcon = () => (
    <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="var(--accent)" strokeWidth="1.5">
      <path d="M22 16.5L12 2 2 16.5l4-1.5 6 4 6-4 4 1.5z"/>
    </svg>
  )

  const ShieldIcon = () => (
    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="var(--accent)" strokeWidth="1.5">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      <path d="M9 12l2 2 4-4"/>
    </svg>
  )

  const accounts = [
    { username: 'ahmed.hassan',   role: 'Admin',             password: 'Admin#Cairo1' },
    { username: 'omar.nasser',    role: 'Flight Manager',     password: 'Flight@Ops1' },
    { username: 'mahmoud.sayed',  role: 'Maint. Chief',       password: 'Maint#Chief1' },
    { username: 'karim.ali',      role: 'Viewer',             password: 'Worker@Cairo1' },
  ]

  return (
    <div style={{
      minHeight: '100dvh', display: 'flex', flexDirection: 'column',
      background: 'var(--bg-base)', alignItems: 'center', justifyContent: 'center',
      padding: '24px 16px',
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 32 }}>
        <PlaneIcon />
        <div>
          <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.03em' }}>AeroVault</div>
          <div style={{ fontSize: 11, fontFamily: 'var(--font-data)', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Cairo Intl · CAI/HECA
          </div>
        </div>
      </div>

      {step === 'credentials' ? (
        <div style={{ width: '100%', maxWidth: 400 }}>
          <div className="card" style={{ marginBottom: 20 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>Sign in</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 20 }}>
              Use your staff credentials to access AeroVault.
            </p>

            {error && (
              <div style={{
                background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)',
                borderRadius: 'var(--radius-sm)', padding: '10px 14px',
                color: 'var(--status-red)', fontSize: 13, marginBottom: 16,
              }}>
                {error}
              </div>
            )}

            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="form-group">
                <label>Username</label>
                <input
                  value={username} onChange={e => setUsername(e.target.value)}
                  placeholder="e.g. omar.nasser" required autoFocus
                  autoComplete="username"
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password" value={password} onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••" required autoComplete="current-password"
                />
              </div>
              <button type="submit" className="btn btn-primary" style={{ marginTop: 4, justifyContent: 'center' }} disabled={loading}>
                {loading ? <span className="loading-ring" /> : 'Sign in'}
              </button>
            </form>
          </div>

          {/* Demo accounts */}
          <div className="card">
            <div className="card-title" style={{ marginBottom: 10, fontSize: 12, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>
              Demo Accounts
            </div>
            {accounts.map(a => (
              <button
                key={a.username}
                onClick={() => { setUsername(a.username); setPassword(a.password) }}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  width: '100%', padding: '8px 10px', marginBottom: 4,
                  background: 'var(--bg-hover)', border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                  color: 'var(--text-primary)',
                }}
              >
                <span style={{ fontFamily: 'var(--font-data)', fontSize: 13 }}>{a.username}</span>
                <span style={{ fontSize: 11, color: 'var(--text-muted)', background: 'var(--bg-surface)', padding: '2px 8px', borderRadius: 20 }}>{a.role}</span>
              </button>
            ))}
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8 }}>
              Superuser login requires Google Authenticator — see setup guide.
            </div>
          </div>
        </div>
      ) : (
        <div style={{ width: '100%', maxWidth: 400 }}>
          <div className="card">
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <ShieldIcon />
              <h2 style={{ fontSize: 18, fontWeight: 700, marginTop: 12, marginBottom: 4 }}>
                Two-Factor Verification
              </h2>
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                Open Google Authenticator and enter the 6-digit code for <strong style={{ color: 'var(--text-primary)' }}>AeroVault</strong>. Codes refresh every 30 seconds.
              </p>
            </div>

            {error && (
              <div style={{
                background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)',
                borderRadius: 'var(--radius-sm)', padding: '10px 14px',
                color: 'var(--status-red)', fontSize: 13, marginBottom: 16,
              }}>
                {error}
              </div>
            )}

            <form onSubmit={handleTotp} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div className="form-group">
                <label>Authenticator Code</label>
                <input
                  value={totpCode}
                  onChange={e => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000 000"
                  required autoFocus maxLength={6}
                  style={{ fontFamily: 'var(--font-data)', fontSize: 24, textAlign: 'center', letterSpacing: '0.2em' }}
                  inputMode="numeric"
                />
              </div>
              <button type="submit" className="btn btn-primary" style={{ justifyContent: 'center' }} disabled={loading || totpCode.length < 6}>
                {loading ? <span className="loading-ring" /> : 'Verify & Sign in'}
              </button>
              <button type="button" className="btn btn-secondary" style={{ justifyContent: 'center' }} onClick={() => { setStep('credentials'); setError('') }}>
                ← Back
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
