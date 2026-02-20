from typing import List, Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core import security
from app.crud import crud_notification
from app.schemas.notification import NotificationOut

router = APIRouter()

@router.get("/", response_model=dict)
def read_notifications(
    skip: int = 0,
    limit: int = 10,
    filter: Literal["all", "unread"] = "all",
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """
    Get notifications for the Dashboard.
    Supports pagination (skip/limit) and tabs (filter).
    """
    items, total = crud_notification.get_notifications(
        db, 
        user_id=current_user_id, 
        skip=skip, 
        limit=limit, 
        filter_type=filter
    )
    
    # Return count for pagination logic on frontend
    return {
        "total": total,
        "page": (skip // limit) + 1,
        "items": [NotificationOut.model_validate(item) for item in items]
    }

@router.patch("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """Call this when user clicks 'Mark all as read'"""
    crud_notification.mark_all_as_read(db, user_id=current_user_id)
    return {"message": "All notifications marked as read"}

@router.patch("/{notification_id}/read")
def mark_one_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """Call this when user clicks a specific notification"""
    crud_notification.mark_one_as_read(db, notification_id, current_user_id)
    return {"message": "Notification marked as read"}