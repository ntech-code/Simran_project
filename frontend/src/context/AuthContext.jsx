import { createContext, useContext, useState, useEffect } from 'react'
import { jwtDecode } from 'jwt-decode'

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

    if (storedUser && storedToken) {
      try {
        const decoded = jwtDecode(storedToken)
        // Check if token is expired
        if (decoded.exp * 1000 > Date.now()) {
          setUser(JSON.parse(storedUser))
        } else {
          // Token expired, clear storage
          localStorage.removeItem('user')
          localStorage.removeItem('token')
        }
      } catch (error) {
        console.error('Invalid token:', error)
        localStorage.removeItem('user')
        localStorage.removeItem('token')
      }
    }
    setLoading(false)
  }, [])

  const loginWithGoogle = (credential) => {
    try {
      const decoded = jwtDecode(credential)
      const userData = {
        email: decoded.email,
        name: decoded.name,
        picture: decoded.picture,
        sub: decoded.sub
      }

      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
      localStorage.setItem('token', credential)

      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }

  const loginAsDev = () => {
    // Development mode login - bypass Google OAuth
    const devUser = {
      email: 'dev@example.com',
      name: 'Developer User',
      picture: 'https://ui-avatars.com/api/?name=Dev+User&background=3b82f6&color=fff',
      sub: 'dev123'
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
    loginAsDev,
    logout,
    isAuthenticated: !!user
  }

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  )
}
