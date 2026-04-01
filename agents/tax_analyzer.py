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
        from agents.genai_client import get_genai_client, get_model_name
        self.client = get_genai_client()
        if not self.client:
            raise ValueError("No AI credentials found (Vertex AI or Gemini API key)")
        self.model = get_model_name()

        self.rules = {}
        print("✓ TaxAnalyzerAgent initialized")

    def load_rules(self, regime: str, financial_year: str = "2025-26") -> bool:
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
        """
        Calculate tax based on user financial data.
        Implements:
        - Standard slab-based tax calculation
        - Section 87A rebate with MARGINAL RELIEF
        - Surcharge with MARGINAL RELIEF
        - Health & Education Cess (4%)
        """

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

            # ===== SECTION 87A REBATE WITH MARGINAL RELIEF =====
            # If taxable income ≤ threshold: full rebate (tax = 0)
            # If taxable income slightly > threshold: apply marginal relief
            #   → Tax cannot exceed the amount by which income exceeds the threshold
            rebate = 0
            marginal_relief_87a = 0
            tax_after_rebate = tax_from_slabs

            for rebate_rule in self.rules.get('rebates', []):
                threshold = rebate_rule['income_threshold']
                max_rebate = rebate_rule['max_rebate']

                if taxable_income <= threshold:
                    # Full rebate — tax becomes 0
                    rebate = min(tax_from_slabs, max_rebate)
                    tax_after_rebate = tax_from_slabs - rebate
                else:
                    # Income exceeds threshold — no rebate normally
                    # But apply MARGINAL RELIEF:
                    # Tax payable should not exceed (income - threshold)
                    excess_income = taxable_income - threshold
                    normal_tax = tax_from_slabs  # tax without any rebate

                    if normal_tax > excess_income:
                        # Marginal relief applies!
                        marginal_relief_87a = normal_tax - excess_income
                        rebate = marginal_relief_87a  # treat marginal relief as rebate
                        tax_after_rebate = excess_income
                    else:
                        # Normal tax is already less than excess, no relief needed
                        tax_after_rebate = normal_tax
                break  # Only first matching rebate rule applies

            # ===== SURCHARGE WITH MARGINAL RELIEF =====
            surcharge = self._calculate_surcharge_with_marginal_relief(
                taxable_income, tax_after_rebate
            )

            # ===== HEALTH & EDUCATION CESS (4%) =====
            cess_rate = self.rules['cess']['rate'] / 100
            cess = (tax_after_rebate + surcharge) * cess_rate

            # Total tax
            total_tax = max(0, tax_after_rebate + surcharge + cess)

            result = {
                "gross_income": gross_income,
                "total_deductions": total_deductions,
                "taxable_income": taxable_income,
                "tax_breakdown": {
                    "tax_from_slabs": round(tax_from_slabs, 2),
                    "rebate": round(rebate, 2),
                    "marginal_relief_87a": round(marginal_relief_87a, 2),
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

    def _calculate_surcharge_with_marginal_relief(self, taxable_income: float, tax_after_rebate: float) -> float:
        """
        Calculate surcharge with MARGINAL RELIEF.
        
        Marginal relief ensures that when income slightly crosses a surcharge 
        threshold, the taxpayer doesn't pay more in total tax (including surcharge)
        than the tax at the threshold + the excess income.
        
        Example: If threshold is ₹50L and income is ₹51L:
        - Tax+surcharge at ₹51L should not exceed Tax at ₹50L + ₹1L
        """
        surcharges = self.rules.get('surcharges', [])
        if not surcharges:
            return 0

        # Find current surcharge rate
        current_rate = 0
        for sc in surcharges:
            min_inc = sc['min_income']
            max_inc = sc['max_income']
            rate = sc['rate'] / 100

            if max_inc is None:
                if taxable_income > min_inc:
                    current_rate = rate
            else:
                if min_inc <= taxable_income <= max_inc:
                    current_rate = rate

        if current_rate == 0:
            return 0

        # Calculate normal surcharge
        normal_surcharge = tax_after_rebate * current_rate

        # Find the threshold that was just crossed
        # Sort surcharge slabs by min_income to find boundaries
        thresholds = sorted(set(sc['min_income'] for sc in surcharges if sc['min_income'] > 0))
        
        for threshold in thresholds:
            if taxable_income > threshold:
                # Find the surcharge rate BELOW this threshold
                prev_rate = 0
                for sc in surcharges:
                    min_inc = sc['min_income']
                    max_inc = sc['max_income']
                    if max_inc is not None and max_inc <= threshold:
                        prev_rate = sc['rate'] / 100
                    elif min_inc < threshold and (max_inc is None or max_inc >= threshold):
                        prev_rate = 0  # rate at threshold boundary may be the one below
                        for sc2 in surcharges:
                            if sc2['max_income'] is not None and sc2['max_income'] == threshold:
                                prev_rate = sc2['rate'] / 100
                                break

                # Tax at the threshold (just below)
                tax_at_threshold = self._calculate_slab_tax(threshold)
                surcharge_at_threshold = tax_at_threshold * prev_rate
                total_at_threshold = tax_at_threshold + surcharge_at_threshold

                # Total with current surcharge
                total_with_surcharge = tax_after_rebate + normal_surcharge

                # Excess income over this threshold
                excess_income = taxable_income - threshold

                # Maximum total tax = tax at threshold + excess income
                max_total = total_at_threshold + excess_income

                if total_with_surcharge > max_total:
                    # Marginal relief applies
                    marginal_surcharge = max_total - tax_after_rebate
                    return max(0, marginal_surcharge)

        return normal_surcharge

    def _calculate_surcharge(self, taxable_income: float, tax_before_surcharge: float) -> float:
        """Legacy surcharge calculation (without marginal relief)"""
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

    def compare_regimes(self, old_data: Dict, new_data: Dict, financial_year: str = "2025-26") -> Dict:
        """Compare tax in both old and new regimes"""
        results = {}

        # Calculate Old Regime
        self.load_rules('old', financial_year)
        old_tax_result = self.calculate_tax(old_data)
        old_fraud_result = self.detect_fraud(old_data, old_tax_result)
        results['old'] = {
            "tax_calculation": old_tax_result,
            "fraud_analysis": old_fraud_result
        }

        # Calculate New Regime
        self.load_rules('new', financial_year)
        new_tax_result = self.calculate_tax(new_data)
        new_fraud_result = self.detect_fraud(new_data, new_tax_result)
        results['new'] = {
            "tax_calculation": new_tax_result,
            "fraud_analysis": new_fraud_result
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
