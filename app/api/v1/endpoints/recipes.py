from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.schemas.recipe import RecipeOut, RecipeCreate, RecipeExploreOut
from app.crud import crud_recipe
from app.core import security
from app.models.user import User

router = APIRouter()

# 1. GET ALL RECIPES (Home Page & Search)
@router.get("/", response_model=List[RecipeOut])
def read_recipes(
    skip: int = 0, 
    limit: int = 100, 
    q: Optional[str] = None, # Search query (e.g., "Pizza")
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    recipes = crud_recipe.get_recipes(db, skip=skip, limit=limit, search=q)
    
    # Check which ones are favorited by the current user
    user = db.query(User).filter(User.id == current_user_id).first()
    user_fav_ids = [r.id for r in user.favorite_recipes] if user else []

    results = []
    for r in recipes:
        # We manually construct the response to inject 'is_favorite'
        r_out = RecipeOut.model_validate(r)
        r_out.is_favorite = r.id in user_fav_ids
        results.append(r_out)
        
    return results

@router.get("/explore", response_model=List[RecipeExploreOut])
def explore_recipes(
    skip: int = 0, 
    limit: int = 100, 
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """
    Get a simplified list of recipes for the Home/Explore feed.
    Excludes ingredients and heavy details.
    """
    # 1. Fetch Recipes
    recipes = crud_recipe.get_recipes(db, skip=skip, limit=limit, search=q)
    
    # 2. Get User Favorites (to mark is_favorite=True/False)
    user = db.query(User).filter(User.id == current_user_id).first()
    user_fav_ids = [r.id for r in user.favorite_recipes] if user else []

    # 3. Map to the simplified schema
    results = []
    for r in recipes:
        # Create the simplified object
        r_out = RecipeExploreOut(
            id=r.id,
            title=r.title,
            difficulty=r.difficulty,
            cooking_time=r.cooking_time,
            # category=r.category,
            image_url=r.image_url,
            is_favorite=(r.id in user_fav_ids) 
        )
        results.append(r_out)
        
    return results

# 2. CREATE RECIPE (Restored Endpoint)
@router.post("/", response_model=RecipeOut)
def create_recipe(
    recipe: RecipeCreate, 
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user) # Secure this endpoint
):
    """
    Create a new recipe.
    """
    new_recipe = crud_recipe.create_recipe(db, recipe=recipe)
    
    # Convert to output schema
    r_out = RecipeOut.model_validate(new_recipe)
    r_out.is_favorite = False # A new recipe is not favorite by default
    
    return r_out


# 3. GET RECIPE DETAILS
@router.get("/{recipe_id}", response_model=RecipeOut)
def read_recipe(
    recipe_id: int, 
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    recipe = crud_recipe.get_recipe(db, recipe_id=recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    recipe.views_count += 1
    db.commit() # Save to database
    db.refresh(recipe) # Refresh to get the new number
    
    user = db.query(User).filter(User.id == current_user_id).first()
    is_fav = recipe in user.favorite_recipes if user else False
    
    r_out = RecipeOut.model_validate(recipe)
    r_out.is_favorite = is_fav
    
    # Ensure the dynamic count is passed to the schema
    r_out.favorites_count = recipe.favorites_count 
    r_out.views_count = recipe.views_count

    return r_out


# 4. TOGGLE FAVORITE (Heart Icon)
@router.post("/{recipe_id}/favorite")
def favorite_recipe(
    recipe_id: int, 
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    is_now_favorite = crud_recipe.toggle_favorite(db, user_id=current_user_id, recipe_id=recipe_id)
    if is_now_favorite is None:
        raise HTTPException(status_code=404, detail="Recipe or User not found")
        
    return {
        "recipe_id": recipe_id, 
        "is_favorite": is_now_favorite, 
        "message": "Favorite status updated"
    }


# 5. GET MY FAVORITES
@router.get("/me/favorites", response_model=List[RecipeOut])
def read_my_favorites(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    recipes = crud_recipe.get_user_favorites(db, user_id=current_user_id)
    
    results = []
    for r in recipes:
        r_out = RecipeOut.model_validate(r)
        r_out.is_favorite = True
        results.append(r_out)
        
    return results


# 6. DELETE RECIPE (Restored Endpoint)
@router.delete("/{recipe_id}")
def delete_recipe(
    recipe_id: int, 
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    # Optional: Add check here to ensure only admin can delete
    deleted_recipe = crud_recipe.delete_recipe(db, recipe_id)
    if not deleted_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"message": "Recipe deleted successfully"}

class ReviewCreate(BaseModel):
    rating: int
    comment: str

@router.post("/{recipe_id}/reviews")
def create_review(
    recipe_id: int,
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    # Logic to save review to database...
    return {"message": "Review added"}