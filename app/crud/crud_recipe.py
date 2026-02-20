from sqlalchemy.orm import Session
from fastapi import HTTPException 
from app.models.receipe import Recipe, RecipeIngredient
from app.models.ingredient import Ingredient 
from app.models.user import User
from app.schemas.recipe import RecipeCreate, RecipeUpdate

def get_recipes(db: Session, skip: int = 0, limit: int = 100, search: str = None):
    query = db.query(Recipe)
    
    if search:
        query = query.filter(Recipe.title.ilike(f"%{search}%"))
        
    return query.offset(skip).limit(limit).all()

def get_recipe(db: Session, recipe_id: int):
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()

def create_recipe(db: Session, recipe: RecipeCreate):
    # 1. Validate that all Ingredient IDs exist
    for item in recipe.ingredients:
        ingredient_exists = db.query(Ingredient).filter(Ingredient.id == item.ingredient_id).first()
        if not ingredient_exists:
            raise HTTPException(
                status_code=404, 
                detail=f"Ingredient with ID {item.ingredient_id} not found. Please create it first."
            )

    # 2. Create the Recipe object
    db_recipe = Recipe(
        title=recipe.title,
        description=recipe.description,
        difficulty=recipe.difficulty,
        cooking_time=recipe.cooking_time,
        servings=recipe.servings,
        # category=recipe.category,
        image_url=recipe.image_url,
        video_url=recipe.video_url
    )
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)

    # 3. Create the relations in RecipeIngredient table
    for item in recipe.ingredients:
        db_relation = RecipeIngredient(
            recipe_id=db_recipe.id,
            ingredient_id=item.ingredient_id,
            quantity=item.quantity
        )
        db.add(db_relation)
    
    db.commit()
    
    # 4. Refresh to load the relationships for Pydantic
    db.refresh(db_recipe)
    return db_recipe 

def update_recipe(db: Session, recipe_id: int, recipe_update: RecipeUpdate):
    # 1. Fetch existing recipe
    db_recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not db_recipe:
        return None

    # 2. Update Basic Fields (Title, Description, etc.)
    update_data = recipe_update.model_dump(exclude_unset=True)
    
    # Separate ingredients data from basic data
    ingredients_data = update_data.pop("ingredients", None)

    for key, value in update_data.items():
        setattr(db_recipe, key, value)

    # 3. Handle Ingredients Update (The tricky part)
    if ingredients_data is not None:
        # A. Clear existing ingredients for this recipe
        db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe_id).delete()
        
        # B. Add the new list
        for item in ingredients_data:
            # Check if ingredient exists (Safety check)
            ing_exists = db.query(Ingredient).filter(Ingredient.id == item['ingredient_id']).first()
            if ing_exists:
                new_relation = RecipeIngredient(
                    recipe_id=recipe_id,
                    ingredient_id=item['ingredient_id'],
                    quantity=item['quantity']
                )
                db.add(new_relation)

    db.commit()
    db.refresh(db_recipe)
    return db_recipe

def delete_recipe(db: Session, recipe_id: int):
    obj = db.query(Recipe).get(recipe_id)
    if obj:
        db.delete(obj)
        db.commit()
    return obj

def toggle_favorite(db: Session, user_id: int, recipe_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    
    if not user or not recipe:
        return None

    if recipe in user.favorite_recipes:
        # User is removing favorite (Un-like)
        user.favorite_recipes.remove(recipe)
        
        # --- FIX: Decrement Count ---
        if recipe.favorites_count > 0:
            recipe.favorites_count -= 1
        is_fav = False
    else:
        # User is adding favorite (Like)
        user.favorite_recipes.append(recipe)
        
        # --- FIX: Increment Count ---
        recipe.favorites_count += 1
        is_fav = True
        
    db.commit()
    db.refresh(recipe) # Ensure we get the latest count
    return is_fav

def get_user_favorites(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    return user.favorite_recipes if user else []