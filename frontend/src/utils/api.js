import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add a request interceptor to inject the JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token && token !== 'dev-token') { // Don't send dev-token to real backend
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export const authAPI = {
  sendOtp: async (email, type) => {
    const response = await api.post('/auth/send-otp', { email, type })
    return response.data
  },
  signup: async (data) => {
    const response = await api.post('/auth/signup', data)
    return response.data
  },
  login: async (data) => {
    const response = await api.post('/auth/login', data)
    return response.data
  },
  googleLogin: async (credential) => {
    const response = await api.post('/auth/google-login', { credential })
    return response.data
  },
  resetPassword: async (data) => {
    const response = await api.post('/auth/reset-password', data)
    return response.data
  }
}

export const adminAPI = {
  getUsers: async () => {
    const response = await api.get('/admin/users')
    return response.data
  },
  deleteUser: async (id) => {
    const response = await api.delete(`/admin/users/${id}`)
    return response.data
  },
  getAuditLogs: async () => {
    const response = await api.get('/admin/audit-logs')
    return response.data
  },
  getMLLogs: async () => {
    const response = await api.get('/admin/ml-logs')
    return response.data
  },
  retrainModel: async () => {
    const response = await api.post('/admin/retrain-ml')
    return response.data
  }
}

export const taxAPI = {
  // Health check
  healthCheck: async () => {
    const response = await api.get('/')
    return response.data
  },

  // Get tax rules
  getRules: async (regime = 'old', financialYear = '2024-25') => {
    const response = await api.get('/rules/current', {
      params: { regime, financial_year: financialYear }
    })
    return response.data
  },

  // Analyze tax
  analyzeTax: async (userData) => {
    const response = await api.post('/analyze-tax', userData)
    return response.data
  },

  // Compare regimes
  compareRegimes: async (comparisonData) => {
    const response = await api.post('/compare-regimes', comparisonData)
    return response.data
  },

  // Generate report
  generateReport: async (userData) => {
    const response = await api.post('/generate-report', userData)
    return response.data
  },

  // Simulate scenarios
  simulateScenario: async (simulationData) => {
    const response = await api.post('/simulate-scenario', simulationData)
    return response.data
  },

  // Generate rules
  generateRules: async (regime = 'both', financialYear = '2024-25') => {
    const response = await api.post('/generate-rules', null, {
      params: { regime, financial_year: financialYear }
    })
    return response.data
  },
}

export const analyticsAPI = {
  analyzeBulk: async (formData) => {
    const response = await api.post('/analytics/analyze-bulk', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },
  predictMLFraud: async (data) => {
    const response = await api.post('/analytics/ml-predict', data)
    return response.data
  },
  analyzeStatements: async (formData) => {
    const response = await api.post('/analytics/analyze-statements', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },
  extractTaxDocuments: async (formData) => {
    const response = await api.post('/analytics/document-tax-extraction', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000  // 3 minutes — AI parsing takes 45-60s for massive PDFs
    })
    return response.data
  },
  analyzeSpending: async (formData) => {
    const response = await api.post('/analytics/analyze-spending', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000  // 3 minutes — AI review takes 20-60s for large PDFs
    })
    return response.data
  }
}

export const newsAPI = {
  getFinanceNews: async () => {
    const response = await api.get('/news/finance-news')
    return response.data
  }
}

export default api
