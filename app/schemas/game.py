from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field

# --- WORD SEARCH DATA MODEL ---
class WordSearchData(BaseModel):
    mode: Literal["word_search"]
    grid_size: int = 10
    words: List[str]

# --- CROSSWORD DATA MODEL ---
class CrosswordWord(BaseModel):
    answer: str
    hint_image: str
    start_x: int
    start_y: int
    direction: Literal["horizontal", "vertical"]

class CrosswordData(BaseModel):
    mode: Literal["crossword"]
    grid_cols: int = 8
    grid_rows: int = 8
    words: List[CrosswordWord]

# --- MAIN GAME SCHEMAS ---

class GameBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str  # "word_search" or "crossword"
    difficulty: str # "Easy", "Medium"
    thumbnail_url: Optional[str] = None
    xp_reward: int = 10

class GameCreate(GameBase):
    # This magic line allows either format
    game_data: Union[WordSearchData, CrosswordData, dict] 

class GameOut(GameBase):
    id: int
    game_data: Union[WordSearchData, CrosswordData, dict]
    is_completed: bool = False

    class Config:
        from_attributes = True

class GameResult(BaseModel):
    is_win: bool
    score: int