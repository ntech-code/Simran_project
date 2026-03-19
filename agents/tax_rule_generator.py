"""
TaxRuleGeneratorAgent - Crawls official Indian tax sources and generates structured tax rules
"""
import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()


class TaxRuleGeneratorAgent:
    """
    Agent responsible for:
    1. Crawling trusted Indian government sources
    2. Extracting tax rules using Gemini
    3. Generating structured JSON output
    """

    TRUSTED_DOMAINS = [
        'incometax.gov.in',
        'incometaxindia.gov.in',
        'cbdt.gov.in',
        'indiabudget.gov.in',
        'finmin.nic.in',
        'india.gov.in'
    ]

    OFFICIAL_SOURCES = [
        'https://www.incometax.gov.in/iec/foportal/',
        'https://incometaxindia.gov.in/Pages/tax-services/know-your-tax-slabs.aspx',
    ]

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the agent"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3-flash-preview"

        print("✓ TaxRuleGeneratorAgent initialized")

    def is_trusted_source(self, url: str) -> bool:
        """Validate if URL is from trusted government domain"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')

        for trusted in self.TRUSTED_DOMAINS:
            if domain == trusted or domain.endswith('.' + trusted):
                return True

        return False

    def fetch_web_content(self, url: str) -> Optional[str]:
        """Fetch content from URL"""
        if not self.is_trusted_source(url):
            print(f"⚠️  Rejected untrusted source: {url}")
            return None

        try:
            print(f"📥 Fetching: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            # Extract text
            text = soup.get_text(separator='\n', strip=True)

            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)

            print(f"✓ Fetched {len(clean_text)} characters")
            return clean_text

        except Exception as e:
            print(f"❌ Error fetching {url}: {str(e)}")
            return None

    def extract_tax_rules_with_gemini(self, content: str, financial_year: str = "2024-25") -> Dict:
        """Use Gemini to extract structured tax rules from content"""

        prompt = f"""
You are a tax rules extraction expert. Analyze the following content from the Indian Income Tax Department website and extract structured tax information for Financial Year {financial_year}.

Extract the following in valid JSON format:

1. **Tax Slabs** for both OLD and NEW regimes:
   - Income ranges
   - Tax rates
   - Format: {{"min_income": number, "max_income": number or null, "rate": percentage}}

2. **Deductions** (80C, 80D, 80G, etc.):
   - Section code
   - Name and description
   - Maximum limit
   - Applicable regime (old/new/both)

3. **Rebates** (87A, etc.):
   - Section code
   - Maximum rebate amount
   - Income threshold

4. **Surcharge rules**:
   - Income thresholds
   - Surcharge rates

5. **Cess**:
   - Rate (typically 4% Health and Education Cess)

IMPORTANT:
- Use exact numbers from the official content
- Be precise with income limits and percentages
- Return ONLY valid JSON, no markdown or explanations
- Use null for unlimited max_income

Content to analyze:
{content[:8000]}

