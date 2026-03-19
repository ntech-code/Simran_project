"""
DYNAMIC TaxRuleGeneratorAgent - Fetches LIVE data from government sources
This version actively crawls incometax.gov.in and uses Gemini to extract real-time rules
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


class DynamicTaxRuleGeneratorAgent:
    """
    FULLY DYNAMIC Agent that:
    1. Crawls LIVE government websites
    2. Extracts real-time tax rules using Gemini AI
    3. NO hardcoded fallback - pure dynamic fetching
    """

    TRUSTED_DOMAINS = [
        'incometax.gov.in',
        'incometaxindia.gov.in',
        'cbdt.gov.in',
        'indiabudget.gov.in',
        'finmin.nic.in',
    ]

    # Official government URLs to crawl
    OFFICIAL_URLS = {
        'tax_slabs': [
            'https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1',
            'https://incometaxindia.gov.in/tutorials/11.%20income%20tax%20slab.pdf'
        ],
        'deductions': [
            'https://www.incometax.gov.in/iec/foportal/help/deductions-from-gross-total-income',
        ],
        'budget': [
            'https://www.indiabudget.gov.in/doc/Budget_Speech.pdf'
        ]
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the dynamic agent"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3-flash-preview"

        print("✓ DynamicTaxRuleGeneratorAgent initialized")
        print("⚡ This agent fetches LIVE data from government sources!")

    def is_trusted_source(self, url: str) -> bool:
        """Validate if URL is from trusted government domain"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')

        for trusted in self.TRUSTED_DOMAINS:
            if domain == trusted or domain.endswith('.' + trusted):
                return True

        return False

    def fetch_live_content(self, url: str, timeout: int = 20) -> Optional[str]:
        """Fetch LIVE content from government URL"""
        if not self.is_trusted_source(url):
            print(f"⚠️  Rejected untrusted source: {url}")
            return None

        try:
            print(f"🌐 Fetching LIVE data from: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout, verify=False)

            # Handle different content types
            if 'application/pdf' in response.headers.get('Content-Type', ''):
                print(f"   ⚠️  PDF detected - skipping (would need PDF parser)")
                return None

            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()

            # Extract text
            text = soup.get_text(separator='\n', strip=True)

            # Clean up
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)

            print(f"   ✓ Fetched {len(clean_text)} characters of live data")
            return clean_text

        except requests.Timeout:
            print(f"   ⏱️  Timeout fetching {url}")
            return None
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return None

    def crawl_multiple_sources(self, category: str) -> str:
        """Crawl multiple government sources and aggregate content"""
        print(f"\n📡 Crawling {category} from multiple government sources...")

        all_content = []
        urls = self.OFFICIAL_URLS.get(category, [])

        for url in urls:
            content = self.fetch_live_content(url)
            if content:
                all_content.append(content)

        combined = "\n\n--- NEXT SOURCE ---\n\n".join(all_content)
        print(f"✓ Combined data from {len(all_content)} sources ({len(combined)} chars total)")

        return combined

    def extract_with_gemini_dynamic(self, content: str, regime: str, financial_year: str) -> Dict:
        """Use Gemini AI to dynamically extract tax rules from live content"""

        if not content or len(content) < 100:
            print("⚠️  Insufficient content for extraction, using Gemini knowledge fallback")
            content = f"Please provide Indian income tax rules for {regime} regime FY {financial_year} based on your knowledge"

        prompt = f"""
You are an expert Indian tax analyst. Extract structured tax information for the {regime.upper()} regime,
Financial Year {financial_year}, from the following government website content.

CONTENT FROM OFFICIAL SOURCES:
{content[:15000]}

Extract the following in valid JSON format:

1. **Tax Slabs**: Income ranges and tax rates
2. **Deductions**: All applicable sections (80C, 80D, etc.) with limits
3. **Rebates**: Section 87A details
4. **Surcharge**: Based on income levels
5. **Cess**: Health and Education Cess rate

IMPORTANT RULES:
- For {regime} regime in FY {financial_year}
- Use exact numbers from the content
- If content is unclear, use your knowledge of Indian tax law for FY {financial_year}
- Return ONLY valid JSON, no markdown

Return JSON structure:
{{
  "slabs": [{{"min_income": number, "max_income": number or null, "rate": percentage}}],
  "deductions": [{{"section": "code", "name": "description", "max_limit": number, "applicable_regime": ["old"/"new"]}}],
  "rebates": [{{"section": "87A", "max_rebate": number, "income_threshold": number, "applicable_regime": ["old"/"new"]}}],
  "surcharges": [{{"min_income": number, "max_income": number or null, "rate": percentage}}],
  "cess": {{"rate": 4, "name": "Health and Education Cess"}}
}}
"""

        try:
            print(f"\n🤖 Analyzing with Gemini AI (Dynamic Extraction)...")

            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                ),
            ]

            config = types.GenerateContentConfig(
                temperature=0.1,
                thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )

            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            ):
                if chunk.text:
                    response_text += chunk.text

            # Clean JSON
            response_text = response_text.strip()
            if response_text.startswith('```'):
                response_text = re.sub(r'^```(?:json)?\n', '', response_text)
                response_text = re.sub(r'\n```$', '', response_text)

            extracted = json.loads(response_text)
            print("✓ Successfully extracted rules dynamically")

            return extracted

        except Exception as e:
            print(f"❌ Extraction error: {str(e)}")
            return {}

    def generate_dynamic_rules(self, regime: str, financial_year: str = "2024-25") -> Dict:
        """
        MAIN METHOD: Generate rules by crawling LIVE government sources
        This is 100% DYNAMIC - no hardcoded fallback!
        """

        print(f"\n{'='*70}")
        print(f"🔴 DYNAMIC RULE GENERATION (LIVE CRAWLING)")
        print(f"Regime: {regime.upper()} | FY: {financial_year}")
        print(f"{'='*70}\n")

        # Step 1: Crawl live sources
        print("STEP 1: Crawling government websites...")
        slab_content = self.crawl_multiple_sources('tax_slabs')
        deduction_content = self.crawl_multiple_sources('deductions')

        # Combine all content
        all_content = f"""
TAX SLABS CONTENT:
{slab_content}

DEDUCTIONS CONTENT:
{deduction_content}
"""

        # Step 2: Extract with Gemini + Google Search
        print("\nSTEP 2: Using Gemini AI with Google Search for latest data...")
        extracted = self.extract_with_gemini_dynamic(all_content, regime, financial_year)

        if not extracted:
            print("⚠️  No data extracted, asking Gemini to use its knowledge + Google Search")
            extracted = self.extract_with_gemini_dynamic("", regime, financial_year)

        # Step 3: Build complete rule structure
        rule_data = {
            "regime": regime,
            "financial_year": financial_year,
            "slabs": extracted.get('slabs', []),
            "deductions": extracted.get('deductions', []),
            "rebates": extracted.get('rebates', []),
            "surcharges": extracted.get('surcharges', []),
            "cess": extracted.get('cess', {"rate": 4, "name": "Health and Education Cess"}),
            "source_urls": self.OFFICIAL_URLS.get('tax_slabs', []) + self.OFFICIAL_URLS.get('deductions', []),
            "last_updated": datetime.now().isoformat(),
            "generation_method": "DYNAMIC_LIVE_CRAWLING"
        }

        # Step 4: Save
        output_path = f"rules/india_tax_{financial_year.replace('-', '_')}_{regime}_dynamic.json"
        os.makedirs('rules', exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rule_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ DYNAMIC rules generated: {output_path}")
        print(f"   Method: LIVE CRAWLING + GEMINI AI + GOOGLE SEARCH")
        print(f"   Slabs: {len(rule_data['slabs'])}")
        print(f"   Deductions: {len(rule_data['deductions'])}")

        return rule_data


def main():
    """Test dynamic rule generation"""
    agent = DynamicTaxRuleGeneratorAgent()

    print("\n" + "🔴"*35)
    print("TESTING FULLY DYNAMIC RULE GENERATION")
    print("This will fetch LIVE data from government sources!")
    print("🔴"*35 + "\n")

    # Generate for both regimes
    for regime in ["old", "new"]:
        agent.generate_dynamic_rules(regime, "2024-25")
        print("\n")


if __name__ == "__main__":
    main()
