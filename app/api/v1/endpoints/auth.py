from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from pydantic.v1 import BaseModel, EmailStr
from sqlalchemy.orm import Session
import random
import string
import os
from typing import Annotated
from app.database import get_db
from app.core import security
from app.core.config import settings
from app.crud import crud_user
from app.schemas.token import Token
from app.schemas.auth import LoginRequest
from app.schemas.user import (
    UserCreate, 
    User as UserSchema, 
    ForgotPasswordRequest, 
    ResetPasswordRequest, 
    VerifyOTPRequest,
    ChangePasswordRequest
)
from app.models.user import User
from app.crud import crud_notification
from app.schemas.notification import NotificationCreate

# Email Logic Import (Try/Except allows code to run even if haven't created the email util yet)
try:
    from app.core.email_utils import send_otp_email
except ImportError:
    send_otp_email = None

router = APIRouter()

# HELPER: OTP SENDER
def deliver_otp(email: str, otp: str):
    """
    Attempts to send OTP via Email. 
    Falls back to Console Print if Email fails or isn't configured.
    """
    email_sent = False
    
    # Try sending real email if utility exists and config is present
    if send_otp_email and os.getenv("EMAIL_PASSWORD"):
        print(f"📧 Attempting to send email to {email}...")
        email_sent = send_otp_email(email, otp)
    
    # Fallback to Console (For Development/Testing)
    if not email_sent:
        print(f"\n" + "="*50)
        print(f"⚠️  EMAIL SIMULATION (SMTP not configured or failed)")
        print(f"📨  To: {email}")
        print(f"🔑  OTP CODE: {otp}")
        print(f"="*50 + "\n")

# 1. SIGN UP
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
    # 1. Find all Superusers (Admins)
    admins = db.query(User).filter(User.is_superuser == True).all()
    
    # 2. Create a notification for each Admin
    for admin in admins:
        notification_data = NotificationCreate(
            recipient_id=admin.id,
            title="New user joined",
            message=f"{new_user.full_name} has joined",
            type="info"
        )
        crud_notification.create_notification(db, notification_data)
    return new_user

# This system i used in previous but for company policy i used to now json payload instead of this form data.
'''
# 2. LOGIN (Swagger UI / Form Data)
# @router.post("/login", response_model=Token)
# def login_access_token(
#     db: Session = Depends(get_db),
#     form_data: OAuth2PasswordRequestForm = Depends()
# ):
#     """
#     Standard OAuth2 login for Swagger UI documentation.
#     """
#     user = crud_user.authenticate_user(db, email=form_data.username, password=form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
    
#     if not user.is_active:
#          raise HTTPException(status_code=400, detail="Inactive user")

#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = security.create_access_token(
#         subject=user.id, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "user_role": "admin" if user.is_superuser else "user"}
'''

# 2. LOGIN (JSON - For Flutter/React)
@router.post("/login", response_model=Token)
def login(
    # Annotated + Body to strictly define this as JSON Body
    login_data: Annotated[LoginRequest, Body()],
    db: Session = Depends(get_db)
):
    """
    Login using JSON payload:
    {
      "email": "user@example.com",
      "password": "secretpassword"
    }
    """
    # Authenticate
    user = crud_user.authenticate_user(db, email=login_data.email, password=login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
         raise HTTPException(status_code=400, detail="Inactive user")

    # Generate Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": user.id,
        "user_role": "admin" if user.is_superuser else "user"
    }


# 3. LOGIN (Form Data - For Swagger UI Support)
@router.post("/login/access-token", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, required for the Swagger UI 'Authorize' button.
    """
    user = crud_user.authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
         raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# 4. FORGOT PASSWORD (OTP Generation)
@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Generates a 6-digit OTP and sends it via Email (or Console).
    """
    user = crud_user.get_user_by_email(db, email=request.email)
    
    # Security: Always return success to prevent email enumeration
    if not user:
        return {"message": "If this email exists, an OTP has been sent."}

    # Generate 6-digit OTP
    otp = "".join(random.choices(string.digits, k=6))
    
    # Set expiration (10 minutes from now)
    expiration = datetime.utcnow() + timedelta(minutes=10)

    # Save to DB
    user.reset_otp = otp
    user.reset_otp_expires = expiration
    db.commit()

    # Send the OTP
    deliver_otp(user.email, otp)

    return {"message": "OTP sent successfully"}

@router.post("/resend-otp")
def resend_otp(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Resends a new OTP to the user's email.
    Invalidates the previous OTP and resets the 10-minute timer.
    """
    user = crud_user.get_user_by_email(db, email=request.email)
    
    # Security: Always return success to prevent email enumeration
    if not user:
        return {"message": "OTP resent successfully"}

    # 1. Generate a NEW 6-digit OTP
    new_otp = "".join(random.choices(string.digits, k=6))
    
    # 2. Reset expiration (10 minutes from NOW)
    expiration = datetime.utcnow() + timedelta(minutes=10)

    # 3. Update Database
    user.reset_otp = new_otp
    user.reset_otp_expires = expiration
    db.commit()

    # 4. Send the new OTP
    deliver_otp(user.email, new_otp)

    return {"message": "OTP resent successfully"}

# 5. VERIFY OTP
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

    # Check matches
    if not user.reset_otp or user.reset_otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check expiration
    if user.reset_otp_expires and datetime.utcnow() > user.reset_otp_expires:
        raise HTTPException(status_code=400, detail="OTP has expired")

    return {"message": "OTP verified successfully"}


# 6. RESET PASSWORD (Unauthenticated flow)
@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Sets a new password using a valid OTP.
    """
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = crud_user.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify OTP again (Critical Security Step)
    if user.reset_otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    if user.reset_otp_expires and datetime.utcnow() > user.reset_otp_expires:
        raise HTTPException(status_code=400, detail="OTP has expired")

    # Update Password
    user.hashed_password = security.get_password_hash(request.new_password)
    
    # Clear OTP so it can't be reused
    user.reset_otp = None
    user.reset_otp_expires = None
    
    db.commit()

    return {"message": "Password reset successfully. Please login."}


# 7. CHANGE PASSWORD (Authenticated flow)
@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """
    Allows a logged-in user to change their password from settings.
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

@router.post("/logout")
def logout(current_user_id: int = Depends(security.get_current_user)):
    """
    Log out the current user. 
    In a stateless JWT setup, this primarily serves as a confirmation 
    and a place to hook in analytics or token blacklisting in the future.
    """
    return {"message": "Successfully logged out"}

# 8. GET CURRENT USER PROFILE
@router.get("/me", response_model=UserSchema)
def read_users_me(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    user = crud_user.get_user_by_id(db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# 9. Delete Account (Authenticated)
@router.delete("/delete-account")
def delete_account(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    user = crud_user.get_user_by_id(db, user_id=current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    crud_user.delete_user(db, user_id=current_user_id)
    return {"message": "Account deleted successfully"}