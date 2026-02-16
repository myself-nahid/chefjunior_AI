from sqlalchemy.orm import Session
from app.models.receipe import Recipe, RecipeIngredient
from app.schemas.recipe import RecipeCreate

def get_recipes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Recipe).offset(skip).limit(limit).all()

def get_recipe(db: Session, recipe_id: int):
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()

def create_recipe(db: Session, recipe: RecipeCreate):
    # 1. Extract ingredients data
    ingredients_data = recipe.ingredients
    
    # 2. Create the Recipe object (without ingredients first)
    db_recipe = Recipe(
        title=recipe.title,
        description=recipe.description,
        difficulty=recipe.difficulty,
        cooking_time=recipe.cooking_time,
        servings=recipe.servings,
        image_url=recipe.image_url,
        video_url=recipe.video_url
    )
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)

    # 3. Create the relations in RecipeIngredient table
    for item in ingredients_data:
        db_relation = RecipeIngredient(
            recipe_id=db_recipe.id,
            ingredient_id=item.ingredient_id,
            quantity=item.quantity
        )
        db.add(db_relation)
    
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

def delete_recipe(db: Session, recipe_id: int):
    obj = db.query(Recipe).get(recipe_id)
    if obj:
        db.delete(obj)
        db.commit()
    return obj