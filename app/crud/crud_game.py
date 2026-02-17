from sqlalchemy.orm import Session
from app.models.game import Game, UserGameProgress
from app.models.user import User
from app.schemas.game import GameCreate

def get_games(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    games = db.query(Game).offset(skip).limit(limit).all()
    
    # Fetch user's progress to mark games as completed
    progress_map = {
        p.game_id: p.is_completed 
        for p in db.query(UserGameProgress).filter(UserGameProgress.user_id == user_id).all()
    }

    # Attach 'is_completed' status dynamically (not stored in Game model)
    for game in games:
        game.is_completed = progress_map.get(game.id, False)
        
    return games

def get_game(db: Session, game_id: int):
    return db.query(Game).filter(Game.id == game_id).first()

def create_game(db: Session, game: GameCreate):
    game_data_dict = game.game_data
    if hasattr(game_data_dict, "model_dump"):
        game_data_dict = game_data_dict.model_dump()
    elif hasattr(game_data_dict, "dict"):
        game_data_dict = game_data_dict.dict()

    db_game = Game(
        title=game.title,
        description=game.description,
        type=game.type,
        difficulty=game.difficulty,
        thumbnail_url=game.thumbnail_url,
        game_data=game_data_dict,  # Use the dictionary version
        xp_reward=game.xp_reward
    )
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game

def record_progress(db: Session, user_id: int, game_id: int, score: int):
    # Check if record exists
    progress = db.query(UserGameProgress).filter(
        UserGameProgress.user_id == user_id,
        UserGameProgress.game_id == game_id
    ).first()

    if not progress:
        progress = UserGameProgress(
            user_id=user_id,
            game_id=game_id,
            is_completed=True,
            score=score
        )
        db.add(progress)
        
        # Update User Total XP / Games Played count
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.games_played += 1
            # user.total_xp += 10 (If you have an XP field)
            
    else:
        # Update score if better
        if score > progress.score:
            progress.score = score
            
    db.commit()
    return progress