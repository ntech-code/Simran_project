import React, { useState } from 'react';
import { analyticsAPI } from '../utils/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip, Legend } from 'recharts';

const FraudAnalysis = () => {
    const [files, setFiles] = useState([]);
    const [passwords, setPasswords] = useState({});
    const [requiredFiles, setRequiredFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            setFiles(Array.from(e.target.files));
            setError(null);
            setResult(null);
            setRequiredFiles([]);
            setPasswords({});
        }
    };

    const handleAnalyze = async () => {
        if (files.length === 0) {
            setError("Please select at least one file to analyze.");
            return;
        }

        const isPdfMode = files.some(f => f.name.toLowerCase().endsWith('.pdf'));

        // Validate mixed file types
        for (let f of files) {
            const isPdf = f.name.toLowerCase().endsWith('.pdf');
            if (isPdfMode && !isPdf) {
                setError("Please upload ONLY PDF statements, or a single CSV/Excel ledger.");
                return;
            }
            if (!isPdfMode && isPdf) {
                setError("Please upload ONLY PDF statements, or a single CSV/Excel ledger.");
                return;
            }
        }

        if (!isPdfMode && files.length > 1) {
            setError("For large spreadsheets (CSV/Excel), please upload only ONE master file. Use PDFs for multi-file statement scans.");
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        const formData = new FormData();
        if (isPdfMode) {
            files.forEach(f => formData.append('files', f));
            if (Object.keys(passwords).length > 0) {
                formData.append('passwords', JSON.stringify(passwords));
            }
        } else {
            formData.append('file', files[0]);
        }

        try {
            const response = isPdfMode
                ? await analyticsAPI.analyzeStatements(formData)
                : await analyticsAPI.analyzeBulk(formData);

            if (response.requires_password) {
                const stillRequired = [...(response.required_files || []), ...(response.incorrect_files || [])];
                setRequiredFiles(stillRequired);
                setError(response.message || "Document is password protected.");
                setLoading(false);
                return;
            }

            if (response.error) {
                setError(response.message || "Failed to analyze document.");
            } else {
                setResult(response);
                setRequiredFiles([]);
            }
        } catch (err) {
            setError(err.response?.data?.detail || "An unexpected error occurred during the forensic analysis.");
        } finally {
            setLoading(false);
        }
    };

    const getRiskColor = (level) => {
        switch (level?.toUpperCase()) {
            case 'CRITICAL': return '#dc2626'; // red-600
            case 'HIGH': return '#ea580c'; // orange-600
            case 'MEDIUM': return '#eab308'; // yellow-500
            case 'LOW': return '#16a34a'; // green-600
            default: return 'var(--text-secondary)';
        }
    };

    return (
        <div className="dashboard-container" style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>

            <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
                <h1 style={{ fontSize: '2.5rem', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                    🕵️ AI Fraud Forensics
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', maxWidth: '750px', margin: '0 auto', lineHeight: '1.6' }}>
                    <strong>Dual-Engine Architecture:</strong> Upload PDF Bank Statements for instant, 100% offline analysis using our <strong>Local Kaggle ML Model</strong>. Or, upload massive CSV Ledgers to trigger our <strong>Gemini LLM Agent</strong> for deep structural forensic scanning.
                </p>
            </div>

            <div className="card" style={{ marginBottom: '2rem', textAlign: 'center', padding: '3rem 2rem', border: '2px dashed var(--border-color)', transition: 'all 0.3s ease' }}>
                <div style={{ marginBottom: '1.5rem' }}>
                    <span style={{ fontSize: '3rem' }}>📄</span>
                </div>
                <h3 style={{ marginBottom: '1rem', color: 'var(--text-primary)' }}>Upload Financial Documents</h3>

                <input
                    type="file"
                    id="file-upload"
                    multiple
                    accept=".pdf, .csv, .xlsx, .xls"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                />

                <label
                    htmlFor="file-upload"
                    className="btn btn-secondary"
                    style={{ cursor: 'pointer', display: 'inline-block', marginBottom: '1rem', fontWeight: 'bold' }}
                >
                    + Select PDF Statements or CSV Files
                </label>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)', marginBottom: '1.5rem' }}>Multi-select enabled for PDF Bank Statements.</div>

                {files.length > 0 && (
                    <div style={{ marginTop: '1rem', background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: '8px', maxWidth: '600px', margin: '0 auto', textAlign: 'left' }}>
                        <div style={{ fontWeight: '600', color: 'var(--primary-color)', marginBottom: '0.5rem' }}>
                            Ready to analyze {files.length} document{files.length > 1 ? 's' : ''}:
                        </div>
                        <ul style={{ margin: 0, paddingLeft: '1.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1rem' }}>
                            {files.map((f, i) => (
                                <li key={i}>{f.name} ({(f.size / 1024).toFixed(1)} KB)</li>
                            ))}
                        </ul>

                        {requiredFiles.length > 0 && (
                            <div style={{ marginTop: '1rem', background: 'rgba(239, 68, 68, 0.05)', padding: '1.5rem', borderRadius: '8px', border: '1px solid var(--danger-color)' }}>
                                <label style={{ display: 'block', fontSize: '1rem', color: 'var(--danger-color)', marginBottom: '1rem', fontWeight: 'bold' }}>
                                    {error ? error : "The following documents are encrypted. Please unlock them:"}
                                </label>

                                {requiredFiles.map(filename => (
                                    <div key={filename} style={{ marginBottom: '1rem' }}>
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
                                                border: '1px solid var(--danger-color)',
                                                width: '100%',
                                                maxWidth: '350px',
                                                backgroundColor: 'var(--bg-primary)',
                                                color: 'var(--text-primary)'
                                            }}
                                        />
                                    </div>
                                ))}
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '0.5rem' }}>
                                    Your passwords are encrypted in transit and never permanently stored.
                                </div>
                            </div>
                        )}
                    </div>
                )}

                <div style={{ marginTop: '2rem' }}>
                    <button
                        className="btn btn-primary"
                        onClick={handleAnalyze}
                        disabled={files.length === 0 || loading}
                        style={{ padding: '1rem 2.5rem', fontSize: '1.1rem', width: '100%', maxWidth: '350px', background: '#e11d48', borderColor: '#e11d48' }}
                    >
                        {loading ? '🔍 Running AI Forensics... (10-20s)' : requiredFiles.length > 0 ? '🔓 Unlock & Analyze' : '🚨 Deploy AI Forensic Agent'}
                    </button>
                </div>

                {error && requiredFiles.length === 0 && (
                    <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#fef2f2', color: '#dc2626', borderRadius: '8px', border: '1px solid #fca5a5', maxWidth: '600px', margin: '1.5rem auto 0' }}>
                        <strong>Error:</strong> {error}
                    </div>
                )}
            </div>

            {result && (
                <div className="card mt-4 fade-in" style={{ padding: '2rem' }}>

                    {/* Dynamic AI Conclusion Block */}
                    {result.conclusion && (
                        <div style={{ padding: '1.5rem', background: result.risk_level === 'LOW' ? 'rgba(16, 185, 129, 0.05)' : 'rgba(239, 68, 68, 0.05)', borderRadius: '12px', borderLeft: `6px solid ${result.risk_level === 'LOW' ? '#10b981' : 'var(--danger-color)'}`, marginBottom: '2.5rem' }}>
                            <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: result.risk_level === 'LOW' ? '#059669' : 'var(--danger-color)' }}>
                                {result.risk_level === 'LOW' ? '✅' : '🚨'} AI Forensic Conclusion
                            </h3>
                            <p style={{ fontSize: '1.05rem', lineHeight: '1.6', color: 'var(--text-secondary)', marginBottom: 0 }}>
                                {result.conclusion}
                            </p>
                        </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
                        <h2 style={{ fontSize: '1.8rem', color: 'var(--text-primary)', margin: 0 }}>Forensic AI Report</h2>
                        <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '2.5rem', fontWeight: '800', color: getRiskColor(result.risk_level), lineHeight: '1' }}>
                                {result.risk_level}
                            </div>
                            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem', letterSpacing: '1px', textTransform: 'uppercase' }}>
                                Total Risk Assessment ({Math.round(result.risk_score * 100)}% Severity)
                            </div>
                        </div>
                    </div>

                    <div style={{ marginBottom: '2.5rem', backgroundColor: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: '12px', borderLeft: `6px solid ${getRiskColor(result.risk_level)}` }}>
                        <h3 style={{ marginBottom: '0.75rem', color: 'var(--text-primary)' }}>Executive Summary</h3>
                        <p style={{ color: 'var(--text-secondary)', lineHeight: '1.7', whiteSpace: 'pre-wrap', margin: 0 }}>
                            {result.forensic_summary}
                        </p>
                        {result.financial_metrics && (
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
                                <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Total Deposits Received</div>
                                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--success-color)' }}>
                                        ₹ {result.financial_metrics.total_deposits.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                                    </div>
                                </div>
                                <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Total Expenditures</div>
                                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--primary-color)' }}>
                                        ₹ {result.financial_metrics.total_withdrawals.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                                    </div>
                                </div>
                                <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--danger-color)' }}>
                                    <div style={{ fontSize: '0.85rem', color: 'var(--danger-color)', marginBottom: '0.25rem', fontWeight: '500' }}>Suspicious Volume Detected</div>
                                    <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--danger-color)' }}>
                                        ₹ {result.financial_metrics.suspicious_volume.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                                    </div>
                                </div>
                            </div>
                        )}

                        {result.financial_metrics?.categories && (
                            <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'var(--bg-primary)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                                <h4 style={{ marginBottom: '1rem', color: 'var(--text-primary)', textAlign: 'center' }}>Categorical Transaction Fingerprint</h4>
                                <div style={{ height: '300px', width: '100%' }}>
                                    <ResponsiveContainer>
                                        <PieChart>
                                            <Pie
                                                data={Object.entries(result.financial_metrics.categories)
                                                    .filter(([_, value]) => value > 0)
                                                    .map(([name, value]) => ({ name, value }))
                                                }
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={60}
                                                outerRadius={100}
                                                paddingAngle={5}
                                                dataKey="value"
                                            >
                                                {Object.entries(result.financial_metrics.categories)
                                                    .filter(([_, value]) => value > 0)
                                                    .map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'][index % 5]} />
                                                    ))}
                                            </Pie>
                                            <RechartsTooltip formatter={(value) => `₹${value.toLocaleString('en-IN')}`} />
                                            <Legend verticalAlign="bottom" height={36} />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        )}
                        <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #cbd5e1', fontSize: '0.9rem', color: 'var(--text-tertiary)', fontWeight: 'bold' }}>
                            {result.total_analyzed}
                        </div>
                    </div>

                    <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-primary)' }}>Flags and Anomalies Detected ({result.anomalies?.length || 0})</h3>

                    {result.anomalies && result.anomalies.length > 0 ? (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                                <thead>
                                    <tr style={{ backgroundColor: 'var(--bg-secondary)', borderBottom: '2px solid var(--border-color)' }}>
                                        <th style={{ padding: '1rem', fontWeight: '600' }}>Severity</th>
                                        <th style={{ padding: '1rem', fontWeight: '600' }}>Location / Date</th>
                                        <th style={{ padding: '1rem', fontWeight: '600' }}>Forensic Observation</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {result.anomalies.map((anomaly, idx) => (
                                        <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)', transition: 'background-color 0.2s' }}>
                                            <td style={{ padding: '1rem' }}>
                                                <span style={{
                                                    padding: '0.35rem 0.75rem',
                                                    borderRadius: '20px',
                                                    fontSize: '0.85rem',
                                                    fontWeight: '700',
                                                    backgroundColor: `${getRiskColor(anomaly.severity)}20`,
                                                    color: getRiskColor(anomaly.severity)
                                                }}>
                                                    {anomaly.severity}
                                                </span>
                                            </td>
                                            <td style={{ padding: '1rem', color: 'var(--text-secondary)', fontWeight: '500' }}>
                                                {anomaly.transaction_id || `Row #${anomaly.row_index || 'N/A'}`}
                                            </td>
                                            <td style={{ padding: '1rem', color: 'var(--text-primary)', lineHeight: '1.5' }}>{anomaly.reason}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div style={{ padding: '3rem', textAlign: 'center', backgroundColor: '#f0fdf4', borderRadius: '12px', border: '1px dashed #86efac', color: '#166534' }}>
                            <h4 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>✅ Clean Document</h4>
                            <p>The forensic analyzer found no suspicious patterns, smurfing, or tax evasion traits in the provided documents.</p>
                        </div>
                    )}

                    {/* Self-Training ML Status */}
                    {result.model_training && (
                        <div style={{
                            marginTop: '2rem',
                            padding: '1.5rem',
                            background: result.model_training.retrained
                                ? 'linear-gradient(135deg, #f0fdf4, #dcfce7)'
                                : 'linear-gradient(135deg, #eff6ff, #dbeafe)',
                            borderRadius: '12px',
                            border: `1px solid ${result.model_training.retrained ? '#86efac' : '#93c5fd'}`
                        }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                                <span style={{ fontSize: '1.5rem' }}>{result.model_training.retrained ? '🧠' : '📊'}</span>
                                <h4 style={{ margin: 0, color: result.model_training.retrained ? '#166534' : '#1e40af' }}>
                                    {result.model_training.retrained ? 'Model Auto-Retrained!' : 'Self-Training ML Active'}
                                </h4>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
                                <div style={{ background: 'rgba(255,255,255,0.7)', padding: '0.75rem', borderRadius: '8px' }}>
                                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Rows Added This Session</div>
                                    <div style={{ fontSize: '1.3rem', fontWeight: '700', color: '#0f172a' }}>
                                        +{result.model_training.rows_added_this_session?.toLocaleString() || 0}
                                    </div>
                                </div>
                                <div style={{ background: 'rgba(255,255,255,0.7)', padding: '0.75rem', borderRadius: '8px' }}>
                                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>Total Training Dataset</div>
                                    <div style={{ fontSize: '1.3rem', fontWeight: '700', color: '#0f172a' }}>
                                        {result.model_training.total_dataset_rows?.toLocaleString() || '—'} rows
                                    </div>
                                </div>
                                {result.model_training.retrained && (
                                    <div style={{ background: 'rgba(255,255,255,0.7)', padding: '0.75rem', borderRadius: '8px' }}>
                                        <div style={{ fontSize: '0.8rem', color: '#64748b' }}>New Model Accuracy</div>
                                        <div style={{ fontSize: '1.3rem', fontWeight: '700', color: '#16a34a' }}>
                                            {result.model_training.new_accuracy}%
                                        </div>
                                    </div>
                                )}
                            </div>
                            {result.model_training.message && (
                                <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: '#475569', fontStyle: 'italic' }}>
                                    {result.model_training.message}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

        </div>
    );
};

export default FraudAnalysis;
