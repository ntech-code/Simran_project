"""
FastAPI Backend for Multi-Agent Tax Analysis System
"""
import sys
import os
from typing import Dict, Optional, List
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from agents.tax_analyzer import TaxAnalyzerAgent
from agents.tax_rule_generator import TaxRuleGeneratorAgent
from agents.tax_chatbot import TaxChatbotAgent
from agents.transaction_analyzer import TransactionAnalyzerAgent
import shutil
import tempfile

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize FastAPI app
app = FastAPI(
    title="Indian Tax Analysis API",
    description="Multi-Agent Tax Analysis System with Fraud Detection",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
analyzer_agent = TaxAnalyzerAgent()
rule_generator_agent = TaxRuleGeneratorAgent()
chatbot_agent = TaxChatbotAgent()
transaction_analyzer_agent = TransactionAnalyzerAgent()


# Pydantic models
class UserFinancialData(BaseModel):
    """User financial input model"""
    gross_income: float = Field(..., gt=0, description="Annual gross income")
    regime: str = Field(..., pattern="^(old|new)$", description="Tax regime: old or new")
    financial_year: str = Field(default="2024-25", description="Financial year")
    deductions: Dict[str, float] = Field(default={}, description="Deductions claimed by section")
    previous_year_income: Optional[float] = Field(default=None, description="Previous year income for fraud detection")

    class Config:
        json_schema_extra = {
            "example": {
                "gross_income": 1200000,
                "regime": "old",
                "financial_year": "2024-25",
                "deductions": {
                    "80C": 150000,
                    "80D": 25000,
                    "Standard Deduction": 50000
                },
                "previous_year_income": 1000000
            }
        }


class CompareRegimesData(BaseModel):
    """Input for regime comparison"""
    gross_income: float = Field(..., gt=0)
    financial_year: str = Field(default="2024-25")
    deductions_old: Dict[str, float] = Field(default={}, description="Deductions for old regime")
    deductions_new: Dict[str, float] = Field(default={}, description="Deductions for new regime")
    previous_year_income: Optional[float] = Field(default=None)


class SimulationData(BaseModel):
    """Simulation scenario input"""
    base_income: float = Field(..., gt=0)
    income_increments: list[float] = Field(..., description="Income levels to simulate")
    regime: str = Field(..., pattern="^(old|new)$")
    deductions: Dict[str, float] = Field(default={})


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Indian Tax Analysis API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/rules/current")
async def get_current_rules(regime: str = "old", financial_year: str = "2024-25"):
    """
    Get current tax rules for specified regime and financial year

    - **regime**: old or new
    - **financial_year**: Format YYYY-YY (e.g., 2024-25)
    """
    if regime not in ["old", "new"]:
        raise HTTPException(status_code=400, detail="regime must be 'old' or 'new'")

    try:
        import json
        fy_formatted = financial_year.replace('-', '_')
        rule_path = f"rules/india_tax_{fy_formatted}_{regime}.json"

        with open(rule_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)

        return {
            "status": "success",
            "regime": regime,
            "financial_year": financial_year,
            "rules": rules
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Rules not found for {regime} regime, FY {financial_year}. Generate rules first."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-tax")
async def analyze_tax(user_data: UserFinancialData):
    """
    Analyze tax for user financial data

    Returns:
    - Tax calculation breakdown
    - Fraud detection analysis
    - Compliance recommendations
    """
    try:
        # Load appropriate rules
        analyzer_agent.load_rules(user_data.regime, user_data.financial_year)

        # Prepare data for agent
        agent_input = {
            "gross_income": user_data.gross_income,
            "deductions": user_data.deductions,
            "previous_year_income": user_data.previous_year_income or user_data.gross_income
        }

        # Calculate tax
        tax_result = analyzer_agent.calculate_tax(agent_input)

        # Detect fraud
        fraud_result = analyzer_agent.detect_fraud(agent_input, tax_result)

        return {
            "status": "success",
            "regime": user_data.regime,
            "financial_year": user_data.financial_year,
            "tax_calculation": tax_result,
            "fraud_analysis": fraud_result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/compare-regimes")
async def compare_regimes(data: CompareRegimesData):
    """
    Compare tax in old vs new regime

    Returns which regime is better and potential savings
    """
    try:
        # Prepare data for old regime
        old_data = {
            "gross_income": data.gross_income,
            "deductions": data.deductions_old,
            "previous_year_income": data.previous_year_income or data.gross_income
        }

        # Prepare data for new regime
        new_data = {
            "gross_income": data.gross_income,
            "deductions": data.deductions_new,
            "previous_year_income": data.previous_year_income or data.gross_income
        }

        # Compare using agent
        comparison = analyzer_agent.compare_regimes(old_data)

        return {
            "status": "success",
            "comparison": comparison,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@app.post("/generate-report")
async def generate_report(user_data: UserFinancialData):
    """
    Generate comprehensive tax report

    Returns detailed text report with all analysis
    """
    try:
        analyzer_agent.load_rules(user_data.regime, user_data.financial_year)

        agent_input = {
            "gross_income": user_data.gross_income,
            "deductions": user_data.deductions,
            "previous_year_income": user_data.previous_year_income or user_data.gross_income
        }

        report = analyzer_agent.generate_report(agent_input, user_data.regime)

        return {
            "status": "success",
            "report": report,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.post("/simulate-scenario")
async def simulate_scenario(sim_data: SimulationData):
    """
    Simulate tax for multiple income scenarios

    Useful for tax planning and optimization
    """
    try:
        analyzer_agent.load_rules(sim_data.regime)

        results = []

        for income in sim_data.income_increments:
            agent_input = {
                "gross_income": income,
                "deductions": sim_data.deductions
            }

            tax_result = analyzer_agent.calculate_tax(agent_input)

            results.append({
                "income": income,
                "tax": tax_result.get('total_tax', 0),
                "effective_rate": tax_result.get('effective_tax_rate', 0)
            })

        return {
            "status": "success",
            "regime": sim_data.regime,
            "simulations": results,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@app.post("/generate-rules")
async def generate_rules(regime: str = "both", financial_year: str = "2024-25"):
    """
    Trigger tax rule generation

    This endpoint triggers the TaxRuleGeneratorAgent to fetch and generate rules
    """
    try:
        if regime == "both":
            regimes = ["old", "new"]
        elif regime in ["old", "new"]:
            regimes = [regime]
        else:
            raise HTTPException(status_code=400, detail="regime must be 'old', 'new', or 'both'")

        generated = []
        for reg in regimes:
            rule_data = rule_generator_agent.generate_rule_file(reg, financial_year)
            generated.append({
                "regime": reg,
                "slabs_count": len(rule_data['slabs']),
                "deductions_count": len(rule_data['deductions'])
            })

        return {
            "status": "success",
            "message": "Tax rules generated successfully",
            "generated": generated,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rule generation failed: {str(e)}")


# Chatbot Models
class ChatMessage(BaseModel):
    """Chat message model"""
    message: str = Field(..., min_length=1, description="User's question")


class SetChatContext(BaseModel):
    """Set chatbot context with user's tax data"""
    gross_income: float
    regime: str
    deductions: Dict[str, float] = {}
    taxable_income: Optional[float] = None
    total_tax: Optional[float] = None
    effective_tax_rate: Optional[float] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    compliance_score: Optional[float] = None
    flags: Optional[List[str]] = []


# Chatbot Endpoints

@app.post("/chatbot/set-context")
async def set_chatbot_context(context_data: SetChatContext):
    """
    Set user's tax context for chatbot
    Call this after tax calculation to make chatbot aware of user's details
    """
    try:
        chatbot_agent.set_user_context(context_data.dict())

        return {
            "status": "success",
            "message": "Chatbot context updated. I'm now aware of your tax details!",
            "context_summary": {
                "income": context_data.gross_income,
                "regime": context_data.regime,
                "tax": context_data.total_tax,
                "risk_level": context_data.risk_level
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set context: {str(e)}")


@app.post("/chatbot/chat")
async def chat_with_bot(chat_msg: ChatMessage):
    """
    Chat with tax expert bot
    Bot is aware of user's tax details if context was set
    """
    try:
        response = chatbot_agent.chat(chat_msg.message)

        return {
            "status": "success",
            "user_message": chat_msg.message,
            "bot_response": response,
            "timestamp": datetime.now().isoformat(),
            "has_context": bool(chatbot_agent.user_context)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.get("/chatbot/suggestions")
async def get_tax_suggestions():
    """
    Get personalized tax-saving suggestions based on user's context
    """
    try:
        suggestions = chatbot_agent.get_personalized_suggestions()

        return {
            "status": "success",
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@app.post("/chatbot/clear")
async def clear_chatbot():
    """Clear chatbot context and conversation history"""
    try:
        chatbot_agent.clear_context()

        return {
            "status": "success",
            "message": "Chatbot context and history cleared"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear: {str(e)}")


@app.post("/analyze-transactions")
async def analyze_transactions(file: UploadFile = File(...)):
    """
    Analyze uploaded transaction file (CSV or Excel)

    Args:
        file: Uploaded CSV or Excel file

    Returns:
        Analysis results with AI insights and tax implications
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in ['csv', 'xlsx', 'xls']:
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Please upload CSV or Excel file (.csv, .xlsx, .xls)"
            )

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as tmp_file:
            # Copy uploaded file to temporary file
            shutil.copyfileobj(file.file, tmp_file)
            tmp_file_path = tmp_file.name

        try:
            # Analyze the file using the agent
            result = transaction_analyzer_agent.analyze_file(tmp_file_path)

            return result

        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except:
                pass

    except HTTPException:
        raise
    except Exception as e:
        print(f"Transaction analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze transactions: {str(e)}")


# Run with: uvicorn api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🚀 Starting Indian Tax Analysis API Server")
    print("="*70 + "\n")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📋 Alternative docs: http://localhost:8000/redoc")
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
