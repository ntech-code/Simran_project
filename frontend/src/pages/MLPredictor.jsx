import React, { useState } from 'react';
import { analyticsAPI } from '../utils/api';

const MLPredictor = () => {
    const [formData, setFormData] = useState({
        Age: 35,
        Gross_Income: 1500000,
        Business_Income_Ratio: 0.1,
        HRA_Claimed: 0,
        Section_80C: 150000,
        Section_80G: 0
    });

    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: parseFloat(value) || 0
        }));
    };

    const handlePredict = async () => {
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await analyticsAPI.predictMLFraud(formData);
            setResult(response);
        } catch (err) {
            const errorDetail = err.response?.data?.detail;
            if (Array.isArray(errorDetail)) {
                // Format FastAPI Pydantic array errors gracefully so React doesn't crash
                setError(errorDetail.map(e => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join(' | '));
            } else {
                setError(errorDetail || "Failed to get prediction from ML model.");
            }
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
        <div className="dashboard-container" style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
                <h1 style={{ fontSize: '2.5rem', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                    🤖 Kaggle ML Predictor
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', maxWidth: '700px', margin: '0 auto' }}>
                    This model is trained on a synthesized dataset of 15,000 Indian tax profiles using a <strong>Scikit-Learn Random Forest Classifier</strong>. It instantly detects complex statistical anomalies in tax evasion patterns.
                </p>
            </div>

            <div className="grid grid-2" style={{ gap: '2rem' }}>
                <div className="card">
                    <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-primary)', borderBottom: '2px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                        Input Taxpayer Profile
                    </h3>

                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                        <label className="form-label">Age</label>
                        <input type="number" name="Age" className="form-input" value={formData.Age} onChange={handleInputChange} />
                    </div>

                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                        <label className="form-label">Gross Income (₹)</label>
                        <input type="number" name="Gross_Income" className="form-input" value={formData.Gross_Income} onChange={handleInputChange} />
                    </div>

                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                        <label className="form-label">Business Income Ratio (0.0 to 1.0)</label>
                        <input type="number" step="0.1" name="Business_Income_Ratio" className="form-input" value={formData.Business_Income_Ratio} onChange={handleInputChange} />
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>0 = purely Salary. 1 = purely Business.</span>
                    </div>

                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                        <label className="form-label">HRA Claimed (₹)</label>
                        <input type="number" name="HRA_Claimed" className="form-input" value={formData.HRA_Claimed} onChange={handleInputChange} />
                    </div>

                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                        <label className="form-label">Section 80C Claimed (₹)</label>
                        <input type="number" name="Section_80C" className="form-input" value={formData.Section_80C} onChange={handleInputChange} />
                    </div>

                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                        <label className="form-label">Section 80G Donations (₹)</label>
                        <input type="number" name="Section_80G" className="form-input" value={formData.Section_80G} onChange={handleInputChange} />
                    </div>

                    <button
                        className="btn btn-primary"
                        onClick={handlePredict}
                        disabled={loading}
                        style={{ width: '100%', padding: '1rem', marginTop: '1rem', background: '#4f46e5', fontSize: '1.1rem' }}
                    >
                        {loading ? 'Running Random Forest Model...' : '🔍 Predict Evasion Risk'}
                    </button>

                    {error && <div className="alert alert-danger mt-2">{error}</div>}
                </div>

                <div>
                    {result ? (
                        <div className="card fade-in" style={{ height: '100%' }}>
                            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                                <h2 style={{ fontSize: '1.5rem', color: 'var(--text-secondary)' }}>Prediction Result</h2>
                                <div style={{
                                    fontSize: '4rem',
                                    fontWeight: '800',
                                    color: getRiskColor(result.risk_level),
                                    lineHeight: '1',
                                    marginTop: '1rem'
                                }}>
                                    {result.evasion_probability}%
                                </div>
                                <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: getRiskColor(result.risk_level), marginTop: '0.5rem', textTransform: 'uppercase', letterSpacing: '2px' }}>
                                    {result.risk_level} RISK
                                </div>
                            </div>

                            <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: '8px', borderLeft: `4px solid ${getRiskColor(result.risk_level)}` }}>
                                <h4 style={{ marginBottom: '1rem' }}>Top Contributing Features:</h4>
                                <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--text-secondary)' }}>
                                    {result.top_contributing_factors.map((factor, idx) => (
                                        <li key={idx} style={{ marginBottom: '0.5rem' }}>
                                            <strong>{factor.feature.replace('_', ' ')}</strong> ({factor.importance}% impact)
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            <div style={{ marginTop: '2rem', textAlign: 'center' }}>
                                {result.is_evasion_suspect ? (
                                    <span style={{ background: '#fef2f2', color: '#dc2626', padding: '0.5rem 1rem', borderRadius: '20px', fontWeight: 'bold' }}>
                                        ⚠️ Profile patterns match known evasion clusters in the Kaggle dataset.
                                    </span>
                                ) : (
                                    <span style={{ background: '#f0fdf4', color: '#16a34a', padding: '0.5rem 1rem', borderRadius: '20px', fontWeight: 'bold' }}>
                                        ✅ Profile conforms to standard taxpayer benchmarks.
                                    </span>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="card" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', color: 'var(--text-tertiary)', border: '2px dashed var(--border-color)' }}>
                            <span style={{ fontSize: '4rem', marginBottom: '1rem' }}>🌲</span>
                            <h3>Random Forest Idle</h3>
                            <p style={{ textAlign: 'center', maxWidth: '300px' }}>Enter a financial profile and run the prediction to see the AI's risk assessment and feature importances.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MLPredictor;
