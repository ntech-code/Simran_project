import { useState } from 'react'
import { taxAPI } from '../utils/api'

function Reports() {
  const [formData, setFormData] = useState({
    gross_income: '',
    regime: 'old',
    deductions: {}
  })
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

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

  const handleGenerateReport = async () => {
    try {
      setLoading(true)
      setError(null)

      const requestData = {
        gross_income: parseFloat(formData.gross_income),
        regime: formData.regime,
        financial_year: '2024-25',
        deductions: formData.deductions
      }

      const response = await taxAPI.generateReport(requestData)
      setReport(response)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  const deductionOptions = {
    old: [
      { section: '80C', name: 'Investments', placeholder: '150000' },
      { section: '80D', name: 'Health Insurance', placeholder: '25000' },
      { section: 'Standard Deduction', name: 'Standard Deduction', placeholder: '50000' },
      { section: '24(b)', name: 'Home Loan Interest', placeholder: '0' },
    ],
    new: [
      { section: 'Standard Deduction', name: 'Standard Deduction', placeholder: '50000' },
    ]
  }

  const downloadReport = () => {
    if (!report) return

    const element = document.createElement('a')
    const file = new Blob([report.report], { type: 'text/plain' })
    element.href = URL.createObjectURL(file)
    element.download = `tax_report_${formData.regime}_${Date.now()}.txt`
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  return (
    <div>
      <div className="mb-3">
        <h2>Tax Reports</h2>
        <p className="text-secondary">
          Generate comprehensive tax analysis reports
        </p>
      </div>

      <div className="grid grid-2">
        {/* Input Form */}
        <div className="card">
          <h3>Report Configuration</h3>

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

          <h4 className="mt-2">Deductions</h4>
          {deductionOptions[formData.regime].map((deduction) => (
            <div key={deduction.section} className="form-group">
              <label className="form-label">
                {deduction.section} - {deduction.name}
              </label>
              <input
                type="number"
                className="form-input"
                placeholder={deduction.placeholder}
                onChange={(e) => handleDeductionChange(deduction.section, e.target.value)}
              />
            </div>
          ))}

          <button
            className="btn btn-primary"
            onClick={handleGenerateReport}
            disabled={loading || !formData.gross_income}
            style={{ width: '100%', marginTop: '1rem' }}
          >
            {loading ? 'Generating...' : 'Generate Report'}
          </button>

          {error && (
            <div className="alert alert-danger mt-2">
              {error}
            </div>
          )}
        </div>

        {/* Report Display */}
        <div>
          {report && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 className="mb-0">Generated Report</h3>
                <button
                  className="btn btn-secondary"
                  onClick={downloadReport}
                >
                  Download Report
                </button>
              </div>

              <div
                style={{
                  background: 'var(--bg-tertiary)',
                  padding: '1rem',
                  borderRadius: '6px',
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                  whiteSpace: 'pre-wrap',
                  maxHeight: '600px',
                  overflowY: 'auto',
                  lineHeight: '1.5'
                }}
              >
                {report.report}
              </div>

              <div className="mt-2 text-xs text-secondary">
                Generated: {new Date(report.timestamp).toLocaleString()}
              </div>
            </div>
          )}

          {!report && !loading && (
            <div className="card">
              <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-tertiary)' }}>
                <h3>No Report Generated</h3>
                <p className="text-sm">
                  Configure your income details and click "Generate Report" to create a comprehensive tax analysis report
                </p>
                <div className="mt-3 text-left">
                  <h4 className="text-sm font-bold mb-2">Report includes:</h4>
                  <ul className="text-sm text-secondary" style={{ listStyle: 'none', padding: 0 }}>
                    <li>✓ Complete tax calculation breakdown</li>
                    <li>✓ Deduction analysis</li>
                    <li>✓ Fraud & compliance assessment</li>
                    <li>✓ Risk score and red flags</li>
                    <li>✓ Recommendations</li>
                    <li>✓ Downloadable format</li>
                  </ul>
                </div>
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

      {/* Sample Reports Section */}
      <div className="card mt-3">
        <h3>Report Features</h3>
        <div className="grid grid-3">
          <div>
            <h4 className="text-sm font-bold mb-1">Tax Breakdown</h4>
            <p className="text-xs text-secondary">
              Detailed calculation showing gross income, deductions, taxable income, and tax computation across all slabs
            </p>
          </div>
          <div>
            <h4 className="text-sm font-bold mb-1">Fraud Analysis</h4>
            <p className="text-xs text-secondary">
              AI-powered risk assessment with compliance score, red flags detection, and detailed recommendations
            </p>
          </div>
          <div>
            <h4 className="text-sm font-bold mb-1">Professional Format</h4>
            <p className="text-xs text-secondary">
              Clean, structured report format suitable for documentation and record-keeping purposes
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Reports
