import React, { useState, useEffect } from 'react';
import { newsAPI } from '../utils/api';

const FinanceNews = () => {
    const [news, setNews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchNews = async () => {
            try {
                const data = await newsAPI.getFinanceNews();
                // Randomize to mix Tax and Market news natively
                const shuffled = data.articles.sort(() => 0.5 - Math.random());
                setNews(shuffled);
            } catch (err) {
                setError('Failed to fetch the latest Indian finance news. Please try again later.');
            } finally {
                setLoading(false);
            }
        };
        fetchNews();
    }, []);

    if (loading) {
        return (
            <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                <h2>📰 Fetching Live Updates...</h2>
                <p>Connecting to The Economic Times India global feeds...</p>
            </div>
        );
    }

    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1rem' }}>
            <div style={{ marginBottom: '2.5rem', textAlign: 'center' }}>
                <h1 style={{ color: 'var(--primary-color)', marginBottom: '0.5rem', fontSize: '2.5rem' }}>Live Finance intelligence</h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>Real-time Tax, Wealth, and Corporate Market updates curated for professionals.</p>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '2rem' }}>
                {news.map((article, index) => (
                    <div key={index} style={{
                        background: 'var(--bg-secondary)',
                        borderRadius: '16px',
                        padding: '1.75rem',
                        boxShadow: '0 10px 15px -3px rgba(0,0,0,0.05)',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        border: '1px solid var(--border-color)',
                        transition: 'all 0.3s ease',
                        cursor: 'pointer'
                    }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'translateY(-6px)';
                            e.currentTarget.style.boxShadow = '0 20px 25px -5px rgba(0,0,0,0.1)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'translateY(0)';
                            e.currentTarget.style.boxShadow = '0 10px 15px -3px rgba(0,0,0,0.05)';
                        }}
                        onClick={() => window.open(article.link, '_blank')}
                    >
                        <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                                <span style={{
                                    background: article.category === 'Stock Market' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(37, 99, 235, 0.15)',
                                    color: article.category === 'Stock Market' ? '#059669' : '#1d4ed8',
                                    padding: '0.4rem 1rem',
                                    borderRadius: '20px',
                                    fontSize: '0.8rem',
                                    fontWeight: '700',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.5px'
                                }}>
                                    {article.category}
                                </span>
                                <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', fontWeight: '500' }}>
                                    {new Date(article.published).toLocaleDateString()}
                                </span>
                            </div>
                            <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', lineHeight: '1.4', color: 'var(--text-primary)' }}>{article.title}</h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.6', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                {article.summary ? article.summary.replace(/<[^>]+>/g, '') : "Click to read the full analytical report directly on the publisher's site."}
                            </p>
                        </div>
                        <div style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.85rem', color: 'var(--text-tertiary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontWeight: '600' }}>{article.source}</span>
                            <span style={{ color: 'var(--primary-color)', fontWeight: 'bold' }}>Read story →</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default FinanceNews;
