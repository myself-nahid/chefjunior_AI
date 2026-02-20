from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate

def create_notification(db: Session, notification: NotificationCreate):
    db_obj = Notification(**notification.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_notifications(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 10, 
    filter_type: str = "all" # "all" or "unread"
):
    query = db.query(Notification).filter(Notification.recipient_id == user_id)
    
    # Handle the Tabs (All vs Unread)
    if filter_type == "unread":
        query = query.filter(Notification.is_read == False)
        
    # Apply Ordering (Newest first)
    query = query.order_by(Notification.created_at.desc())
    
    # Apply Pagination
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return items, total

def mark_all_as_read(db: Session, user_id: int):
    db.query(Notification).filter(
        Notification.recipient_id == user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()

def mark_one_as_read(db: Session, notification_id: int, user_id: int):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == user_id
    ).first()
    
    if notification:
        notification.is_read = True
        db.commit()
        db.refresh(notification)
    return notification