import { useState } from 'react'
import { taxAPI } from '../utils/api'

function CompareRegimes() {
  const [income, setIncome] = useState('')
  const [deductionsOld, setDeductionsOld] = useState({})
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleCompare = async () => {
    try {
      setLoading(true)
      setError(null)

      const requestData = {
        gross_income: parseFloat(income),
        financial_year: '2024-25',
        deductions_old: deductionsOld,
        deductions_new: {
          'Standard Deduction': 50000
        }
      }

      const response = await taxAPI.compareRegimes(requestData)
      setResult(response)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to compare regimes')
    } finally {
      setLoading(false)
    }
  }

  const handleDeductionChange = (section, value) => {
    setDeductionsOld(prev => ({
      ...prev,
      [section]: parseFloat(value) || 0
    }))
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  return (
    <div>
      <div className="mb-3">
        <h2>Compare Tax Regimes</h2>
        <p className="text-secondary">
          Find out which regime saves you more money
        </p>
      </div>

      {/* Input Section */}
      <div className="card mb-3">
        <h3>Income & Deductions</h3>
        <div className="grid grid-2">
          <div className="form-group">
            <label className="form-label">Gross Annual Income *</label>
            <input
              type="number"
              className="form-input"
              placeholder="e.g., 1200000"
              value={income}
              onChange={(e) => setIncome(e.target.value)}
            />
          </div>
        </div>

        <h4 className="mt-2">Old Regime Deductions</h4>
        <div className="grid grid-3">
          <div className="form-group">
            <label className="form-label">80C (Max: ₹1.5L)</label>
            <input
              type="number"
              className="form-input"
              placeholder="0"
              onChange={(e) => handleDeductionChange('80C', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">80D (Max: ₹75K)</label>
            <input
              type="number"
              className="form-input"
              placeholder="0"
              onChange={(e) => handleDeductionChange('80D', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">24(b) Home Loan (Max: ₹2L)</label>
            <input
              type="number"
              className="form-input"
              placeholder="0"
              onChange={(e) => handleDeductionChange('24(b)', e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Standard Deduction</label>
            <input
              type="number"
              className="form-input"
              placeholder="50000"
              defaultValue="50000"
              onChange={(e) => handleDeductionChange('Standard Deduction', e.target.value)}
            />
          </div>
        </div>

        <button
          className="btn btn-primary mt-2"
          onClick={handleCompare}
          disabled={loading || !income}
        >
          {loading ? 'Comparing...' : 'Compare Regimes'}
        </button>

        {error && (
          <div className="alert alert-danger mt-2">
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Summary */}
          <div className="card mb-3">
            <h3>Comparison Summary</h3>
            <div className="results-summary">
              <div className="result-item">
                <div className="result-label">Old Regime Tax</div>
                <div className="result-value">
                  {formatCurrency(result.comparison.comparison.old_regime_tax)}
                </div>
              </div>
              <div className="result-item">
                <div className="result-label">New Regime Tax</div>
                <div className="result-value">
                  {formatCurrency(result.comparison.comparison.new_regime_tax)}
                </div>
              </div>
              <div className="result-item" style={{ background: 'var(--primary-color)', color: 'white', borderRadius: '8px' }}>
                <div className="result-label" style={{ color: 'rgba(255,255,255,0.9)' }}>
                  Better Option
                </div>
                <div className="result-value" style={{ color: 'white' }}>
                  {result.comparison.comparison.better_regime.toUpperCase()}
                </div>
              </div>
              <div className="result-item" style={{ background: 'var(--success-color)', color: 'white', borderRadius: '8px' }}>
                <div className="result-label" style={{ color: 'rgba(255,255,255,0.9)' }}>
                  You Save
                </div>
                <div className="result-value" style={{ color: 'white' }}>
                  {formatCurrency(result.comparison.comparison.savings)}
                </div>
              </div>
            </div>
          </div>

          {/* Detailed Comparison */}
          <div className="grid grid-2">
            {/* Old Regime */}
            <div className="card">
              <h3>Old Regime Details</h3>
              <div className="mb-2">
                <div className="deduction-item">
                  <span>Gross Income</span>
                  <span className="font-bold">
                    {formatCurrency(result.comparison.old.tax_calculation.gross_income)}
                  </span>
                </div>
                <div className="deduction-item">
                  <span>Total Deductions</span>
                  <span className="font-bold text-success">
                    -{formatCurrency(result.comparison.old.tax_calculation.total_deductions)}
                  </span>
                </div>
                <div className="deduction-item">
                  <span>Taxable Income</span>
                  <span className="font-bold">
                    {formatCurrency(result.comparison.old.tax_calculation.taxable_income)}
                  </span>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <div className="deduction-item">
                  <span className="text-lg font-bold">Total Tax</span>
                  <span className="text-lg font-bold">
                    {formatCurrency(result.comparison.old.tax_calculation.total_tax)}
                  </span>
                </div>
                <div className="deduction-item">
                  <span>Effective Rate</span>
                  <span>{result.comparison.old.tax_calculation.effective_tax_rate}%</span>
                </div>
              </div>

              <div className="mt-2">
                <span className={`badge badge-${result.comparison.old.fraud_analysis.risk_level === 'LOW' ? 'success' : result.comparison.old.fraud_analysis.risk_level === 'MEDIUM' ? 'warning' : 'danger'}`}>
                  Risk: {result.comparison.old.fraud_analysis.risk_level}
                </span>
                <span className="text-xs text-secondary ml-2">
                  Compliance: {result.comparison.old.fraud_analysis.compliance_score}%
                </span>
              </div>
            </div>

            {/* New Regime */}
            <div className="card">
              <h3>New Regime Details</h3>
              <div className="mb-2">
                <div className="deduction-item">
                  <span>Gross Income</span>
                  <span className="font-bold">
                    {formatCurrency(result.comparison.new.tax_calculation.gross_income)}
                  </span>
                </div>
                <div className="deduction-item">
                  <span>Total Deductions</span>
                  <span className="font-bold text-success">
                    -{formatCurrency(result.comparison.new.tax_calculation.total_deductions)}
                  </span>
                </div>
                <div className="deduction-item">
                  <span>Taxable Income</span>
                  <span className="font-bold">
                    {formatCurrency(result.comparison.new.tax_calculation.taxable_income)}
                  </span>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <div className="deduction-item">
                  <span className="text-lg font-bold">Total Tax</span>
                  <span className="text-lg font-bold">
                    {formatCurrency(result.comparison.new.tax_calculation.total_tax)}
                  </span>
                </div>
                <div className="deduction-item">
                  <span>Effective Rate</span>
                  <span>{result.comparison.new.tax_calculation.effective_tax_rate}%</span>
                </div>
              </div>

              <div className="mt-2">
                <span className={`badge badge-${result.comparison.new.fraud_analysis.risk_level === 'LOW' ? 'success' : result.comparison.new.fraud_analysis.risk_level === 'MEDIUM' ? 'warning' : 'danger'}`}>
                  Risk: {result.comparison.new.fraud_analysis.risk_level}
                </span>
                <span className="text-xs text-secondary ml-2">
                  Compliance: {result.comparison.new.fraud_analysis.compliance_score}%
                </span>
              </div>
            </div>
          </div>

          {/* Recommendation */}
          <div className="card mt-3">
            <h3>Recommendation</h3>
            <div className="alert alert-success">
              <strong>
                Based on your income of {formatCurrency(parseFloat(income))},
                the {result.comparison.comparison.better_regime.toUpperCase()} regime is better for you.
              </strong>
              <p className="mb-0 mt-1">
                You will save {formatCurrency(result.comparison.comparison.savings)} by choosing the {result.comparison.comparison.better_regime} regime.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default CompareRegimes
