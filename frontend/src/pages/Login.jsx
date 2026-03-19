import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google'
import { useAuth } from '../context/AuthContext'

// Get Google Client ID from environment variable
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '1234567890-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com'

function LoginPage() {
  const { loginWithGoogle, loginAsDev, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    // Redirect if already logged in
    if (isAuthenticated) {
      navigate('/')
    }
  }, [isAuthenticated, navigate])

  const handleSuccess = (credentialResponse) => {
    const success = loginWithGoogle(credentialResponse.credential)
    if (success) {
      navigate('/')
    }
  }

  const handleError = () => {
    alert('Login failed. Please try again.')
  }

  const handleDevLogin = () => {
    loginAsDev()
    navigate('/')
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '70vh',
      padding: '2rem'
    }}>
      <div className="card" style={{ maxWidth: '500px', width: '100%', textAlign: 'center' }}>
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>Welcome Back</h1>
          <p className="text-secondary">
            Sign in to access your Indian Tax Analysis Dashboard
          </p>
        </div>

        <div style={{
          background: 'var(--bg-tertiary)',
          padding: '2rem',
          borderRadius: '8px',
          marginBottom: '2rem'
        }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Features you'll get access to:</h3>
            <ul style={{ textAlign: 'left', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              <li style={{ marginBottom: '0.5rem' }}>📊 Tax calculation for FY 2024-25</li>
              <li style={{ marginBottom: '0.5rem' }}>🔍 AI-powered fraud detection</li>
              <li style={{ marginBottom: '0.5rem' }}>⚖️ Regime comparison</li>
              <li style={{ marginBottom: '0.5rem' }}>💬 Tax assistant chatbot</li>
              <li style={{ marginBottom: '0.5rem' }}>📈 Transaction analysis (CSV/Excel upload)</li>
              <li style={{ marginBottom: '0.5rem' }}>📄 Comprehensive tax reports</li>
            </ul>
          </div>

          <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              marginTop: '1.5rem'
            }}>
              <GoogleLogin
                onSuccess={handleSuccess}
                onError={handleError}
                theme="filled_blue"
                size="large"
                text="signin_with"
                shape="rectangular"
              />
            </div>
          </GoogleOAuthProvider>

          <div style={{ margin: '1.5rem 0', color: 'var(--text-secondary)' }}>
            OR
          </div>

          <button
            className="btn btn-secondary"
            onClick={handleDevLogin}
            style={{ width: '100%' }}
          >
            Continue as Developer (Testing Mode)
          </button>
        </div>

        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          <p>
            By signing in, you agree to our Terms of Service and Privacy Policy.
          </p>
          <p style={{ marginTop: '0.5rem' }}>
            Your data is secure and never shared with third parties.
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
