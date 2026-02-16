from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import User, UserCreate, UserUpdate
from app.core import security
from app.crud import crud_user

router = APIRouter()


@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users with pagination"""
    return crud_user.get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    db_user = crud_user.get_user_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """Update user information (only own profile or admin)"""
    if current_user_id != user_id:
        # Check if current user is admin
        current_user = db.query(crud_user.get_user_by_id.__globals__['User']).filter(
            crud_user.get_user_by_id.__globals__['User'].id == current_user_id
        ).first()
        if not current_user or not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user"
            )
    
    db_user = crud_user.update_user(db, user_id=user_id, user_update=user)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """Delete a user (only own profile or admin)"""
    if current_user_id != user_id:
        # Check if current user is admin
        current_user = db.query(crud_user.get_user_by_id.__globals__['User']).filter(
            crud_user.get_user_by_id.__globals__['User'].id == current_user_id
        ).first()
        if not current_user or not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this user"
            )
    
    db_user = crud_user.delete_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@router.patch("/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user) # In real app, check if admin
):
    db_user = crud_user.get_user_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Flip the status
    db_user.is_active = not db_user.is_active
    db.commit()
    db.refresh(db_user)
    return {"message": "User status updated", "is_active": db_user.is_active}