import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def train_fraud_model():
    data_path = os.path.join(os.path.dirname(__file__), "tax_fraud_10k_dataset.csv")
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}")
        return
        
    df = pd.read_csv(data_path)
    
    # Separate Features and Target
    X = df.drop(columns=['Is_Fraud'])
    y = df['Is_Fraud']
    
    # 80-20 Train-Test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Training Gradient Boosting Fraud Classifier...")
    model = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Validation against isolated test set
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Validation Accuracy: {accuracy * 100:.2f}%")
    print("\nClassification Report:\n")
    print(classification_report(y_test, y_pred))
    
    # Save the trained model parameter space natively to OS
    model_path = os.path.join(os.path.dirname(__file__), "game_xgboost_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
        
    print(f"Model successfully saved to {model_path}")
    print("This binary Gradient Boosting instance will power the Three.js 3D Interactive Cyber-Auditor Game.")

if __name__ == "__main__":
    train_fraud_model()
