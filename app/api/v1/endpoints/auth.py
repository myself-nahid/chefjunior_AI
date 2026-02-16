from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import random
import string

from app.database import get_db
from app.core import security
from app.core.config import settings
from app.crud import crud_user
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import (
    UserCreate, 
    User as UserSchema, 
    ForgotPasswordRequest, 
    ResetPasswordRequest, 
    VerifyOTPRequest,
    ChangePasswordRequest
)

router = APIRouter()

# --- 1. SIGN UP ---
@router.post("/signup", response_model=UserSchema)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    db_user = crud_user.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    new_user = crud_user.create_user(db, user=user)
    return new_user


# --- 2. LOGIN (Form Data - For Swagger UI) ---
@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = crud_user.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- 2b. LOGIN (JSON Body - For Flutter App) ---
class LoginRequest(UserCreate):
    pass # Re-using UserCreate because it has email & password

@router.post("/login-json", response_model=Token)
def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = crud_user.authenticate_user(db, email=login_data.email, password=login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- 3. FORGOT PASSWORD (Generate OTP) ---
@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Generates a 6-digit OTP and 'sends' it (prints to console for testing).
    """
    user = crud_user.get_user_by_email(db, email=request.email)
    if not user:
        # We return 200 even if user doesn't exist to prevent email enumeration attacks
        return {"message": "If this email exists, an OTP has been sent."}

    # Generate 6-digit OTP
    otp = "".join(random.choices(string.digits, k=6))
    
    # Set expiration (e.g., 10 minutes from now)
    expiration = datetime.utcnow() + timedelta(minutes=10)

    # Save to DB
    user.reset_otp = otp
    user.reset_otp_expires = expiration
    db.commit()

    # --- MOCK EMAIL SENDING ---
    print(f"========================================")
    print(f"PASSWORD RESET OTP FOR {user.email}: {otp}")
    print(f"========================================")
    # In production, use an email service here (e.g., SendGrid, AWS SES)

    return {"message": "OTP sent successfully"}


# --- 4. VERIFY OTP ---
@router.post("/verify-otp")
def verify_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Verifies if the OTP is correct and not expired.
    """
    user = crud_user.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.reset_otp or user.reset_otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if user.reset_otp_expires and datetime.utcnow() > user.reset_otp_expires:
        raise HTTPException(status_code=400, detail="OTP has expired")

    return {"message": "OTP verified successfully"}


# --- 5. RESET PASSWORD ---
@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Sets a new password using the OTP.
    """
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = crud_user.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify OTP again to be safe
    if user.reset_otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    if user.reset_otp_expires and datetime.utcnow() > user.reset_otp_expires:
        raise HTTPException(status_code=400, detail="OTP has expired")

    # Update Password
    user.hashed_password = security.get_password_hash(request.new_password)
    
    # Clear OTP
    user.reset_otp = None
    user.reset_otp_expires = None
    
    db.commit()

    return {"message": "Password reset successfully. Please login."}


# --- 6. CHANGE PASSWORD (Authenticated) ---
@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """
    Allows a logged-in user to change their password.
    """
    user = crud_user.get_user_by_id(db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify current password
    if not security.verify_password(request.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    # Update to new password
    user.hashed_password = security.get_password_hash(request.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


# --- 7. GET CURRENT USER ---
@router.get("/me", response_model=UserSchema)
def read_users_me(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    user = crud_user.get_user_by_id(db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user