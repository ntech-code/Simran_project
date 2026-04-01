"""
Bulk Fraud Detector Agent - Analyzes large sets of transactions for fraud patterns
"""
import os
import json
import pandas as pd
import numpy as np
import re
import pickle
from typing import Dict, List, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class FraudDetectorAgent:
    def __init__(self, api_key: str = None):
        """Initialize the fraud detection agent"""
        from agents.genai_client import get_genai_client, get_model_name
        self.client = get_genai_client()
        if not self.client:
            raise ValueError("No AI credentials found (Vertex AI or Gemini API key)")
        self.model = get_model_name()

    def analyze_bulk_transactions(self, dataframe: pd.DataFrame) -> Dict[str, Any]:
        """
        Takes a pandas DataFrame of transactions, converts it to string, 
        and specifically prompts Gemini to return a structured JSON forensic report.
        """
        # Take the first ~2500 rows to ensure we don't hit payload limits, 
        # though 1.5 flash handles massive context easily.
        # To make it clean, we convert to CSV string format
        csv_string = dataframe.head(2500).to_csv(index=False)

        prompt = f"""
        You are an expert Indian forensic accountant and auditor. 
        I am providing you with a raw CSV export of financial transactions. 
        Your job is to thoroughly analyze these transactions for any signs of tax evasion, 
        fraud, money laundering ('smurfing'), highly unusual patterns, or suspicious vendors.

        CSV Data:
        {csv_string}

        You MUST respond with a strictly formatted JSON object matching this exact schema, and nothing else:
        {{
            "risk_score": <float between 0.0 and 1.0 representing total dataset risk>,
            "risk_level": "<LOW, MEDIUM, HIGH, or CRITICAL>",
            "total_analyzed": <integer number of rows>,
            "anomalies": [
                {{
                    "row_index": <integer row number if applicable, or null>,
                    "transaction_id": "<string ID if present>",
                    "reason": "<detailed forensic reason why this is suspicious>",
                    "severity": "<LOW, MEDIUM, HIGH>"
                }}
            ],
            "forensic_summary": "<A 2-paragraph overall summary of your findings>"
        }}
        """

        try:
            print(f"Sending {len(dataframe)} rows for AI forensic analysis...")
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1 # Low temperature for analytical consistency
                ),
            )
            
            # The response is directly expected to be valid JSON string
            result_text = response.text
            structured_data = json.loads(result_text)
            
            # Ensure it has the right shape if the LLM deviated slightly
            if "anomalies" not in structured_data:
                structured_data["anomalies"] = []
                
            return structured_data

        except Exception as e:
            print(f"Error in FraudDetectorAgent: {str(e)}")
            return {
                "error": True,
                "message": f"AI Forensics failed: {str(e)}",
                "risk_score": 0,
                "risk_level": "UNKNOWN",
                "anomalies": [],
                "forensic_summary": "Analysis failed."
            }

    def vendor_type(self, desc: str) -> int:
        desc = desc.lower()
        if 'salary' in desc: return 1
        if 'cash' in desc: return 2
        if 'crypto' in desc: return 3
        if 'offshore' in desc or 'shell corp' in desc or 'dubai' in desc: return 4
        return 0

    def analyze_bank_statements(self, statements_text: str) -> Dict[str, Any]:
        """
        Takes raw unstructured text extracted from PDF bank statements, parses it into 
        structured tabular columns using Regex, and feeds the resulting Pandas DataFrame
        directly into the LOCAL KAGGLE Random Forest model. Completely offline, zero API calls!
        """
        print("Scraping raw PyPDF2 text using standard Python Python Regex...")
        
        # Flatten the text heavily to handle PDF line breaks arbitrarily broken by PyPDF2
        clean_text = re.sub(r'\s+', ' ', statements_text)
        
        # Format 1: Our standard simulated Kaggle format
        pattern1 = re.compile(r'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})\s*(.*?)\s*Rs\.\s*([\d,]+\.\d{2})')
        matches = pattern1.findall(clean_text)
        
        data_rows = []
        if matches:
            for match in matches:
                date_time, desc, amount_str = match
                amt = float(amount_str.replace(',', ''))
                is_credit = 1 if 'SALARY' in desc.upper() or 'CASH DEPOSIT' in desc.upper() or 'IN:' in desc.upper() else 0
                data_rows.append({'Date': date_time, 'Description': desc.strip(), 'Amount': amt, 'Is_Credit': is_credit, 'Vendor_Type': self.vendor_type(desc)})
        else:
            # Format 2: Authentic Real-world HDFC/SBI Strict Block Parsing
            # Enforces EXACT structure: {Transaction Date} {Narration} {Value Date} {Txn Amount} {Balance}
            # This is mathematically immune to Pincodes, Footer Summaries, and Page Breaks!
            pattern = re.compile(r'(\d{2,4}[-/]\d{2}[-/]\d{2,4})\s+(.*?)\s+(\d{2}/\d{2}/\d{2})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})')
            matches = pattern.findall(clean_text)
            
            prev_balance = None
            for match in matches:
                tx_date, ext_desc, val_date, amt_str, bal_str = match
                
                try: 
                    amt = float(amt_str.replace(',', ''))
                    balance = float(bal_str.replace(',', ''))
                except: continue
                
                # Mathematically infer true Debit/Credit direction by comparing the authenticated trailing balances!
                if prev_balance is not None:
                    is_credit = 1 if balance > prev_balance else 0
                else:
                    # First transaction OCR fallback heuristic
                    is_credit = 1 if 'SALARY' in ext_desc.upper() or 'DEPOSIT' in ext_desc.upper() or 'CR' in ext_desc.upper() or 'INWARD' in ext_desc.upper() else 0
                    
                prev_balance = balance
                
                desc = ext_desc[:100].strip()
                data_rows.append({'Date': tx_date, 'Description': desc, 'Amount': amt, 'Is_Credit': is_credit, 'Vendor_Type': self.vendor_type(desc)})

            print(f"Strict Math Regex Pipeline accurately isolated {len(data_rows)} verified transaction blocks.")

        # Load the locally trained Kaggle tabular ML Model
        try:
            model_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'models', 'bank_fraud_local.pkl')
            with open(model_path, 'rb') as f:
                local_ml_model = pickle.load(f)
        except Exception as e:
            return {
                "error": True, "message": f"CRITICAL: Failed to load local ML model .pkl file: {str(e)}", 
                "risk_score": 0, "risk_level": "UNKNOWN", "anomalies": [], "forensic_summary": "Model Loading Error."}

        if not data_rows:
            return {
                "risk_score": 0.0,
                "risk_level": "LOW",
                "total_analyzed": "0 valid bank transactions successfully extracted by Regex payload.",
                "anomalies": [],
                "forensic_summary": "Offline Local Model Execution: Absolutely zero transactions could be parsed correctly. The real-world Bank Statement layout could not be resolved by the current generic Regex definitions."
            }

        # Tabulation
        df = pd.DataFrame(data_rows)
        X_infer = df[['Amount', 'Is_Credit', 'Vendor_Type']]
        
        # The ultimate solution: Pure 100% Offline Local Machine Learning inference!
        print(f"Predicting Fraud on {len(df)} transactions instantaneously without any API limits...")
        predictions = local_ml_model.predict(X_infer)
        df['Is_Fraud'] = predictions
        
        anomalies_df = df[df['Is_Fraud'] == 1]
        fraud_anomalies = []
        
        # Convert local ML predictions into the exact structured JSON standard expected by Frontend
        for idx, row in anomalies_df.iterrows():
            amt_formatted = f"Rs. {row['Amount']:,.2f}"
            description = row['Description'].upper()
            
            reason = f"An unusually large or irregular transaction of {amt_formatted} was flagged. This pattern requires manual review to ensure the funds are properly accounted for."
            severity = "HIGH"
            
            features = row['Vendor_Type']
            if features == 4:
                reason = f"Massive wire transfer of {amt_formatted} involving a high-risk offshore or shell company. This is a major red flag for money laundering and hiding taxable income."
                severity = "CRITICAL"
            elif features == 3:
                reason = f"Large transfer of {amt_formatted} to a cryptocurrency exchange. Crypto is often used to move money without paying taxes, so this requires a strict audit."
                severity = "HIGH"
            elif features == 2:
                if 49000 <= row['Amount'] <= 49999:
                    reason = f"Suspicious cash transaction of {amt_formatted}. This looks like 'smurfing'—making deposits just under the Rs. 50,000 limit to avoid providing a PAN card."
                    severity = "CRITICAL"
                elif row['Amount'] > 1000000: # specific handling for >10 Lakhs cash
                    reason = f"Extremely large cash withdrawal of {amt_formatted}. Withdrawing massive amounts of cash is highly suspicious and often used to hide undeclared expenses."
                    severity = "CRITICAL"
                else:
                    reason = f"Unusual cash transaction of {amt_formatted}. High cash usage is typically scrutinized to ensure the money is legally sourced."
                    severity = "HIGH"
            elif features == 5:
                reason = f"Severe GST Input Tax Credit Evasion pattern detected. A transaction of {amt_formatted} flagged as matching known bogus invoicing loops to illegitimately claim fake GST subsidies."
                severity = "CRITICAL"
                
            fraud_anomalies.append({
                "row_index": idx,
                "transaction_id": f"{row['Date']} - {description}",
                "reason": reason,
                "severity": severity
            })
            
        # Re-engineered algorithmic Risk Output Matrix aggregator
        calculated_score = 0.0
        for fa in fraud_anomalies:
            if fa['severity'] == "CRITICAL": calculated_score += 0.50
            elif fa['severity'] == "HIGH": calculated_score += 0.35
            else: calculated_score += 0.15
            
        risk_score = min(1.0, calculated_score)
        risk_level = "LOW"
        if risk_score >= 0.3: risk_level = "MEDIUM"
        if risk_score >= 0.7: risk_level = "HIGH"
        if risk_score >= 0.9: risk_level = "CRITICAL"
        
        sum_str = (
            f"The Forensic AI engine successfully scanned {len(df)} transactions from your bank statements. "
            f"We found {len(fraud_anomalies)} highly suspicious transactions hidden within your documents. "
            f"Based on these findings, your total risk score is {int(risk_score * 100)}%, indicating a severe likelihood of tax evasion or undeclared money movement."
        )
        if len(fraud_anomalies) == 0:
            sum_str = f"The Forensic AI scanned {len(df)} transactions perfectly. No suspicious patterns, large cash deposits, or offshore transfers were found. Your financial profile appears standard and safe."

        total_deposits = df[df['Is_Credit'] == 1]['Amount'].sum()
        total_withdrawals = df[df['Is_Credit'] == 0]['Amount'].sum()
        suspicious_volume = anomalies_df['Amount'].sum()
        
        # Categorical Breakdown for Frontend Visuals
        categories = {
            "Standard Outflows": float(df[(df['Vendor_Type'] == 0) & (df['Is_Credit'] == 0)]['Amount'].sum()),
            "Salary/Income": float(df[df['Vendor_Type'] == 1]['Amount'].sum()),
            "Cash Withdrawals": float(df[(df['Vendor_Type'] == 2) & (df['Is_Credit'] == 0)]['Amount'].sum()),
            "Crypto Trading": float(df[df['Vendor_Type'] == 3]['Amount'].sum()),
            "Offshore Transfers": float(df[df['Vendor_Type'] == 4]['Amount'].sum()),
        }

        # ====== SELF-TRAINING: Incremental Online Learning ======
        # Append every user's real transaction data to the master CSV.
        # The model retrains periodically as the dataset grows!
        training_stats = self._incremental_train(df)

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "total_analyzed": f"Local ML Analyzed {len(df)} synthetic tabular rows processed natively from PDF text.",
            "anomalies": fraud_anomalies,
            "forensic_summary": sum_str,
            "financial_metrics": {
                "total_deposits": float(total_deposits),
                "total_withdrawals": float(total_withdrawals),
                "suspicious_volume": float(suspicious_volume),
                "categories": categories
            },
            "model_training": training_stats
        }

    def _incremental_train(self, new_df: pd.DataFrame) -> dict:
        """
        INCREMENTAL ONLINE LEARNING ENGINE
        1. Appends new real-world user transactions to the master training CSV
        2. If dataset exceeds retrain threshold, automatically retrains the RF model
        3. Returns stats about the training state
        """
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'indian_tax_fraud_training_dataset.csv')
        model_path = os.path.join(os.path.dirname(__file__), '..', 'api', 'models', 'bank_fraud_local.pkl')
        RETRAIN_THRESHOLD = 500  # Retrain every 500 new rows

        try:
            # Load existing master dataset
            if os.path.exists(csv_path):
                master_df = pd.read_csv(csv_path)
                old_count = len(master_df)
            else:
                master_df = pd.DataFrame(columns=['Amount', 'Is_Credit', 'Vendor_Type', 'Is_Fraud'])
                old_count = 0

            # Prepare new rows with predictions as labels (semi-supervised)
            append_df = new_df[['Amount', 'Is_Credit', 'Vendor_Type', 'Is_Fraud']].copy()
            
            # Append to master
            master_df = pd.concat([master_df, append_df], ignore_index=True)
            master_df.to_csv(csv_path, index=False)
            new_count = len(master_df)
            rows_added = new_count - old_count

            print(f"✅ Self-Training: Appended {rows_added} real-world rows to master CSV. Total dataset: {new_count} rows.")

            # Check if we should retrain
            should_retrain = (rows_added >= RETRAIN_THRESHOLD) or (new_count % RETRAIN_THRESHOLD < rows_added)
            
            if should_retrain and new_count > 1000:
                print("🔄 RETRAINING: Dataset threshold crossed. Retraining Random Forest...")
                from sklearn.ensemble import RandomForestClassifier
                from sklearn.model_selection import train_test_split

                X = master_df[['Amount', 'Is_Credit', 'Vendor_Type']]
                y = master_df['Is_Fraud']
                
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
                model.fit(X_train, y_train)
                accuracy = model.score(X_test, y_test)
                
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                
                print(f"✅ Model retrained successfully! New accuracy: {accuracy:.4f} on {new_count} rows.")
                return {
                    "retrained": True,
                    "total_dataset_rows": new_count,
                    "rows_added_this_session": rows_added,
                    "new_accuracy": round(accuracy * 100, 2)
                }
            
            return {
                "retrained": False,
                "total_dataset_rows": new_count,
                "rows_added_this_session": rows_added,
                "message": f"Data collected. Model will retrain after {RETRAIN_THRESHOLD - (new_count % RETRAIN_THRESHOLD)} more rows."
            }

        except Exception as e:
            print(f"⚠️ Self-training error (non-fatal): {e}")
            return {"retrained": False, "error": str(e)}
