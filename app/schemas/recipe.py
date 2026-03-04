from typing import Optional, List
from pydantic import BaseModel, field_validator
from app.schemas.ingradient import Ingredient

# 1. Create a flattened schema (Ingredient attributes + Quantity)
class IngredientWithQuantity(Ingredient):
    quantity: str

class RecipeIngredientBase(BaseModel):
    ingredient_id: int
    quantity: str 

class RecipeBase(BaseModel):
    title: str
    description: Optional[str] = None
    difficulty: str
    # Fixed typo in your previous code (type -> category to match DB)
    type : Optional[str] = "Fast Food"
    cooking_time: str
    servings: int
    image_url: Optional[str] = None
    video_url: Optional[str] = None

class RecipeCreate(RecipeBase):
    class IngredientLink(BaseModel):
        ingredient_id: int
        quantity: str
    
    ingredients: List[IngredientLink] = []

class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    cooking_time: Optional[str] = None
    servings: Optional[int] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    
    class IngredientLink(BaseModel):
        ingredient_id: int
        quantity: str

    ingredients: Optional[List[IngredientLink]] = None

class RecipeOut(RecipeBase):
    id: int
    # Change the list type to use the flattened schema
    ingredients: List[IngredientWithQuantity] = []
    
    is_favorite: bool = False 
    views_count: int = 0
    favorites_count: int = 0

    # Validator to flatten the structure
    @field_validator('ingredients', mode='before')
    @classmethod
    def flatten_ingredients(cls, v):
        # 'v' is the list of RecipeIngredient association objects from SQL
        flattened_list = []
        for link in v:
            if link.ingredient:
                # Extract the ingredient data
                ing_data = link.ingredient.__dict__.copy()
                # Inject the quantity from the relationship table
                ing_data['quantity'] = link.quantity
                flattened_list.append(ing_data)
        return flattened_list

    class Config:
        from_attributes = True

Recipe = RecipeOut

class RecipeExploreOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    servings: int = 1
    difficulty: str
    cooking_time: str
    category: Optional[str] = "Fast Food"
    image_url: Optional[str] = None
    is_favorite: bool = False
    favorites_count: int = 0 

    class Config:
        from_attributes = True

class RecipePagination(BaseModel):
    total: int
    page: int
    size: int
    items: List[RecipeExploreOut]