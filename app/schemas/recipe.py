from typing import Optional, List
from pydantic import BaseModel
from .ingradient import Ingredient as IngredientSchema
from app.schemas.ingradient import Ingredient

class RecipeIngredientBase(BaseModel):
    ingredient_id: int
    quantity: str # e.g. "100gm"

class RecipeIngredientDetail(BaseModel):
    """Used when reading a recipe to show full ingredient details"""
    quantity: str
    ingredient: Optional[Ingredient] = None 

    class Config:
        from_attributes = True

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

class RecipeOut(RecipeBase):
    id: int
    # This ensures we send the ingredients AND their specific quantities
    ingredients: List[RecipeIngredientDetail] = []
    
    # Computed field to tell frontend if the heart should be red or empty
    is_favorite: bool = False 

    class Config:
        from_attributes = True