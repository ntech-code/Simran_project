from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import pandas as pd
import PyPDF2
import io
import json
import pickle
import os

from agents.fraud_detector import FraudDetectorAgent
from agents.document_tax_parser import DocumentTaxParserAgent
from agents.spend_analyzer import SpendAnalyzerAgent
from api.utils.auth import get_current_user
from api.models import User, AnalysisHistory, MLPredictionLog, BankTransaction
from api.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

@router.post("/analyze-bulk")
async def analyze_bulk(file: UploadFile = File(...), current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Accepts a CSV or Excel file of transactions, parses it via pandas, 
    and passes it to the Gemini FraudDetectorAgent.
    """
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV or Excel files are accepted.")
    
    try:
        # Read file contents into memory
        contents = await file.read()
        
        # Parse into Pandas DataFrame
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
            
        if df.empty:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")
            
        # Instantiate agent and analyze
        agent = FraudDetectorAgent()
        result = agent.analyze_bulk_transactions(df)
        
        return result
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="The uploaded file contains no data or is malformed.")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a standard UTF-8 CSV.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-statements")
async def analyze_statements(
    files: List[UploadFile] = File(...), 
    passwords: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Accepts multiple PDF bank statements, extracts all text, 
    and passes the combined text to the Gemini FraudDetectorAgent.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
        
    password_dict = {}
    if passwords:
        try:
            password_dict = json.loads(passwords)
        except:
            pass
            
    required_passwords = []
    incorrect_passwords = []
    file_contents = {}
    
    # Pre-flight parse into memory to avoid blocking streams
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF. Please upload only PDF bank statements.")
        file_contents[file.filename] = await file.read()
        
    # Validation Pass
    for filename, contents in file_contents.items():
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
            if pdf_reader.is_encrypted:
                pwd = password_dict.get(filename)
                if not pwd:
                    required_passwords.append(filename)
                else:
                    success = pdf_reader.decrypt(pwd)
                    if not success:
                        incorrect_passwords.append(filename)
        except Exception as e:
            pwd = password_dict.get(filename)
            if not pwd:
                required_passwords.append(filename)
            else:
                incorrect_passwords.append(filename)
                    
    if required_passwords or incorrect_passwords:
        return {
            "error": True,
            "requires_password": True, # Keep legacy flag for UI triggering
            "required_files": required_passwords,
            "incorrect_files": incorrect_passwords,
            "message": "One or more documents are locked. Please provide valid passwords for the specific files below."
        }

    # Extraction Pass
    combined_text = ""
    for filename, contents in file_contents.items():
        combined_text += f"\n--- START OF DOCUMENT: {filename} ---\n"
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
            if pdf_reader.is_encrypted:
                pdf_reader.decrypt(password_dict.get(filename))
                
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    combined_text += text + "\n"
        except Exception as e:
            combined_text += f"[Failed to extract text from {filename}: {str(e)}]\n"
        combined_text += f"\n--- END OF DOCUMENT: {filename} ---\n"
            
    try:
        if not combined_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from the provided PDFs. They might be scanned images.")
            
        # Instantiate agent and analyze
        agent = FraudDetectorAgent()
        result = agent.analyze_bank_statements(combined_text)
        
        try:
            # Broadcast the Audit Log to the relational DB
            metrics = result.get("financial_metrics", {})
            sus_vol = metrics.get("suspicious_volume", 0)
            
            history = AnalysisHistory(
                user_id=current_user.id,
                filenames=", ".join([f.filename for f in files])[:490],
                risk_level=result.get("risk_level", "UNKNOWN"),
                total_volume=int(sus_vol),
                transaction_count=len(result.get("anomalies", []))
            )
            db.add(history)
            db.commit()
            db.refresh(history)
            
            # Massive DB Insert: Log all anomalous transactions
            anomalies = result.get("anomalies", [])
            for txn in anomalies:
                bt = BankTransaction(
                    history_id=history.id,
                    date=txn.get("Date", "Unknown"),
                    narration=txn.get("Narration", "Unknown"),
                    ref_no=txn.get("Ref No.", ""),
                    withdrawal=txn.get("Withdrawal", 0.0),
                    deposit=txn.get("Deposit", 0.0),
                    balance=txn.get("Closing Balance", 0.0),
                    is_anomaly=True,
                    anomaly_reason=txn.get("AI Reasoning", "")
                )
                db.add(bt)
            db.commit()
            
        except Exception as db_err:
            print(f"Non-fatal Database Error recording Audit Log: {db_err}")
            db.rollback()
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class MLPredictionRequest(BaseModel):
    Age: int = Field(..., ge=18, le=120)
    Gross_Income: float = Field(..., ge=0)
    Business_Income_Ratio: float = Field(..., ge=0.0, le=1.0)
    HRA_Claimed: float = Field(..., ge=0)
    Section_80C: float = Field(..., ge=0)
    Section_80G: float = Field(..., ge=0)

# Lazy load model
ml_model = None

def get_ml_model():
    global ml_model
    if ml_model is None:
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'tax_fraud_model.pkl')
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                ml_model = pickle.load(f)
        else:
            raise HTTPException(status_code=503, detail="ML Model not trained yet. Run generate script.")
    return ml_model

@router.post("/ml-predict")
async def predict_ml_fraud(
    data: MLPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Predict tax evasion risk using the Kaggle-style Random Forest model,
    AND permanently log the query in the SQLite Database for MLOps tracking.
    """
    try:
        model = get_ml_model()
        
        # Create DataFrame with exact column names expected by scikit-learn
        input_df = pd.DataFrame([{
            'Age': data.Age,
            'Gross_Income': data.Gross_Income,
            'Business_Income_Ratio': data.Business_Income_Ratio,
            'HRA_Claimed': data.HRA_Claimed,
            'Section_80C': data.Section_80C,
            'Section_80G': data.Section_80G
        }])
        
        # Get prediction and probabilities
        prediction = int(model.predict(input_df)[0])
        probabilities = model.predict_proba(input_df)[0]
        evasion_prob = probabilities[1]
        
        # Get feature importances to show user WHY it flagged them
        feature_names = input_df.columns
        importances = model.feature_importances_
        
        # Top 3 contributing factors
        factors = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:3]
        top_factors = [{"feature": f, "importance": round(imp * 100, 1)} for f, imp in factors]
        
        risk_level = "CRITICAL" if evasion_prob > 0.8 else "HIGH" if evasion_prob > 0.5 else "MEDIUM" if evasion_prob > 0.3 else "LOW"

        # Expand Database Usage: Log this ML prediction
        try:
            log_entry = MLPredictionLog(
                user_id=current_user.id,
                age=data.Age,
                gross_income=data.Gross_Income,
                biz_ratio=data.Business_Income_Ratio,
                hra=data.HRA_Claimed,
                sec80c=data.Section_80C,
                sec80g=data.Section_80G,
                evasion_probability=evasion_prob,
                risk_level=risk_level
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            print("Failed to log ML Prediction to DB:", e)
            db.rollback()

        return {
            "status": "success",
            "prediction": prediction,
            "is_evasion_suspect": bool(prediction == 1),
            "evasion_probability": round(evasion_prob * 100, 2),
            "risk_level": risk_level,
            "top_contributing_factors": top_factors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/document-tax-extraction")
async def extract_tax_documents(
    files: List[UploadFile] = File(...),
    passwords: str = Form(None)
) -> Dict[str, Any]:
    """
    Ingests up to 12 Salary Slips and Bank Statements natively, combining all
    raw PyPDF2 extracts into a massive context block, passing them to the Gemini
    Document Parser agent to dynamically auto-fill the Tax Calculator form natively.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
        
    password_dict = {}
    if passwords:
        try:
            password_dict = json.loads(passwords)
        except:
            pass
            
    required_passwords = []
    incorrect_passwords = []
    file_contents = {}
    
    # Pre-flight parse into memory to avoid blocking streams
    for file in files:
        file_contents[file.filename] = await file.read()
        
    # Validation Pass for Encrypted PDFs
    for filename, contents in file_contents.items():
        if filename.lower().endswith('.pdf'):
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
                if pdf_reader.is_encrypted:
                    pwd = password_dict.get(filename)
                    if not pwd:
                        required_passwords.append(filename)
                    else:
                        success = pdf_reader.decrypt(pwd)
                        if not success:
                            incorrect_passwords.append(filename)
            except Exception as e:
                pwd = password_dict.get(filename)
                if not pwd:
                    required_passwords.append(filename)
                else:
                    incorrect_passwords.append(filename)
                    
    if required_passwords or incorrect_passwords:
        return {
            "error": True,
            "requires_password": True,
            "required_files": required_passwords,
            "incorrect_files": incorrect_passwords,
            "message": "One or more documents are locked. Please provide valid passwords for the specific files below."
        }

    try:
        combined_text = ""
        
        for filename, content in file_contents.items():
            combined_text += f"\n\n--- UPLOADED DOCUMENT: {filename} ---\n"
            
            if filename.lower().endswith(".pdf"):
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                    if pdf_reader.is_encrypted:
                        pdf_reader.decrypt(password_dict.get(filename))
                        
                    for page in pdf_reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            combined_text += extracted + "\n"
                except Exception as pdf_err:
                    combined_text += f"[Failed to parse PDF: {pdf_err}]"
            elif filename.lower().endswith((".csv", ".txt")):
                combined_text += content.decode("utf-8", errors="ignore")
            elif filename.lower().endswith((".xlsx", ".xls")):
                try:
                    df = pd.read_excel(io.BytesIO(content))
                    combined_text += df.to_csv(index=False)
                except:
                    combined_text += "[Failed to extract exact tabular string from Excel chunk]"
            else:
                combined_text += "[Unsupported File Format Skipped]"
                
        # Send huge chunk to dedicated parsing layer
        agent = DocumentTaxParserAgent()
        extraction_result = agent.parse_documents(combined_text)
        
        if extraction_result.get("error"):
             raise HTTPException(status_code=500, detail=extraction_result["message"])
             
        return {
            "status": "success",
            "extracted_data": extraction_result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to auto-extract tax documents: {str(e)}")

@router.post("/analyze-spending")
async def analyze_spending(
    files: List[UploadFile] = File(...),
    passwords: str = Form(None),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Smart Spend Analyzer: Accepts bank statement PDFs/Excel,
    extracts all transactions, and categorizes them using ML + LLM.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    
    password_dict = {}
    if passwords:
        try:
            password_dict = json.loads(passwords)
        except:
            pass
    
    # Check for encrypted PDFs
    required_passwords = []
    incorrect_passwords = []
    file_contents = {}
    
    for file in files:
        file_contents[file.filename] = await file.read()
    
    for filename, contents in file_contents.items():
        if filename.lower().endswith('.pdf'):
            try:
                reader = PyPDF2.PdfReader(io.BytesIO(contents))
                if reader.is_encrypted:
                    pwd = password_dict.get(filename)
                    if not pwd:
                        required_passwords.append(filename)
                    else:
                        if not reader.decrypt(pwd):
                            incorrect_passwords.append(filename)
            except:
                pwd = password_dict.get(filename)
                if not pwd:
                    required_passwords.append(filename)
                else:
                    incorrect_passwords.append(filename)
    
    if required_passwords or incorrect_passwords:
        return {
            "error": True,
            "requires_password": True,
            "required_files": required_passwords,
            "incorrect_files": incorrect_passwords,
            "message": "One or more documents are locked. Please provide passwords."
        }
    
    try:
        agent = SpendAnalyzerAgent()
        all_transactions = pd.DataFrame()
        
        for filename, contents in file_contents.items():
            if filename.lower().endswith('.pdf'):
                pwd = password_dict.get(filename)
                txn_df = agent.extract_transactions_from_pdf(contents, pwd)
                all_transactions = pd.concat([all_transactions, txn_df], ignore_index=True)
            elif filename.lower().endswith(('.csv', '.xlsx', '.xls')):
                if filename.lower().endswith('.csv'):
                    txn_df = pd.read_csv(io.BytesIO(contents))
                else:
                    txn_df = pd.read_excel(io.BytesIO(contents))
                # Normalize columns
                col_map = {}
                for col in txn_df.columns:
                    cl = col.lower()
                    if 'desc' in cl or 'narr' in cl or 'particular' in cl:
                        col_map[col] = 'description'
                    elif 'amount' in cl or 'debit' in cl or 'credit' in cl:
                        col_map[col] = 'amount'
                    elif 'date' in cl:
                        col_map[col] = 'date'
                txn_df = txn_df.rename(columns=col_map)
                if 'description' in txn_df.columns:
                    all_transactions = pd.concat([all_transactions, txn_df], ignore_index=True)
        
        if all_transactions.empty:
            raise HTTPException(status_code=400, detail="Could not extract any transactions from the uploaded files.")
        
        result = agent.categorize_transactions(all_transactions)
        return {"status": "success", **result}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spend analysis failed: {str(e)}")
