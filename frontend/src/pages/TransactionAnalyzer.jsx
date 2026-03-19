import { useState } from 'react'
import axios from 'axios'
import Markdown from 'react-markdown'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function TransactionAnalyzer() {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      // Validate file type
      const validTypes = [
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv'
      ]

      if (validTypes.includes(selectedFile.type) ||
          selectedFile.name.endsWith('.csv') ||
          selectedFile.name.endsWith('.xlsx') ||
          selectedFile.name.endsWith('.xls')) {
        setFile(selectedFile)
        setError(null)
      } else {
        setError('Please upload a valid CSV or Excel file (.csv, .xlsx, .xls)')
        setFile(null)
      }
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first')
      return
    }

    setUploading(true)
    setError(null)
    setAnalysis(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${API_BASE}/analyze-transactions`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      setAnalysis(response.data)
    } catch (err) {
      console.error('Upload failed:', err)
      setError(err.response?.data?.detail || 'Failed to analyze transactions. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const handleClear = () => {
    setFile(null)
    setAnalysis(null)
    setError(null)
  }

  return (
    <div>
      <div className="mb-3">
        <h2>Transaction Analyzer</h2>
        <p className="text-secondary">
          Upload your CSV or Excel file of transactions for AI-powered analysis
        </p>
      </div>

      {/* Upload Section */}
      <div className="card mb-3">
        <h3>Upload Transactions File</h3>

        <div style={{ marginBottom: '1.5rem' }}>
          <p className="text-sm text-secondary mb-2">
            Supported formats: CSV (.csv), Excel (.xlsx, .xls)
          </p>
          <p className="text-sm text-secondary mb-2">
            Your file should contain transaction data with columns like: Date, Description, Amount, Category, etc.
          </p>
        </div>

        <div style={{
          border: '2px dashed var(--border-color)',
          borderRadius: '8px',
          padding: '2rem',
          textAlign: 'center',
          background: 'var(--bg-tertiary)',
          marginBottom: '1rem'
        }}>
          <input
            type="file"
            id="file-upload"
            accept=".csv,.xlsx,.xls,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          <label
            htmlFor="file-upload"
            className="btn btn-primary"
            style={{ cursor: 'pointer', marginBottom: '1rem' }}
          >
            Choose File
          </label>

          {file && (
            <div style={{ marginTop: '1rem' }}>
              <p className="text-sm">
                <strong>Selected:</strong> {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </p>
            </div>
          )}

          {!file && (
            <p className="text-sm text-secondary" style={{ marginTop: '1rem' }}>
              No file selected
            </p>
          )}
        </div>

        {error && (
          <div style={{
            padding: '1rem',
            background: '#fee',
            border: '1px solid #fcc',
            borderRadius: '6px',
            marginBottom: '1rem'
          }}>
            <p className="text-danger text-sm">{error}</p>
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? 'Analyzing...' : 'Analyze Transactions'}
          </button>

          {(file || analysis) && (
            <button
              className="btn btn-secondary"
              onClick={handleClear}
              disabled={uploading}
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Loading State */}
      {uploading && (
        <div className="card">
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <div className="spinner" style={{ width: '40px', height: '40px', margin: '0 auto 1rem' }}></div>
            <p className="text-secondary">
              Analyzing your transactions with AI...
            </p>
          </div>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && !uploading && (
        <div className="grid grid-2">
          {/* Summary Stats */}
          <div className="card">
            <h3>Transaction Summary</h3>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Transactions</div>
                <div className="stat-value">{analysis.total_transactions || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Date Range</div>
                <div className="stat-value text-sm">
                  {analysis.date_range || 'N/A'}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Total Amount</div>
                <div className="stat-value text-primary">
                  ₹{analysis.total_amount?.toLocaleString('en-IN') || '0'}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Categories Found</div>
                <div className="stat-value">{analysis.categories_count || 0}</div>
              </div>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="card">
            <h3>AI Insights</h3>
            <div style={{
              background: 'var(--bg-tertiary)',
              padding: '1rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              maxHeight: '300px',
              overflowY: 'auto'
            }}>
              <Markdown>{analysis.ai_analysis || 'No insights available'}</Markdown>
            </div>
          </div>

          {/* Detailed Analysis */}
          {analysis.detailed_analysis && (
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <h3>Detailed Analysis</h3>
              <div style={{
                background: 'var(--bg-tertiary)',
                padding: '1.5rem',
                borderRadius: '6px',
                fontSize: '0.875rem',
                lineHeight: '1.6'
              }}>
                <Markdown>{analysis.detailed_analysis}</Markdown>
              </div>
            </div>
          )}

          {/* Tax Implications */}
          {analysis.tax_implications && (
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <h3>Tax Implications</h3>
              <div style={{
                background: '#fef9e7',
                padding: '1.5rem',
                borderRadius: '6px',
                fontSize: '0.875rem',
                border: '1px solid #f9e79f'
              }}>
                <Markdown>{analysis.tax_implications}</Markdown>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Info Section */}
      {!analysis && !uploading && (
        <div className="card">
          <h3>How it works</h3>
          <div className="grid grid-3">
            <div>
              <h4 className="text-sm font-bold mb-1">1. Upload File</h4>
              <p className="text-xs text-secondary">
                Upload your transaction history in CSV or Excel format from your bank or expense tracker.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-bold mb-1">2. AI Analysis</h4>
              <p className="text-xs text-secondary">
                Our AI agent will analyze spending patterns, categorize transactions, and identify tax implications.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-bold mb-1">3. Get Insights</h4>
              <p className="text-xs text-secondary">
                Receive detailed insights, tax-saving opportunities, and compliance recommendations.
              </p>
            </div>
          </div>

          <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--bg-tertiary)', borderRadius: '6px' }}>
            <h4 className="text-sm font-bold mb-1">Expected File Format</h4>
            <p className="text-xs text-secondary mb-2">
              Your file should contain these columns (names can vary):
            </p>
            <ul className="text-xs text-secondary" style={{ marginLeft: '1.5rem' }}>
              <li>Date (transaction date)</li>
              <li>Description or Narration (transaction details)</li>
              <li>Amount (transaction amount)</li>
              <li>Category (optional - expense category)</li>
              <li>Type (optional - debit/credit or income/expense)</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

export default TransactionAnalyzer
