from email.mime import image
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.ingradient import Ingredient, IngredientCreate, IngredientUpdate
from app.crud import crud_ingredient
from fastapi import Form, Depends
from sqlalchemy.orm import Session
from fastapi import Form, File, UploadFile, Depends
from sqlalchemy.orm import Session
import shutil
import os
import uuid

router = APIRouter()

@router.get("/", response_model=List[Ingredient])
def read_ingredients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all ingredients with pagination"""
    return crud_ingredient.get_ingredients(db, skip=skip, limit=limit)

@router.get("/{ingredient_id}", response_model=Ingredient)
def read_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """Get a specific ingredient by ID"""
    db_ingredient = crud_ingredient.get_ingredient(db, ingredient_id=ingredient_id)
    if not db_ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return db_ingredient

@router.post("/", response_model=Ingredient)
def create_ingredient(
    name: str = Form(...),
    origin: str = Form(...),
    type: str = Form(...),
    history: str = Form(...),
    protein: str = Form(...),
    carbohydrates: str = Form(...),
    fun_facts: str = Form(...),
    fats: str = Form(...),
    others: str = Form(...),
    image: str = Form(...),
    db: Session = Depends(get_db)
):
    # """Create ingredient with image upload (Production Ready)"""

    # upload_dir = "uploads"
    # os.makedirs(upload_dir, exist_ok=True)

    # file_extension = image.filename.split(".")[-1]
    # unique_filename = f"{uuid.uuid4()}.{file_extension}"

    # file_path = os.path.join(upload_dir, unique_filename)

    # with open(file_path, "wb") as buffer:
    #     shutil.copyfileobj(image.file, buffer)

    # image_url = f"/uploads/{unique_filename}"

    ingredient_data = IngredientCreate(
        name=name,
        origin=origin,
        type=type,
        history=history,
        protein=protein,
        carbohydrates=carbohydrates,
        fun_facts=fun_facts,
        fats=fats,
        others=others,
        image_url=image
    )

    return crud_ingredient.create_ingredient(db, ingredient=ingredient_data)

@router.put("/{ingredient_id}", response_model=Ingredient)
def update_ingredient(
    ingredient_id: int,
    ingredient: IngredientUpdate = Depends(IngredientUpdate.as_form),
    db: Session = Depends(get_db),
):
    """Update an existing ingredient using form data"""

    db_ingredient = crud_ingredient.update_ingredient(
        db=db,
        ingredient_id=ingredient_id,
        ingredient=ingredient
    )

    if not db_ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    return db_ingredient

@router.delete("/{ingredient_id}")
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    """Delete an ingredient"""
    db_ingredient = crud_ingredient.delete_ingredient(db, ingredient_id)
    if not db_ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return {"message": "Ingredient deleted successfully"}
