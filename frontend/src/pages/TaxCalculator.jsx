import { useState, useEffect, useRef } from 'react'
import { taxAPI, analyticsAPI } from '../utils/api'
import html2pdf from 'html2pdf.js'
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from 'recharts'

function TaxCalculator() {
  const [step, setStep] = useState(1)
  const [financialYear, setFinancialYear] = useState('2025-26')
  const [ageGroup, setAgeGroup] = useState('0-60')

  // Income fields
  const [income, setIncome] = useState({
    salary: '',
    exemptAllowances: '',
    interestIncome: '',
    rentalIncome: '',
    homeLoanSelfOccupied: '',
    homeLoanLetOut: '',
    digitalAssets: '',
    otherIncome: ''
  })

  // Deductions (only matter for Old Regime comparison)
  const [deductions, setDeductions] = useState({
    '80C': '',
    '80D': '',
    '80TTA': '',
    '80G': '',
    '80E': '',
    '80CCD': '',
    '80CCD2': '',
    otherDeductions: ''
  })

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const reportRef = useRef(null)

  const downloadReport = () => {
    if (!reportRef.current) return
    const opt = {
      margin: [10, 10, 10, 10],
      filename: `Tax_Analysis_FY${financialYear}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true, logging: false },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    }

    // Briefly style for PDF bounds
    reportRef.current.style.padding = '20px'

    html2pdf().set(opt).from(reportRef.current).save().then(() => {
      reportRef.current.style.padding = '0px'
    })
  }

  // Calculate total gross income
  const totalIncome = () => {
    const sal = parseFloat(income.salary) || 0
    const exempt = parseFloat(income.exemptAllowances) || 0
    const interest = parseFloat(income.interestIncome) || 0
    const rental = parseFloat(income.rentalIncome) || 0
    const digital = parseFloat(income.digitalAssets) || 0
    const other = parseFloat(income.otherIncome) || 0
    return sal - exempt + interest + rental + digital + other
  }

  // Total deductions
  const totalDeductions = () => {
    return Object.values(deductions).reduce((sum, val) => sum + (parseFloat(val) || 0), 0)
  }

  const handleIncomeChange = (field, value) => {
    setIncome(prev => ({ ...prev, [field]: value }))
  }

  const handleDeductionChange = (field, value) => {
    setDeductions(prev => ({ ...prev, [field]: value }))
  }

  // --- AUTO EXTRACT PIPELINE ---
  const [entryMode, setEntryMode] = useState('manual')
  const [bankFiles, setBankFiles] = useState([])
  const [salaryFiles, setSalaryFiles] = useState([])
  const [passwords, setPasswords] = useState({})
  const [requiredFiles, setRequiredFiles] = useState([])
  const [extracting, setExtracting] = useState(false)
  const [aiAnalysis, setAiAnalysis] = useState(null)
  const [showDeductionModal, setShowDeductionModal] = useState(false)

  const handleBankFileChange = (e) => {
    setBankFiles(Array.from(e.target.files))
    setRequiredFiles([])
    setPasswords({})
    setError(null)
  }

  const handleSalaryFileChange = (e) => {
    setSalaryFiles(Array.from(e.target.files))
    setRequiredFiles([])
    setPasswords({})
    setError(null)
  }

  const handleSmartUpload = async () => {
    const allFiles = [...bankFiles, ...salaryFiles]
    if (allFiles.length === 0) return

    try {
      setExtracting(true)
      setError(null)
      setAiAnalysis(null)

      const formData = new FormData()
      allFiles.forEach(file => {
        formData.append('files', file)
      })

      if (Object.keys(passwords).length > 0) {
        formData.append('passwords', JSON.stringify(passwords))
      }

      const response = await analyticsAPI.extractTaxDocuments(formData)

      if (response.requires_password) {
        const stillRequired = [...(response.required_files || []), ...(response.incorrect_files || [])]
        setRequiredFiles(stillRequired)
        setError(response.message || "Document is password protected.")
        setExtracting(false)
        return
      }

      const data = response.extracted_data

      // Auto-Fill States
      setIncome(prev => ({ ...prev, salary: data.gross_income || 0 }))
      if (data.deductions) {
        setDeductions(prev => ({
          ...prev,
          '80C': data.deductions['80C'] || '',
          '80D': data.deductions['80D'] || '',
          '80TTA': data.deductions['80TTA'] || '',
          '80G': data.deductions['80G'] || '',
          '80E': data.deductions['80E'] || '',
          '80CCD': data.deductions['80CCD'] || '',
          '80CCD2': data.deductions['80CCD2'] || '',
          'otherDeductions': data.deductions['otherDeductions'] || ''
        }))
      }

      setAiAnalysis(data)
      setRequiredFiles([])
      
      // Instead of instantly calculating and silently rendering below, pop up a confirmation modal 
      // asking the user to manually verify/add to the deductions found by the AI ledger!
      setShowDeductionModal(true)
      
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to analyze documents')
    } finally {
      setExtracting(false)
    }
  }

  const handleCalculate = async () => {
    try {
      setLoading(true)
      setError(null)

      const gross = totalIncome()

      // Build deductions map for old regime (standard deduction auto-applied by backend)
      const oldDeductions = {}
      if (parseFloat(deductions['80C'])) oldDeductions['80C'] = parseFloat(deductions['80C'])
      if (parseFloat(deductions['80D'])) oldDeductions['80D'] = parseFloat(deductions['80D'])
      if (parseFloat(deductions['80TTA'])) oldDeductions['80TTA'] = parseFloat(deductions['80TTA'])
      if (parseFloat(deductions['80G'])) oldDeductions['80G'] = parseFloat(deductions['80G'])
      if (parseFloat(deductions['80E'])) oldDeductions['80E'] = parseFloat(deductions['80E'])
      if (parseFloat(deductions['80CCD'])) oldDeductions['80CCD(1B)'] = parseFloat(deductions['80CCD'])
      if (parseFloat(deductions['80CCD2'])) oldDeductions['80CCD(2)'] = parseFloat(deductions['80CCD2'])
      if (parseFloat(deductions.otherDeductions)) oldDeductions['Other'] = parseFloat(deductions.otherDeductions)

      // Home loan interest as 24(b)
      const homeLoan = parseFloat(income.homeLoanSelfOccupied) || 0
      if (homeLoan > 0) oldDeductions['24(b)'] = homeLoan

      // Determine new regime deductions
      const newDeductions = { 'Standard Deduction': financialYear === '2025-26' ? 75000 : 50000 }
      if (parseFloat(deductions['80CCD2'])) newDeductions['80CCD(2)'] = parseFloat(deductions['80CCD2'])

      // Compare both regimes
      const compareData = {
        gross_income: gross,
        financial_year: financialYear,
        deductions_old: { 'Standard Deduction': 50000, ...oldDeductions },
        deductions_new: newDeductions
      }

      const response = await taxAPI.compareRegimes(compareData)
      setResult(response)

      // Save for chatbot
      const taxDataForChatbot = {
        gross_income: gross,
        regime: response.comparison?.comparison?.better_regime || 'new',
        deductions: oldDeductions,
        total_tax: Math.min(
          response.comparison?.old?.tax_calculation?.total_tax || 0,
          response.comparison?.new?.tax_calculation?.total_tax || 0
        ),
        effective_tax_rate: response.comparison?.new?.tax_calculation?.effective_tax_rate || 0,
        risk_level: response.comparison?.new?.fraud_analysis?.risk_level || 'LOW'
      }
      localStorage.setItem('lastTaxCalculation', JSON.stringify(taxDataForChatbot))

    } catch (err) {
      let errorMsg = 'Failed to calculate tax. Please check your inputs.'
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          errorMsg = err.response.data.detail[0].msg
        } else {
          errorMsg = err.response.data.detail
        }
      }
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount) => {
    if (!amount && amount !== 0) return '₹0'
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const newRegimeSlabs = financialYear === '2025-26' ? [
    { range: 'Up to ₹4 lakh', rate: 'Nil' },
    { range: '₹4 lakh – ₹8 lakh', rate: '5%' },
    { range: '₹8 lakh – ₹12 lakh', rate: '10%' },
    { range: '₹12 lakh – ₹16 lakh', rate: '15%' },
    { range: '₹16 lakh – ₹20 lakh', rate: '20%' },
    { range: '₹20 lakh – ₹24 lakh', rate: '25%' },
    { range: 'Above ₹24 lakh', rate: '30%' },
  ] : [
    { range: 'Up to ₹3 lakh', rate: 'Nil' },
    { range: '₹3 lakh – ₹7 lakh', rate: '5%' },
    { range: '₹7 lakh – ₹10 lakh', rate: '10%' },
    { range: '₹10 lakh – ₹12 lakh', rate: '15%' },
    { range: '₹12 lakh – ₹15 lakh', rate: '20%' },
    { range: 'Above ₹15 lakh', rate: '30%' },
  ]

  const oldRegimeSlabs = ageGroup === '60-80' ? [
    { range: 'Up to ₹3 lakh', rate: 'Nil' },
    { range: '₹3 lakh – ₹5 lakh', rate: '5%' },
    { range: '₹5 lakh – ₹10 lakh', rate: '20%' },
    { range: 'Above ₹10 lakh', rate: '30%' },
  ] : ageGroup === '80+' ? [
    { range: 'Up to ₹5 lakh', rate: 'Nil' },
    { range: '₹5 lakh – ₹10 lakh', rate: '20%' },
    { range: 'Above ₹10 lakh', rate: '30%' },
  ] : [
    { range: 'Up to ₹2.5 lakh', rate: 'Nil' },
    { range: '₹2.5 lakh – ₹5 lakh', rate: '5%' },
    { range: '₹5 lakh – ₹10 lakh', rate: '20%' },
    { range: 'Above ₹10 lakh', rate: '30%' },
  ]

  const tabStyle = (tabNum) => ({
    padding: '0.75rem 1.5rem',
    cursor: 'pointer',
    borderBottom: step === tabNum ? '3px solid #6366f1' : '3px solid transparent',
    color: step === tabNum ? '#6366f1' : 'var(--text-secondary)',
    fontWeight: step === tabNum ? '600' : '400',
    background: 'none',
    border: 'none',
    borderBottomStyle: 'solid',
    fontSize: '0.95rem',
    transition: 'all 0.2s'
  })

  const inputGroupStyle = {
    marginBottom: '1.25rem'
  }

  const inputLabelStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '0.5rem',
    fontSize: '0.9rem',
    fontWeight: '500',
    color: 'var(--text-primary)'
  }

  const infoIconStyle = {
    width: '18px',
    height: '18px',
    borderRadius: '50%',
    border: '1.5px solid #94a3b8',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.7rem',
    color: '#94a3b8',
    cursor: 'help',
    flexShrink: 0
  }

  const rupeeInputStyle = {
    position: 'relative'
  }

  return (
    <div>
      <div className="mb-3">
        <h2>🧮 Income Tax Calculator</h2>
        <p className="text-secondary">
          Calculate your income tax for <strong>FY {financialYear}</strong> (AY {financialYear === '2025-26' ? '2026-27' : '2025-26'})
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '1.5rem', alignItems: 'start' }}>
        {/* Main Calculator Area */}
        <div className="card">
          {/* Mode Toggle */}
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
            <button
              className={`btn ${entryMode === 'manual' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setEntryMode('manual')}
              style={{ flex: 1 }}
            >
              ✍️ Manual Entry
            </button>
            <button
              className={`btn ${entryMode === 'auto' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setEntryMode('auto')}
              style={{ flex: 1, background: entryMode === 'auto' ? '#10b981' : 'transparent', borderColor: '#10b981', color: entryMode === 'auto' ? 'white' : '#10b981' }}
            >
              🤖 Smart Auto-Extract
            </button>
          </div>

          {/* AUTO EXTRACT MODE VIEW */}
          {entryMode === 'auto' && (
            <div style={{ animation: 'fadeIn 0.4s ease-out' }}>
              <h3 style={{ marginBottom: '1rem', color: '#10b981' }}>Automated Document Ingestion</h3>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                Securely upload your 12-Month Bank Statement alongside your Salary Slips (up to 12). The Gemini Forensic AI will extract annualized income, 80C deductions, and computationally cross-reference expenses to detect tax evasion flags. If your PDFs are protected by bank passwords, you will be securely prompted to instantly decrypt them in memory without permanently storing your keys.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                {/* Bank Statement Dropzone */}
                <div style={{
                  border: '2px dashed #cbd5e1',
                  borderRadius: '12px',
                  padding: '2rem 1rem',
                  textAlign: 'center',
                  background: '#f8fafc'
                }}>
                  <input
                    type="file"
                    accept=".pdf,.csv,.xlsx"
                    onChange={handleBankFileChange}
                    id="bankUpload"
                    style={{ display: 'none' }}
                  />
                  <label htmlFor="bankUpload" style={{ cursor: 'pointer', display: 'block' }}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🏦</div>
                    <h4 style={{ marginBottom: '0.5rem', color: '#334155' }}>Bank Statement</h4>
                    <p style={{ fontSize: '0.8rem', color: '#64748b' }}>Upload exactly 1 Document covering the financial year (12-mo ledger).</p>
                  </label>

                  {bankFiles.length > 0 && (
                    <div style={{ marginTop: '1rem', textAlign: 'left', background: 'white', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                      {bankFiles.map((f, i) => (
                        <div key={i} style={{ fontSize: '0.8rem', color: '#475569', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span>✓</span> {f.name} ({(f.size / 1024).toFixed(1)} KB)
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Salary Slips Dropzone */}
                <div style={{
                  border: '2px dashed #cbd5e1',
                  borderRadius: '12px',
                  padding: '2rem 1rem',
                  textAlign: 'center',
                  background: '#f8fafc'
                }}>
                  <input
                    type="file"
                    multiple
                    accept=".pdf"
                    onChange={handleSalaryFileChange}
                    id="salaryUpload"
                    style={{ display: 'none' }}
                  />
                  <label htmlFor="salaryUpload" style={{ cursor: 'pointer', display: 'block' }}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>💼</div>
                    <h4 style={{ marginBottom: '0.5rem', color: '#334155' }}>Salary Slips</h4>
                    <p style={{ fontSize: '0.8rem', color: '#64748b' }}>Select up to 12 PDFs. If your salary is static, simply upload 1.</p>
                  </label>

                  {salaryFiles.length > 0 && (
                    <div style={{ marginTop: '1rem', textAlign: 'left', background: 'white', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0', maxHeight: '100px', overflowY: 'auto' }}>
                      <div style={{ fontWeight: '600', marginBottom: '0.2rem', fontSize: '0.75rem' }}>{salaryFiles.length}/12 Slips Selected</div>
                      {salaryFiles.map((f, i) => (
                        <div key={i} style={{ fontSize: '0.8rem', color: '#475569', display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.2rem 0' }}>
                          <span>✓</span> {f.name.substring(0, 15)}... ({(f.size / 1024).toFixed(1)} KB)
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Secure Password UI Block */}
              {requiredFiles.length > 0 && (
                <div style={{ marginBottom: '2rem', background: 'rgba(239, 68, 68, 0.05)', padding: '1.5rem', borderRadius: '8px', border: '1px solid #ef4444', textAlign: 'left' }}>
                  <label style={{ display: 'block', fontSize: '1rem', color: '#ef4444', marginBottom: '1rem', fontWeight: 'bold' }}>
                    {error ? error : "🔒 The following documents are encrypted. Please unlock them:"}
                  </label>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
                    {requiredFiles.map(filename => (
                      <div key={filename}>
                        <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                          📄 {filename}
                        </div>
                        <input
                          type="password"
                          placeholder={`Password for ${filename}`}
                          value={passwords[filename] || ''}
                          onChange={(e) => setPasswords({ ...passwords, [filename]: e.target.value })}
                          style={{
                            padding: '0.75rem',
                            borderRadius: '8px',
                            border: '1px solid #ef4444',
                            width: '100%',
                            backgroundColor: 'white',
                            color: '#0f172a'
                          }}
                        />
                      </div>
                    ))}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '0.75rem' }}>
                    Your passwords are AES-256 encrypted in transit and instantly flushed from memory.
                  </div>
                </div>
              )}

              <div style={{ textAlign: 'center' }}>
                <button
                  className="btn btn-primary"
                  onClick={handleSmartUpload}
                  disabled={extracting || (bankFiles.length === 0 && salaryFiles.length === 0)}
                  style={{ padding: '1rem 3rem', background: '#10b981', border: 'none', fontSize: '1.1rem' }}
                >
                  {extracting ? '🔍 AI is cross-referencing documents...' : requiredFiles.length > 0 ? '🔓 Unlock & Extract' : 'Extract Data & Auto-Fill →'}
                </button>
              </div>

              {error && <div className="alert alert-danger" style={{ marginTop: '2rem' }}>{error}</div>}

              {/* AI Extracted Results Block */}
              {aiAnalysis && (
                <div style={{ marginTop: '3rem', paddingTop: '2rem', borderTop: '2px solid #e2e8f0' }}>
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0f172a' }}>
                    <span>🧠</span> AI Extraction Ledger
                  </h3>

                  {/* Data Visualization Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginTop: '1.5rem' }}>
                    {/* Metrics Panel */}
                    <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                      <div style={{ marginBottom: '1rem', fontSize: '0.9rem', color: '#64748b' }}>Found Parameters:</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontWeight: 600 }}>Extrapolated Income:</span>
                        <span style={{ color: '#10b981', fontWeight: 700 }}>₹{aiAnalysis.gross_income?.toLocaleString('en-IN')}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontWeight: 600 }}>Total Found Deductions:</span>
                        <span>₹{(aiAnalysis.deductions?.['80C'] || 0) + (aiAnalysis.deductions?.['80D'] || 0)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontWeight: 600 }}>Total Bank Deposits:</span>
                        <span>₹{aiAnalysis.total_deposits?.toLocaleString('en-IN')}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontWeight: 600 }}>Total Bank Expenses:</span>
                        <span style={{ color: '#ef4444' }}>₹{aiAnalysis.total_expenses?.toLocaleString('en-IN')}</span>
                      </div>
                      <hr style={{ margin: '1rem 0', borderColor: '#e2e8f0' }} />

                      {/* Dynamic Graphical Canvas */}
                      <div style={{ height: '250px', width: '100%', marginBottom: '1.5rem' }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={[
                              { name: 'Income', value: aiAnalysis.gross_income || 0, fill: '#10b981' },
                              { name: 'Deposits', value: aiAnalysis.total_deposits || 0, fill: '#3b82f6' },
                              { name: 'Expenses', value: aiAnalysis.total_expenses || 0, fill: '#ef4444' }
                            ]}
                            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                          >
                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                            <YAxis tickFormatter={(val) => `₹${val / 1000}k`} tick={{ fontSize: 12 }} />
                            <RechartsTooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                              {
                                [0, 1, 2].map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={['#10b981', '#3b82f6', '#ef4444'][index]} />
                                ))
                              }
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>

                      {/* Follow up AI Chat */}
                      {aiAnalysis.follow_up_questions?.length > 0 && (
                        <div>
                          <div style={{ fontWeight: 600, color: '#3b82f6', marginBottom: '0.5rem', fontSize: '0.9rem' }}>🤖 AI Follow-up Required:</div>
                          {aiAnalysis.follow_up_questions.map((q, i) => (
                            <div key={i} style={{ background: '#eff6ff', padding: '0.75rem', borderRadius: '8px', fontSize: '0.85rem', color: '#1e3a8a', marginBottom: '0.5rem' }}>
                              {q}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Fraud Flag Panel */}
                    <div style={{
                      background: aiAnalysis.fraud_risk === 'HIGH' ? '#fef2f2' : aiAnalysis.fraud_risk === 'MEDIUM' ? '#fefce8' : '#f0fdf4',
                      border: `1px solid ${aiAnalysis.fraud_risk === 'HIGH' ? '#fca5a5' : aiAnalysis.fraud_risk === 'MEDIUM' ? '#fde047' : '#86efac'}`,
                      padding: '1.5rem',
                      borderRadius: '12px',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>
                        {aiAnalysis.fraud_risk === 'HIGH' ? '🚨' : aiAnalysis.fraud_risk === 'MEDIUM' ? '⚠️' : '✅'}
                      </div>
                      <h4 style={{
                        color: aiAnalysis.fraud_risk === 'HIGH' ? '#dc2626' : aiAnalysis.fraud_risk === 'MEDIUM' ? '#ca8a04' : '#166534',
                        marginBottom: '1rem'
                      }}>
                        Evaluation Risk Level: {aiAnalysis.fraud_risk}
                      </h4>
                      <p style={{ fontSize: '0.9rem', color: '#475569', lineHeight: 1.6 }}>
                        {aiAnalysis.fraud_explanation}
                      </p>
                    </div>
                  </div>

                  <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                    <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '1rem' }}>
                      We have loaded these AI extractions into your calculator. Before running the final FY 2025-26 Dual-Regime math, please declare any additional tax deductions (like Mutual Funds, Health Insurance, or Corporate NPS) that weren't discovered inside your uploaded PDFs.
                    </p>
                    <button
                      className="btn btn-primary"
                      onClick={() => { setEntryMode('manual'); setStep(3); }}
                      style={{ padding: '1rem 3rem' }}
                    >
                      Proceed to Add Extra Deductions →
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* MANUAL ENTRY VIEW */}
          {entryMode === 'manual' && (
            <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
              {/* Step Tabs */}
              <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', marginBottom: '1.5rem' }}>
                <button style={tabStyle(1)} onClick={() => setStep(1)}>Basic details</button>
                <button style={tabStyle(2)} onClick={() => setStep(2)}>Income details</button>
                <button style={tabStyle(3)} onClick={() => setStep(3)}>Deduction</button>
              </div>

              {/* Step 1: Basic Details */}
              {step === 1 && (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>Financial year</div>
                      <select
                        className="form-select"
                        value={financialYear}
                        onChange={(e) => setFinancialYear(e.target.value)}
                        style={{ width: '100%' }}
                      >
                        <option value="2025-26">FY 2025-26 (Return to be filed between 1st April 2026 – 31st Dec 2026)</option>
                        <option value="2024-25">FY 2024-25 (Return to be filed between 1st April 2025 – 31st Dec 2025)</option>
                      </select>
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>Age group</div>
                      <select
                        className="form-select"
                        value={ageGroup}
                        onChange={(e) => setAgeGroup(e.target.value)}
                        style={{ width: '100%' }}
                      >
                        <option value="0-60">0-60</option>
                        <option value="60-80">60-80 (Senior Citizen)</option>
                        <option value="80+">80+ (Super Senior Citizen)</option>
                      </select>
                    </div>
                  </div>

                  <h3 style={{ textAlign: 'center', marginBottom: '1.5rem', fontSize: '1.1rem' }}>Income Tax Slab Rates</h3>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                    {/* New Regime Slabs */}
                    <div>
                      <h4 style={{ textAlign: 'center', marginBottom: '1rem', color: '#6366f1', fontSize: '0.95rem' }}>New Regime Slab Rates</h4>
                      <table className="comparison-table">
                        <thead>
                          <tr>
                            <th style={{ fontSize: '0.8rem' }}>Income Tax Slabs (Rs.)</th>
                            <th style={{ fontSize: '0.8rem' }}>Income Tax Rates</th>
                          </tr>
                        </thead>
                        <tbody>
                          {newRegimeSlabs.map((s, i) => (
                            <tr key={i}>
                              <td style={{ fontSize: '0.85rem' }}>{s.range}</td>
                              <td style={{ fontSize: '0.85rem', fontWeight: '500' }}>{s.rate}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Old Regime Slabs */}
                    <div>
                      <h4 style={{ textAlign: 'center', marginBottom: '1rem', color: '#f59e0b', fontSize: '0.95rem' }}>Old Regime Slab Rates</h4>
                      <table className="comparison-table">
                        <thead>
                          <tr>
                            <th style={{ fontSize: '0.8rem' }}>Income Tax Slabs (Rs.)</th>
                            <th style={{ fontSize: '0.8rem' }}>Income Tax Rates</th>
                          </tr>
                        </thead>
                        <tbody>
                          {oldRegimeSlabs.map((s, i) => (
                            <tr key={i}>
                              <td style={{ fontSize: '0.85rem' }}>{s.range}</td>
                              <td style={{ fontSize: '0.85rem', fontWeight: '500' }}>{s.rate}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <p style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '1rem', fontStyle: 'italic' }}>
                    * Slab rates vary for resident senior and super senior citizens.
                  </p>

                  <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
                    <button
                      className="btn btn-primary"
                      onClick={() => setStep(2)}
                      style={{ padding: '0.75rem 3rem', fontSize: '1rem' }}
                    >
                      Continue →
                    </button>
                  </div>
                </div>
              )}

              {/* Step 2: Income Details */}
              {step === 2 && (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Income from Salary
                        <span style={infoIconStyle} title="Your gross salary before any deductions or exemptions. Include basic pay + DA + HRA + special allowances.">ⓘ</span>
                      </div>
                      <div style={rupeeInputStyle}>
                        <input
                          type="number"
                          className="form-input"
                          placeholder="₹"
                          value={income.salary}
                          onChange={(e) => handleIncomeChange('salary', e.target.value)}
                        />
                      </div>
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Exempt allowances
                        <span style={infoIconStyle} title="HRA exemption, LTA, transport allowance and other exempt portions of your salary.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={income.exemptAllowances}
                        onChange={(e) => handleIncomeChange('exemptAllowances', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Income from interest
                        <span style={infoIconStyle} title="Interest from fixed deposits, recurring deposits, and other interest income.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={income.interestIncome}
                        onChange={(e) => handleIncomeChange('interestIncome', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Interest on home loan - Self occupied
                        <span style={infoIconStyle} title="Interest portion of home loan EMI for a house you live in. Max ₹2 Lakh deduction under old regime.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={income.homeLoanSelfOccupied}
                        onChange={(e) => handleIncomeChange('homeLoanSelfOccupied', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Rental income received
                        <span style={infoIconStyle} title="Rent received from a property you own and have rented out.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={income.rentalIncome}
                        onChange={(e) => handleIncomeChange('rentalIncome', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Interest on Home Loan - Let Out
                        <span style={infoIconStyle} title="Interest on home loan for a property that is rented out (let out). No max limit.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={income.homeLoanLetOut}
                        onChange={(e) => handleIncomeChange('homeLoanLetOut', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Income from digital assets
                        <span style={infoIconStyle} title="Net income from sale of cryptocurrency, NFT, or other virtual digital assets (Sale price - Cost of acquisition). Taxed at flat 30%.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={income.digitalAssets}
                        onChange={(e) => handleIncomeChange('digitalAssets', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Other income
                        <span style={infoIconStyle} title="Any other taxable income not covered above — business income, freelance income, etc.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={income.otherIncome}
                        onChange={(e) => handleIncomeChange('otherIncome', e.target.value)}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem' }}>
                    <button className="btn btn-secondary" onClick={() => setStep(1)}>
                      ← Back
                    </button>
                    <button className="btn btn-primary" onClick={() => setStep(3)} style={{ padding: '0.75rem 3rem' }}>
                      Continue →
                    </button>
                  </div>
                </div>
              )}

              {/* Step 3: Deductions */}
              {step === 3 && (
                <div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem', background: '#fef3c7', padding: '0.75rem', borderRadius: '8px' }}>
                    💡 Most of these deductions (80C, 80D, etc.) are applicable <strong>only under the Old Regime</strong>. However, <strong>80CCD(2) (Employer's NPS) is allowed in BOTH regimes</strong>. Under the New Regime, the Standard Deduction (₹{financialYear === '2025-26' ? '75,000' : '50,000'}) is auto-applied.
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Basic deductions - 80C
                        <span style={infoIconStyle} title="PPF, ELSS, LIC premium, EPF, NSC, Sukanya Samriddhi, 5yr FD, Home loan principal. Max ₹1.5 Lakh.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={deductions['80C']}
                        onChange={(e) => handleDeductionChange('80C', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Interest from deposits - 80TTA
                        <span style={infoIconStyle} title="Interest earned on savings bank account (not FDs). Max ₹10,000.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={deductions['80TTA']}
                        onChange={(e) => handleDeductionChange('80TTA', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Medical insurance - 80D
                        <span style={infoIconStyle} title="Health insurance premiums paid for self, spouse, children (₹25K) and parents (₹25K or ₹50K for seniors). Max ₹75K.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={deductions['80D']}
                        onChange={(e) => handleDeductionChange('80D', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Donations to charity - 80G
                        <span style={infoIconStyle} title="Donations to eligible charitable institutions. 50% or 100% deduction depending on the institution.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={deductions['80G']}
                        onChange={(e) => handleDeductionChange('80G', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Education loan interest - 80E
                        <span style={infoIconStyle} title="Interest paid on education loan for higher studies. No max limit, available for up to 8 years.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={deductions['80E']}
                        onChange={(e) => handleDeductionChange('80E', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Employee's contribution to NPS - 80CCD
                        <span style={infoIconStyle} title="Your own contribution to National Pension System (NPS). Additional ₹50K over 80C limit.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={deductions['80CCD']}
                        onChange={(e) => handleDeductionChange('80CCD', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Employer's contribution to NPS - 80CCD(2)
                        <span style={infoIconStyle} title="Employer's contribution to NPS. Up to 10% of salary (14% for central govt). Available in both regimes.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={deductions['80CCD2']}
                        onChange={(e) => handleDeductionChange('80CCD2', e.target.value)}
                      />
                    </div>

                    <div style={inputGroupStyle}>
                      <div style={inputLabelStyle}>
                        Any other deduction
                        <span style={infoIconStyle} title="Any other deductions not listed above.">ⓘ</span>
                      </div>
                      <input
                        type="number"
                        className="form-input"
                        placeholder="₹"
                        value={deductions.otherDeductions}
                        onChange={(e) => handleDeductionChange('otherDeductions', e.target.value)}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1.5rem' }}>
                    <button className="btn btn-secondary" onClick={() => setStep(2)}>
                      ← Back
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={handleCalculate}
                      disabled={loading}
                      style={{ padding: '0.75rem 3rem', fontSize: '1rem' }}
                    >
                      {loading ? 'Calculating...' : 'View Calculation'}
                    </button>
                  </div>

                  {error && (
                    <div className="alert alert-danger mt-2">
                      {error}
                    </div>
                  )}
                </div>
              )}

            </div> /* End of Manual Entry View */
          )}
        </div>

        {/* Sidebar - Tax Liability Summary */}
        <div style={{ position: 'sticky', top: '80px' }}>
          <div className="card" style={{ textAlign: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '1.5rem', fontWeight: '700' }}>Tax Liability Summary</h3>

            {result ? (
              <>
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Old Regime</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>
                    {formatCurrency(result.comparison?.old?.tax_calculation?.total_tax || 0)}
                  </div>
                </div>

                <div style={{ color: 'var(--text-tertiary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>vs</div>

                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}>
                    New Regime
                    {result.comparison?.comparison?.better_regime === 'new' && (
                      <span style={{ background: '#10b981', color: 'white', padding: '0.1rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: '600' }}>Recommended</span>
                    )}
                  </div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>
                    {formatCurrency(result.comparison?.new?.tax_calculation?.total_tax || 0)}
                  </div>
                </div>

                <div style={{
                  background: '#d1fae5',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  marginBottom: '1rem'
                }}>
                  <div style={{ fontSize: '0.85rem', color: '#065f46' }}>You save</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: '700', color: '#10b981' }}>
                    {formatCurrency(result.comparison?.comparison?.savings || 0)}
                  </div>
                </div>

                {/* Breakdown details */}
                <div style={{ textAlign: 'left', fontSize: '0.8rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                  <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>Best Regime: {result.comparison?.comparison?.better_regime?.toUpperCase()}</div>
                  <div className="deduction-item" style={{ padding: '0.4rem 0', fontSize: '0.8rem' }}>
                    <span>Gross Income</span>
                    <span>{formatCurrency(totalIncome())}</span>
                  </div>
                  <div className="deduction-item" style={{ padding: '0.4rem 0', fontSize: '0.8rem' }}>
                    <span>Old Effective Rate</span>
                    <span>{result.comparison?.old?.tax_calculation?.effective_tax_rate || 0}%</span>
                  </div>
                  <div className="deduction-item" style={{ padding: '0.4rem 0', fontSize: '0.8rem' }}>
                    <span>New Effective Rate</span>
                    <span>{result.comparison?.new?.tax_calculation?.effective_tax_rate || 0}%</span>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div style={{ marginBottom: '0.75rem' }}>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Old Regime</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>₹0</div>
                </div>

                <div style={{ color: 'var(--text-tertiary)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>vs</div>

                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>New Regime</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>₹0</div>
                </div>

                <div style={{
                  background: '#d1fae5',
                  padding: '0.75rem',
                  borderRadius: '8px'
                }}>
                  <div style={{ fontSize: '0.85rem', color: '#065f46' }}>You save</div>
                  <div style={{ fontSize: '1.3rem', fontWeight: '700', color: '#10b981' }}>₹0</div>
                </div>
              </>
            )}
          </div>

          {/* Quick info */}
          <div className="card" style={{ marginTop: '1rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <div style={{ fontWeight: '600', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>ℹ️ Auto-applied:</div>
            <ul style={{ margin: 0, paddingLeft: '1.2rem' }}>
              <li>Standard Deduction: {financialYear === '2025-26' ? '₹75,000 (New) / ₹50,000 (Old)' : '₹50,000 (Both)'}</li>
              <li>Section 87A Rebate (if eligible)</li>
              <li>Health & Education Cess (4%)</li>
              <li>Surcharge (if applicable)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Detailed Results */}
      {result && (
        <div style={{ marginTop: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 style={{ margin: 0 }}>Official Tax Analysis</h2>
            <button
              className="btn btn-primary"
              onClick={downloadReport}
              style={{ background: '#10b981', borderColor: '#10b981', boxShadow: '0 4px 6px -1px rgba(16, 185, 129, 0.4)' }}
            >
              📄 Download PDF Report
            </button>
          </div>

          <div ref={reportRef} style={{ background: 'white', borderRadius: '12px' }}>
            <div style={{ paddingBottom: '1rem', borderBottom: '2px solid #3b82f6', marginBottom: '1.5rem', display: 'none' }} className="pdf-header">
              <h1 style={{ fontSize: '1.8rem', color: '#1e3a8a', margin: '0 0 0.5rem 0' }}>Official Tax Analysis</h1>
              <div style={{ fontSize: '1.2rem', fontWeight: '700', color: '#0f172a' }}>FY {financialYear}</div>
            </div>

            <div className="grid grid-2">
              <div className="card" style={{ borderTop: '4px solid #f59e0b' }}>
                <h3>Old Regime — Detailed Breakdown</h3>
                <div className="deduction-item">
                  <span>Gross Income</span>
                  <span className="font-bold">{formatCurrency(result.comparison?.old?.tax_calculation?.gross_income)}</span>
                </div>
                <div className="deduction-item">
                  <span>Standard Deduction</span>
                  <span className="font-bold text-success">-₹50,000</span>
                </div>
                <div className="deduction-item">
                  <span>Other Deductions</span>
                  <span className="font-bold text-success">-{formatCurrency(Math.max(0, (result.comparison?.old?.tax_calculation?.total_deductions || 0) - 50000))}</span>
                </div>
                <div className="deduction-item">
                  <span>Taxable Income</span>
                  <span className="font-bold">{formatCurrency(result.comparison?.old?.tax_calculation?.taxable_income)}</span>
                </div>
                <div className="deduction-item" style={{ borderTop: '2px solid #f59e0b', marginTop: '0.5rem', paddingTop: '0.75rem' }}>
                  <span className="text-lg font-bold">Total Tax</span>
                  <span className="text-lg font-bold">{formatCurrency(result.comparison?.old?.tax_calculation?.total_tax)}</span>
                </div>
                <div className="deduction-item">
                  <span>Effective Rate</span>
                  <span className="font-bold">{result.comparison?.old?.tax_calculation?.effective_tax_rate}%</span>
                </div>
              </div>

              <div className="card" style={{ borderTop: '4px solid #6366f1' }}>
                <h3>New Regime — Detailed Breakdown</h3>
                <div className="deduction-item">
                  <span>Gross Income</span>
                  <span className="font-bold">{formatCurrency(result.comparison?.new?.tax_calculation?.gross_income)}</span>
                </div>
                <div className="deduction-item">
                  <span>Standard Deduction</span>
                  <span className="font-bold text-success">-{formatCurrency(financialYear === '2025-26' ? 75000 : 50000)}</span>
                </div>
                {(result.comparison?.new?.tax_calculation?.total_deductions || 0) > (financialYear === '2025-26' ? 75000 : 50000) && (
                  <div className="deduction-item">
                    <span>Other Deductions 80CCD(2)</span>
                    <span className="font-bold text-success">-{formatCurrency((result.comparison?.new?.tax_calculation?.total_deductions || 0) - (financialYear === '2025-26' ? 75000 : 50000))}</span>
                  </div>
                )}
                <div className="deduction-item">
                  <span>Taxable Income</span>
                  <span className="font-bold">{formatCurrency(result.comparison?.new?.tax_calculation?.taxable_income)}</span>
                </div>
                <div className="deduction-item" style={{ borderTop: '2px solid #6366f1', marginTop: '0.5rem', paddingTop: '0.75rem' }}>
                  <span className="text-lg font-bold">Total Tax</span>
                  <span className="text-lg font-bold">{formatCurrency(result.comparison?.new?.tax_calculation?.total_tax)}</span>
                </div>
                <div className="deduction-item">
                  <span>Effective Rate</span>
                  <span className="font-bold">{result.comparison?.new?.tax_calculation?.effective_tax_rate}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modern Deduction Popup Overlay */}
      {showDeductionModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
          backgroundColor: 'rgba(15, 23, 42, 0.75)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div style={{
            background: 'white', borderRadius: '16px', padding: '2rem',
            width: '90%', maxWidth: '500px', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            maxHeight: '90vh', overflowY: 'auto'
          }}>
            <h2 style={{ marginTop: 0, marginBottom: '0.5rem', color: '#0f172a', fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>🎯</span> Active Deductions Found
            </h2>
            <p style={{ color: '#64748b', fontSize: '0.9rem', marginBottom: '1.5rem', lineHeight: '1.5' }}>
              The AI has scanned your bank statements. Please verify the automated deductions below or add any manual cash deductions before finalizing your official tax calculation.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
              <div>
                <label className="form-label" style={{ fontWeight: '600' }}>Section 80C</label>
                <div style={{ fontSize: '0.70rem', color: '#64748b', marginBottom: '0.25rem' }}>LIC, ELSS, PPF, EPF</div>
                <input
                  type="number" className="form-input" placeholder="₹0"
                  value={deductions['80C']}
                  onChange={(e) => handleDeductionChange('80C', e.target.value)}
                  style={{ border: '1px solid #cbd5e1', background: '#f8fafc' }}
                />
              </div>

              <div>
                <label className="form-label" style={{ fontWeight: '600' }}>Section 80D</label>
                <div style={{ fontSize: '0.70rem', color: '#64748b', marginBottom: '0.25rem' }}>Health Insurance Premiums</div>
                <input
                  type="number" className="form-input" placeholder="₹0"
                  value={deductions['80D']}
                  onChange={(e) => handleDeductionChange('80D', e.target.value)}
                  style={{ border: '1px solid #cbd5e1', background: '#f8fafc' }}
                />
              </div>

              <div>
                <label className="form-label" style={{ fontWeight: '600' }}>Section 80TTA</label>
                <div style={{ fontSize: '0.70rem', color: '#64748b', marginBottom: '0.25rem' }}>Interest from deposits</div>
                <input
                  type="number" className="form-input" placeholder="₹0"
                  value={deductions['80TTA']}
                  onChange={(e) => handleDeductionChange('80TTA', e.target.value)}
                  style={{ border: '1px solid #cbd5e1', background: '#f8fafc' }}
                />
              </div>

              <div>
                <label className="form-label" style={{ fontWeight: '600' }}>Section 80G</label>
                <div style={{ fontSize: '0.70rem', color: '#64748b', marginBottom: '0.25rem' }}>Donations to charity</div>
                <input
                  type="number" className="form-input" placeholder="₹0"
                  value={deductions['80G']}
                  onChange={(e) => handleDeductionChange('80G', e.target.value)}
                  style={{ border: '1px solid #cbd5e1', background: '#f8fafc' }}
                />
              </div>

              <div>
                <label className="form-label" style={{ fontWeight: '600' }}>Section 80E</label>
                <div style={{ fontSize: '0.70rem', color: '#64748b', marginBottom: '0.25rem' }}>Education loan interest</div>
                <input
                  type="number" className="form-input" placeholder="₹0"
                  value={deductions['80E']}
                  onChange={(e) => handleDeductionChange('80E', e.target.value)}
                  style={{ border: '1px solid #cbd5e1', background: '#f8fafc' }}
                />
              </div>

              <div>
                <label className="form-label" style={{ fontWeight: '600' }}>Section 80CCD</label>
                <div style={{ fontSize: '0.70rem', color: '#64748b', marginBottom: '0.25rem' }}>Employee NPS</div>
                <input
                  type="number" className="form-input" placeholder="₹0"
                  value={deductions['80CCD']}
                  onChange={(e) => handleDeductionChange('80CCD', e.target.value)}
                  style={{ border: '1px solid #cbd5e1', background: '#f8fafc' }}
                />
              </div>

              <div>
                <label className="form-label" style={{ fontWeight: '600' }}>Section 80CCD(2)</label>
                <div style={{ fontSize: '0.70rem', color: '#64748b', marginBottom: '0.25rem' }}>Employer's NPS (Both Regimes)</div>
                <input
                  type="number" className="form-input" placeholder="₹0"
                  value={deductions['80CCD2']}
                  onChange={(e) => handleDeductionChange('80CCD2', e.target.value)}
                  style={{ border: '1px solid #cbd5e1', background: '#f8fafc' }}
                />
              </div>

              <div>
                <label className="form-label" style={{ fontWeight: '600' }}>Any Other</label>
                <div style={{ fontSize: '0.70rem', color: '#64748b', marginBottom: '0.25rem' }}>Other Deductions</div>
                <input
                  type="number" className="form-input" placeholder="₹0"
                  value={deductions.otherDeductions}
                  onChange={(e) => handleDeductionChange('otherDeductions', e.target.value)}
                  style={{ border: '1px solid #cbd5e1', background: '#f8fafc' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button
                className="btn btn-secondary"
                onClick={() => setShowDeductionModal(false)}
                style={{ padding: '0.75rem 1.5rem', background: '#f1f5f9', color: '#475569', border: 'none' }}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={() => {
                  setShowDeductionModal(false)
                  setTimeout(() => handleCalculate(), 50)
                }}
                disabled={loading}
                style={{
                  padding: '0.75rem 1.5rem', background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                  boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.5)', border: 'none'
                }}
              >
                {loading ? 'Calculating...' : 'Calculate Official Tax'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}

export default TaxCalculator
