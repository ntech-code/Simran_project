# 🇮🇳 Indian Tax Analysis System

A comprehensive Multi-Agent AI-powered tax analysis system for Indian taxation (FY 2024-25) with fraud detection, regime comparison, transaction analysis, and interactive chatbot.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18.2.0-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

### 🔐 User Authentication
- **Google OAuth Integration** - Secure login with Google account
- **Development Mode** - Quick bypass for testing without OAuth setup
- **Session Management** - Automatic token validation and renewal

### 📊 Tax Calculation & Analysis
- **Accurate Tax Calculation** - Support for both Old and New tax regimes (FY 2024-25)
- **Deduction Validation** - Automatic validation of common deductions (80C, 80D, HRA, etc.)
- **Surcharge & Cess** - Accurate computation of surcharges and health & education cess
- **Section 87A Rebate** - Automatic rebate application for eligible taxpayers

### 🔍 AI-Powered Fraud Detection
- **Risk Scoring** - ML-based risk assessment (0-1 scale)
- **Pattern Analysis** - Anomaly detection in deduction claims
- **Compliance Checking** - Automated compliance validation
- **Red Flag Identification** - Highlights potential audit triggers

### ⚖️ Regime Comparison
- **Side-by-Side Analysis** - Compare Old vs New regime
- **Savings Calculation** - Shows which regime saves more money
- **Visual Charts** - Interactive Recharts visualization
- **Smart Recommendations** - AI suggests best regime for your situation

### 📈 Transaction Analyzer
- **CSV/Excel Upload** - Process bank statements and transaction files
- **AI-Powered Insights** - Gemini AI analyzes spending patterns
- **Tax Implications** - Identifies deductible expenses automatically
- **Category Analysis** - Smart categorization of transactions
- **Compliance Recommendations** - Suggests tax-saving opportunities

### 💬 Tax Assistant Chatbot
- **Context-Aware** - Knows your tax calculation details
- **Natural Language** - Ask questions in plain English
- **Personalized Advice** - Tailored recommendations based on your data
- **Markdown Support** - Rich formatted responses
- **24/7 Availability** - Instant answers to tax questions

### 📄 Reports & Documentation
- **Comprehensive Reports** - Detailed tax breakdown
- **Fraud Analysis Report** - Risk assessment summary
- **Downloadable Format** - Export reports as text files
- **Audit Trail** - Complete calculation history

### 📊 Interactive Dashboard
- **Visual Analytics** - Tax slabs, breakdowns, and deductions charts
- **Real-time Stats** - Income, tax, effective rate, risk level
- **Pie Charts** - Tax component distribution
- **Bar Charts** - Deduction visualization

---

## 🚀 Quick Start (1 Command!)

### Windows:
```bash
# Clone and setup automatically
git clone https://github.com/Pratham-Solanki911/TaxAnalyst.git
cd TaxAnalyst
setup.bat
```

### Linux/Mac:
```bash
# Clone and setup automatically
git clone https://github.com/Pratham-Solanki911/TaxAnalyst.git
cd TaxAnalyst
chmod +x setup.sh
./setup.sh
```

The setup script will:
- ✅ Check prerequisites (Python, Node.js, Git)
- ✅ Install all dependencies (backend & frontend)
- ✅ Create environment file templates
- ✅ Generate start scripts
- ✅ Configure the application

---

## 📋 Prerequisites

Before running the setup script, ensure you have:

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)

### Verify Installation:
```bash
python --version  # Should show Python 3.8+
node --version    # Should show v16+
git --version     # Should show git version
```

---

## ⚙️ Configuration

### 1. Get Gemini API Key (Required)

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key
4. Edit `.env` file:
   ```env
   GEMINI_API_KEY=your-actual-api-key-here
   ```

### 2. Configure Google OAuth (Optional)

**Option A: Use Development Mode** (Recommended for testing)
- No setup needed!
- Click "Continue as Developer" on login page
- Start using immediately

**Option B: Setup Google OAuth** (For production and real Google login)
1. Follow the complete guide: **[GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md)**
2. Takes 10 minutes
3. Get your Google Client ID
4. Add to `frontend/.env`:
   ```env
   VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   ```

**Quick Setup:**
- [Complete OAuth Setup Guide](GOOGLE_OAUTH_SETUP.md) - Step-by-step with screenshots
- [OAuth Troubleshooting](OAUTH_FIX.md) - Fix common errors

---

## 🎮 Running the Application

### Windows:

**Option 1: Start Both Servers**
```bash
start-all.bat
```

**Option 2: Start Individually**
```bash
# Terminal 1: Backend
start-backend.bat

# Terminal 2: Frontend
start-frontend.bat
```

### Linux/Mac:

**Option 1: Start Both Servers**
```bash
./start-all.sh
```

**Option 2: Start Individually**
```bash
# Terminal 1: Backend
./start-backend.sh

# Terminal 2: Frontend
./start-frontend.sh
```

