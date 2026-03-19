"""
TaxAnalyzerAgent - Analyzes user financial data, calculates tax, and detects fraud
"""
import os
import sys
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()


class TaxAnalyzerAgent:
    """
    Agent responsible for:
    1. Loading tax rules
    2. Calculating tax for user inputs
    3. Fraud detection and risk scoring
    4. Generating detailed reports
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the analyzer agent"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-3-flash-preview"

        self.rules = {}
        print("✓ TaxAnalyzerAgent initialized")

    def load_rules(self, regime: str, financial_year: str = "2024-25") -> bool:
        """Load tax rules from JSON file"""
        try:
            fy_formatted = financial_year.replace('-', '_')
            rule_path = f"rules/india_tax_{fy_formatted}_{regime}.json"

            with open(rule_path, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)

            print(f"✓ Loaded {regime} regime rules for FY {financial_year}")
            return True

        except FileNotFoundError:
            print(f"❌ Rule file not found: {rule_path}")
            return False
        except Exception as e:
            print(f"❌ Error loading rules: {str(e)}")
            return False

    def calculate_tax(self, user_data: Dict) -> Dict:
        """Calculate tax based on user financial data"""

        if not self.rules:
            return {"error": "Tax rules not loaded"}

        try:
            gross_income = user_data.get('gross_income', 0)
            deductions_claimed = user_data.get('deductions', {})

            # Calculate total deductions
            total_deductions = self._calculate_total_deductions(deductions_claimed)

            # Calculate taxable income
            taxable_income = max(0, gross_income - total_deductions)

            # Calculate tax from slabs
            tax_from_slabs = self._calculate_slab_tax(taxable_income)

            # Apply rebate
            rebate = self._calculate_rebate(taxable_income, tax_from_slabs)

            # Calculate surcharge
            surcharge = self._calculate_surcharge(taxable_income, tax_from_slabs - rebate)

            # Calculate cess
            cess_rate = self.rules['cess']['rate'] / 100
            cess = (tax_from_slabs - rebate + surcharge) * cess_rate

            # Total tax
            total_tax = tax_from_slabs - rebate + surcharge + cess

            result = {
                "gross_income": gross_income,
                "total_deductions": total_deductions,
                "taxable_income": taxable_income,
                "tax_breakdown": {
                    "tax_from_slabs": round(tax_from_slabs, 2),
                    "rebate": round(rebate, 2),
                    "surcharge": round(surcharge, 2),
                    "cess": round(cess, 2)
                },
                "total_tax": round(total_tax, 2),
                "effective_tax_rate": round((total_tax / gross_income * 100), 2) if gross_income > 0 else 0,
                "regime": self.rules['regime'],
                "financial_year": self.rules['financial_year']
            }

            return result

        except Exception as e:
            return {"error": f"Calculation error: {str(e)}"}

    def _calculate_total_deductions(self, deductions_claimed: Dict) -> float:
        """Calculate total valid deductions"""
        total = 0

        for deduction in self.rules['deductions']:
            section = deduction['section']
            max_limit = deduction['max_limit']
            claimed_amount = deductions_claimed.get(section, 0)

            if max_limit > 0:
                allowed = min(claimed_amount, max_limit)
            else:
                # No limit (e.g., 80G, 80E)
                allowed = claimed_amount

            total += allowed

        return total

    def _calculate_slab_tax(self, taxable_income: float) -> float:
        """Calculate tax based on slabs"""
        tax = 0

        for slab in self.rules['slabs']:
            min_inc = slab['min_income']
            max_inc = slab['max_income']
            rate = slab['rate'] / 100

            if max_inc is None:
                # Highest slab
                if taxable_income > min_inc:
                    tax += (taxable_income - min_inc) * rate
            else:
                if taxable_income > min_inc:
                    taxable_in_slab = min(taxable_income, max_inc) - min_inc
                    tax += taxable_in_slab * rate

        return tax

    def _calculate_rebate(self, taxable_income: float, tax_amount: float) -> float:
        """Calculate applicable rebate"""
        for rebate in self.rules.get('rebates', []):
            if taxable_income <= rebate['income_threshold']:
                return min(tax_amount, rebate['max_rebate'])

        return 0

    def _calculate_surcharge(self, taxable_income: float, tax_before_surcharge: float) -> float:
        """Calculate surcharge"""
        for surcharge in self.rules['surcharges']:
            min_inc = surcharge['min_income']
            max_inc = surcharge['max_income']
            rate = surcharge['rate'] / 100

            if max_inc is None:
                if taxable_income > min_inc:
                    return tax_before_surcharge * rate
            else:
                if min_inc <= taxable_income <= max_inc:
                    return tax_before_surcharge * rate

        return 0

    def detect_fraud(self, user_data: Dict, tax_result: Dict) -> Dict:
        """Detect potential fraud patterns and calculate risk score"""

        flags = []
        risk_score = 0.0

        gross_income = user_data.get('gross_income', 0)
        deductions_claimed = user_data.get('deductions', {})

        if gross_income == 0:
            return {
                "risk_score": 0,
                "risk_level": "N/A",
                "flags": [],
                "recommendations": []
            }

        # Calculate total deductions claimed
        total_deductions = sum(deductions_claimed.values())
        deduction_ratio = total_deductions / gross_income if gross_income > 0 else 0

        # FRAUD CHECK 1: Excessive deduction ratio
        if deduction_ratio > 0.5:
            flags.append("High deduction-to-income ratio (>50%)")
            risk_score += 0.3

        if deduction_ratio > 0.7:
            flags.append("Very high deduction-to-income ratio (>70%)")
            risk_score += 0.2

        # FRAUD CHECK 2: Repeated max-limit deductions
        max_limit_count = 0
        for deduction in self.rules['deductions']:
            section = deduction['section']
            max_limit = deduction['max_limit']

            if max_limit > 0:
                claimed = deductions_claimed.get(section, 0)
                if claimed >= max_limit * 0.95:  # Within 5% of max
                    max_limit_count += 1

        if max_limit_count >= 3:
            flags.append(f"Multiple deductions at maximum limit ({max_limit_count} sections)")
            risk_score += 0.25

        # FRAUD CHECK 3: Unusual 80C usage (old regime)
        if self.rules['regime'] == 'old':
            section_80c = deductions_claimed.get('80C', 0)
            if section_80c >= 150000 and gross_income < 500000:
                flags.append("80C deduction unusually high for income level")
                risk_score += 0.15

        # FRAUD CHECK 4: Suspicious income patterns
        previous_income = user_data.get('previous_year_income', gross_income)
        if previous_income > 0:
            income_change = abs(gross_income - previous_income) / previous_income
            if income_change > 0.5:
                flags.append(f"Significant income change ({income_change*100:.1f}%)")
                risk_score += 0.1

        # FRAUD CHECK 5: Section misuse patterns
        if self.rules['regime'] == 'new':
            # New regime shouldn't have most deductions
            invalid_sections = ['80C', '80D', '80G', '24(b)']
            for section in invalid_sections:
                if deductions_claimed.get(section, 0) > 0:
                    flags.append(f"Invalid deduction {section} claimed in new regime")
                    risk_score += 0.2

        # Cap risk score at 1.0
        risk_score = min(risk_score, 1.0)

        # Determine risk level
        if risk_score < 0.3:
            risk_level = "LOW"
        elif risk_score < 0.6:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # Generate recommendations
        recommendations = self._generate_recommendations(flags, risk_level, user_data)

        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "flags": flags,
            "recommendations": recommendations,
            "compliance_score": round((1 - risk_score) * 100, 1)
        }

    def _generate_recommendations(self, flags: List[str], risk_level: str, user_data: Dict) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []

        if risk_level == "HIGH":
            recommendations.append("⚠️ HIGH RISK - Review all deductions with supporting documents")
            recommendations.append("Consider consulting a tax professional")

        if "High deduction-to-income ratio" in ' '.join(flags):
            recommendations.append("Verify all deduction claims have proper documentation")

        if "Multiple deductions at maximum limit" in ' '.join(flags):
            recommendations.append("Ensure accurate calculation - avoid rounding to max limits")

        if "Invalid deduction" in ' '.join(flags):
            recommendations.append("Remove deductions not applicable to selected regime")

        if not flags:
            recommendations.append("✓ No major compliance issues detected")
            recommendations.append("Keep all supporting documents for 7 years")

        return recommendations

    def compare_regimes(self, user_data: Dict) -> Dict:
        """Compare tax in both old and new regimes"""
        results = {}

        for regime in ['old', 'new']:
            self.load_rules(regime)
            tax_result = self.calculate_tax(user_data)
            fraud_result = self.detect_fraud(user_data, tax_result)

            results[regime] = {
                "tax_calculation": tax_result,
                "fraud_analysis": fraud_result
            }

        # Determine better regime
        old_tax = results['old']['tax_calculation'].get('total_tax', float('inf'))
        new_tax = results['new']['tax_calculation'].get('total_tax', float('inf'))

        better_regime = 'old' if old_tax < new_tax else 'new'
        savings = abs(old_tax - new_tax)

        results['comparison'] = {
            "better_regime": better_regime,
            "savings": round(savings, 2),
            "old_regime_tax": round(old_tax, 2),
            "new_regime_tax": round(new_tax, 2)
        }

        return results

    def generate_report(self, user_data: Dict, regime: str) -> str:
        """Generate comprehensive text report"""

        self.load_rules(regime)
        tax_result = self.calculate_tax(user_data)
        fraud_result = self.detect_fraud(user_data, tax_result)

        report = f"""
{'='*70}
TAX ANALYSIS REPORT
Financial Year: {self.rules['financial_year']} | Regime: {regime.upper()}
{'='*70}

