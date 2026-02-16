from typing import Optional
from pydantic import BaseModel

class IngredientBase(BaseModel):
    name: str
    origin: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    fun_facts: Optional[str] = None
    image_url: Optional[str] = None
    # Updated nutrition fields
    protein: Optional[str] = None
    carbohydrates: Optional[str] = None
    fats: Optional[str] = None
    others: Optional[str] = None

class IngredientCreate(IngredientBase):
    pass

class IngredientUpdate(IngredientBase):
    name: Optional[str] = None

class Ingredient(IngredientBase):
    id: int

    class Config:
        from_attributes = True