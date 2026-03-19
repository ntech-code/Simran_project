import { useState, useEffect } from 'react'
import { taxAPI } from '../utils/api'
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import { useAuth } from '../context/AuthContext'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Dashboard() {
  const { user } = useAuth()
  const [systemStatus, setSystemStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [taxData, setTaxData] = useState(null)

  // Tax Rules state
  const [regime, setRegime] = useState('new')
  const [financialYear, setFinancialYear] = useState('2024-25')
  const [rules, setRules] = useState(null)
  const [rulesLoading, setRulesLoading] = useState(false)
  const [rulesError, setRulesError] = useState('')

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
      console.error('Failed to check system status:', error)
      setSystemStatus({ status: 'offline' })
    } finally {
      setLoading(false)
    }
  }

  const loadTaxData = () => {
    const savedData = localStorage.getItem('lastTaxCalculation')
    if (savedData) {
      setTaxData(JSON.parse(savedData))
    }
  }

  const handleFetchRules = async () => {
    setRulesLoading(true)
    setRulesError('')
    setRules(null)

    try {
      const response = await axios.get(`${API_URL}/rules/current`, {
        params: {
          regime,
          financial_year: financialYear
        }
      })
      setRules(response.data)
    } catch (err) {
      setRulesError(err.response?.data?.detail || 'Failed to fetch tax rules')
    } finally {
      setRulesLoading(false)
    }
  }

  const handleGenerateRules = async () => {
    setRulesLoading(true)
    setRulesError('')
    setRules(null)

    try {
      const response = await axios.post(`${API_URL}/generate-rules`, null, {
        params: {
          regime: regime === 'both' ? 'both' : regime,
          financial_year: financialYear
        }
      })
      setRules(response.data)
    } catch (err) {
      setRulesError(err.response?.data?.detail || 'Failed to generate tax rules')
    } finally {
      setRulesLoading(false)
    }
  }

  const formatValue = (value) => {
    if (typeof value === 'boolean') return value ? 'Yes' : 'No'
    if (typeof value === 'number') return value.toLocaleString('en-IN')
    if (typeof value === 'string') return value
    if (Array.isArray(value)) {
      return (
        <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
          {value.map((item, idx) => (
            <li key={idx}>{typeof item === 'object' ? formatValue(item) : item}</li>
          ))}
        </ul>
      )
    }
    if (typeof value === 'object' && value !== null) {
      return (
        <div style={{ marginLeft: '1rem' }}>
          {Object.entries(value).map(([k, v]) => (
            <div key={k} style={{ marginBottom: '0.25rem' }}>
              <strong>{k.replace(/_/g, ' ')}:</strong> {formatValue(v)}
            </div>
          ))}
        </div>
      )
    }
    return String(value)
  }

  const renderRulesSection = (title, data) => {
    if (!data) return null

    return (
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', color: 'var(--primary-color)' }}>{title}</h3>
        <div style={{ display: 'grid', gap: '0.5rem' }}>
          {typeof data === 'object' && !Array.isArray(data) ? (
            Object.entries(data).map(([key, value]) => (
              <div key={key} style={{
                padding: '0.75rem',
                background: 'var(--bg-secondary)',
                borderRadius: '4px'
              }}>
                <div style={{ fontWeight: '500', marginBottom: '0.25rem' }}>
                  {key.replace(/_/g, ' ').toUpperCase()}
                </div>
                <div>{formatValue(value)}</div>
              </div>
            ))
          ) : Array.isArray(data) ? (
            <div style={{
              padding: '0.75rem',
              background: 'var(--bg-secondary)',
              borderRadius: '4px'
            }}>
              {formatValue(data)}
            </div>
          ) : (
            <div style={{
              padding: '0.75rem',
              background: 'var(--bg-secondary)',
              borderRadius: '4px'
            }}>
              {formatValue(data)}
            </div>
          )}
        </div>
      </div>
    )
  }

  // Prepare chart data
  const getRegimeComparisonData = () => {
    if (!taxData) return []

    const slabs = taxData.regime === 'old' ? [
      { range: '0-2.5L', rate: 0 },
      { range: '2.5L-5L', rate: 5 },
      { range: '5L-10L', rate: 20 },
      { range: '10L+', rate: 30 }
    ] : [
      { range: '0-3L', rate: 0 },
      { range: '3L-7L', rate: 5 },
      { range: '7L-10L', rate: 10 },
      { range: '10L-12L', rate: 15 },
      { range: '12L-15L', rate: 20 },
      { range: '15L+', rate: 30 }
    ]

    return slabs
  }

  const getTaxBreakdownData = () => {
    if (!taxData) return []

    return [
      { name: 'Base Tax', value: taxData.base_tax || 0 },
      { name: 'Surcharge', value: taxData.surcharge || 0 },
      { name: 'Cess', value: taxData.cess || 0 }
    ].filter(item => item.value > 0)
  }

  const getDeductionsData = () => {
    if (!taxData?.deductions) return []

    return Object.entries(taxData.deductions)
      .map(([name, value]) => ({ name, value }))
      .filter(item => item.value > 0)
  }

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-3">
        <h2>Dashboard</h2>
        <p className="text-secondary">
          Welcome back, {user?.name}! Your Multi-Agent Tax Analysis System
        </p>
      </div>

      {/* Analytics Charts - Show only if user has calculated tax */}
      {taxData && (
        <>
          <div className="grid grid-2 mb-3">
            {/* Tax Overview Stats */}
            <div className="card">
              <h3>Your Tax Overview</h3>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-label">Gross Income</div>
                  <div className="stat-value">₹{taxData.gross_income?.toLocaleString('en-IN')}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Total Tax</div>
                  <div className="stat-value text-primary">₹{taxData.total_tax?.toLocaleString('en-IN')}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Effective Rate</div>
                  <div className="stat-value">{taxData.effective_tax_rate?.toFixed(2)}%</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Risk Level</div>
                  <div className={`stat-value ${
                    taxData.risk_level === 'LOW' ? 'text-success' :
                    taxData.risk_level === 'MEDIUM' ? 'text-warning' : 'text-danger'
                  }`}>
                    {taxData.risk_level}
                  </div>
                </div>
              </div>
            </div>

            {/* Tax Regime Slabs */}
            <div className="card">
              <h3>{taxData.regime?.toUpperCase()} Regime Tax Slabs</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={getRegimeComparisonData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" style={{ fontSize: '0.75rem' }} />
                  <YAxis style={{ fontSize: '0.75rem' }} />
                  <Tooltip />
                  <Bar dataKey="rate" fill="#3b82f6" name="Tax Rate %" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-2 mb-3">
            {/* Tax Breakdown Pie Chart */}
            {getTaxBreakdownData().length > 0 && (
              <div className="card">
                <h3>Tax Breakdown</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={getTaxBreakdownData()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {getTaxBreakdownData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Deductions Chart */}
            {getDeductionsData().length > 0 && (
              <div className="card">
                <h3>Your Deductions</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={getDeductionsData()} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" style={{ fontSize: '0.75rem' }} />
                    <YAxis dataKey="name" type="category" width={100} style={{ fontSize: '0.75rem' }} />
                    <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                    <Bar dataKey="value" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </>
      )}

      {/* System Status */}
      <div className="card mb-3">
        <h3>System Status</h3>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">API Status</div>
            <div className="stat-value">
              {systemStatus?.status === 'online' ? (
                <span className="text-success">Online</span>
              ) : (
                <span className="text-danger">Offline</span>
              )}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Service</div>
            <div className="stat-value text-sm">{systemStatus?.service || 'N/A'}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Version</div>
            <div className="stat-value">{systemStatus?.version || '1.0.0'}</div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="grid grid-2">
        <div className="card">
          <h3>Tax Calculator</h3>
          <p className="text-secondary mb-2">
            Calculate your income tax for FY 2024-25 using either the old or new regime.
          </p>
          <ul className="text-sm text-secondary" style={{ listStyle: 'none' }}>
            <li>✓ Accurate slab-based calculation</li>
            <li>✓ Deduction validation</li>
            <li>✓ Surcharge & cess computation</li>
            <li>✓ Rebate application (Section 87A)</li>
          </ul>
        </div>

        <div className="card">
          <h3>Fraud Detection</h3>
          <p className="text-secondary mb-2">
            AI-powered fraud detection analyzes your tax filing for compliance issues.
          </p>
          <ul className="text-sm text-secondary" style={{ listStyle: 'none' }}>
            <li>✓ Deduction ratio analysis</li>
            <li>✓ Pattern anomaly detection</li>
            <li>✓ Risk scoring (0-1 scale)</li>
            <li>✓ Compliance recommendations</li>
          </ul>
        </div>

        <div className="card">
          <h3>Regime Comparison</h3>
          <p className="text-secondary mb-2">
            Compare old vs new tax regime to find which saves you more money.
          </p>
          <ul className="text-sm text-secondary" style={{ listStyle: 'none' }}>
            <li>✓ Side-by-side comparison</li>
            <li>✓ Savings calculation</li>
            <li>✓ Best regime recommendation</li>
            <li>✓ Visual charts</li>
          </ul>
        </div>

        <div className="card">
          <h3>Tax Reports</h3>
          <p className="text-secondary mb-2">
            Generate comprehensive tax reports with detailed breakdowns.
          </p>
          <ul className="text-sm text-secondary" style={{ listStyle: 'none' }}>
            <li>✓ Detailed tax breakdown</li>
            <li>✓ Fraud analysis report</li>
            <li>✓ Compliance summary</li>
            <li>✓ Downloadable format</li>
          </ul>
        </div>
      </div>

      {/* Getting Started */}
      <div className="card mt-3">
        <h3>Getting Started</h3>
        <div className="grid grid-3">
          <div>
            <h4 className="text-sm font-bold mb-1">1. Enter Income</h4>
            <p className="text-xs text-secondary">
              Go to Tax Calculator and enter your gross annual income and select your preferred regime.
            </p>
          </div>
          <div>
            <h4 className="text-sm font-bold mb-1">2. Add Deductions</h4>
            <p className="text-xs text-secondary">
              Add applicable deductions like 80C, 80D, home loan interest, etc.
            </p>
          </div>
          <div>
            <h4 className="text-sm font-bold mb-1">3. Get Analysis</h4>
            <p className="text-xs text-secondary">
              View detailed tax calculation, fraud risk score, and compliance recommendations.
            </p>
          </div>
        </div>
      </div>

      {/* Tax Slabs Quick Reference */}
      <div className="grid grid-2 mt-3">
        <div className="card">
          <h3>Old Regime Slabs (FY 2024-25)</h3>
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Income Range</th>
                <th>Tax Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Up to ₹2.5L</td>
                <td>0%</td>
              </tr>
              <tr>
                <td>₹2.5L - ₹5L</td>
                <td>5%</td>
              </tr>
              <tr>
                <td>₹5L - ₹10L</td>
                <td>20%</td>
              </tr>
              <tr>
                <td>Above ₹10L</td>
                <td>30%</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3>New Regime Slabs (FY 2024-25)</h3>
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Income Range</th>
                <th>Tax Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Up to ₹3L</td>
                <td>0%</td>
              </tr>
              <tr>
                <td>₹3L - ₹7L</td>
                <td>5%</td>
              </tr>
              <tr>
                <td>₹7L - ₹10L</td>
                <td>10%</td>
              </tr>
              <tr>
                <td>₹10L - ₹12L</td>
                <td>15%</td>
              </tr>
              <tr>
                <td>₹12L - ₹15L</td>
                <td>20%</td>
              </tr>
              <tr>
                <td>Above ₹15L</td>
                <td>30%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Tax Rules Viewer */}
      <div className="card mt-3">
        <h3>Tax Rules Viewer</h3>
        <p className="text-secondary mb-2">View detailed tax rules and regulations for any financial year</p>

        {/* Controls */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          <div className="form-group">
            <label>Tax Regime</label>
            <select
              value={regime}
              onChange={(e) => setRegime(e.target.value)}
              className="form-input"
            >
              <option value="new">New Regime</option>
              <option value="old">Old Regime</option>
              <option value="both">Both Regimes</option>
            </select>
          </div>

          <div className="form-group">
            <label>Financial Year</label>
            <select
              value={financialYear}
              onChange={(e) => setFinancialYear(e.target.value)}
              className="form-input"
            >
              <option value="2024-25">2024-25</option>
              <option value="2023-24">2023-24</option>
              <option value="2022-23">2022-23</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            onClick={handleFetchRules}
            disabled={rulesLoading || regime === 'both'}
            className="btn btn-primary"
          >
            {rulesLoading ? 'Loading...' : 'Fetch Tax Rules'}
          </button>
          <button
            onClick={handleGenerateRules}
            disabled={rulesLoading}
            className="btn btn-secondary"
          >
            {rulesLoading ? 'Generating...' : 'Generate Tax Rules (AI)'}
          </button>
        </div>

        {/* Error Message */}
        {rulesError && (
          <div className="alert alert-error" style={{ marginTop: '1rem' }}>
            {rulesError}
          </div>
        )}

        {/* Rules Display */}
        {rules && (
          <div style={{ marginTop: '2rem' }}>
            <div className="card" style={{ marginBottom: '1.5rem', background: 'linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%)', color: 'white' }}>
              <h2 style={{ margin: 0, marginBottom: '0.5rem' }}>
                {rules.regime === 'new' ? 'New Tax Regime' : 'Old Tax Regime'}
              </h2>
              <p style={{ margin: 0, opacity: 0.9 }}>Financial Year: {rules.financial_year}</p>
            </div>

            {renderRulesSection('Tax Slabs', rules.slabs)}
            {renderRulesSection('Standard Deduction', rules.standard_deduction)}
            {renderRulesSection('Section 80C Deductions', rules.section_80c)}
            {renderRulesSection('Section 80D (Health Insurance)', rules.section_80d)}
            {renderRulesSection('HRA (House Rent Allowance)', rules.hra)}
            {renderRulesSection('Home Loan Interest', rules.home_loan_interest)}
            {renderRulesSection('Other Deductions', rules.other_deductions)}
            {renderRulesSection('Surcharge Rules', rules.surcharge)}
            {renderRulesSection('Education Cess', rules.cess)}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
