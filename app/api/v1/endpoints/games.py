from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.game import GameOut, GameCreate, GameResult
from app.crud import crud_game
from app.core import security

router = APIRouter()

@router.get("/", response_model=List[GameOut])
def read_games(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """
    Get list of all games with completion status for current user.
    """
    return crud_game.get_games(db, user_id=current_user_id, skip=skip, limit=limit)

@router.post("/", response_model=GameOut)
def create_game(
    game: GameCreate, 
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """Admin endpoint to create a new game configuration"""
    # In real app: Add admin check here
    return crud_game.create_game(db, game=game)

@router.get("/{game_id}", response_model=GameOut)
def play_game(
    game_id: int, 
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """Get specific game details (words list, grid, etc.)"""
    game = crud_game.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    # Just setting default for schema
    game.is_completed = False 
    return game

@router.post("/{game_id}/complete")
def complete_game(
    game_id: int,
    result: GameResult,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """
    Call this when user finishes the game.
    Updates 'Games Played' count and marks level as done.
    """
    if result.is_win:
        crud_game.record_progress(db, user_id=current_user_id, game_id=game_id, score=result.score)
        return {"message": "Progress saved", "xp_earned": 10}
    else:
        return {"message": "Game over, no points awarded"}