"""
Test the API endpoints locally without starting server
"""
import sys
import json

sys.path.append('.')

from api.main import (
    root, get_current_rules, analyze_tax, compare_regimes,
    generate_report, simulate_scenario, UserFinancialData,
    CompareRegimesData, SimulationData
)


async def test_api():
    """Test all API endpoints"""

    print("\n" + "="*70)
    print("TESTING API ENDPOINTS")
    print("="*70 + "\n")

    # Test 1: Health check
    print("1. Testing Health Check...")
    result = await root()
    print(f"   ✓ Status: {result['status']}")
    print(f"   ✓ Service: {result['service']}\n")

    # Test 2: Get rules
    print("2. Testing Get Rules (Old Regime)...")
    result = await get_current_rules(regime="old")
    print(f"   ✓ Regime: {result['regime']}")
    print(f"   ✓ Slabs: {len(result['rules']['slabs'])}")
    print(f"   ✓ Deductions: {len(result['rules']['deductions'])}\n")

    # Test 3: Analyze tax
    print("3. Testing Tax Analysis...")
    user_data = UserFinancialData(
        gross_income=1200000,
        regime="old",
        deductions={"80C": 150000, "80D": 25000, "Standard Deduction": 50000},
        previous_year_income=1000000
    )
    result = await analyze_tax(user_data)
    print(f"   ✓ Total Tax: ₹{result['tax_calculation']['total_tax']:,.2f}")
    print(f"   ✓ Risk Level: {result['fraud_analysis']['risk_level']}")
    print(f"   ✓ Compliance Score: {result['fraud_analysis']['compliance_score']}%\n")

    # Test 4: Compare regimes
    print("4. Testing Regime Comparison...")
    compare_data = CompareRegimesData(
        gross_income=1200000,
        deductions_old={"80C": 150000, "80D": 25000, "Standard Deduction": 50000},
        deductions_new={"Standard Deduction": 50000}
    )
    result = await compare_regimes(compare_data)
    comp = result['comparison']['comparison']
    print(f"   ✓ Old Regime Tax: ₹{comp['old_regime_tax']:,.2f}")
    print(f"   ✓ New Regime Tax: ₹{comp['new_regime_tax']:,.2f}")
    print(f"   ✓ Better Option: {comp['better_regime'].upper()}")
    print(f"   ✓ Savings: ₹{comp['savings']:,.2f}\n")

    # Test 5: Generate report
    print("5. Testing Report Generation...")
    result = await generate_report(user_data)
    print(f"   ✓ Report generated successfully")
    print(f"   ✓ Report length: {len(result['report'])} characters\n")

    # Test 6: Simulate scenarios
    print("6. Testing Tax Simulation...")
    sim_data = SimulationData(
        base_income=500000,
        income_increments=[500000, 1000000, 1500000, 2000000],
        regime="new",
        deductions={"Standard Deduction": 50000}
    )
    result = await simulate_scenario(sim_data)
    print(f"   ✓ Simulations run: {len(result['simulations'])}")
    for sim in result['simulations']:
        print(f"      Income: ₹{sim['income']:,.0f} → Tax: ₹{sim['tax']:,.2f} ({sim['effective_rate']:.2f}%)")

    print("\n" + "="*70)
    print("✅ ALL API TESTS PASSED")
    print("="*70 + "\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_api())