INCOME DETAILS
{'-'*70}
Gross Income:                 ₹{tax_result['gross_income']:,.2f}
Total Deductions:             ₹{tax_result['total_deductions']:,.2f}
Taxable Income:               ₹{tax_result['taxable_income']:,.2f}

TAX CALCULATION
{'-'*70}
Tax from Slabs:               ₹{tax_result['tax_breakdown']['tax_from_slabs']:,.2f}
Rebate (87A):                 ₹{tax_result['tax_breakdown']['rebate']:,.2f}
Surcharge:                    ₹{tax_result['tax_breakdown']['surcharge']:,.2f}
Health & Education Cess (4%): ₹{tax_result['tax_breakdown']['cess']:,.2f}
{'-'*70}
TOTAL TAX PAYABLE:            ₹{tax_result['total_tax']:,.2f}
Effective Tax Rate:           {tax_result['effective_tax_rate']:.2f}%

FRAUD & COMPLIANCE ANALYSIS
{'-'*70}
Risk Score:                   {fraud_result['risk_score']} / 1.0
Risk Level:                   {fraud_result['risk_level']}
Compliance Score:             {fraud_result['compliance_score']}%

"""

        if fraud_result['flags']:
            report += f"\n⚠️ RED FLAGS DETECTED:\n"
            for i, flag in enumerate(fraud_result['flags'], 1):
                report += f"   {i}. {flag}\n"

        report += f"\n📋 RECOMMENDATIONS:\n"
        for i, rec in enumerate(fraud_result['recommendations'], 1):
            report += f"   {i}. {rec}\n"

        report += f"\n{'='*70}\n"
        report += f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"{'='*70}\n"

        return report


def main():
    """Test the analyzer"""
    agent = TaxAnalyzerAgent()

    # Sample user data
    test_user_data = {
        "gross_income": 1200000,
        "deductions": {
            "80C": 150000,
            "80D": 25000,
            "Standard Deduction": 50000,
        },
        "previous_year_income": 1000000
    }

    print("\n" + "="*70)
    print("TESTING TAX ANALYZER AGENT")
    print("="*70 + "\n")

    # Test Old Regime
    print(agent.generate_report(test_user_data, "old"))

    # Test New Regime
    print("\n")
    print(agent.generate_report(test_user_data, "new"))

    # Compare regimes
    print("\n" + "="*70)
    print("REGIME COMPARISON")
    print("="*70 + "\n")

    comparison = agent.compare_regimes(test_user_data)
    comp = comparison['comparison']

    print(f"Old Regime Tax: ₹{comp['old_regime_tax']:,.2f}")
    print(f"New Regime Tax: ₹{comp['new_regime_tax']:,.2f}")
    print(f"\nBetter Option: {comp['better_regime'].upper()} regime")
    print(f"Savings: ₹{comp['savings']:,.2f}")


if __name__ == "__main__":
    main()
