import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Dashboard from './pages/Dashboard'
import TaxCalculator from './pages/TaxCalculator'
import Login from './pages/Login'
import AdminDashboard from './pages/AdminDashboard'
import CyberFraudGame from './pages/CyberFraudGame'
import FraudAnalysis from './pages/FraudAnalysis'
import SpendAnalyzer from './pages/SpendAnalyzer'
import FinanceNews from './pages/FinanceNews'
import ChatbotBubble from './components/ChatbotBubble'
import './App.css'

function AppContent() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const { user, logout, isAuthenticated, isAdmin } = useAuth()
  const location = useLocation()
  const isGameRoute = location.pathname === '/play'

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
                  to="/fraud-analysis"
                  className={`nav-link ${activeTab === 'fraud-analysis' ? 'active' : ''}`}
                  onClick={() => setActiveTab('fraud-analysis')}
                  style={{ color: '#ea580c', fontWeight: 'bold' }}
                >
                  🕵️ Fraud Detection
                </Link>
                <Link
                  to="/spend-analyzer"
                  className={`nav-link ${activeTab === 'spend-analyzer' ? 'active' : ''}`}
                  onClick={() => setActiveTab('spend-analyzer')}
                  style={{ color: '#8b5cf6', fontWeight: 'bold' }}
                >
                  💸 Smart Spends
                </Link>
                <Link
                  to="/news"
                  className={`nav-link ${activeTab === 'news' ? 'active' : ''}`}
                  onClick={() => setActiveTab('news')}
                  style={{ color: '#059669', fontWeight: 'bold' }}
                >
                  📰 Live News
                </Link>
                <Link
                  to="/play"
                  className={`nav-link ${activeTab === 'play' ? 'active' : ''}`}
                  onClick={() => setActiveTab('play')}
                  style={{ color: '#ec4899', fontWeight: 'bold', textShadow: '0 0 10px rgba(236, 72, 153, 0.4)' }}
                >
                  🎮 Cyber-Auditor Game
                </Link>
                {isAdmin && (
                  <Link
                    to="/admin"
                    className={`nav-link ${activeTab === 'admin' ? 'active' : ''}`}
                    onClick={() => setActiveTab('admin')}
                    style={{ color: 'var(--primary-color)', fontWeight: 'bold' }}
                  >
                    🛡️ Admin Panel
                  </Link>
                )}
              </div>
            </div>
          </nav>
        )}

        {/* Main Content */}
        <main className={isGameRoute ? "" : "main-content"} style={isGameRoute ? { padding: 0, margin: 0, width: '100%', maxWidth: '100vw', overflowX: 'hidden' } : {}}>
          <div className={isGameRoute ? "" : "container"} style={isGameRoute ? { padding: 0, margin: 0, maxWidth: '100%' } : {}}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/play" element={<CyberFraudGame />} />
              <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/calculator" element={<ProtectedRoute><TaxCalculator /></ProtectedRoute>} />
              <Route path="/fraud-analysis" element={<ProtectedRoute><FraudAnalysis /></ProtectedRoute>} />
              <Route path="/spend-analyzer" element={<ProtectedRoute><SpendAnalyzer /></ProtectedRoute>} />
              <Route path="/news" element={<ProtectedRoute><FinanceNews /></ProtectedRoute>} />
              <Route path="/admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
            </Routes>
          </div>
        </main>

        {/* Footer */}
        <footer className="footer" style={{ marginTop: 'auto', padding: '1.5rem 1rem', borderTop: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)', textAlign: 'center' }}>
          <div className="container">
            <p className="text-secondary" style={{ fontSize: '0.9rem', marginBottom: '0.5rem', fontWeight: '500' }}>
              © 2025-26 Indian Tax Analysis System | Powered by Multi-Agent AI | FY 2025-26
            </p>
            <p className="text-secondary" style={{ fontSize: '0.82rem', margin: '0' }}>
              Submitted to AISSMS’S Institute of Information Technology, Pune<br />
              Created by: Simran Gaykar (22510018) • Neha Sonar (22510060) • Nidhi Warishe (22510061)
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
