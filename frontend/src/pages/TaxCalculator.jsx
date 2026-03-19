import { useState } from 'react'
import { taxAPI } from '../utils/api'

function TaxCalculator() {
  const [formData, setFormData] = useState({
    gross_income: '',
    regime: 'old',
    financial_year: '2024-25',
    deductions: {},
    previous_year_income: ''
  })

  const [deductions, setDeductions] = useState([])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const deductionOptions = {
    old: [
      { section: '80C', name: 'Investments & Expenses', max: 150000 },
      { section: '80D', name: 'Health Insurance', max: 75000 },
      { section: '80G', name: 'Donations', max: 0 },
      { section: '80E', name: 'Education Loan Interest', max: 0 },
      { section: '80TTA', name: 'Savings Account Interest', max: 10000 },
      { section: 'Standard Deduction', name: 'Standard Deduction', max: 50000 },
      { section: '24(b)', name: 'Home Loan Interest', max: 200000 },
    ],
    new: [
      { section: 'Standard Deduction', name: 'Standard Deduction', max: 50000 },
    ]
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleDeductionChange = (section, value) => {
    setFormData(prev => ({
      ...prev,
      deductions: {
        ...prev.deductions,
        [section]: parseFloat(value) || 0
      }
    }))
  }

  const handleCalculate = async () => {
    try {
      setLoading(true)
      setError(null)

      const requestData = {
        gross_income: parseFloat(formData.gross_income),
        regime: formData.regime,
        financial_year: formData.financial_year,
        deductions: formData.deductions,
        previous_year_income: formData.previous_year_income
          ? parseFloat(formData.previous_year_income)
          : null
      }

      const response = await taxAPI.analyzeTax(requestData)
      setResult(response)

      // Save to localStorage for chatbot context
      const taxDataForChatbot = {
        gross_income: parseFloat(formData.gross_income),
        regime: formData.regime,
        deductions: formData.deductions,
        taxable_income: response.tax_calculation.taxable_income,
        total_tax: response.tax_calculation.total_tax,
        effective_tax_rate: response.tax_calculation.effective_tax_rate,
        risk_score: response.fraud_analysis.risk_score,
        risk_level: response.fraud_analysis.risk_level,
        compliance_score: response.fraud_analysis.compliance_score,
        flags: response.fraud_analysis.flags
      }
      localStorage.setItem('lastTaxCalculation', JSON.stringify(taxDataForChatbot))

    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to calculate tax')
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const getRiskClass = (level) => {
    switch(level) {
      case 'LOW': return 'risk-low'
      case 'MEDIUM': return 'risk-medium'
      case 'HIGH': return 'risk-high'
      default: return 'risk-low'
    }
  }

  return (
    <div>
      <div className="mb-3">
        <h2>Tax Calculator</h2>
        <p className="text-secondary">
          Calculate your income tax for FY 2024-25
        </p>
      </div>

      <div className="grid grid-2">
        {/* Input Form */}
        <div className="card">
          <h3>Income Details</h3>

          <div className="form-group">
            <label className="form-label">Gross Annual Income *</label>
            <input
              type="number"
              name="gross_income"
              className="form-input"
              placeholder="e.g., 1200000"
              value={formData.gross_income}
              onChange={handleInputChange}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Tax Regime *</label>
            <select
              name="regime"
              className="form-select"
              value={formData.regime}
              onChange={handleInputChange}
            >
              <option value="old">Old Regime</option>
              <option value="new">New Regime</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Previous Year Income (Optional)</label>
            <input
              type="number"
              name="previous_year_income"
              className="form-input"
              placeholder="For fraud detection analysis"
              value={formData.previous_year_income}
              onChange={handleInputChange}
            />
          </div>

          <h3 className="mt-3">Deductions</h3>
          {deductionOptions[formData.regime].map((deduction) => (
            <div key={deduction.section} className="form-group">
              <label className="form-label">
                {deduction.section} - {deduction.name}
                {deduction.max > 0 && (
                  <span className="text-xs text-secondary"> (Max: {formatCurrency(deduction.max)})</span>
                )}
              </label>
              <input
                type="number"
                className="form-input"
                placeholder="0"
                onChange={(e) => handleDeductionChange(deduction.section, e.target.value)}
              />
            </div>
          ))}

          <button
            className="btn btn-primary"
            onClick={handleCalculate}
            disabled={loading || !formData.gross_income}
            style={{ width: '100%', marginTop: '1rem' }}
          >
            {loading ? 'Calculating...' : 'Calculate Tax'}
          </button>

          {error && (
            <div className="alert alert-danger mt-2">
              {error}
            </div>
          )}
        </div>

        {/* Results */}
        <div>
          {result && (
            <>
              {/* Tax Calculation Results */}
              <div className="card mb-3">
                <h3>Tax Calculation</h3>
                <div className="results-summary">
                  <div className="result-item">
                    <div className="result-label">Gross Income</div>
                    <div className="result-value">
                      {formatCurrency(result.tax_calculation.gross_income)}
                    </div>
                  </div>
                  <div className="result-item">
                    <div className="result-label">Total Deductions</div>
                    <div className="result-value text-success">
                      -{formatCurrency(result.tax_calculation.total_deductions)}
                    </div>
                  </div>
                  <div className="result-item">
                    <div className="result-label">Taxable Income</div>
                    <div className="result-value">
                      {formatCurrency(result.tax_calculation.taxable_income)}
                    </div>
                  </div>
                </div>

                <div className="mt-3" style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                  <div className="deduction-item">
                    <span>Tax from Slabs</span>
                    <span className="font-bold">
                      {formatCurrency(result.tax_calculation.tax_breakdown.tax_from_slabs)}
                    </span>
                  </div>
                  <div className="deduction-item">
                    <span>Rebate (Section 87A)</span>
                    <span className="font-bold text-success">
                      -{formatCurrency(result.tax_calculation.tax_breakdown.rebate)}
                    </span>
                  </div>
                  <div className="deduction-item">
                    <span>Surcharge</span>
                    <span className="font-bold">
                      {formatCurrency(result.tax_calculation.tax_breakdown.surcharge)}
                    </span>
                  </div>
                  <div className="deduction-item">
                    <span>Health & Education Cess (4%)</span>
                    <span className="font-bold">
                      {formatCurrency(result.tax_calculation.tax_breakdown.cess)}
                    </span>
                  </div>
                  <div className="deduction-item" style={{ borderTop: '2px solid var(--primary-color)', paddingTop: '1rem', marginTop: '1rem' }}>
                    <span className="text-lg font-bold">TOTAL TAX PAYABLE</span>
                    <span className="text-lg font-bold" style={{ color: 'var(--primary-color)' }}>
                      {formatCurrency(result.tax_calculation.total_tax)}
                    </span>
                  </div>
                  <div className="deduction-item">
                    <span>Effective Tax Rate</span>
                    <span className="font-bold">
                      {result.tax_calculation.effective_tax_rate}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Fraud Analysis */}
              <div className="card">
                <h3>Fraud & Compliance Analysis</h3>

                <div className="risk-meter">
                  <div className={`risk-score-circle ${getRiskClass(result.fraud_analysis.risk_level)}`}>
                    {(result.fraud_analysis.risk_score * 100).toFixed(0)}%
                  </div>
                  <div className="text-lg font-bold mb-1">
                    Risk Level: {result.fraud_analysis.risk_level}
                  </div>
                  <div className="text-sm text-secondary">
                    Compliance Score: {result.fraud_analysis.compliance_score}%
                  </div>
                </div>

                {result.fraud_analysis.flags.length > 0 && (
                  <div className="alert alert-warning">
                    <strong>Red Flags Detected:</strong>
                    <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                      {result.fraud_analysis.flags.map((flag, index) => (
                        <li key={index}>{flag}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="mt-2">
                  <strong className="text-sm">Recommendations:</strong>
                  <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                    {result.fraud_analysis.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm text-secondary">{rec}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </>
          )}

          {!result && !loading && (
            <div className="card">
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-tertiary)' }}>
                <h3>No Results Yet</h3>
                <p className="text-sm">
                  Enter your income details and click "Calculate Tax" to see results
                </p>
              </div>
            </div>
          )}

          {loading && (
            <div className="card">
              <div className="loading">
                <div className="spinner"></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default TaxCalculator
