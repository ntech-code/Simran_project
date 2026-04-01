import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class DocumentTaxParserAgent:
    """
    Dedicated LLM Agent to simultaneously structure 12 months of Salary Slips 
    alongside Bank Statements into a unified Indian Tax Calculation JSON profile.
    """

    def __init__(self, api_key: str = None):
        from agents.genai_client import get_genai_client, get_model_name
        self.client = get_genai_client()
        if not self.client:
            raise ValueError("No AI credentials found (Vertex AI or Gemini API key)")
        self.model = get_model_name()
        print("✓ DocumentTaxParserAgent initialized")

    def parse_documents(self, multi_document_text: str) -> Dict[str, Any]:
        """
        Takes raw string concatenations of all uploaded PDFs/CSVs and converts 
        them into a mathematically checked FY25-26 Tax JSON form format.
        Uses a map-reduce chunking strategy to avoid Vertex AI 128k token limits.
        """
         
        from agents.genai_client import safe_generate
        import json
        
        # With standard Gemini API, we have a 1,000,000+ token context window.
        # We can pass the ENTIRE 125-page, 300,000 character document in exactly ONE single API call!
        # This completely avoids all the chunking architecture needed for Vertex AI.
        
        extract_instruction = """
You are an elite Indian Chartered Accountant and Forensic Financial Auditor.
You are reviewing a taxpayer's Bank Statements (and potentially Salary Slips) for Financial Year 2025-26.

CRITICAL INSTRUCTION ON INCOME (gross_income): 
You MUST accurately detect the user's Salary. Look for incoming NEFT/IMPS/RTGS credits with employer names (e.g. 'VADINI INFOCENTER PVT LTD' or 'SALARY'). If you identify regular monthly deposits from a corporate entity, SUM THEM UP as the annual `gross_income`! NEVER output 0 if there are active salaries flowing in. Include ALL taxable incoming cashflows into this `gross_income` value.

CRITICAL INSTRUCTION ON DEDUCTIONS:
Analyze the transactions for tax deduction proofs. 
Look for Mutual Funds, LIC, EPF, ELSS, PPF (80C limited to 150000).
Look for Medical/Health Insurance (80D). 
Look for Charity (80G), Education Loan (80E), and NPS (80CCD).
Return the exact totals for each category you find.

CRITICAL INSTRUCTION ON FRAUD DETECTION:
Compare the calculated `gross_income` against total bank expenses and deposits!
If total transactions (e.g., millions of rupees) vastly exceed the stated salary (e.g., 5-6 lakhs), you MUST FLAG IT AS HIGH RISK.
Explicitly name any individuals or high-frequency payees (like 'Arya', 'Sakshi', etc.) that the user is exchanging huge volumes of money with in the `fraud_explanation` and `follow_up_questions`. Be highly specific about the exact numbers and names.

RETURN ONLY VALID JSON RESPONDING TO THIS EXACT SCHEMA:
{
    "gross_income": float (The true annualized income, extracted from salary deposits or slips),
    "deductions": {
        "80C": float (Max 150000 limit),
        "80D": float,
        "80TTA": float,
        "80G": float,
        "80E": float,
        "80CCD": float,
        "80CCD2": float,
        "Standard Deduction": 75000,
        "otherDeductions": float
    },
    "total_expenses": float,
    "total_deposits": float,
    "fraud_risk": "LOW" | "MEDIUM" | "HIGH",
    "fraud_explanation": "Extremely detailed 2-3 sentence explanation naming exact parties like Arya or corporate entities causing discrepancies.",
    "follow_up_questions": ["Ask tough, specific questions naming exact high-volume counterparties found in the statement"]
}
Never output markdown. Ensure numbers are floats without commas.
"""
        
        print("Sending full document to Standard Gemini 2.5 Flash...", flush=True)
        config = types.GenerateContentConfig(
            temperature=0.0,
            system_instruction=extract_instruction,
            response_mime_type="application/json"
        )
        
        try:
            resp = safe_generate(self.client, self.model, multi_document_text, config, max_retries=3)
            data = json.loads(resp.text.strip())
            return data
            
        except Exception as e:
            err_msg = str(e)
            print(f"Document Parser Agent Error: {err_msg}")
            return {
                "error": True,
                "message": f"AI Parsing failed: {err_msg}"
            }
