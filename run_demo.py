"""
Quick Demo Script - Runs complete demonstration of the tax analysis system
"""
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from agents.tax_analyzer import TaxAnalyzerAgent
from agents.tax_rule_generator import TaxRuleGeneratorAgent


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def demo_scenario_1():
    """Demo Scenario 1: Regular Taxpayer (Low Risk)"""
    print_header("SCENARIO 1: Regular Taxpayer - Old Regime")

    agent = TaxAnalyzerAgent()
    agent.load_rules('old', '2024-25')

    user_data = {
        "gross_income": 1200000,
        "deductions": {
            "80C": 150000,
            "80D": 25000,
            "Standard Deduction": 50000
        },
        "previous_year_income": 1100000
    }

    print("INPUT:")
    print(f"  Gross Income: ₹{user_data['gross_income']:,}")
    print(f"  Deductions: 80C (₹{user_data['deductions']['80C']:,}), "
          f"80D (₹{user_data['deductions']['80D']:,})")
    print()

    # Calculate tax
    result = agent.calculate_tax(user_data)
    fraud = agent.detect_fraud(user_data, result)

    print("RESULTS:")
    print(f"  Total Tax Payable: ₹{result['total_tax']:,.2f}")
    print(f"  Effective Tax Rate: {result['effective_tax_rate']:.2f}%")
    print(f"  Risk Score: {fraud['risk_score']:.2f} ({fraud['risk_level']})")
    print(f"  Compliance Score: {fraud['compliance_score']}%")
    print()

    if fraud['flags']:
        print("  ⚠️  RED FLAGS:")
        for flag in fraud['flags']:
            print(f"      - {flag}")
    else:
        print("  ✓ No compliance issues detected")


def demo_scenario_2():
    """Demo Scenario 2: High Risk Taxpayer"""
    print_header("SCENARIO 2: Suspicious Pattern - Fraud Detection")

    agent = TaxAnalyzerAgent()
    agent.load_rules('old', '2024-25')

    user_data = {
        "gross_income": 800000,
        "deductions": {
            "80C": 150000,
            "80D": 75000,
            "80G": 100000,
            "80E": 50000,
            "24(b)": 200000,
            "Standard Deduction": 50000
        },
        "previous_year_income": 400000  # 100% income jump
    }

    print("INPUT:")
    print(f"  Gross Income: ₹{user_data['gross_income']:,}")
    print(f"  Total Deductions Claimed: ₹{sum(user_data['deductions'].values()):,}")
    print(f"  Previous Year Income: ₹{user_data['previous_year_income']:,}")
    print()

    # Calculate tax
    result = agent.calculate_tax(user_data)
    fraud = agent.detect_fraud(user_data, result)

    print("RESULTS:")
    print(f"  Total Tax Payable: ₹{result['total_tax']:,.2f}")
    print(f"  Risk Score: {fraud['risk_score']:.2f} ({fraud['risk_level']})")
    print(f"  Compliance Score: {fraud['compliance_score']}%")
    print()

    print("  ⚠️  RED FLAGS DETECTED:")
    for i, flag in enumerate(fraud['flags'], 1):
        print(f"      {i}. {flag}")

    print("\n  📋 RECOMMENDATIONS:")
    for i, rec in enumerate(fraud['recommendations'], 1):
        print(f"      {i}. {rec}")


def demo_scenario_3():
    """Demo Scenario 3: Regime Comparison"""
    print_header("SCENARIO 3: Old vs New Regime Comparison")

    agent = TaxAnalyzerAgent()

    user_data_old = {
        "gross_income": 1500000,
        "deductions": {
            "80C": 150000,
            "80D": 50000,
            "Standard Deduction": 50000,
            "24(b)": 200000
        }
    }

    user_data_new = {
        "gross_income": 1500000,
        "deductions": {
            "Standard Deduction": 50000
        }
    }

    print("INPUT:")
    print(f"  Gross Income: ₹{user_data_old['gross_income']:,}")
    print(f"  Old Regime Deductions: ₹{sum(user_data_old['deductions'].values()):,}")
    print(f"  New Regime Deductions: ₹{sum(user_data_new['deductions'].values()):,}")
    print()

    # Calculate for both regimes
    agent.load_rules('old')
    old_result = agent.calculate_tax(user_data_old)

    agent.load_rules('new')
    new_result = agent.calculate_tax(user_data_new)

    # Compare
    old_tax = old_result['total_tax']
    new_tax = new_result['total_tax']
    savings = abs(old_tax - new_tax)
    better = 'OLD' if old_tax < new_tax else 'NEW'

    print("COMPARISON RESULTS:")
    print(f"  Old Regime Tax: ₹{old_tax:,.2f} ({old_result['effective_tax_rate']:.2f}%)")
    print(f"  New Regime Tax: ₹{new_tax:,.2f} ({new_result['effective_tax_rate']:.2f}%)")
    print()
    print(f"  🎯 RECOMMENDATION: Choose {better} regime")
    print(f"  💰 SAVINGS: ₹{savings:,.2f}")


