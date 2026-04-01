import pandas as pd
import numpy as np
import os

def generate_indian_tax_dataset(num_samples=10000):
    np.random.seed(42)
    
    # 1. Generate Base Demographics & Income
    age = np.random.randint(21, 80, num_samples)
    
    # Gross Income distribution (skewed towards lower/middle class, but with long tail)
    # Most between 3L and 20L, some up to 5Cr
    log_income = np.random.normal(loc=13.8, scale=1.0, size=num_samples) # exp(13.8) is ~9.8 Lakhs
    gross_income = np.round(np.exp(log_income))
    gross_income = np.clip(gross_income, 300000, 50000000)
    
    # Business Income Ratio (0.0 means purely salaried, 1.0 means purely business)
    # ~70% salaried, 30% business/mixed
    business_income_ratio = np.where(np.random.rand(num_samples) > 0.3, 0.0, np.random.beta(2, 5, num_samples))
    
    # 2. Generate Deductions (with some realistic bounds)
    # HRA is normally only for salaried, up to 40% of salary
    salary_income = gross_income * (1 - business_income_ratio)
    hra_eligible = np.where(business_income_ratio < 0.5, 1, 0)
    hra_claimed = np.round(np.random.uniform(0, 0.4) * salary_income * hra_eligible * np.random.binomial(1, 0.6, num_samples))
    
    # 80C is up to 1.5L
    section_80c = np.round(np.random.uniform(0, 150000, num_samples) * np.random.binomial(1, 0.8, num_samples))
    
    # 80G (Donations) - usually small, but fraud cases inflate this
    section_80g = np.round(np.random.exponential(scale=10000, size=num_samples))
    
    # 3. Inject Fraud / Evasion Indicators
    is_evasion_suspect = np.zeros(num_samples, dtype=int)
    
    # Fraud Pattern A: Massive fake donations (80G > 10% of Gross Income)
    # Let's artificially create some fraudsters
    fraud_idx_A = np.random.choice(num_samples, size=int(num_samples * 0.05), replace=False)
    section_80g[fraud_idx_A] = gross_income[fraud_idx_A] * np.random.uniform(0.15, 0.30, len(fraud_idx_A))
    
    # Fraud Pattern B: Claiming HRA while having high business income
    fraud_idx_B = np.random.choice(num_samples, size=int(num_samples * 0.04), replace=False)
    business_income_ratio[fraud_idx_B] = np.random.uniform(0.8, 1.0, len(fraud_idx_B))
    hra_claimed[fraud_idx_B] = gross_income[fraud_idx_B] * np.random.uniform(0.2, 0.4, len(fraud_idx_B))
    
    # Fraud Pattern C: High income (>50L), 0 tax/deduction matching (Unrealistic zeroes)
    fraud_idx_C = np.random.choice(np.where(gross_income > 5000000)[0], size=int((gross_income > 5000000).sum() * 0.1), replace=False)
    # We leave their deductions low, but flag them if they have weird ratios
    
    # Apply ground truth labels based on explicit logic + some noise
    for i in range(num_samples):
        risk_score = 0
        
        # Rule 1: High 80G relative to income
        if section_80g[i] > gross_income[i] * 0.12:
            risk_score += 3
            
        # Rule 2: HRA claim with high business income ratio
        if hra_claimed[i] > 0 and business_income_ratio[i] > 0.5:
            risk_score += 4
            
        # Rule 3: Maxed out 80C but very low income (suspicious)
        if section_80c[i] > 140000 and gross_income[i] < 400000:
            risk_score += 2
            
        # Add label if high risk
        if risk_score >= 3:
            is_evasion_suspect[i] = 1
            
        # Add 1% noisy labels (false positives/negatives)
        if np.random.rand() < 0.01:
            is_evasion_suspect[i] = 1 - is_evasion_suspect[i]
            
    # Compile dataset
    df = pd.DataFrame({
        'Age': age,
        'Gross_Income': gross_income,
        'Business_Income_Ratio': np.round(business_income_ratio, 2),
        'HRA_Claimed': hra_claimed,
        'Section_80C': section_80c,
        'Section_80G': section_80g,
        'is_evasion_suspect': is_evasion_suspect
    })
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    file_path = 'data/indian_tax_fraud_dataset.csv'
    df.to_csv(file_path, index=False)
    print(f"Generated {num_samples} records to {file_path}")
    print(df['is_evasion_suspect'].value_counts(normalize=True))

if __name__ == '__main__':
    generate_indian_tax_dataset(15000)
