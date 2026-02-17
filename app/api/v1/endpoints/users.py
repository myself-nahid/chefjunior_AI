from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import shutil
import os
import uuid

from app.database import get_db
from app.schemas.user import User as UserSchema, UserUpdateProfile, UserUpdate
from app.core import security
from app.crud import crud_user
from app.models.game import UserGameProgress

router = APIRouter()

# ==================================================================
# 1. STATIC ROUTES (MUST BE AT THE TOP)
# ==================================================================

@router.get("/me", response_model=UserSchema)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """
    Get the current logged-in user's profile.
    This MUST be defined before /{user_id} to avoid conflicts.
    """
    db_user = crud_user.get_user_by_id(db, user_id=current_user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate Stats
    games_won = db.query(UserGameProgress).filter(
        UserGameProgress.user_id == current_user_id,
        UserGameProgress.is_completed == True
    ).count()

    recipes_done = len(db_user.favorite_recipes) 

    # Attach to schema
    user_out = UserSchema.model_validate(db_user)
    user_out.games_won_count = games_won
    user_out.recipes_completed_count = recipes_done
    
    return user_out


@router.patch("/me", response_model=UserSchema)
def update_my_profile(
    profile_update: UserUpdateProfile,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """Update profile info (Name, Language)"""
    db_user = crud_user.get_user_by_id(db, user_id=current_user_id)
    
    if profile_update.full_name:
        db_user.full_name = profile_update.full_name
    if profile_update.language:
        db_user.language = profile_update.language
        
    db.commit()
    db.refresh(db_user)
    
    # Return with stats
    user_out = UserSchema.model_validate(db_user)
    # (Simple logic for stats to avoid errors)
    user_out.recipes_completed_count = len(db_user.favorite_recipes)
    return user_out


@router.post("/me/avatar", response_model=UserSchema)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """Upload a profile picture"""
    db_user = crud_user.get_user_by_id(db, user_id=current_user_id)
    
    # Generate filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"user_{current_user_id}_{uuid.uuid4().hex}.{file_extension}"
    file_location = f"static/avatars/{unique_filename}"
    
    # Save file
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not upload image")

    # Save URL
    base_url = "http://127.0.0.1:8000"
    db_user.avatar_url = f"{base_url}/{file_location}"
    
    db.commit()
    db.refresh(db_user)
    
    return UserSchema.model_validate(db_user)


# ==================================================================
# 2. DYNAMIC ROUTES (MUST BE AT THE BOTTOM)
# ==================================================================

@router.get("/", response_model=List[UserSchema])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users (Admin)"""
    return crud_user.get_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserSchema)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Get specific user by ID"""
    db_user = crud_user.get_user_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.patch("/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """Admin: Block/Unblock user"""
    db_user = crud_user.get_user_by_id(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.is_active = not db_user.is_active
    db.commit()
    return {"message": "User status updated", "is_active": db_user.is_active}


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """Delete a user"""
    # Add check for admin/self here
    db_user = crud_user.delete_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}