from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id")) # Who gets the notification
    title = Column(String)   # e.g., "New user joined"
    message = Column(String) # e.g., "John Doe has joined"
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Optional: Type of notification (for the icon color/shape)
    # "info", "warning", "success"
    type = Column(String, default="info") 

    recipient = relationship("app.models.user.User", back_populates="notifications")