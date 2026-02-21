from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False

class UserUpdateProfile(BaseModel):
    full_name: Optional[str] = None
    language: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None
    full_name: Optional[str] = None

class AdminProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None

class User(UserBase):
    id: int
    avatar_url: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    recipes_tried: int = 0
    games_played: int = 0
    joined_at: Optional[datetime] = None
    recipes_completed_count: int = 0 
    games_won_count: int = 0

    class Config:
        from_attributes = True

class UserAdminList(BaseModel):
    id: int
    name: Optional[str] = "Unknown" # Maps to full_name
    email: EmailStr
    recipes_tried: int      # From DB column
    favorites_count: int    # Calculated field
    joined_date: str        # Formatted date string
    is_active: bool         # For the Toggle Switch

    class Config:
        from_attributes = True

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