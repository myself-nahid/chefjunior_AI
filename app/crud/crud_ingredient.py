from sqlalchemy.orm import Session
from app.models.ingredient import Ingredient
from app.schemas.ingradient import IngredientCreate, IngredientUpdate


def get_ingredient(db: Session, ingredient_id: int):
    return db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()


def get_ingredients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Ingredient).offset(skip).limit(limit).all()


def create_ingredient(db: Session, ingredient: IngredientCreate):
    db_obj = Ingredient(**ingredient.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_ingredient(db: Session, ingredient_id: int, ingredient: IngredientUpdate):
    db_obj = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if db_obj:
        update_data = ingredient.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
    return db_obj


def delete_ingredient(db: Session, ingredient_id: int):
    obj = db.query(Ingredient).get(ingredient_id)
    if obj:
        db.delete(obj)
        db.commit()
    return obj
