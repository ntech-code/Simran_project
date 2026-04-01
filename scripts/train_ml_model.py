import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import pickle
import os

def train_fraud_model():
    print("Loading Kaggle-style synthetic dataset...")
    try:
        df = pd.read_csv('data/indian_tax_fraud_dataset.csv')
    except FileNotFoundError:
        print("Dataset not found. Please run generate_kaggle_dataset.py first.")
        return
    
    # Features and Target
    X = df.drop('is_evasion_suspect', axis=1)
    y = df['is_evasion_suspect']
    
    print(f"Total features: {X.columns.tolist()}")
    
    print("Splitting data into train/test (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Initialize Random Forest
    print("Training Random Forest Classifier on tax profiles...")
    # class_weight='balanced' helps with the fact that fraud cases are rarer than clean ones
    rf_model = RandomForestClassifier(n_estimators=100, max_depth=10, class_weight='balanced', random_state=42)
    rf_model.fit(X_train, y_train)
    
    # Evaluate
    print("Evaluating Model Accuracy & Precision...")
    y_pred = rf_model.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Feature Importances
    importances = pd.DataFrame({
        'Feature': X.columns,
        'Importance': rf_model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    print("\nFeature Importances:")
    print(importances)
    
    # Save Model
    os.makedirs('api/models', exist_ok=True)
    model_path = 'api/models/tax_fraud_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(rf_model, f)
        
    print(f"\nModel successfully saved to {model_path}!")
    print("Ready to be deployed in the FastAPI backend.")

if __name__ == '__main__':
    train_fraud_model()
