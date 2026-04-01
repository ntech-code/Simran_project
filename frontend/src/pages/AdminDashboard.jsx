import { useState, useEffect } from 'react'
import { adminAPI } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

function AdminDashboard() {
    const { isAdmin } = useAuth()
    const navigate = useNavigate()

    const [users, setUsers] = useState([])
    const [auditLogs, setAuditLogs] = useState([])
    const [mlLogs, setMlLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    useEffect(() => {
        if (!isAdmin) {
            navigate('/')
            return
        }

        const fetchData = async () => {
            try {
                const [usersData, logsData, mlData] = await Promise.all([
                    adminAPI.getUsers(),
                    adminAPI.getAuditLogs().catch(() => []),
                    adminAPI.getMLLogs().catch(() => [])
                ]);
                setUsers(usersData)
                setAuditLogs(logsData)
                setMlLogs(mlData)
            } catch (err) {
                setError('Failed to fetch users. Are you sure you have admin privileges?')
            } finally {
                setLoading(false)
            }
        }

        fetchData()
    }, [isAdmin, navigate])

    const handleToggleBlock = async (userId, currentStatus) => {
        if (window.confirm(`Are you sure you want to ${currentStatus ? 'unblock' : 'block'} this user?`)) {
            try {
                await adminAPI.toggleBlockUser(userId)
                setUsers(users.map(u => u.id === userId ? { ...u, is_blocked: !currentStatus } : u))
            } catch (err) {
                alert(err.response?.data?.detail || 'Failed to update user block status')
            }
        }
    }

    const handleDelete = async (userId) => {
        if (window.confirm('WARNING: Are you sure you want to permanently delete this user? This action cannot be undone.')) {
            try {
                await adminAPI.deleteUser(userId)
                setUsers(users.filter(u => u.id !== userId))
            } catch (err) {
                alert(err.response?.data?.detail || 'Failed to delete user')
            }
        }
    }

    if (!isAdmin) return null

    if (loading) {
        return (
            <div className="card text-center" style={{ padding: '3rem' }}>
                <p className="text-secondary">Loading admin dashboard...</p>
            </div>
        )
    }

    return (
        <div>
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: 'none' }}>
                <div>
                    <h1>Admin Dashboard</h1>
                    <p className="text-secondary">Manage system users and view activity</p>
                </div>
                <div className="badge badge-success" style={{ padding: '0.4rem 1rem', fontSize: '0.9rem' }}>
                    Admin Mode Active
                </div>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            <div className="card">
                <h3>Registered Users ({users.length})</h3>
                <p className="text-secondary mb-3">List of all users registered in the Indian Tax Analysis System.</p>

                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                        <thead>
                            <tr style={{ borderBottom: '2px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                                <th style={{ padding: '0.75rem' }}>ID</th>
                                <th style={{ padding: '0.75rem' }}>Name</th>
                                <th style={{ padding: '0.75rem' }}>Email</th>
                                <th style={{ padding: '0.75rem' }}>Role/Status</th>
                                <th style={{ padding: '0.75rem' }}>Joined On</th>
                                <th style={{ padding: '0.75rem', textAlign: 'right' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(user => (
                                <tr key={user.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                                    <td style={{ padding: '0.75rem' }}>{user.id}</td>
                                    <td style={{ padding: '0.75rem', fontWeight: '500' }}>{user.name || 'N/A'}</td>
                                    <td style={{ padding: '0.75rem' }}>{user.email}</td>
                                    <td style={{ padding: '0.75rem' }}>
                                        {user.is_admin ? (
                                            <span className="badge badge-warning" style={{ marginRight: '0.5rem' }}>Admin</span>
                                        ) : (
                                            <span className="badge badge-success" style={{ backgroundColor: '#e0f2fe', color: '#0369a1', marginRight: '0.5rem' }}>User</span>
                                        )}
                                        {user.is_blocked && (
                                            <span className="badge badge-danger">Blocked</span>
                                        )}
                                    </td>
                                    <td style={{ padding: '0.75rem', color: 'var(--text-tertiary)' }}>
                                        {new Date(user.created_at).toLocaleDateString()}
                                    </td>
                                    <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                                        {!user.is_admin && (
                                            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                                                <button
                                                    className={`btn ${user.is_blocked ? 'btn-success' : 'btn-warning'}`}
                                                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                                                    onClick={() => handleToggleBlock(user.id, user.is_blocked)}
                                                >
                                                    {user.is_blocked ? 'Unblock' : 'Block'}
                                                </button>
                                                <button
                                                    className="btn btn-danger"
                                                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', backgroundColor: '#dc2626', color: 'white', border: 'none' }}
                                                    onClick={() => handleDelete(user.id)}
                                                >
                                                    Delete
                                                </button>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {users.length === 0 && (
                                <tr>
                                    <td colSpan="6" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                        No users found in the database.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Global System Audit Trail */}
            <div className="card" style={{ marginTop: '2rem' }}>
                <h3>Global System Audit Trail</h3>
                <p className="text-secondary mb-3">Live chronological history of all Forensic AI and Document Analysis operations across the system.</p>

                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                        <thead>
                            <tr style={{ borderBottom: '2px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                                <th style={{ padding: '0.75rem' }}>Log ID</th>
                                <th style={{ padding: '0.75rem' }}>User Email</th>
                                <th style={{ padding: '0.75rem' }}>Files Analyzed</th>
                                <th style={{ padding: '0.75rem' }}>Risk Signature</th>
                                <th style={{ padding: '0.75rem' }}>Fraud Vol.</th>
                                <th style={{ padding: '0.75rem' }}>Flagged Txns</th>
                                <th style={{ padding: '0.75rem' }}>Timestamp</th>
                            </tr>
                        </thead>
                        <tbody>
                            {auditLogs.map(log => (
                                <tr key={log.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                                    <td style={{ padding: '0.75rem', fontWeight: 'bold' }}>#{log.id}</td>
                                    <td style={{ padding: '0.75rem' }}>{log.user_email}</td>
                                    <td style={{ padding: '0.75rem', maxWidth: '250px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                        {log.filenames}
                                    </td>
                                    <td style={{ padding: '0.75rem' }}>
                                        <span className={`badge badge-${log.risk_level === 'CRITICAL' ? 'danger' : log.risk_level === 'HIGH' ? 'warning' : 'success'}`}>
                                            {log.risk_level}
                                        </span>
                                    </td>
                                    <td style={{ padding: '0.75rem', color: log.total_volume > 0 ? 'var(--danger-color)' : 'var(--text-secondary)', fontWeight: log.total_volume > 0 ? 'bold' : 'normal' }}>
                                        ₹ {Number(log.total_volume).toLocaleString('en-IN')}
                                    </td>
                                    <td style={{ padding: '0.75rem' }}>{log.transaction_count}</td>
                                    <td style={{ padding: '0.75rem', color: 'var(--text-tertiary)' }}>
                                        {new Date(log.created_at).toLocaleString()}
                                    </td>
                                </tr>
                            ))}
                            {auditLogs.length === 0 && (
                                <tr>
                                    <td colSpan="7" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                                        No forensic logs captured in the database yet.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>


        </div>
    )
}

export default AdminDashboard