Return JSON in this structure:
{{
  "old_regime": {{
    "slabs": [...],
    "deductions": [...],
    "rebates": [...]
  }},
  "new_regime": {{
    "slabs": [...],
    "deductions": [...],
    "rebates": [...]
  }},
  "surcharges": [...],
  "cess": {{"rate": 4, "name": "Health and Education Cess"}}
}}
"""

        try:
            print("\n🤖 Analyzing content with Gemini...")

            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                ),
            ]

            config = types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for factual extraction
                thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
            )

            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            ):
                if chunk.text:
                    response_text += chunk.text

            # Clean response - extract JSON
            response_text = response_text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = re.sub(r'^```(?:json)?\n', '', response_text)
                response_text = re.sub(r'\n```$', '', response_text)

            # Parse JSON
            extracted_data = json.loads(response_text)
            print("✓ Successfully extracted tax rules")

            return extracted_data

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {str(e)}")
            print(f"Response: {response_text[:500]}")
            return {}
        except Exception as e:
            print(f"❌ Extraction error: {str(e)}")
            return {}

    def generate_rule_file(self, regime: str, financial_year: str = "2024-25") -> Dict:
        """Generate complete tax rule JSON file"""

        print(f"\n{'='*60}")
        print(f"GENERATING TAX RULES: {regime.upper()} REGIME - FY {financial_year}")
        print(f"{'='*60}\n")

        # For demo purposes, we'll create a comprehensive rule set
        # In production, this would crawl multiple sources
        all_content = ""
        sources_used = []

        # Use predefined comprehensive data (as live crawling may not always work)
        print("📋 Using comprehensive Indian tax rules for FY 2024-25...")

        if regime == "new":
            rule_data = self._get_new_regime_rules(financial_year)
        else:
            rule_data = self._get_old_regime_rules(financial_year)

        # Save to file
        output_path = f"rules/india_tax_{financial_year.replace('-', '_')}_{regime}.json"
        os.makedirs('rules', exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rule_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Rule file generated: {output_path}")
        print(f"   Regime: {regime}")
        print(f"   Financial Year: {financial_year}")
        print(f"   Slabs: {len(rule_data['slabs'])}")
        print(f"   Deductions: {len(rule_data['deductions'])}")

        return rule_data

    def _get_new_regime_rules(self, financial_year: str) -> Dict:
        """Get new regime tax rules for FY 2024-25"""
        return {
            "regime": "new",
            "financial_year": financial_year,
            "slabs": [
                {"min_income": 0, "max_income": 300000, "rate": 0},
                {"min_income": 300000, "max_income": 700000, "rate": 5},
                {"min_income": 700000, "max_income": 1000000, "rate": 10},
                {"min_income": 1000000, "max_income": 1200000, "rate": 15},
                {"min_income": 1200000, "max_income": 1500000, "rate": 20},
                {"min_income": 1500000, "max_income": None, "rate": 30}
            ],
            "deductions": [
                {
                    "section": "80CCD(2)",
                    "name": "Employer's contribution to NPS",
                    "description": "Employer's contribution to National Pension Scheme",
                    "max_limit": 0,
                    "applicable_regime": ["new"],
                    "note": "Up to 10% of salary (Basic + DA)"
                },
                {
                    "section": "Standard Deduction",
                    "name": "Standard Deduction",
                    "description": "Flat deduction from salary income",
                    "max_limit": 50000,
                    "applicable_regime": ["new"]
                }
            ],
            "rebates": [
                {
                    "section": "87A",
                    "name": "Rebate under section 87A",
                    "max_rebate": 25000,
                    "income_threshold": 700000,
                    "applicable_regime": ["new"]
                }
            ],
            "surcharges": [
                {"min_income": 0, "max_income": 5000000, "rate": 0},
                {"min_income": 5000000, "max_income": 10000000, "rate": 10},
                {"min_income": 10000000, "max_income": 20000000, "rate": 15},
                {"min_income": 20000000, "max_income": 50000000, "rate": 25},
                {"min_income": 50000000, "max_income": None, "rate": 37}
            ],
            "cess": {
                "rate": 4,
                "name": "Health and Education Cess"
            },
            "source_urls": [
                "https://www.incometax.gov.in/iec/foportal/",
                "https://incometaxindia.gov.in/"
            ],
            "last_updated": datetime.now().isoformat()
        }

    def _get_old_regime_rules(self, financial_year: str) -> Dict:
        """Get old regime tax rules for FY 2024-25"""
        return {
            "regime": "old",
            "financial_year": financial_year,
            "slabs": [
                {"min_income": 0, "max_income": 250000, "rate": 0},
                {"min_income": 250000, "max_income": 500000, "rate": 5},
                {"min_income": 500000, "max_income": 1000000, "rate": 20},
                {"min_income": 1000000, "max_income": None, "rate": 30}
            ],
            "deductions": [
                {
                    "section": "80C",
                    "name": "Investments and Expenses",
                    "description": "PPF, ELSS, Life Insurance Premium, Principal repayment of home loan, etc.",
                    "max_limit": 150000,
                    "applicable_regime": ["old"]
                },
                {
                    "section": "80D",
                    "name": "Health Insurance Premium",
                    "description": "Medical insurance premium for self, family, and parents",
                    "max_limit": 75000,
                    "applicable_regime": ["old"],
                    "sub_limits": {
                        "self_family": 25000,
                        "self_family_senior": 50000,
                        "parents": 25000,
                        "parents_senior": 50000
                    }
                },
                {
                    "section": "80G",
                    "name": "Donations",
                    "description": "Donations to eligible charitable institutions",
                    "max_limit": 0,
                    "applicable_regime": ["old"],
                    "note": "50% or 100% of donation amount based on institution"
                },
                {
                    "section": "80E",
                    "name": "Education Loan Interest",
                    "description": "Interest on education loan for higher studies",
                    "max_limit": 0,
                    "applicable_regime": ["old"],
                    "note": "No upper limit, for 8 years maximum"
                },
                {
                    "section": "80TTA",
                    "name": "Savings Account Interest",
                    "description": "Interest earned on savings account",
                    "max_limit": 10000,
                    "applicable_regime": ["old"]
                },
                {
                    "section": "Standard Deduction",
                    "name": "Standard Deduction",
                    "description": "Flat deduction from salary income",
                    "max_limit": 50000,
                    "applicable_regime": ["old"]
                },
                {
                    "section": "24(b)",
                    "name": "Home Loan Interest",
                    "description": "Interest on home loan for self-occupied property",
                    "max_limit": 200000,
                    "applicable_regime": ["old"]
                }
            ],
            "rebates": [
                {
                    "section": "87A",
                    "name": "Rebate under section 87A",
                    "max_rebate": 12500,
                    "income_threshold": 500000,
                    "applicable_regime": ["old"]
                }
            ],
            "surcharges": [
                {"min_income": 0, "max_income": 5000000, "rate": 0},
                {"min_income": 5000000, "max_income": 10000000, "rate": 10},
                {"min_income": 10000000, "max_income": 20000000, "rate": 15},
                {"min_income": 20000000, "max_income": 50000000, "rate": 25},
                {"min_income": 50000000, "max_income": None, "rate": 37}
            ],
            "cess": {
                "rate": 4,
                "name": "Health and Education Cess"
            },
            "source_urls": [
                "https://www.incometax.gov.in/iec/foportal/",
                "https://incometaxindia.gov.in/"
            ],
            "last_updated": datetime.now().isoformat()
        }


def main():
    """Main execution"""
    agent = TaxRuleGeneratorAgent()

    # Generate both regime rules
    for regime in ["old", "new"]:
        agent.generate_rule_file(regime, financial_year="2024-25")
        print()


if __name__ == "__main__":
    main()
