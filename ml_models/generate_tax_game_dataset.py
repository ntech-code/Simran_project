import pandas as pd
import numpy as np
import random
import os

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

NUM_RECORDS = 10500

def generate_dataset():
    data = []
    
    for _ in range(NUM_RECORDS):
        age = random.randint(22, 75)
        years_worked = max(0, age - 22)
        location_tier = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0] # 1=Metro, 2=Urban, 3=Rural
        housing_types = ['Rented', 'Owned', 'Company Leased']
        housing_type = random.choices(housing_types, weights=[0.5, 0.4, 0.1])[0]
        dependents = random.randint(0, 5)
        
        # Base Income based on Age & Tier
        base_income = random.randint(20000, 150000)
        if location_tier == 1:
            base_income *= 1.5
        if age > 40:
            base_income *= 1.8
            
        monthly_income = int(np.random.normal(base_income, base_income * 0.3))
        monthly_income = max(10000, monthly_income)
        
        # Realistic Baseline
        annual_income = monthly_income * 12
        estimated_lifetime_earnings = annual_income * years_worked * 0.6
        
        reported_savings = max(0, int(np.random.normal(estimated_lifetime_earnings * 0.3, 500000)))
        
        # Introducing New Complexity: Property Domains
        # Ancestral Property (Inherited, requires NO income justification)
        has_ancestral = random.random() > 0.4 # 60% chance of inheritance
        ancestral_property_value = 0
        if has_ancestral:
            ancestral_property_value = random.randint(1000000, 50000000) # 10 Lakhs to 5 Cr inherited
            
        # Non-Ancestral Property (Purchased, requires income/EMI/savings justification!)
        has_purchased_property = random.random() > 0.5
        non_ancestral_property_value = 0
        estimated_emi_payments = 0
        
        if has_purchased_property:
            # Maybe they bought a 40L house like in the example
            non_ancestral_property_value = random.randint(500000, 20000000)
            
            # If they bought it, did they use a loan? (If Non-Ancestral > Savings, they must have an EMI)
            if non_ancestral_property_value > reported_savings:
                loan_amount = non_ancestral_property_value - reported_savings
                # Rough EMI calculation: 1% per month roughly for 15-20 yrs (simplistic proxy for game)
                estimated_emi_payments = int(loan_amount * 0.008)
                
        total_property_value = ancestral_property_value + non_ancestral_property_value
                
        # Calculate Monthly Expenses (Includes EMI)
        base_living_expenses = max(5000, int(np.random.normal(monthly_income * 0.4, monthly_income * 0.1)))
        monthly_expenses = base_living_expenses + estimated_emi_payments
        
        # Deterministic Risk Definition Pipeline mapped to English Explanations
        is_fraud = 0
        risk_level = 0 # 0=Low, 1=Medium, 2=High
        
        # Risk Rule 1: High EMI Justification (Medium Risk - Justified by Property)
        # If salary is 80k, Non-Ancestral is 41L, matching savings=1L, EMI is massive leading to 67k expenses
        if monthly_expenses > (monthly_income * 0.75):
            if estimated_emi_payments > 0 and non_ancestral_property_value > 0:
                # Expenses look dangerously high, BUT it's justified by the non-ancestral property loan!
                risk_level = 1 # Moderate risk
                if monthly_expenses >= monthly_income:
                    # Literally living above 100% of legal cashflow even with EMI factor = High risk of default/fraud
                    risk_level = 2
                    is_fraud = 1
            else:
                # High expenses with NO loan/EMI to justify it
                risk_level = 2
                is_fraud = 1
                
        # Risk Rule 2: Unexplained Non-Ancestral Wealth (High Risk - Not Fraud IF Ancestral)
        # "If Non-Ancestral is 20L, Ancestral is 2.8Cr -> Total 3Cr. Salary is 40k. -> VALID."
        # If Non-ancestral property vastly exceeds lifetime earnings + savings WITHOUT a loan footprint
        total_cache_justification = reported_savings + estimated_lifetime_earnings + (estimated_emi_payments * 240)
        
        if non_ancestral_property_value > total_cache_justification * 1.5:
            # They bought massive property they cannot afford with no visible loan
            risk_level = 2
            is_fraud = 1
            
        # Exception Override: If they are young (24) and have 3Cr property but 2.8Cr is ANCESTRAL -> NO FRAUD.
        # The equation naturally handles this because 'ancestral_property_value' is excluded from the cache justification limit.
        if is_fraud == 1 and non_ancestral_property_value < (reported_savings + estimated_lifetime_earnings):
             # Actually, if their non-ancestral purchases are small, the rest MUST be ancestral, so they are cleared.
             is_fraud = 0
             risk_level = 0
                
        # Pure ML noise vector (5%) to enforce ensemble trees to adapt probabilistically
        if random.random() > 0.95:
            is_fraud = 1 if is_fraud == 0 else 0
            
        data.append([
            age, location_tier, housing_type, monthly_income, monthly_expenses,
            reported_savings, ancestral_property_value, non_ancestral_property_value, total_property_value, estimated_emi_payments, years_worked, dependents, is_fraud
        ])
        
    df = pd.DataFrame(data, columns=[
        "Age", "Location_Tier", "Housing_Type", "Monthly_Income", "Monthly_Expenses",
        "Reported_Savings", "Ancestral_Property_Value", "Non_Ancestral_Property_Value", "Total_Property_Value", "Estimated_EMI_Payments", "Years_Worked", "Dependents", "Is_Fraud"
    ])
    
    # Label encode Housing_Type for XGBoost native integers
    df['Housing_Type'] = df['Housing_Type'].map({'Rented': 0, 'Owned': 1, 'Company Leased': 2})
    
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "tax_fraud_10k_dataset.csv")
    df.to_csv(out_path, index=False)
    print(f"Generated {NUM_RECORDS} rows of realistic Synthetic Fraud Scenarios at {out_path}.")
    print(df['Is_Fraud'].value_counts())

if __name__ == "__main__":
    generate_dataset()
