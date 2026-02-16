from sqlalchemy import Boolean, Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Analytics
    recipes_tried = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Password Reset Fields
    reset_otp = Column(String, nullable=True) # Stores the 6-digit code
    reset_otp_expires = Column(DateTime, nullable=True)