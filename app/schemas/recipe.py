from typing import Optional, List
from pydantic import BaseModel
from .ingradient import Ingredient as IngredientSchema

# --- Nested Schemas for Recipe Creation ---

class RecipeIngredientBase(BaseModel):
    ingredient_id: int
    quantity: str # e.g. "100gm"

class RecipeIngredientDetail(BaseModel):
    """Used when reading a recipe to show full ingredient details"""
    quantity: str
    ingredient: IngredientSchema 

    class Config:
        from_attributes = True

# --- Main Recipe Schemas ---

class RecipeBase(BaseModel):
    title: str
    description: Optional[str] = None
    difficulty: str
    cooking_time: str
    servings: int
    image_url: Optional[str] = None
    video_url: Optional[str] = None

class RecipeCreate(RecipeBase):
    # Receives a list of IDs and Quantities
    ingredients: List[RecipeIngredientBase] = []

class Recipe(RecipeBase):
    id: int
    favorites_count: int
    views_count: int
    # Returns the full ingredient object + quantity
    ingredients: List[RecipeIngredientDetail] = []

    class Config:
        from_attributes = True