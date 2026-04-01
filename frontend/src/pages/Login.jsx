import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google'
import { useAuth } from '../context/AuthContext'
import { authAPI } from '../utils/api'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '169755292585-6705iio0nl2gcadosa80fntkckopkktf.apps.googleusercontent.com'

function LoginPage() {
  const { loginWithGoogle, loginCustom, signupCustom, loginAsDev, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  // Views: LOGIN, SIGNUP, SIGNUP_OTP, FORGOT, FORGOT_OTP
  const [view, setView] = useState('LOGIN')

  // Form State
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [otp, setOtp] = useState('')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  useEffect(() => {
    if (isAuthenticated) navigate('/')
  }, [isAuthenticated, navigate])

  const clearMessages = () => { setError(''); setMsg(''); }

  const handleGoogleSuccess = async (credentialResponse) => {
    const result = await loginWithGoogle(credentialResponse.credential)
    if (result.success) {
      navigate('/')
    } else {
      setError(result.error || 'Google Login Failed via backend')
    }
  }

  const handleDevLogin = () => {
    loginAsDev()
    navigate('/')
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    clearMessages()
    setLoading(true)
    const result = await loginCustom(email, password)
    if (result.success) navigate('/')
    else setError(result.error)
    setLoading(false)
  }

  const handleSignupReq = async (e) => {
    e.preventDefault()
    clearMessages()
    setLoading(true)
    try {
      await authAPI.sendOtp(email, 'signup')
      setMsg('OTP sent to your email!')
      setView('SIGNUP_OTP')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP')
    }
    setLoading(false)
  }

  const handleSignupSubmit = async (e) => {
    e.preventDefault()
    clearMessages()
    setLoading(true)
    const result = await signupCustom(email, password, name, otp)
    if (result.success) navigate('/')
    else setError(result.error)
    setLoading(false)
  }

  const handleForgotReq = async (e) => {
    e.preventDefault()
    clearMessages()
    setLoading(true)
    try {
      await authAPI.sendOtp(email, 'reset_password')
      setMsg('OTP sent to your email!')
      setView('FORGOT_OTP')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP')
    }
    setLoading(false)
  }

  const handleForgotSubmit = async (e) => {
    e.preventDefault()
    clearMessages()
    setLoading(true)
    try {
      await authAPI.resetPassword({ email, otp, new_password: password })
      setMsg('Password reset successful! You can now login.')
      setView('LOGIN')
      setPassword('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password')
    }
    setLoading(false)
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', padding: '2rem' }}>
      <div className="card" style={{ maxWidth: '400px', width: '100%' }}>

        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <h1 style={{ fontSize: '1.5rem' }}>Indian Tax Analysis</h1>
          <p className="text-secondary" style={{ fontSize: '0.9rem' }}>
            {view === 'LOGIN' && 'Sign in to access your dashboard'}
            {view === 'SIGNUP' && 'Create your new account'}
            {(view === 'SIGNUP_OTP' || view === 'FORGOT_OTP') && 'Verify your Email'}
            {view === 'FORGOT' && 'Reset your password'}
          </p>
        </div>

        {error && <div className="alert alert-danger" style={{ padding: '0.75rem', marginBottom: '1rem', fontSize: '0.9rem' }}>{error}</div>}
        {msg && <div className="alert alert-success" style={{ padding: '0.75rem', marginBottom: '1rem', fontSize: '0.9rem' }}>{msg}</div>}

        {/* LOGIN VIEW */}
        {view === 'LOGIN' && (
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input type="email" required className="form-input" value={email} onChange={e => setEmail(e.target.value)} />
            </div>
            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <label className="form-label">Password</label>
                <span style={{ fontSize: '0.8rem', color: 'var(--primary-color)', cursor: 'pointer' }} onClick={() => { clearMessages(); setView('FORGOT'); }}>Forgot Password?</span>
              </div>
              <input type="password" required className="form-input" value={password} onChange={e => setPassword(e.target.value)} />
            </div>
            <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%', marginBottom: '1rem' }}>
              {loading ? 'Logging in...' : 'Sign In'}
            </button>
            <div style={{ textAlign: 'center', fontSize: '0.9rem', marginBottom: '1rem' }}>
              <span className="text-secondary">Don't have an account? </span>
              <span style={{ color: 'var(--primary-color)', cursor: 'pointer', fontWeight: '500' }} onClick={() => { clearMessages(); setView('SIGNUP'); }}>Sign up</span>
            </div>
            <div style={{ textAlign: 'center', margin: '1rem 0', color: 'var(--text-tertiary)', fontSize: '0.8rem' }}>OR</div>
            <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
                <GoogleLogin onSuccess={handleGoogleSuccess} onError={() => setError('Google Login Failed')} theme="outline" size="large" width="100%" />
              </div>
            </GoogleOAuthProvider>
            <button type="button" className="btn btn-secondary" onClick={handleDevLogin} style={{ width: '100%', fontSize: '0.85rem' }}>
              Continue as Developer (Testing Mode)
            </button>
          </form>
        )}

        {/* SIGNUP VIEW */}
        {view === 'SIGNUP' && (
          <form onSubmit={handleSignupReq}>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input type="text" required className="form-input" value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input type="email" required className="form-input" value={email} onChange={e => setEmail(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Create Password</label>
              <input type="password" required minLength="6" className="form-input" value={password} onChange={e => setPassword(e.target.value)} />
            </div>
            <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%', marginBottom: '1rem' }}>
              {loading ? 'Sending OTP...' : 'Next'}
            </button>
            <div style={{ textAlign: 'center', fontSize: '0.9rem' }}>
              <span className="text-secondary">Already have an account? </span>
              <span style={{ color: 'var(--primary-color)', cursor: 'pointer', fontWeight: '500' }} onClick={() => { clearMessages(); setView('LOGIN'); }}>Sign in</span>
            </div>
          </form>
        )}

        {/* SIGNUP OTP VIEW */}
        {view === 'SIGNUP_OTP' && (
          <form onSubmit={handleSignupSubmit}>
            <div className="form-group">
              <label className="form-label">Enter the 6-digit OTP sent to {email}</label>
              <input type="text" maxLength="6" required className="form-input" value={otp} onChange={e => setOtp(e.target.value)} style={{ textAlign: 'center', letterSpacing: '2px', fontSize: '1.2rem' }} />
            </div>
            <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%', marginBottom: '1rem' }}>
              {loading ? 'Verifying...' : 'Verify & Create Account'}
            </button>
            <div style={{ textAlign: 'center', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--text-secondary)', cursor: 'pointer' }} onClick={() => setView('SIGNUP')}>Back</span>
            </div>
          </form>
        )}

        {/* FORGOT PASSWORD VIEW */}
        {view === 'FORGOT' && (
          <form onSubmit={handleForgotReq}>
            <div className="form-group">
              <label className="form-label">Enter your registered email</label>
              <input type="email" required className="form-input" value={email} onChange={e => setEmail(e.target.value)} />
            </div>
            <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%', marginBottom: '1rem' }}>
              {loading ? 'Sending OTP...' : 'Send Reset OTP'}
            </button>
            <div style={{ textAlign: 'center', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--text-secondary)', cursor: 'pointer' }} onClick={() => { clearMessages(); setView('LOGIN'); }}>Back to Login</span>
            </div>
          </form>
        )}

        {/* FORGOT PASSWORD OTP VIEW */}
        {view === 'FORGOT_OTP' && (
          <form onSubmit={handleForgotSubmit}>
            <div className="form-group">
              <label className="form-label">Enter OTP sent to {email}</label>
              <input type="text" maxLength="6" required className="form-input" value={otp} onChange={e => setOtp(e.target.value)} style={{ textAlign: 'center', letterSpacing: '2px' }} />
            </div>
            <div className="form-group">
              <label className="form-label">New Password</label>
              <input type="password" required minLength="6" className="form-input" value={password} onChange={e => setPassword(e.target.value)} />
            </div>
            <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%', marginBottom: '1rem' }}>
              {loading ? 'Resetting...' : 'Reset Password'}
            </button>
            <div style={{ textAlign: 'center', fontSize: '0.9rem' }}>
              <span style={{ color: 'var(--text-secondary)', cursor: 'pointer' }} onClick={() => setView('FORGOT')}>Back</span>
            </div>
          </form>
        )}

      </div>

      {/* College Project Credits Footer */}
      <div style={{
        position: 'absolute',
        bottom: '0',
        left: '0',
        width: '100%',
        padding: '1.5rem',
        background: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(10px)',
        borderTop: '3px solid var(--primary-color)',
        boxShadow: '0 -4px 32px rgba(0, 0, 0, 0.1)',
        textAlign: 'center',
        zIndex: 10
      }}>
        <p style={{ fontWeight: '700', marginBottom: '0.75rem', color: 'var(--primary-color)', fontSize: '1.1rem', textTransform: 'uppercase', letterSpacing: '2px' }}>
          A Final Year College Project Created By:
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1.5rem', flexWrap: 'wrap', marginBottom: '0.75rem', fontSize: '1.1rem', fontWeight: '600' }}>
          <span style={{ padding: '0.5rem 1rem', background: '#e0f2fe', borderRadius: '20px', color: '#0369a1', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>Simran Gaykar (22510018)</span>
          <span style={{ padding: '0.5rem 1rem', background: '#e0f2fe', borderRadius: '20px', color: '#0369a1', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>Neha Sonar (22510060)</span>
          <span style={{ padding: '0.5rem 1rem', background: '#e0f2fe', borderRadius: '20px', color: '#0369a1', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>Nidhi Warishe (2251006)</span>
        </div>
        <p style={{ fontWeight: '700', color: 'var(--text-secondary)', letterSpacing: '1px', fontSize: '1rem', marginTop: '0.75rem' }}>
          SUBMITTED TO AISSMS’S INSTITUTE OF INFORMATION TECHNOLOGY, PUNE
        </p>
      </div>

    </div>
  )
}

export default LoginPage