### Access the Application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📚 User Guide

### 1. Login
- Go to http://localhost:3000/login
- Click "Continue as Developer (Testing Mode)"
- Or use "Sign in with Google" if configured

### 2. Calculate Tax
- Navigate to **Tax Calculator**
- Enter your gross income
- Select tax regime (Old/New)
- Add deductions (80C, 80D, etc.)
- Click "Calculate Tax"
- View detailed breakdown and fraud risk score

### 3. View Dashboard
- After calculating tax, return to **Dashboard**
- See interactive charts:
  - Tax overview statistics
  - Tax regime slabs
  - Tax breakdown pie chart
  - Deductions bar chart

### 4. Compare Regimes
- Go to **Compare Regimes**
- Enter income and deductions for both regimes
- Click "Compare"
- See side-by-side comparison and savings

### 5. Analyze Transactions
- Navigate to **📊 Transactions**
- Upload CSV or Excel file
- Wait for AI analysis (10-30 seconds)
- Review:
  - Transaction summary
  - AI insights
  - Tax implications
  - Deductible expenses

### 6. Chat with Tax Assistant
- Click the floating chatbot bubble (bottom-right)
- Ask questions about your tax calculation
- Get personalized recommendations
- Learn about tax-saving strategies

### 7. Generate Reports
- Go to **Reports**
- Select report type
- Click "Generate Report"
- Download or view in browser

---

## 🗂️ Project Structure

```
TaxAnalyst/
├── agents/                      # AI Agent modules
│   ├── tax_analyzer.py         # Tax calculation agent
│   ├── tax_rule_generator.py   # Rule generation agent
│   ├── tax_chatbot.py          # Conversational AI agent
│   └── transaction_analyzer.py # Transaction analysis agent
├── api/                         # FastAPI backend
│   └── main.py                 # API endpoints
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── context/            # Auth context
│   │   └── utils/              # Utility functions
│   └── package.json
├── .env                        # Backend environment variables
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── setup.bat                   # Windows setup script
├── setup.sh                    # Linux/Mac setup script
├── start-all.bat              # Windows start script
├── start-all.sh               # Linux/Mac start script
└── README.md                   # This file
```

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Google Gemini AI** - Advanced language models
- **Pandas** - Data analysis and processing
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### Frontend
- **React 18** - UI framework
- **React Router** - Navigation
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **React Markdown** - Markdown rendering
- **Google OAuth** - Authentication

### AI/ML
- **Gemini 2.0 Flash** - Conversational AI
- **Gemini 3 Flash Preview** - Transaction analysis
- **Pattern Recognition** - Fraud detection algorithms

---

## 📊 Sample Data Formats

### Transaction CSV Format:
```csv
Date,Description,Amount,Category,Type
2024-01-15,Salary Credit,100000,Salary,Credit
2024-01-16,Rent Payment,25000,Rent,Debit
2024-01-20,Medical Insurance,15000,Insurance,Debit
2024-02-01,PPF Deposit,12500,Investment,Debit
2024-02-05,Grocery Shopping,5000,Food,Debit
```

### Tax Input Example:
```json
{
  "gross_income": 1200000,
  "regime": "old",
  "deductions": {
    "80C": 150000,
    "80D": 25000,
    "Standard Deduction": 50000,
    "HRA": 100000
  }
}
```

---

## 🔒 Security & Privacy

- ✅ All tax calculations stored locally (localStorage)
- ✅ Uploaded files processed in-memory and deleted immediately
- ✅ No server-side data persistence
- ✅ Google OAuth for secure authentication
- ✅ HTTPS support ready for production
- ✅ Environment variables for sensitive data

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Try different port
uvicorn api.main:app --port 8001
```

### Frontend won't start
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Google OAuth not working
- Use "Continue as Developer" button instead
- See [OAUTH_FIX.md](OAUTH_FIX.md) for detailed fix

### Transaction upload fails
```bash
# Install missing dependencies
pip install python-multipart openpyxl pandas
```

---

## 📖 Documentation

- **[Setup Instructions](SETUP_INSTRUCTIONS.md)** - Detailed setup guide for all features
- **[Google OAuth Setup](GOOGLE_OAUTH_SETUP.md)** - Complete step-by-step OAuth configuration
- **[OAuth Troubleshooting](OAUTH_FIX.md)** - Fix common OAuth errors
- **[New Features Summary](NEW_FEATURES_SUMMARY.md)** - Documentation of recent additions
- **[Client Setup Guide](CLIENT_SETUP.md)** - Simple guide for end users
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when server running)

---

## 👨‍💻 Developer

**Pratham Solanki**
- GitHub: [@Pratham-Solanki911](https://github.com/Pratham-Solanki911)
- Repository: [TaxAnalyst](https://github.com/Pratham-Solanki911/TaxAnalyst)

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

**Made with ❤️ for Indian Taxpayers**

</div>
