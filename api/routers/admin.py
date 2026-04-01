from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from api.database import get_db
from api.models import User, AnalysisHistory, MLPredictionLog
import subprocess
import os
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.utils.auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/admin", tags=["Admin"])
security = HTTPBearer()

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        is_admin: bool = payload.get("is_admin", False)
        
        if email is None or not is_admin:
            raise HTTPException(status_code=403, detail="Not enough privileges")
            
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Not enough privileges")
            
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


@router.get("/users")
def get_all_users(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    # Return everything except hashed_password
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "is_admin": u.is_admin,
            "is_blocked": u.is_blocked,
            "created_at": u.created_at
        } for u in users
    ]

@router.put("/users/{user_id}/block")
def toggle_block_user(user_id: int, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot block another admin user")
        
    user.is_blocked = not user.is_blocked
    db.commit()
    
    return {
        "message": f"User {'blocked' if user.is_blocked else 'unblocked'} successfully",
        "is_blocked": user.is_blocked
    }

@router.delete("/users/{user_id}")
def delete_user(user_id: int, current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot delete an admin user")
        
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.get("/audit-logs")
def get_audit_logs(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    logs = db.query(AnalysisHistory).order_by(AnalysisHistory.created_at.desc()).limit(150).all()
    
    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        result.append({
            "id": log.id,
            "user_email": user.email if user else "Deleted User",
            "filenames": log.filenames,
            "risk_level": log.risk_level,
            "total_volume": log.total_volume,
            "transaction_count": log.transaction_count,
            "created_at": log.created_at
        })
    return result

@router.get("/ml-logs")
def get_ml_prediction_logs(
    limit: int = 100,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        logs = db.query(MLPredictionLog).order_by(MLPredictionLog.created_at.desc()).limit(limit).all()
        return [
            {
                "id": l.id,
                "user_id": l.user_id,
                "age": l.age,
                "gross_income": l.gross_income,
                "biz_ratio": l.biz_ratio,
                "risk_level": l.risk_level,
                "evasion_probability": round(l.evasion_probability * 100, 2),
                "timestamp": l.created_at.isoformat() if l.created_at else None
            } for l in logs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retrain-ml")
def trigger_ml_retraining(current_admin: User = Depends(get_current_admin)):
    """
    Subprocess execution of the Scikit-Learn Random Forest Generator script.
    Allows Admins to dynamically retrain the offline weights.
    """
    try:
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scripts', 'train_bank_fraud_model.py')
        result = subprocess.run(["python3", script_path], capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"error": True, "message": "ML Training Failed", "output": e.stdout + e.stderr}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
