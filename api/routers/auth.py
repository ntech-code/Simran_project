from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel

from api.database import get_db
from api.models import User, OTP
from api.utils.auth import get_password_hash, verify_password, create_access_token
from api.utils.email import generate_otp, send_otp_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

class SendOTPRequest(BaseModel):
    email: str
    type: str  # "signup" or "reset_password"

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str
    otp: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

class GoogleLoginRequest(BaseModel):
    credential: str

@router.post("/send-otp")
def send_otp(req: SendOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    
    if req.type == "signup" and user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if req.type == "reset_password" and not user:
        raise HTTPException(status_code=404, detail="Email not found")

    otp_code = generate_otp()
    
    # Invalidate older OTPs for this email in this flow
    db.query(OTP).filter(OTP.email == req.email, OTP.type == req.type).delete()
    
    new_otp = OTP(
        email=req.email,
        otp=otp_code,
        type=req.type,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(new_otp)
    db.commit()
    
    success = send_otp_email(req.email, otp_code, req.type)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")
        
    return {"message": "OTP sent successfully"}

@router.post("/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    # Verify OTP
    otp_record = db.query(OTP).filter(
        OTP.email == req.email,
        OTP.type == "signup",
        OTP.otp == req.otp
    ).first()
    
    if not otp_record or otp_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    # Check if user already exists
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Create user
    new_user = User(
        email=req.email,
        name=req.name,
        hashed_password=get_password_hash(req.password)
    )
    db.add(new_user)
    
    # Delete used OTP
    db.delete(otp_record)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    token = create_access_token(data={"sub": new_user.email, "id": new_user.id, "is_admin": new_user.is_admin})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "is_admin": new_user.is_admin
        }
    }

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User is not registered, please sign up.")
        
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Your account is blocked. Contact support.")
        
    token = create_access_token(data={"sub": user.email, "id": user.id, "is_admin": user.is_admin})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_admin": user.is_admin
        }
    }

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    # Verify OTP
    otp_record = db.query(OTP).filter(
        OTP.email == req.email,
        OTP.type == "reset_password",
        OTP.otp == req.otp
    ).first()
    
    if not otp_record or otp_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Your account is blocked. Contact support.")
        
    user.hashed_password = get_password_hash(req.new_password)
    db.delete(otp_record)
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.post("/google-login")
def google_login(req: GoogleLoginRequest, db: Session = Depends(get_db)):
    from jose import jwt
    try:
        # Provide an empty string for the 'key' argument and disable implicit validation of audience/issuer
        payload = jwt.decode(req.credential, "", options={
            "verify_signature": False, 
            "verify_aud": False, 
            "verify_iss": False,
            "verify_exp": False
        })
        email = payload.get("email")
        
        # Extract full name (Google format handles given_name or name)
        name = payload.get("name") or f"{payload.get('given_name', '')} {payload.get('family_name', '')}".strip()
        
        if not email:
            raise ValueError("No email in token")
    except Exception as e:
        print(f"Token Decode Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid Google token")

    user = db.query(User).filter(User.email == email).first()
    if user:
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Your account is blocked. Contact support.")
    else:
        user = User(email=email, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(data={"sub": user.email, "id": user.id, "is_admin": user.is_admin})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_admin": user.is_admin
        }
    }
