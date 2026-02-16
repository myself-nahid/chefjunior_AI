from typing import Optional
from pydantic import BaseModel, EmailStr, Field

# --- Base Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None
    full_name: Optional[str] = None

class User(UserBase):
    id: int
    recipes_tried: int
    games_played: int

    class Config:
        from_attributes = True

# --- Password Reset Schemas ---

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)