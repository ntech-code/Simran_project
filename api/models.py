from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from api.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True) # Nullable for OAuth users if they don't have password
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    audit_logs = relationship("AnalysisHistory", back_populates="user", cascade="all, delete-orphan")

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filenames = Column(String(500), nullable=False)
    risk_level = Column(String(50), nullable=False)
    total_volume = Column(Integer, default=0)
    transaction_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="audit_logs")
    transactions = relationship("BankTransaction", back_populates="history", cascade="all, delete-orphan")

class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    history_id = Column(Integer, ForeignKey("analysis_history.id"))
    date = Column(String(50))
    narration = Column(String(500))
    ref_no = Column(String(100))
    value_date = Column(String(50))
    withdrawal = Column(Float, default=0.0)
    deposit = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    is_anomaly = Column(Boolean, default=False)
    anomaly_reason = Column(String(500), nullable=True)
    
    history = relationship("AnalysisHistory", back_populates="transactions")

class MLPredictionLog(Base):
    __tablename__ = "ml_prediction_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    age = Column(Integer)
    gross_income = Column(Float)
    biz_ratio = Column(Float)
    hra = Column(Float)
    sec80c = Column(Float)
    sec80g = Column(Float)
    evasion_probability = Column(Float)
    risk_level = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    otp = Column(String(6), nullable=False)
    type = Column(String(50), nullable=False) # e.g., "signup" or "reset_password"
    expires_at = Column(DateTime, nullable=False)
