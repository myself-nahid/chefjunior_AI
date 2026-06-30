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
from app.schemas.token import Token, RefreshTokenRequest 
from app.schemas.auth import LoginRequest
from app.schemas.user import (
    UserCreate, 
    User as UserSchema, 
    ForgotPasswordRequest, 
    ResetPasswordRequest, 
    VerifyOTPRequest,
    ChangePasswordRequest,
    SendVerificationOTPRequest,
    VerifyEmailRequest,
    ResendVerificationOTPRequest
)
from app.models.user import User
from app.crud import crud_notification
from app.schemas.notification import NotificationCreate
from jose import jwt, JWTError

# Email Logic Import (Try/Except allows code to run even if haven't created the email util yet)
try:
    from app.core.email_utils import send_otp_email, send_email_verification_otp
except ImportError:
    send_otp_email = None
    send_email_verification_otp = None

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

# HELPER: VERIFICATION OTP SENDER
def deliver_verification_otp(email: str, otp: str):
    """
    Attempts to send Verification OTP via Email using the Welcome template. 
    """
    email_sent = False
    
    if send_email_verification_otp and os.getenv("EMAIL_PASSWORD"):
        print(f"📧 Attempting to send verification email to {email}...")
        email_sent = send_email_verification_otp(email, otp)
    
    # Fallback to Console (For Development/Testing)
    if not email_sent:
        print(f"\n" + "="*50)
        print(f"⚠️  EMAIL SIMULATION (SMTP not configured or failed)")
        print(f"📨  To: {email}")
        print(f"🔑  VERIFICATION OTP CODE: {otp}")
        print(f"="*50 + "\n")

