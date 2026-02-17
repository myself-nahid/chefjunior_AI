from sqlalchemy import Boolean, Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

# Association Table for Favorites
favorites_table = Table(
    "favorites",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("recipe_id", Integer, ForeignKey("recipes.id"), primary_key=True),
)

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

    # Favorites Relationship
    favorite_recipes = relationship("Recipe", secondary=favorites_table, back_populates="favorited_by")