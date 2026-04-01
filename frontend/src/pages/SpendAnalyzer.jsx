import React, { useState } from 'react';
import { analyticsAPI } from '../utils/api';

const CATEGORY_EMOJIS = {
    'Food': '🍕', 'Entertainment': '🎬', 'Cafes': '☕', 'Pan & Tobacco': '🚬',
    'Credit Card Payment': '💳', 'Bills & Utilities': '💡', 'Travel': '✈️',
    'Investments': '📈', 'Shopping': '🛍️', 'Friends (Sent)': '💸',
    'Friends (Received)': '💰', 'Rent': '🏠', 'Education': '📚',
    'Health': '🏥', 'Salary / Income': '💼', 'Cashback / Refund': '🔄',
    'EMI / Loan': '🏦', 'Liquor / Wine': '🍷', 'Subscription': '🎫',
    'Grocery': '🛒', 'Government / Tax': '🏛️', 'Others': '📦', 'Uncategorized': '❓'
};

const CATEGORY_COLORS = {
    'Food': '#ef4444', 'Entertainment': '#f97316', 'Cafes': '#a16207',
    'Pan & Tobacco': '#65a30d', 'Credit Card Payment': '#0891b2',
    'Bills & Utilities': '#2563eb', 'Travel': '#7c3aed', 'Investments': '#059669',
    'Shopping': '#db2777', 'Friends (Sent)': '#dc2626', 'Friends (Received)': '#16a34a',
    'Rent': '#9333ea', 'Education': '#0d9488', 'Health': '#e11d48',
    'Salary / Income': '#15803d', 'Cashback / Refund': '#0284c7',
    'EMI / Loan': '#b45309', 'Liquor / Wine': '#7e22ce', 'Subscription': '#f43f5e',
    'Grocery': '#84cc16', 'Government / Tax': '#6b7280', 'Others': '#64748b', 'Uncategorized': '#94a3b8'
};

// Fallback generator for entirely new AI categories
const getEmojiForCategory = (cat) => CATEGORY_EMOJIS[cat] || '✨';
const getColorForCategory = (cat) => {
    if (CATEGORY_COLORS[cat]) return CATEGORY_COLORS[cat];
    let hash = 0;
    for (let i = 0; i < cat.length; i++) hash = cat.charCodeAt(i) + ((hash << 5) - hash);
    const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
    return '#' + '00000'.substring(0, 6 - c.length) + c;
};