# 1. SIGN UP (Step 1: Create Inactive User & Send OTP)
@router.post("/signup")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user. The account will be inactive until the email is verified with an OTP.
    """
    db_user = crud_user.get_user_by_email(db, email=user.email)
    
    if db_user:
        if db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered and verified."
            )
        # If user exists but is NOT active, we just generate a new OTP and resend it
    else:
        # Create new user
        db_user = crud_user.create_user(db, user=user)
        # Force the user to be inactive initially
        db_user.is_active = False 

    # Generate 6-digit OTP
    otp = "".join(random.choices(string.digits, k=6))
    expiration = datetime.utcnow() + timedelta(minutes=10)

    # Save OTP to database (reusing the reset_otp columns for simplicity)
    db_user.reset_otp = otp
    db_user.reset_otp_expires = expiration
    db.commit()

    # Send the OTP
    deliver_verification_otp(db_user.email, otp)

    return {
        "message": "Account created. Please check your email for the verification OTP.",
        "email": db_user.email
    }


# 2. VERIFY EMAIL (Step 2: Activate the Account)
@router.post("/verify-email")
def verify_email(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    user = crud_user.get_user_by_email(db, email=request.email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if getattr(user, 'is_email_verified', False) and user.is_active:
        return {"message": "Account is already verified. You can log in."}

    # Check if OTP matches
    if not user.reset_otp or user.reset_otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check if OTP expired
    if user.reset_otp_expires and datetime.utcnow() > user.reset_otp_expires:
        raise HTTPException(status_code=400, detail="OTP has expired.")

    # Success! Activate the user AND verify email
    user.is_active = True
    user.is_email_verified = True  # <--- THIS WAS THE MISSING LINE!
    
    user.reset_otp = None
    user.reset_otp_expires = None
    
    # Forces SQLAlchemy to track the update and save
    db.add(user)      
    db.commit()       
    db.refresh(user)  

    return {"message": "Email verified successfully! You can now log in."}

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
         raise HTTPException(status_code=400, detail="User not found")
    
    # Check if email is verified
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. Check your inbox for the verification code."
        )

    # Generate Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )

    refresh_token = security.create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_role": "admin" if user.is_superuser else "user"
    }

@router.post("/refresh", response_model=Token)
def refresh_access_token(
    request: Annotated[RefreshTokenRequest, Body()], 
    db: Session = Depends(get_db)
):
    """
    Takes a valid refresh token and returns a new access token (and new refresh token).
    """
    try:
        # Decode the refresh token
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token. Please log in again.")
    
    # Verify User still exists and is active
    user = crud_user.get_user_by_id(db, user_id=int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Generate NEW tokens
    new_access_token = security.create_access_token(subject=user.id)
    new_refresh_token = security.create_refresh_token(subject=user.id) # Issue a rotating refresh token
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
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
    
    # Check if email is verified
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. Check your inbox for the verification code."
        )

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


# EMAIL VERIFICATION SYSTEM (2-minute OTP)
# ==========================================

# 1. SEND EMAIL VERIFICATION OTP
@router.post("/send-verification-otp")
def send_verification_otp(
    request: Annotated[SendVerificationOTPRequest, Body()],
    db: Session = Depends(get_db)
):
    """
    Sends an email verification OTP to the user's email address.
    Used during signup to verify email ownership.
    OTP expires in 2 minutes.
    """
    user = crud_user.get_user_by_email(db, email=request.email)
    
    # Security: Always return success to prevent email enumeration
    if not user:
        return {"message": "If this email exists, a verification OTP has been sent."}

    # Generate 6-digit OTP
    otp = "".join(random.choices(string.digits, k=6))
    
    # Set expiration (2 minutes from now)
    expiration = datetime.utcnow() + timedelta(minutes=2)

    # Save to DB
    user.email_verification_otp = otp
    user.email_verification_otp_expires = expiration
    db.commit()

    # Send the OTP
    email_sent = False
    if send_otp_email:
        from app.core.email_utils import send_email_verification_otp
        try:
            email_sent = send_email_verification_otp(user.email, otp)
        except ImportError:
            pass
    
    # Fallback to Console
    if not email_sent:
        print(f"\n" + "="*50)
        print(f"⚠️  EMAIL SIMULATION (SMTP not configured or failed)")
        print(f"📨  To: {user.email}")
        print(f"🔑  VERIFICATION OTP CODE: {otp}")
        print(f"⏰  Expires in: 2 minutes")
        print(f"="*50 + "\n")

    return {"message": "Verification OTP sent successfully"}

# 2. RESEND EMAIL VERIFICATION OTP
@router.post("/resend-verification-otp")
def resend_verification_otp(
    request: Annotated[ResendVerificationOTPRequest, Body()],
    db: Session = Depends(get_db)
):
    """
    Resends a new email verification OTP to the user's email.
    Invalidates the previous OTP and resets the 2-minute timer.
    """
    user = crud_user.get_user_by_email(db, email=request.email)
    
    # Security: Always return success to prevent email enumeration
    if not user:
        return {"message": "OTP resent successfully"}

    # 1. Generate a NEW 6-digit OTP
    new_otp = "".join(random.choices(string.digits, k=6))
    
    # 2. Reset expiration (2 minutes from NOW)
    expiration = datetime.utcnow() + timedelta(minutes=2)

    # 3. Update Database
    user.email_verification_otp = new_otp
    user.email_verification_otp_expires = expiration
    db.commit()

    # 4. Send the new OTP
    email_sent = False
    if send_otp_email:
        from app.core.email_utils import send_email_verification_otp
        try:
            email_sent = send_email_verification_otp(user.email, new_otp)
        except ImportError:
            pass
    
    # Fallback to Console
    if not email_sent:
        print(f"\n" + "="*50)
        print(f"⚠️  EMAIL SIMULATION (SMTP not configured or failed)")
        print(f"📨  To: {user.email}")
        print(f"🔑  VERIFICATION OTP CODE: {new_otp}")
        print(f"⏰  Expires in: 2 minutes")
        print(f"="*50 + "\n")

    return {"message": "OTP resent successfully"}

# # 3. VERIFY EMAIL WITH OTP
# @router.post("/verify-email")
# def verify_email(
#     request: Annotated[VerifyEmailRequest, Body()],
#     db: Session = Depends(get_db)
# ):
#     """
#     Verifies the user's email using the OTP code.
#     Once verified, the user can access all features.
#     """
#     user = crud_user.get_user_by_email(db, email=request.email)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Check OTP matches
#     if not user.email_verification_otp or user.email_verification_otp != request.otp:
#         raise HTTPException(status_code=400, detail="Invalid OTP")

#     # Check expiration
#     if user.email_verification_otp_expires and datetime.utcnow() > user.email_verification_otp_expires:
#         raise HTTPException(status_code=400, detail="OTP has expired")

#     # Mark email as verified
#     user.is_email_verified = True
#     user.email_verification_otp = None
#     user.email_verification_otp_expires = None
#     db.commit()

#     return {"message": "Email verified successfully. You can now login."}

# 4. CHECK EMAIL VERIFICATION STATUS
@router.get("/email-verification-status")
def check_email_verification_status(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Check if an email is verified.
    Useful for frontend to determine if user needs to complete email verification.
    """
    user = crud_user.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": user.email,
        "is_email_verified": user.is_email_verified,
        "full_name": user.full_name
    }


# CHANGE PASSWORD (Authenticated flow)>
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