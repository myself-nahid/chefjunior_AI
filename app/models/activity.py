from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String) # e.g., "completed recipe", "added recipe", "joined"
    target = Column(String) # e.g., "Spaghetti Aglio", "New User"
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("app.models.user.User")