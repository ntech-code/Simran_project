import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Dashboard from './pages/Dashboard'
import TaxCalculator from './pages/TaxCalculator'
import CompareRegimes from './pages/CompareRegimes'
import Reports from './pages/Reports'
import TransactionAnalyzer from './pages/TransactionAnalyzer'
import Login from './pages/Login'
import ChatbotBubble from './components/ChatbotBubble'
import './App.css'

function AppContent() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const { user, logout, isAuthenticated } = useAuth()

  const handleLogout = () => {
    logout()
    setActiveTab('dashboard')
  }

  return (
    <>
      <div className="app">
        {/* Header */}
        <header className="header">
          <div className="container">
            <div className="header-content">
              <div className="logo">
                <h1>Indian Tax Analysis</h1>
                <p className="text-sm text-secondary">Multi-Agent System with AI-Powered Fraud Detection</p>
              </div>
              {isAuthenticated && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {user?.picture && (
                      <img
                        src={user.picture}
                        alt={user.name}
                        style={{
                          width: '32px',
                          height: '32px',
                          borderRadius: '50%',
                          border: '2px solid var(--primary-color)'
                        }}
                      />
                    )}
                    <span className="text-sm">{user?.name}</span>
                  </div>
                  <button className="btn btn-secondary" onClick={handleLogout} style={{ fontSize: '0.875rem' }}>
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Navigation */}
        {isAuthenticated && (
        <nav className="nav">
          <div className="container">
            <div className="nav-links">
              <Link
                to="/"
                className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
                onClick={() => setActiveTab('dashboard')}
              >
                Dashboard
              </Link>
              <Link
                to="/calculator"
                className={`nav-link ${activeTab === 'calculator' ? 'active' : ''}`}
                onClick={() => setActiveTab('calculator')}
              >
                Tax Calculator
              </Link>
              <Link
                to="/compare"
                className={`nav-link ${activeTab === 'compare' ? 'active' : ''}`}
                onClick={() => setActiveTab('compare')}
              >
                Compare Regimes
              </Link>
              <Link
                to="/reports"
                className={`nav-link ${activeTab === 'reports' ? 'active' : ''}`}
                onClick={() => setActiveTab('reports')}
              >
                Reports
              </Link>
              <Link
                to="/transactions"
                className={`nav-link ${activeTab === 'transactions' ? 'active' : ''}`}
                onClick={() => setActiveTab('transactions')}
              >
                📊 Transactions
              </Link>
            </div>
          </div>
        </nav>
        )}

        {/* Main Content */}
        <main className="main-content">
          <div className="container">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/calculator" element={<ProtectedRoute><TaxCalculator /></ProtectedRoute>} />
              <Route path="/compare" element={<ProtectedRoute><CompareRegimes /></ProtectedRoute>} />
              <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
              <Route path="/transactions" element={<ProtectedRoute><TransactionAnalyzer /></ProtectedRoute>} />
            </Routes>
          </div>
        </main>

        {/* Footer */}
        <footer className="footer">
          <div className="container">
            <p className="text-center text-sm text-secondary">
              © 2024-25 Indian Tax Analysis System | Powered by Multi-Agent AI | FY 2024-25
            </p>
          </div>
        </footer>

        {/* Floating Chatbot Bubble - Available on authenticated pages */}
        {isAuthenticated && <ChatbotBubble />}
      </div>
    </>
  )
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  )
}

export default App
