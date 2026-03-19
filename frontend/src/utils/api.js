import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

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

export default api
