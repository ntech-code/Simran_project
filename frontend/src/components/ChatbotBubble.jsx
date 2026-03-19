import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import Markdown from 'react-markdown'
import './ChatbotBubble.css'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function ChatbotBubble() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [hasContext, setHasContext] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const messagesEndRef = useRef(null)
  const chatContainerRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load context when bubble opens
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      loadContext()
    }
  }, [isOpen])

  const loadContext = async () => {
    const savedTaxData = localStorage.getItem('lastTaxCalculation')

    if (savedTaxData) {
      try {
        const taxData = JSON.parse(savedTaxData)

        // Set context in backend
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

        // Welcome message with context
        setMessages([{
          role: 'assistant',
          content: `✅ Hi! I'm your tax assistant. I can see you calculated:\n\n💰 Income: ₹${taxData.gross_income?.toLocaleString('en-IN')}\n📊 Tax: ₹${taxData.total_tax?.toLocaleString('en-IN')}\n⚖️ Regime: ${taxData.regime?.toUpperCase()}\n🎯 Risk: ${taxData.risk_level}\n\nAsk me anything!`,
          timestamp: new Date().toISOString()
        }])

      } catch (error) {
        console.error('Failed to load context:', error)
        setMessages([{
          role: 'assistant',
          content: '👋 Hi! I\'m your tax assistant.\n\nCalculate your tax first in the Tax Calculator, then I\'ll have full context to help you!\n\nYou can still ask general tax questions.',
          timestamp: new Date().toISOString()
        }])
      }
    } else {
      setMessages([{
        role: 'assistant',
        content: '👋 Hi! I\'m your tax assistant.\n\n💡 Quick tip: Calculate your tax first, then I can give you personalized advice!\n\nAsk me anything about Indian taxes!',
        timestamp: new Date().toISOString()
      }])
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
        content: `Sorry, I encountered an error. Please try again.`,
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

  const quickQuestions = [
    "How was my tax calculated?",
    "Can I save more tax?",
    "What's the difference between regimes?",
    "Explain my deductions"
  ]

  const askQuickQuestion = (question) => {
    setInput(question)
  }

  if (!isOpen) {
    return (
      <div className="chatbot-bubble-button" onClick={() => setIsOpen(true)}>
        <div className="bubble-icon">💬</div>
        {hasContext && <div className="context-indicator"></div>}
        <div className="bubble-text">Tax Assistant</div>
      </div>
    )
  }

  return (
    <div className={`chatbot-bubble-container ${isMinimized ? 'minimized' : ''}`}>
      {/* Header */}
      <div className="chatbot-bubble-header">
        <div className="header-left">
          <div className="bot-avatar">🤖</div>
          <div>
            <div className="bot-name">Tax Assistant</div>
            <div className="bot-status">
              {hasContext ? '✓ Context loaded' : 'Online'}
            </div>
          </div>
        </div>
        <div className="header-actions">
          <button
            className="header-btn"
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? "Expand" : "Minimize"}
          >
            {isMinimized ? '▲' : '▼'}
          </button>
          <button
            className="header-btn"
            onClick={() => setIsOpen(false)}
            title="Close"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Chat Body */}
      {!isMinimized && (
        <>
          <div className="chatbot-bubble-body" ref={chatContainerRef}>
            {/* Messages */}
            <div className="messages-container">
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`message ${msg.role === 'user' ? 'user-message' : 'bot-message'}`}
                >
                  <div className="message-content">
                    <Markdown>{msg.content}</Markdown>
                  </div>
                  <div className="message-time">
                    {new Date(msg.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message bot-message">
                  <div className="message-content typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Questions */}
            {messages.length <= 1 && (
              <div className="quick-questions">
                <div className="quick-questions-title">Quick questions:</div>
                {quickQuestions.map((q, i) => (
                  <button
                    key={i}
                    className="quick-question-btn"
                    onClick={() => askQuickQuestion(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Input */}
          <div className="chatbot-bubble-footer">
            <input
              type="text"
              className="chat-input"
              placeholder="Ask me anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            <button
              className="send-btn"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
            >
              {loading ? '⋯' : '➤'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}

export default ChatbotBubble
