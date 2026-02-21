from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True) # e.g. "Word Search - Italian"
    description = Column(Text)
    type = Column(String) # "word_search", "crossword", "image_quiz"
    thumbnail_url = Column(String)
    
    # This stores the specific game configuration
    # For Word Search: {"words": ["Pasta", "Olive", "Onion"]}
    # For Image Quiz: {"questions": [{"image": "url", "answer": "Garlic"}]}
    game_data = Column(JSON) 
    
    difficulty = Column(String) # Easy, Medium, Hard
    xp_reward = Column(Integer, default=10) # Points for winning
    created_at = Column(String) 
    # Relationships
    user_progress = relationship("UserGameProgress", back_populates="game")


class UserGameProgress(Base):
    """Tracks which games a user has completed"""
    __tablename__ = "user_game_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    is_completed = Column(Boolean, default=False)
    score = Column(Integer, default=0)
    
    user = relationship("app.models.user.User", back_populates="game_progress")
    game = relationship("Game", back_populates="user_progress")