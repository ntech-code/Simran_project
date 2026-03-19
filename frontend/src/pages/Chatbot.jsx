import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import Markdown from 'react-markdown'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Chatbot() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [hasContext, setHasContext] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load context from localStorage if user calculated tax
  useEffect(() => {
    const savedTaxData = localStorage.getItem('lastTaxCalculation')
    if (savedTaxData) {
      const taxData = JSON.parse(savedTaxData)
      setContextFromTaxData(taxData)
    } else {
      setMessages([{
        role: 'assistant',
        content: '👋 Hello! I\'m your tax assistant. I can help you with:\n\n• Understanding your tax calculation\n• Explaining deductions\n• Suggesting tax-saving strategies\n• Answering general tax questions\n\n💡 Tip: Calculate your tax first in the Tax Calculator, then I\'ll have full context of your situation!',
        timestamp: new Date().toISOString()
      }])
    }
  }, [])

  const setContextFromTaxData = async (taxData) => {
    try {
      const contextPayload = {
        gross_income: taxData.gross_income || 0,
        regime: taxData.regime || 'old',
        deductions: taxData.deductions || {},
        taxable_income: taxData.taxable_income || 0,
        total_tax: taxData.total_tax || 0,
        effective_tax_rate: taxData.effective_tax_rate || 0,
        risk_score: taxData.risk_score || 0,
        risk_level: taxData.risk_level || 'UNKNOWN',
        compliance_score: taxData.compliance_score || 0,
        flags: taxData.flags || []
      }

      await axios.post(`${API_BASE}/chatbot/set-context`, contextPayload)

      setHasContext(true)
      setMessages([{
        role: 'assistant',
        content: `✅ Great! I'm now aware of your tax details:\n\n• Income: ₹${taxData.gross_income?.toLocaleString('en-IN')}\n• Regime: ${taxData.regime?.toUpperCase()}\n• Tax: ₹${taxData.total_tax?.toLocaleString('en-IN')}\n• Risk Level: ${taxData.risk_level}\n\nAsk me anything about your tax calculation!`,
        timestamp: new Date().toISOString()
      }])

      // Get suggestions
      loadSuggestions()

    } catch (error) {
      console.error('Failed to set context:', error)
    }
  }

  const loadSuggestions = async () => {
    try {
      const response = await axios.get(`${API_BASE}/chatbot/suggestions`)
      setSuggestions(response.data.suggestions || [])
    } catch (error) {
      console.error('Failed to load suggestions:', error)
    }
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = input.trim()
    setInput('')

    // Add user message
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    }])

    setLoading(true)

    try {
      const response = await axios.post(`${API_BASE}/chatbot/chat`, {
        message: userMessage
      })

      // Add bot response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.bot_response,
        timestamp: response.data.timestamp
      }])

      setHasContext(response.data.has_context)

    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date().toISOString()
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const askSuggestion = (suggestion) => {
    // Remove numbering from suggestion
    const cleanSuggestion = suggestion.replace(/^\d+\.\s*/, '')
    setInput(cleanSuggestion)
  }

  const quickQuestions = [
    "How was my tax calculated?",
    "Can I save more tax?",
    "Should I switch regimes?",
    "What are my red flags?",
    "Explain my deductions"
  ]

  return (
    <div>
      <div className="mb-3">
        <h2>Tax Assistant Chatbot</h2>
        <p className="text-secondary">
          AI-powered tax expert that knows your tax details
          {hasContext && <span className="text-success"> ✓ Context loaded</span>}
        </p>
      </div>

      <div className="grid grid-2">
        {/* Chat Window */}
        <div className="card" style={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
          <h3>Chat</h3>

          {/* Messages */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '1rem',
            background: 'var(--bg-tertiary)',
            borderRadius: '6px',
            marginBottom: '1rem'
          }}>
            {messages.map((msg, index) => (
              <div
                key={index}
                style={{
                  marginBottom: '1rem',
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                <div
                  style={{
                    maxWidth: '80%',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    background: msg.role === 'user' ? 'var(--primary-color)' : 'var(--bg-primary)',
                    color: msg.role === 'user' ? 'white' : 'var(--text-primary)',
                    border: msg.role === 'assistant' ? '1px solid var(--border-color)' : 'none',
                    whiteSpace: 'pre-wrap'
                  }}
                >
                  <div style={{ fontSize: '0.875rem' }}>
                    <Markdown>{msg.content}</Markdown>
                  </div>
                  <div style={{
                    fontSize: '0.7rem',
                    opacity: 0.7,
                    marginTop: '0.25rem'
                  }}>
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ textAlign: 'center', padding: '1rem' }}>
                <div className="spinner" style={{ width: '24px', height: '24px', margin: '0 auto' }}></div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Ask me anything about taxes..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
              style={{ flex: 1 }}
            />
            <button
              className="btn btn-primary"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
            >
              Send
            </button>
          </div>
        </div>

        {/* Sidebar */}
        <div>
          {/* Quick Questions */}
          <div className="card mb-3">
            <h3>Quick Questions</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {quickQuestions.map((question, index) => (
                <button
                  key={index}
                  className="btn btn-secondary"
                  onClick={() => setInput(question)}
                  style={{ textAlign: 'left', fontSize: '0.875rem' }}
                >
                  💬 {question}
                </button>
              ))}
            </div>
          </div>

          {/* Personalized Suggestions */}
          {suggestions.length > 0 && (
            <div className="card">
              <h3>💡 Personalized Tips</h3>
              <p className="text-xs text-secondary mb-2">
                Based on your tax calculation
              </p>
              <div style={{ fontSize: '0.875rem' }}>
                {suggestions.map((suggestion, index) => (
                  <div
                    key={index}
                    style={{
                      padding: '0.75rem',
                      background: 'var(--bg-tertiary)',
                      borderRadius: '6px',
                      marginBottom: '0.5rem',
                      cursor: 'pointer'
                    }}
                    onClick={() => askSuggestion(suggestion)}
                  >
                    {suggestion}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Context Status */}
          {!hasContext && (
            <div className="card">
              <h3>📊 No Context Yet</h3>
              <p className="text-sm text-secondary">
                Calculate your tax in the <strong>Tax Calculator</strong> page first, then come back here. I'll have full context of your situation!
              </p>
              <a href="/calculator" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem', textDecoration: 'none' }}>
                Go to Calculator
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Chatbot
