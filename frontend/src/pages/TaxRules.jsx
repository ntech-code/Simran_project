import { useState } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function TaxRules() {
  const [regime, setRegime] = useState('new')
  const [financialYear, setFinancialYear] = useState('2024-25')
  const [rules, setRules] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleFetchRules = async () => {
    setLoading(true)
    setError('')
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
      setError(err.response?.data?.detail || 'Failed to fetch tax rules')
    } finally {
      setLoading(false)
    }
  }

  const renderSection = (title, data) => {
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
                borderRadius: '4px',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <span style={{ fontWeight: '500' }}>{key.replace(/_/g, ' ').toUpperCase()}</span>
                <span>{typeof value === 'object' ? JSON.stringify(value) : value}</span>
              </div>
            ))
          ) : (
            <pre style={{
              background: 'var(--bg-secondary)',
              padding: '1rem',
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '0.875rem'
            }}>
              {JSON.stringify(data, null, 2)}
            </pre>
          )}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <h2>Tax Rules Viewer</h2>
        <p className="text-secondary">View current Indian tax rules and regulations</p>
      </div>

      {/* Controls */}
      <div className="card" style={{ marginBottom: '2rem' }}>
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

        <button
          onClick={handleFetchRules}
          disabled={loading}
          className="btn btn-primary"
        >
          {loading ? 'Loading...' : 'Fetch Tax Rules'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="alert alert-error" style={{ marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      {/* Rules Display */}
      {rules && (
        <div>
          <div className="card" style={{ marginBottom: '1.5rem', background: 'linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%)', color: 'white' }}>
            <h2 style={{ margin: 0, marginBottom: '0.5rem' }}>
              {rules.regime === 'new' ? 'New Tax Regime' : 'Old Tax Regime'}
            </h2>
            <p style={{ margin: 0, opacity: 0.9 }}>Financial Year: {rules.financial_year}</p>
          </div>

          {renderSection('Tax Slabs', rules.slabs)}
          {renderSection('Standard Deduction', rules.standard_deduction)}
          {renderSection('Section 80C Deductions', rules.section_80c)}
          {renderSection('Section 80D (Health Insurance)', rules.section_80d)}
          {renderSection('HRA (House Rent Allowance)', rules.hra)}
          {renderSection('Home Loan Interest', rules.home_loan_interest)}
          {renderSection('Other Deductions', rules.other_deductions)}
          {renderSection('Surcharge Rules', rules.surcharge)}
          {renderSection('Education Cess', rules.cess)}

          {/* Raw JSON for debugging */}
          <details style={{ marginTop: '2rem' }}>
            <summary style={{ cursor: 'pointer', fontWeight: '500', marginBottom: '1rem' }}>
              View Raw JSON
            </summary>
            <pre style={{
              background: 'var(--bg-secondary)',
              padding: '1rem',
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '0.875rem'
            }}>
              {JSON.stringify(rules, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  )
}
