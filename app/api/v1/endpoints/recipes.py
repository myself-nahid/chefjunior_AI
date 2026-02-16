from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import recipe as recipe_schema
from app.crud import crud_recipe

router = APIRouter()

@router.get("/", response_model=List[recipe_schema.Recipe])
def read_recipes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_recipe.get_recipes(db, skip=skip, limit=limit)

@router.post("/", response_model=recipe_schema.Recipe)
def create_recipe(recipe: recipe_schema.RecipeCreate, db: Session = Depends(get_db)):
    return crud_recipe.create_recipe(db, recipe=recipe)

@router.delete("/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    return crud_recipe.delete_recipe(db, recipe_id)