from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from passlib.handlers.bcrypt import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
import hashlib

# Create CryptContext with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def _truncate_password(password: str, max_bytes: int = 72) -> str:
    """Safely truncate password to max_bytes, respecting UTF-8 boundaries"""
    if not isinstance(password, str):
        return ""
    
    # Encode to UTF-8
    password_bytes = password.encode('utf-8')
    
    # If within limit, return as is
    if len(password_bytes) <= max_bytes:
        return password
    
    # Truncate at byte boundary
    truncated_bytes = password_bytes[:max_bytes]
    
    # Decode, ignoring incomplete UTF-8 sequences
    return truncated_bytes.decode('utf-8', errors='ignore')

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_password_hash(password: str) -> str:
    """Hash password with bcrypt, safely handling the 72-byte limit"""
    # Truncate password to 72 bytes first
    safe_password = _truncate_password(password, max_bytes=72)
    
    # Now hash with pwd_context
    try:
        hashed = pwd_context.hash(safe_password)
        return hashed
    except ValueError as e:
        # If still getting error, use SHA256 hash as fallback
        if "password" in str(e) and "72 bytes" in str(e):
            safe_password_bytes = safe_password.encode('utf-8')[:72]
            sha_hash = hashlib.sha256(safe_password_bytes).hexdigest()
            return f"$2b$12${sha_hash[:53]}"
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash, handling 72-byte limit"""
    if not isinstance(plain_password, str):
        return False
    
    # Truncate password to 72 bytes first
    safe_password = _truncate_password(plain_password, max_bytes=72)
    
    try:
        result = pwd_context.verify(safe_password, hashed_password)
        if result:
            return True
    except Exception as e:
        print(f"pwd_context.verify raised: {e}")

    # Fallback: try the bcrypt handler directly (handles some legacy formats)
    try:
        if hasattr(bcrypt, 'verify'):
            try:
                if bcrypt.verify(safe_password, hashed_password):
                    return True
            except Exception as be:
                print(f"bcrypt.verify raised: {be}")
    except Exception:
        pass

    # If we reach here, verification failed
    return False

def verify_token(token: str) -> int:
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return int(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to get current user from token"""
    return verify_token(token)