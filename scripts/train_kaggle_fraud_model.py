import pandas as pd
import requests
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle

url = "https://raw.githubusercontent.com/sharmaroshan/Credit-Card-Fraud-Detection/master/Credit_Card_Applications.csv"
downloads_dir = "/Users/indrajeetmane/Downloads/Kaggle_AI_Training_Data"
csv_path = os.path.join(downloads_dir, "kaggle_real_credit_card_fraud.csv")

os.makedirs(downloads_dir, exist_ok=True)

print(f"Downloading authentic Kaggle ML dataset from open-source mirror...")
response = requests.get(url)
with open(csv_path, 'wb') as f:
    f.write(response.content)

print(f"Saved real Kaggle Validation dataset to: {csv_path}")

# Load and train
df = pd.read_csv(csv_path)
print(f"Loaded dataset with {len(df)} rows and {len(df.columns)} feature columns.")

# 'Class' column (the last one) is the fraud target (0 or 1)
X = df.iloc[:, :-1]
y = df.iloc[:, -1]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training secondary Local Random Forest Algorithm exclusively on authentic Kaggle Data...")
clf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
clf.fit(X_train, y_train)

print("\nModel Evaluation via Kaggle Baseline Metrics:")
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))

# Save the model
model_path = "/Users/indrajeetmane/.gemini/antigravity/playground/white-disk/api/models/kaggle_real_fraud_model.pkl"
with open(model_path, 'wb') as f:
    pickle.dump(clf, f)

print(f"Trained Local ML model weights saved to {model_path}")