def demo_scenario_4():
    """Demo Scenario 4: Invalid Regime Deductions"""
    print_header("SCENARIO 4: Invalid Deduction Detection - New Regime")

    agent = TaxAnalyzerAgent()
    agent.load_rules('new', '2024-25')

    # User incorrectly claims old regime deductions in new regime
    user_data = {
        "gross_income": 1000000,
        "deductions": {
            "80C": 150000,  # Not allowed in new regime
            "80D": 25000,   # Not allowed in new regime
            "Standard Deduction": 50000
        }
    }

    print("INPUT:")
    print(f"  Gross Income: ₹{user_data['gross_income']:,}")
    print(f"  Regime: NEW")
    print(f"  Deductions Claimed: 80C, 80D, Standard Deduction")
    print()

    # Calculate tax
    result = agent.calculate_tax(user_data)
    fraud = agent.detect_fraud(user_data, result)

    print("FRAUD DETECTION RESULTS:")
    print(f"  Risk Score: {fraud['risk_score']:.2f} ({fraud['risk_level']})")
    print()
    print("  ⚠️  RED FLAGS:")
    for flag in fraud['flags']:
        print(f"      - {flag}")
    print()
    print("  📋 RECOMMENDATIONS:")
    for rec in fraud['recommendations']:
        print(f"      - {rec}")


def demo_statistics():
    """Show system statistics"""
    print_header("SYSTEM STATISTICS")

    import json

    # Load rules
    with open('rules/india_tax_2024_25_old.json', 'r') as f:
        old_rules = json.load(f)

    with open('rules/india_tax_2024_25_new.json', 'r') as f:
        new_rules = json.load(f)

    print("TAX RULES DATABASE:")
    print(f"  Financial Year: 2024-25")
    print()
    print("  Old Regime:")
    print(f"    - Tax Slabs: {len(old_rules['slabs'])}")
    print(f"    - Deductions Available: {len(old_rules['deductions'])}")
    print(f"    - Surcharge Levels: {len(old_rules['surcharges'])}")
    print()
    print("  New Regime:")
    print(f"    - Tax Slabs: {len(new_rules['slabs'])}")
    print(f"    - Deductions Available: {len(new_rules['deductions'])}")
    print(f"    - Surcharge Levels: {len(new_rules['surcharges'])}")
    print()

    # Show deduction comparison
    print("DEDUCTION COMPARISON:")
    print(f"  Old Regime: {', '.join([d['section'] for d in old_rules['deductions']])}")
    print(f"  New Regime: {', '.join([d['section'] for d in new_rules['deductions']])}")


def main():
    """Run complete demo"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  INDIAN TAX ANALYSIS SYSTEM - MULTI-AGENT AI PLATFORM".center(68) + "█")
    print("█" + "  Complete Demonstration for FY 2024-25".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    try:
        # Run all scenarios
        demo_statistics()
        demo_scenario_1()
        demo_scenario_2()
        demo_scenario_3()
        demo_scenario_4()

        # Summary
        print_header("DEMO COMPLETED SUCCESSFULLY")
        print("Key Features Demonstrated:")
        print("  ✓ Accurate tax calculation for both regimes")
        print("  ✓ AI-powered fraud detection")
        print("  ✓ Risk scoring and compliance analysis")
        print("  ✓ Regime comparison and recommendations")
        print("  ✓ Invalid deduction detection")
        print("  ✓ Multi-agent architecture")
        print()
        print("Next Steps:")
        print("  1. Run backend: python -m uvicorn api.main:app --reload")
        print("  2. Run frontend: cd frontend && npm run dev")
        print("  3. Open browser: http://localhost:3000")
        print("  4. Test with Postman: Import postman_collection.json")
        print()
        print("="*70)
        print()

    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