const SpendAnalyzer = () => {
    const [files, setFiles] = useState([]);
    const [passwords, setPasswords] = useState({});
    const [requiredFiles, setRequiredFiles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [expandedCats, setExpandedCats] = useState({});

    const toggleCat = (catName) => setExpandedCats(prev => ({ ...prev, [catName]: !prev[catName] }));

    const handleFileChange = (e) => {
        if (e.target.files?.length > 0) {
            setFiles(Array.from(e.target.files));
            setError(null); setResult(null); setRequiredFiles([]);
        }
    };

    const handleAnalyze = async () => {
        if (!files.length) { setError("Please select at least one file."); return; }
        setLoading(true); setError(null); setResult(null);
        const formData = new FormData();
        files.forEach(f => formData.append('files', f));
        if (Object.keys(passwords).length > 0) formData.append('passwords', JSON.stringify(passwords));
        try {
            const response = await analyticsAPI.analyzeSpending(formData);
            if (response.requires_password) {
                setRequiredFiles([...(response.required_files || []), ...(response.incorrect_files || [])]);
                setError(response.message); setLoading(false); return;
            }
            if (response.error) setError(response.message);
            else { setResult(response); setRequiredFiles([]); setExpandedCats({}); }
        } catch (err) {
            setError(err.response?.data?.detail || "Analysis failed.");
        } finally { setLoading(false); }
    };

    const fmt = (n) => `₹${(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

    return (
        <div style={{ padding: '2rem', maxWidth: '1100px', margin: '0 auto' }}>

            {/* Hero */}
            <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                <h1 style={{ fontSize: '2.5rem', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>💸 Smart Spend Analyzer</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', maxWidth: '700px', margin: '0 auto', lineHeight: '1.6' }}>
                    Upload your bank statement. Our <strong>ML + AI engine</strong> will show you <strong>exactly where every rupee went</strong> — down to the merchant name.
                </p>
            </div>

            {/* Upload */}
            <div className="card" style={{ marginBottom: '2rem', textAlign: 'center', padding: '2.5rem 2rem', border: '2px dashed var(--border-color)' }}>
                <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>📄</div>
                <h3 style={{ margin: '0 0 1rem', color: 'var(--text-primary)' }}>Upload Bank Statement</h3>
                <input type="file" id="spend-upload" multiple accept=".pdf,.csv,.xlsx,.xls" onChange={handleFileChange} style={{ display: 'none' }} />
                <label htmlFor="spend-upload" className="btn btn-secondary" style={{ cursor: 'pointer', display: 'inline-block', fontWeight: 'bold', marginBottom: '0.5rem' }}>
                    + Select PDF / Excel Statements
                </label>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>PDF bank statements, CSV, or Excel supported</div>

                {files.length > 0 && (
                    <div style={{ marginTop: '1rem', background: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: '8px', maxWidth: '550px', margin: '1rem auto 0', textAlign: 'left' }}>
                        <div style={{ fontWeight: '600', color: 'var(--primary-color)', marginBottom: '0.4rem', fontSize: '0.9rem' }}>
                            {files.length} file{files.length > 1 ? 's' : ''} ready:
                        </div>
                        <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                            {files.map((f, i) => <li key={i}>{f.name} ({(f.size / 1024).toFixed(1)} KB)</li>)}
                        </ul>
                        {requiredFiles.length > 0 && (
                            <div style={{ marginTop: '1rem', padding: '1rem', border: '1px solid var(--danger-color)', borderRadius: '8px', background: 'rgba(239,68,68,0.05)' }}>
                                <label style={{ display: 'block', color: 'var(--danger-color)', fontWeight: 'bold', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                                    🔐 {error || "Encrypted files:"}
                                </label>
                                {requiredFiles.map(fn => (
                                    <div key={fn} style={{ marginBottom: '0.5rem' }}>
                                        <div style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-secondary)' }}>📄 {fn}</div>
                                        <input type="password" placeholder={`Password for ${fn}`} value={passwords[fn] || ''}
                                            onChange={e => setPasswords({ ...passwords, [fn]: e.target.value })}
                                            style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid var(--danger-color)', width: '100%', maxWidth: '300px', background: 'var(--bg-primary)', color: 'var(--text-primary)', marginTop: '0.25rem' }}
                                        />
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                <div style={{ marginTop: '1.5rem' }}>
                    <button className="btn btn-primary" onClick={handleAnalyze} disabled={!files.length || loading}
                        style={{ padding: '0.9rem 2rem', fontSize: '1.05rem', maxWidth: '320px', width: '100%', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none' }}>
                        {loading ? '🔍 Analyzing...' : requiredFiles.length > 0 ? '🔓 Unlock & Analyze' : '💸 Analyze My Spending'}
                    </button>
                </div>

                {error && requiredFiles.length === 0 && (
                    <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#fef2f2', color: '#dc2626', borderRadius: '8px', border: '1px solid #fca5a5', maxWidth: '500px', margin: '1rem auto 0', fontSize: '0.9rem' }}>
                        <strong>Error:</strong> {error}
                    </div>
                )}
            </div>

            {/* ========= RESULTS ========= */}
            {result && (
                <div className="fade-in">

                    {/* Quick Stats */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
                        <div style={{ padding: '1.2rem', borderRadius: '12px', background: 'linear-gradient(135deg, #fef3c7, #fef9c3)', borderLeft: '4px solid #f59e0b', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.75rem', color: '#92400e', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Transactions</div>
                            <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#78350f' }}>{result.total_transactions?.toLocaleString()}</div>
                        </div>
                        <div style={{ padding: '1.2rem', borderRadius: '12px', background: 'linear-gradient(135deg, #fee2e2, #fecaca)', borderLeft: '4px solid #ef4444', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.75rem', color: '#991b1b', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Total Spent</div>
                            <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#7f1d1d' }}>{fmt(result.total_spent)}</div>
                        </div>
                        <div style={{ padding: '1.2rem', borderRadius: '12px', background: 'linear-gradient(135deg, #dcfce7, #bbf7d0)', borderLeft: '4px solid #22c55e', textAlign: 'center' }}>
                            <div style={{ fontSize: '0.75rem', color: '#166534', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Total Received</div>
                            <div style={{ fontSize: '1.8rem', fontWeight: '800', color: '#14532d' }}>{fmt(result.total_received)}</div>
                        </div>
                    </div>

                    {/* ======= TREE VIEW — THE MAIN FEATURE ======= */}
                    <div className="card" style={{ padding: '2rem', marginBottom: '2rem' }}>
                        <h2 style={{ margin: '0 0 0.5rem', color: 'var(--text-primary)', fontSize: '1.6rem' }}>
                            📊 Where Your Money Went
                        </h2>
                        <p style={{ color: 'var(--text-tertiary)', fontSize: '0.85rem', margin: '0 0 1.5rem' }}>
                            Click any category to expand and see individual merchants & amounts
                        </p>

                        {result.categories && Object.entries(result.categories).map(([catName, catData]) => {
                            const color = getColorForCategory(catName);
                            const emoji = getEmojiForCategory(catName);
                            const isOpen = expandedCats[catName];
                            const isCreditCat = ['Friends (Received)', 'Salary / Income', 'Cashback / Refund'].includes(catName);

                            return (
                                <div key={catName} style={{ marginBottom: '0.5rem' }}>
                                    {/* Category Header */}
                                    <div
                                        onClick={() => toggleCat(catName)}
                                        style={{
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            padding: '0.9rem 1.2rem', cursor: 'pointer', borderRadius: isOpen ? '10px 10px 0 0' : '10px',
                                            background: isOpen ? `${color}12` : 'var(--bg-secondary)',
                                            borderLeft: `4px solid ${color}`, transition: 'all 0.2s',
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                            <span style={{ fontSize: '1.3rem' }}>{emoji}</span>
                                            <span style={{ fontWeight: '700', color: 'var(--text-primary)', fontSize: '1.05rem' }}>{catName}</span>
                                            <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', fontWeight: '500' }}>
                                                ({catData.count} txns)
                                            </span>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                            <span style={{ fontWeight: '800', fontSize: '1.15rem', color: isCreditCat ? '#16a34a' : color }}>
                                                {isCreditCat ? '+' : ''}{fmt(catData.total)}
                                            </span>
                                            <span style={{ fontSize: '0.85rem', color: 'var(--text-tertiary)' }}>
                                                {catData.percentage}%
                                            </span>
                                            <span style={{ transition: 'transform 0.2s', transform: isOpen ? 'rotate(90deg)' : 'rotate(0)', fontSize: '0.9rem', color: 'var(--text-tertiary)' }}>▶</span>
                                        </div>
                                    </div>

                                    {/* Expanded: Merchant Tree */}
                                    {isOpen && catData.subcategories && (
                                        <div style={{
                                            borderLeft: `4px solid ${color}`, borderRadius: '0 0 10px 10px',
                                            background: `${color}06`, padding: '0.5rem 0'
                                        }}>
                                            {Object.entries(catData.subcategories).map(([subName, subData]) => (
                                                <div key={subName}>
                                                    {/* Subcategory: only show if different from merchant names */}
                                                    {Object.keys(subData.merchants).length > 1 && (
                                                        <div style={{ padding: '0.5rem 1.5rem 0.2rem', fontSize: '0.8rem', color: 'var(--text-tertiary)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                                            {subName}
                                                        </div>
                                                    )}
                                                    {/* Individual Merchants */}
                                                    {Object.entries(subData.merchants)
                                                        .sort((a, b) => b[1].total - a[1].total)
                                                        .slice(0, 35)
                                                        .map(([merchName, merchData]) => (
                                                            <div
                                                                key={merchName}
                                                                style={{
                                                                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                                                    padding: '0.55rem 1.5rem 0.55rem 2.5rem',
                                                                    borderBottom: '1px solid rgba(0,0,0,0.04)',
                                                                    transition: 'background 0.15s',
                                                                }}
                                                                onMouseEnter={e => e.currentTarget.style.background = `${color}10`}
                                                                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                                                            >
                                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: color, flexShrink: 0 }} />
                                                                    <span style={{ color: 'var(--text-primary)', fontWeight: '500', fontSize: '0.95rem' }}>
                                                                        {merchName}
                                                                    </span>
                                                                    {merchData.count > 1 && (
                                                                        <span style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', background: 'var(--bg-secondary)', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                                                                            ×{merchData.count}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                                                    <span style={{ fontWeight: '700', color: merchData.is_credit ? '#16a34a' : '#dc2626', fontSize: '0.95rem' }}>
                                                                        {merchData.is_credit ? '+' : '-'}{fmt(merchData.total)}
                                                                    </span>
                                                                    {merchData.count > 1 && (
                                                                        <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)' }}>
                                                                            avg {fmt(merchData.avg)}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        ))}
                                                    {Object.keys(subData.merchants).length > 35 && (
                                                        <div style={{ padding: '0.5rem 2.5rem', fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
                                                            + {Object.keys(subData.merchants).length - 35} more smaller transactions...
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    {/* Friends Detailed */}
                    {(Object.keys(result.friends_sent || {}).length > 0 || Object.keys(result.friends_received || {}).length > 0) && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                            {/* Sent */}
                            {Object.keys(result.friends_sent || {}).length > 0 && (
                                <div className="card" style={{ padding: '1.5rem' }}>
                                    <h3 style={{ margin: '0 0 1rem', color: '#dc2626', fontSize: '1.1rem' }}>
                                        💸 Total Sent to Friends — {fmt(Object.values(result.friends_sent).reduce((a, b) => a + b, 0))}
                                    </h3>
                                    {Object.entries(result.friends_sent).map(([name, amount]) => (
                                        <div key={name} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                                            <span style={{ fontWeight: '500', color: 'var(--text-primary)' }}>→ Sent to {name}</span>
                                            <span style={{ fontWeight: '700', color: '#dc2626' }}>{fmt(amount)}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {/* Received */}
                            {Object.keys(result.friends_received || {}).length > 0 && (
                                <div className="card" style={{ padding: '1.5rem' }}>
                                    <h3 style={{ margin: '0 0 1rem', color: '#16a34a', fontSize: '1.1rem' }}>
                                        💰 Total Received from Friends — {fmt(Object.values(result.friends_received).reduce((a, b) => a + b, 0))}
                                    </h3>
                                    {Object.entries(result.friends_received).map(([name, amount]) => (
                                        <div key={name} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                                            <span style={{ fontWeight: '500', color: 'var(--text-primary)' }}>← Received from {name}</span>
                                            <span style={{ fontWeight: '700', color: '#16a34a' }}>{fmt(amount)}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Top Merchants Overall */}
                    {result.top_merchants?.length > 0 && (
                        <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
                            <h3 style={{ margin: '0 0 1rem', color: 'var(--text-primary)' }}>🏪 Top 15 Merchants (All Categories)</h3>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '0' }}>
                                {result.top_merchants.map((m, i) => {
                                    const maxVal = result.top_merchants[0]?.total || 1;
                                    const pct = (m.total / maxVal) * 100;
                                    return (
                                        <div key={m.name} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                                            <span style={{ width: '28px', fontWeight: '700', color: 'var(--text-tertiary)', fontSize: '0.85rem', textAlign: 'right' }}>
                                                #{i + 1}
                                            </span>
                                            <div style={{ flex: 1, position: 'relative' }}>
                                                <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${pct}%`, background: 'rgba(99, 102, 241, 0.08)', borderRadius: '4px', transition: 'width 0.5s' }} />
                                                <div style={{ position: 'relative', display: 'flex', justifyContent: 'space-between', padding: '0.35rem 0.5rem' }}>
                                                    <span style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.95rem' }}>{m.name}</span>
                                                    <span style={{ fontWeight: '700', color: '#6366f1', fontSize: '0.95rem' }}>{fmt(m.total)}</span>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                </div>
            )}
        </div>
    );
};

export default SpendAnalyzer;
