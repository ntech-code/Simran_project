import { useState, useEffect } from 'react'
import { taxAPI } from '../utils/api'
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { useAuth } from '../context/AuthContext'

function Dashboard() {
  const { user } = useAuth()
  const [systemStatus, setSystemStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [taxData, setTaxData] = useState(null)

  useEffect(() => {
    checkSystemStatus()
    loadTaxData()
  }, [])

  const checkSystemStatus = async () => {
    try {
      setLoading(true)
      const status = await taxAPI.healthCheck()
      setSystemStatus(status)
    } catch (error) {
      setSystemStatus({ status: 'offline' })
    } finally {
      setLoading(false)
    }
  }

  const loadTaxData = () => {
    const savedData = localStorage.getItem('lastTaxCalculation')
    if (savedData && savedData !== 'undefined') {
      try {
        setTaxData(JSON.parse(savedData))
      } catch (err) {
        console.error('Failed to parse cached tax calculation', err)
        localStorage.removeItem('lastTaxCalculation')
      }
    }
  }

  const formatCurrency = (amt) => {
    if (!amt && amt !== 0) return '₹0'
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amt)
  }

  const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6']

  const newRegimeSlabs = [
    { range: '₹0 – ₹4L', rate: 0 },
    { range: '₹4L – ₹8L', rate: 5 },
    { range: '₹8L – ₹12L', rate: 10 },
    { range: '₹12L – ₹16L', rate: 15 },
    { range: '₹16L – ₹20L', rate: 20 },
    { range: '₹20L – ₹24L', rate: 25 },
    { range: 'Above ₹24L', rate: 30 },
  ]

  const oldRegimeSlabs = [
    { range: '₹0 – ₹2.5L', rate: 0 },
    { range: '₹2.5L – ₹5L', rate: 5 },
    { range: '₹5L – ₹10L', rate: 20 },
    { range: 'Above ₹10L', rate: 30 },
  ]

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div>
      {/* Welcome Banner */}
      <div className="card mb-3" style={{ background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%)', color: 'white', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'relative', zIndex: 1 }}>
          <h2 style={{ margin: 0, marginBottom: '0.5rem', fontSize: '1.8rem' }}>
            Welcome back, {user?.name || 'Taxpayer'}! 👋
          </h2>
          <p style={{ opacity: 0.9, margin: 0, marginBottom: '1rem', fontSize: '1.05rem' }}>
            Indian Tax Analysis System · Assessment Year 2026-27 (FY 2025-26)
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span style={{ background: 'rgba(255,255,255,0.2)', padding: '0.4rem 1rem', borderRadius: '20px', fontSize: '0.85rem', backdropFilter: 'blur(10px)' }}>
              {systemStatus?.status === 'online' ? '🟢 System Online' : '🔴 System Offline'}
            </span>
            <span style={{ background: 'rgba(255,255,255,0.2)', padding: '0.4rem 1rem', borderRadius: '20px', fontSize: '0.85rem' }}>
              📅 FY 2025-26 Rules Active
            </span>
          </div>
        </div>
      </div>

      {/* Budget 2025 Highlights */}
      <div className="card mb-3" style={{ borderLeft: '5px solid #f59e0b' }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          🏛️ Union Budget 2025 Highlights — What Changed?
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
          <div style={{ background: '#fef3c7', padding: '1rem', borderRadius: '10px' }}>
            <div style={{ fontWeight: '700', color: '#92400e', marginBottom: '0.25rem' }}>💰 Tax-Free Income Raised</div>
            <p style={{ margin: 0, color: '#78350f', fontSize: '0.9rem' }}>
              No tax on income up to <strong>₹12 Lakh</strong> under New Regime (₹12.75L for salaried). Previously it was ₹7 Lakh.
            </p>
          </div>
          <div style={{ background: '#d1fae5', padding: '1rem', borderRadius: '10px' }}>
            <div style={{ fontWeight: '700', color: '#065f46', marginBottom: '0.25rem' }}>📋 Standard Deduction ↑</div>
            <p style={{ margin: 0, color: '#064e3b', fontSize: '0.9rem' }}>
              Standard Deduction increased to <strong>₹75,000</strong> from ₹50,000 under New Regime. No receipts needed — automatically deducted from your salary.
            </p>
          </div>
          <div style={{ background: '#ede9fe', padding: '1rem', borderRadius: '10px' }}>
            <div style={{ fontWeight: '700', color: '#5b21b6', marginBottom: '0.25rem' }}>🔄 New 7-Slab Structure</div>
            <p style={{ margin: 0, color: '#4c1d95', fontSize: '0.9rem' }}>
              New Regime now has <strong>7 tax slabs</strong> (was 6). Nil slab raised from ₹3L to <strong>₹4 Lakh</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* User's Last Calculation Summary */}
      {taxData && (
        <div className="card mb-3">
          <h3 style={{ marginBottom: '1.5rem' }}>📊 Your Last Tax Calculation</h3>
          <div className="stats-grid">
            <div className="stat-card" style={{ borderLeft: '4px solid #6366f1' }}>
              <div className="stat-label">Gross Income</div>
              <div className="stat-value" style={{ fontSize: '1.6rem' }}>{formatCurrency(taxData.gross_income)}</div>
            </div>
            <div className="stat-card" style={{ borderLeft: '4px solid #ef4444' }}>
              <div className="stat-label">Total Tax</div>
              <div className="stat-value" style={{ fontSize: '1.6rem', color: '#ef4444' }}>{formatCurrency(taxData.total_tax)}</div>
            </div>
            <div className="stat-card" style={{ borderLeft: '4px solid #10b981' }}>
              <div className="stat-label">Take-Home (Yearly)</div>
              <div className="stat-value" style={{ fontSize: '1.6rem', color: '#10b981' }}>
                {formatCurrency((taxData.gross_income || 0) - (taxData.total_tax || 0))}
              </div>
            </div>
            <div className="stat-card" style={{ borderLeft: '4px solid #f59e0b' }}>
              <div className="stat-label">Effective Tax Rate</div>
              <div className="stat-value" style={{ fontSize: '1.6rem' }}>{taxData.effective_tax_rate?.toFixed(2)}%</div>
            </div>
            <div className="stat-card" style={{ borderLeft: '4px solid #8b5cf6' }}>
              <div className="stat-label">Monthly Tax</div>
              <div className="stat-value" style={{ fontSize: '1.6rem' }}>
                {formatCurrency(Math.round((taxData.total_tax || 0) / 12))}
              </div>
            </div>
            <div className="stat-card" style={{ borderLeft: `4px solid ${taxData.risk_level === 'LOW' ? '#10b981' : taxData.risk_level === 'MEDIUM' ? '#f59e0b' : '#ef4444'}` }}>
              <div className="stat-label">Compliance Risk</div>
              <div className="stat-value" style={{ fontSize: '1.6rem', color: taxData.risk_level === 'LOW' ? '#10b981' : taxData.risk_level === 'MEDIUM' ? '#f59e0b' : '#ef4444' }}>
                {taxData.risk_level || 'N/A'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-2 mb-3" style={{ gap: '1rem' }}>
        <a href="/calculator" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ textAlign: 'center', cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s', padding: '2rem' }} onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.boxShadow = '0 12px 40px rgba(0,0,0,0.12)' }} onMouseLeave={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🧮</div>
            <h3 style={{ marginBottom: '0.5rem' }}>Tax Calculator & Reports</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>Calculate tax, compare regimes, and download official PDF reports</p>
          </div>
        </a>
        <a href="/fraud-analysis" style={{ textDecoration: 'none' }}>
          <div className="card" style={{ textAlign: 'center', cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s', padding: '2rem' }} onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.boxShadow = '0 12px 40px rgba(0,0,0,0.12)' }} onMouseLeave={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🕵️</div>
            <h3 style={{ marginBottom: '0.5rem' }}>AI Fraud Detection</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>Upload bank statements for AI-powered forensic analysis</p>
          </div>
        </a>
      </div>

      {/* FY 2025-26 Tax Slabs Reference */}
      <div className="grid grid-2 mb-3">
        <div className="card">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ background: '#6366f1', color: 'white', padding: '0.25rem 0.75rem', borderRadius: '6px', fontSize: '0.8rem' }}>RECOMMENDED</span>
            New Regime (FY 2025-26)
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
            Lower tax rates but <strong>most deductions (80C, 80D, HRA) are NOT allowed</strong>. Best if your deductions are less than ₹3-4 Lakh.
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={newRegimeSlabs}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" style={{ fontSize: '0.65rem' }} angle={-15} textAnchor="end" height={50} />
              <YAxis style={{ fontSize: '0.75rem' }} unit="%" />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="rate" fill="#6366f1" name="Tax Rate" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <table className="comparison-table" style={{ marginTop: '0.5rem' }}>
            <thead>
              <tr><th>Income Range</th><th>Tax Rate</th></tr>
            </thead>
            <tbody>
              {newRegimeSlabs.map((s, i) => (
                <tr key={i}><td>{s.range}</td><td><strong>{s.rate}%</strong></td></tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#ede9fe', borderRadius: '8px', fontSize: '0.85rem', color: '#5b21b6' }}>
            <strong>💡 Key:</strong> Standard Deduction = ₹75,000 · Section 87A Rebate = ₹60,000 (income ≤ ₹12L) · <strong>Effectively tax-free up to ₹12.75L for salaried</strong>
          </div>
        </div>

        <div className="card">
          <h3>Old Regime (FY 2025-26)</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
            Higher tax rates but <strong>you can claim all deductions</strong> like 80C (₹1.5L), 80D, HRA, Home Loan. Best if your deductions exceed ₹3-4 Lakh.
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={oldRegimeSlabs}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" style={{ fontSize: '0.7rem' }} />
              <YAxis style={{ fontSize: '0.75rem' }} unit="%" />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="rate" fill="#f59e0b" name="Tax Rate" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <table className="comparison-table" style={{ marginTop: '0.5rem' }}>
            <thead>
              <tr><th>Income Range</th><th>Tax Rate</th></tr>
            </thead>
            <tbody>
              {oldRegimeSlabs.map((s, i) => (
                <tr key={i}><td>{s.range}</td><td><strong>{s.rate}%</strong></td></tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#fef3c7', borderRadius: '8px', fontSize: '0.85rem', color: '#92400e' }}>
            <strong>💡 Key:</strong> Standard Deduction = ₹50,000 · Section 87A Rebate = ₹12,500 (income ≤ ₹5L) · Allows 80C, 80D, HRA, 24(b) deductions
          </div>
        </div>
      </div>

      {/* Understanding Deductions */}
      <div className="card mb-3">
        <h3 style={{ marginBottom: '1rem' }}>📚 Understanding Tax Deductions (Plain English)</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '10px', borderLeft: '4px solid #6366f1' }}>
            <strong>Standard Deduction</strong>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              A flat amount automatically subtracted from your salary before tax is calculated. <strong>No receipts needed.</strong> New Regime: ₹75,000. Old Regime: ₹50,000.
            </p>
          </div>
          <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '10px', borderLeft: '4px solid #10b981' }}>
            <strong>Section 80C (Old Regime Only)</strong>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Save up to <strong>₹1.5 Lakh</strong> by investing in PPF, ELSS Mutual Funds, EPF, Life Insurance, Home Loan Principal, NSC, 5-yr Fixed Deposit, Sukanya Samriddhi.
            </p>
          </div>
          <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '10px', borderLeft: '4px solid #f59e0b' }}>
            <strong>Section 80D (Old Regime Only)</strong>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Health insurance premiums. <strong>₹25,000</strong> for self/family + <strong>₹25,000</strong> for parents (₹50K if parents are senior citizens). Max total: ₹75,000.
            </p>
          </div>
          <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '10px', borderLeft: '4px solid #ef4444' }}>
            <strong>Section 24(b) — Home Loan Interest (Old Regime Only)</strong>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              If you pay EMI on a home loan, the <strong>interest portion</strong> (not principal) is deductible up to <strong>₹2 Lakh</strong> per year for a self-occupied house.
            </p>
          </div>
          <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '10px', borderLeft: '4px solid #8b5cf6' }}>
            <strong>Section 87A — Tax Rebate</strong>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              If your taxable income is below a threshold, you get a <strong>rebate</strong> (discount) on your tax. New Regime: ₹60,000 rebate if income ≤ ₹12L. Old: ₹12,500 if ≤ ₹5L.
            </p>
          </div>
          <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '10px', borderLeft: '4px solid #14b8a6' }}>
            <strong>Health & Education Cess (4%)</strong>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              A <strong>4% surcharge</strong> applied on top of your final tax amount. This funds government healthcare and education. Both regimes charge this.
            </p>
          </div>
        </div>
      </div>

      {/* Getting Started */}
      <div className="card">
        <h3>🚀 How to Use This System</h3>
        <div className="grid grid-3" style={{ marginTop: '1rem' }}>
          <div style={{ textAlign: 'center', padding: '1rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>1️⃣</div>
            <h4 style={{ marginBottom: '0.5rem' }}>Enter Your Salary</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
              Go to <strong>Tax Calculator</strong>, enter your gross annual income (CTC or total salary before deductions).
            </p>
          </div>
          <div style={{ textAlign: 'center', padding: '1rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>2️⃣</div>
            <h4 style={{ marginBottom: '0.5rem' }}>Add Deductions</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
              If choosing Old Regime, add your investments (80C), insurance (80D), home loan interest, etc.
            </p>
          </div>
          <div style={{ textAlign: 'center', padding: '1rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>3️⃣</div>
            <h4 style={{ marginBottom: '0.5rem' }}>See Results</h4>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
              Get instant tax breakdown, risk analysis, and use <strong>Compare Regimes</strong> to find the better option.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
