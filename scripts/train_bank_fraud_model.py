import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle
import os

# Deterministic Kaggle-style data synthesis
def check_fraud(amt, desc, is_credit):
    desc = desc.lower()
    # Target 1: Smurfing (Deposits just under 50k PAN limit)
    if amt >= 49000 and amt <= 49999 and 'cash' in desc: return 1
    # Target 2: Shell / Offshore
    if amt > 10000000: return 1 
    if 'shell' in desc or 'offshore' in desc: return 1
    # Target 3: Unexplained massive Crypto
    if amt > 500000 and ('crypto' in desc or 'wazirx' in desc): return 1
    # Target 4: Indian GST Fake Invoice & ITC Fraud
    if 'gst refund itc' in desc or 'bogus' in desc: return 1
    return 0

def vendor_type(desc):
    desc = desc.lower()
    if 'salary' in desc: return 1      # 1 = Salary
    if 'cash' in desc: return 2        # 2 = Cash
    if 'crypto' in desc: return 3      # 3 = Crypto
    if 'offshore' in desc or 'shell' in desc or 'dubai' in desc: return 4 # 4 = High Risk Int
    return 0                           # 0 = Standard Retail Noise

print("Generating synthetic Kaggle-style Bank Transaction dataset (50,000 rows)...")
np.random.seed(42)
n_samples = 50000

amounts = np.abs(np.random.normal(1500, 1000, n_samples))
is_credits = np.random.choice([0, 1], size=n_samples, p=[0.9, 0.1])
vendors = [
    'UPI: Swiggy Instamart', 'UPI: Zomato Limited', 'POS: Dmart', 'UPI: Local Chaiwala', 
    'NEFT: TECHCORP SOLUTIONS (SALARY)', 'CASH DEPOSIT - ATM', 
    'IMPS: WAZIRX CRYPTO EXCHANGE', 'SWIFT IN: OFFSHORE HOLDINGS CAYMAN'
]

data = []
for i in range(n_samples):
    v = np.random.choice(vendors, p=[0.3, 0.3, 0.2, 0.1, 0.05, 0.03, 0.015, 0.005])
    amt = amounts[i]
    is_credit = 1 if 'SALARY' in v else is_credits[i]
    
    if v == 'NEFT: TECHCORP SOLUTIONS (SALARY)': amt = 250000
    if v == 'IMPS: WAZIRX CRYPTO EXCHANGE': amt = np.random.randint(5000, 1500000)
    if v == 'SWIFT IN: OFFSHORE HOLDINGS CAYMAN': amt = np.random.randint(5000000, 100000000)
    
    # Inject deliberate smurfing into the dataset
    if np.random.rand() < 0.02:
        v = 'CASH DEPOSIT - SELF'
        amt = 49900
        is_credit = 1
        
    data.append({
        'Amount': round(amt, 2),
        'Is_Credit': is_credit,
        'Vendor_Type': vendor_type(v),
        'Is_Fraud': check_fraud(amt, v, is_credit)
    })

df = pd.DataFrame(data)

# Export the raw training dataset to CSV so the user can show it off during the presentation
csv_path = "indian_tax_fraud_training_dataset.csv"
df.to_csv(csv_path, index=False)
print(f"Raw Training Dataset successfully exported to {csv_path}")

print(f"Dataset generated. Total Fraud labels: {df['Is_Fraud'].sum()} out of {n_samples}")

print("Training Local Random Forest Algorithm...")
X = df[['Amount', 'Is_Credit', 'Vendor_Type']]
y = df['Is_Fraud']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)

print("\nModel Evaluation via Kaggle Metrics:")
print(classification_report(y_test, model.predict(X_test)))

os.makedirs('api/models', exist_ok=True)
model_path = 'api/models/bank_fraud_local.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(model, f)
print(f"Trained Local ML model weights saved to {model_path}")
