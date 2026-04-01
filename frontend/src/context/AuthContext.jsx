import { createContext, useContext, useState, useEffect } from 'react'
import { jwtDecode } from 'jwt-decode'
import { authAPI } from '../utils/api'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for stored user session
    const storedUser = localStorage.getItem('user')
    const storedToken = localStorage.getItem('token')

    const safeParse = (data) => {
      try { return JSON.parse(data) } catch (e) { return null }
    }

    if (storedUser && storedToken && storedToken !== 'dev-token') {
      try {
        const decoded = jwtDecode(storedToken)
        // Check if token is expired
        if (decoded.exp * 1000 > Date.now()) {
          const parsedUser = safeParse(storedUser)
          if (parsedUser) setUser(parsedUser)
          else logout()
        } else {
          // Token expired
          logout()
        }
      } catch (error) {
        console.error('Invalid token:', error)
        logout()
      }
    } else if (storedUser && storedToken === 'dev-token') {
      const parsedUser = safeParse(storedUser)
      if (parsedUser) setUser(parsedUser)
      else logout()
    }
    setLoading(false)
  }, [])

  const handleAuthData = (data) => {
    const userData = data.user
    setUser(userData)
    localStorage.setItem('user', JSON.stringify(userData))
    localStorage.setItem('token', data.access_token)
  }

  const loginWithGoogle = async (credential) => {
    try {
      // Pass the credential to our backend so it can verify and check if blocked
      const response = await authAPI.googleLogin(credential)
      handleAuthData(response)
      return { success: true }
    } catch (error) {
      console.error('Google Login failed:', error)
      return {
        success: false,
        error: error.response?.data?.detail || 'Google Login failed'
      }
    }
  }

  const loginCustom = async (email, password) => {
    try {
      const response = await authAPI.login({ email, password })
      handleAuthData(response)
      return { success: true }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Invalid email or password'
      }
    }
  }

  const signupCustom = async (email, password, name, otp) => {
    try {
      const response = await authAPI.signup({ email, password, name, otp })
      handleAuthData(response)
      return { success: true }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Signup failed'
      }
    }
  }

  const loginAsDev = () => {
    const devUser = {
      email: 'dev@example.com',
      name: 'Developer User',
      picture: 'https://ui-avatars.com/api/?name=Dev+User&background=3b82f6&color=fff',
      sub: 'dev123',
      is_admin: true // Make dev an admin for easy testing
    }
    setUser(devUser)
    localStorage.setItem('user', JSON.stringify(devUser))
    localStorage.setItem('token', 'dev-token')
    return true
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('user')
    localStorage.removeItem('token')
    localStorage.removeItem('lastTaxCalculation')
  }

  const value = {
    user,
    loading,
    loginWithGoogle,
    loginCustom,
    signupCustom,
    loginAsDev,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin || false
  }

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  )
}
