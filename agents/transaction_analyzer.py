"""
Transaction Analyzer Agent
Analyzes uploaded transaction files (CSV/Excel) for tax implications and patterns
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from google import genai
import os


class TransactionAnalyzerAgent:
    """Agent for analyzing financial transactions"""

    def __init__(self):
        """Initialize the Transaction Analyzer Agent"""
        self.model_name = "gemini-2.0-flash-exp"

        # Configure Gemini API (New SDK Syntax)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables")
        
        # Initialize the Client instead of using configure()
        self.client = genai.Client(api_key=api_key)

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze uploaded transaction file

        Args:
            file_path: Path to the uploaded CSV or Excel file

        Returns:
            Dictionary with analysis results
        """
        try:
            # Read file based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format. Please upload CSV or Excel file.")

            # Basic data cleaning
            df = self._clean_dataframe(df)

            # Extract insights
            summary = self._extract_summary(df)

            # Get AI analysis
            ai_insights = self._get_ai_analysis(df, summary)

            # Combine results
            result = {
                **summary,
                "ai_analysis": ai_insights.get("quick_insights", ""),
                "detailed_analysis": ai_insights.get("detailed_analysis", ""),
                "tax_implications": ai_insights.get("tax_implications", ""),
                "status": "success"
            }

            return result

        except Exception as e:
            raise Exception(f"Failed to analyze file: {str(e)}")

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the dataframe"""
        # Convert column names to lowercase
        df.columns = df.columns.str.lower().str.strip()

        # Try to identify date column
        date_cols = [col for col in df.columns if 'date' in col]
        if date_cols:
            try:
                df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors='coerce')
            except:
                pass

        # Try to identify amount column
        amount_cols = [col for col in df.columns if any(term in col for term in ['amount', 'value', 'debit', 'credit'])]
        if amount_cols:
            for col in amount_cols:
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    pass

        return df

    def _extract_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract basic summary statistics from transactions"""
        summary = {
            "total_transactions": len(df),
            "columns_found": list(df.columns),
        }

        # Find date range
        date_cols = [col for col in df.columns if 'date' in col]
        if date_cols:
            try:
                dates = pd.to_datetime(df[date_cols[0]], errors='coerce').dropna()
                if len(dates) > 0:
                    summary["date_range"] = f"{dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}"
                else:
                    summary["date_range"] = "Unknown"
            except:
                summary["date_range"] = "Unknown"
        else:
            summary["date_range"] = "No date column found"

        # Find total amount
        amount_cols = [col for col in df.columns if any(term in col for term in ['amount', 'value'])]
        if amount_cols:
            try:
                total = df[amount_cols[0]].sum()
                summary["total_amount"] = abs(float(total)) if not pd.isna(total) else 0
            except:
                summary["total_amount"] = 0
        else:
            summary["total_amount"] = 0

        # Find categories
        category_cols = [col for col in df.columns if any(term in col for term in ['category', 'type', 'description'])]
        if category_cols:
            try:
                categories = df[category_cols[0]].dropna().unique()
                summary["categories_count"] = len(categories)
                summary["categories"] = list(categories)[:10]  # First 10 categories
            except:
                summary["categories_count"] = 0
        else:
            summary["categories_count"] = 0

        return summary

    def _get_ai_analysis(self, df: pd.DataFrame, summary: Dict[str, Any]) -> Dict[str, str]:
        """Use Gemini AI to analyze transaction patterns"""
        try:
            # Prepare data sample for AI
            data_sample = df.head(20).to_string()

            prompt = f"""You are a financial analyst specializing in Indian taxation. Analyze these transaction data:

TRANSACTION SUMMARY:
- Total Transactions: {summary['total_transactions']}
- Date Range: {summary.get('date_range', 'Unknown')}
- Total Amount: ₹{summary.get('total_amount', 0):,.2f}
- Columns: {', '.join(summary['columns_found'])}

SAMPLE DATA (first 20 rows):
{data_sample}

Please provide:

1. **Quick Insights** (3-5 bullet points):
   - Key patterns you notice
   - Spending trends
   - Any anomalies or red flags

2. **Detailed Analysis** (comprehensive breakdown):
   - Transaction patterns analysis
   - Category-wise breakdown if available
   - Time-based trends
   - Notable observations

3. **Tax Implications** (Indian tax context):
   - Which expenses may be tax-deductible under Indian Income Tax Act
   - Potential deductions (80C, 80D, HRA, etc.)
   - Income sources that need to be reported
   - Compliance recommendations
   - Any transactions that might trigger tax scrutiny

Format your response in markdown with clear sections.
"""

            # Get AI response (New SDK Syntax)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            full_response = response.text

            # Try to split response into sections
            sections = self._parse_ai_response(full_response)

            return sections

        except Exception as e:
            print(f"AI analysis error: {e}")
            return {
                "quick_insights": "Unable to generate AI insights at this time.",
                "detailed_analysis": f"Analysis could not be completed. Found {summary['total_transactions']} transactions.",
                "tax_implications": "Please consult a tax professional for personalized advice."
            }

    def _parse_ai_response(self, response: str) -> Dict[str, str]:
        """Parse AI response into sections"""
        sections = {
            "quick_insights": "",
            "detailed_analysis": "",
            "tax_implications": ""
        }

        # Try to identify sections
        lines = response.split('\n')
        current_section = "quick_insights"

        for line in lines:
            lower_line = line.lower()

            if "quick insights" in lower_line or "key insights" in lower_line:
                current_section = "quick_insights"
                continue
            elif "detailed analysis" in lower_line or "comprehensive" in lower_line:
                current_section = "detailed_analysis"
                continue
            elif "tax implications" in lower_line or "tax" in lower_line and "implications" in lower_line:
                current_section = "tax_implications"
                continue

            sections[current_section] += line + "\n"

        # If parsing didn't work well, just use the full response for quick insights
        if not sections["quick_insights"].strip():
            sections["quick_insights"] = response

        return sections

    def get_spending_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get additional spending insights"""
        insights = {}

        try:
            # Category-wise spending
            category_cols = [col for col in df.columns if 'category' in col.lower()]
            amount_cols = [col for col in df.columns if 'amount' in col.lower()]

            if category_cols and amount_cols:
                category_spending = df.groupby(category_cols[0])[amount_cols[0]].sum().sort_values(ascending=False)
                insights["top_categories"] = category_spending.head(5).to_dict()

            # Monthly spending trend
            date_cols = [col for col in df.columns if 'date' in col.lower()]
            if date_cols and amount_cols:
                df['month'] = pd.to_datetime(df[date_cols[0]], errors='coerce').dt.to_period('M')
                monthly_spending = df.groupby('month')[amount_cols[0]].sum()
                insights["monthly_trend"] = {str(k): float(v) for k, v in monthly_spending.to_dict().items()}

        except Exception as e:
            print(f"Error extracting insights: {e}")

        return insights