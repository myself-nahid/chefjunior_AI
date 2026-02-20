from sqlalchemy.orm import Session
from app.models.activity import ActivityLog

def log_activity(db: Session, user_id: int, action: str, target: str):
    log = ActivityLog(user_id=user_id, action=action, target=target)
    db.add(log)
    db.commit()