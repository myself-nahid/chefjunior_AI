from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.schemas.recipe import Recipe, RecipeOut, RecipeCreate, RecipeExploreOut, RecipePagination, RecipeUpdate
from app.crud import crud_recipe
from app.core import security
from app.models.user import User
router = APIRouter()

# 1. GET ALL RECIPES (Home Page & Search)
@router.get("/", response_model=List[dict])
def read_recipes(
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user),
):
    recipes = crud_recipe.get_recipes(db, skip=skip, limit=limit, search=q)

    user = db.query(User).filter(User.id == current_user_id).first()
    user_fav_ids = {r.id for r in user.favorite_recipes} if user else set()

    results = []
    for r in recipes:
        r_out = RecipeOut.model_validate(r)
        r_out.is_favorite = r.id in user_fav_ids

        results.append(
            r_out.model_dump(exclude={"ingredients", "is_favorite", "favorites_count", "views_count", "video_url"})
        )

    return results

@router.get("/search", response_model=List[dict])
def read_recipes(
    skip: int = 0,
    limit: int = 100,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user),
):
    recipes = crud_recipe.get_recipes(db, skip=skip, limit=limit, search=q)

    user = db.query(User).filter(User.id == current_user_id).first()
    user_fav_ids = {r.id for r in user.favorite_recipes} if user else set()

    results = []
    for r in recipes:
        r_out = RecipeOut.model_validate(r)
        r_out.is_favorite = r.id in user_fav_ids

        results.append(
            r_out.model_dump(exclude={"ingredients", "is_favorite", "favorites_count", "views_count", "video_url"})
        )

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
            description=r.description,
            difficulty=r.difficulty,
            cooking_time=r.cooking_time,
            servings=r.servings,
            # category=r.category,
            image_url=r.image_url,
            is_favorite=(r.id in user_fav_ids) 
        )
        results.append(r_out)
        
    return results

# GET TOP PERFORMING RECIPES (Based on Favorites)
@router.get("/popular", response_model=RecipePagination) 
def get_popular_recipes(
    skip: int = 0,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    # 1. Fetch Items AND Total Count
    recipes, total_count = crud_recipe.get_top_recipes(db, skip=skip, limit=limit)
    
    # 2. Calculate Favorites logic
    user = db.query(User).filter(User.id == current_user_id).first()
    user_fav_ids = [r.id for r in user.favorite_recipes] if user else []

    # 3. Process Items
    results = []
    for r in recipes:
        r_out = RecipeExploreOut(
            id=r.id,
            title=r.title,
            difficulty=r.difficulty,
            cooking_time=r.cooking_time,
            # category=r.category,
            image_url=r.image_url,
            is_favorite=(r.id in user_fav_ids),
            favorites_count=r.favorites_count
        )
        results.append(r_out)
        
    return {
        "total": total_count,
        "page": (skip // limit) + 1,
        "size": limit,
        "items": results
    }

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

# --- UPDATE RECIPE ---
@router.put("/{recipe_id}", response_model=RecipeOut)
def update_recipe(
    recipe_id: int,
    recipe_data: RecipeUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):
    """
    Update a recipe.
    To update ingredients, send the FULL list of ingredients. 
    The old list will be replaced by the new one.
    """
    # Optional: Add admin check logic here
    
    updated_recipe = crud_recipe.update_recipe(db, recipe_id, recipe_data)
    if not updated_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
        
    # Re-validate to ensure output schema logic (is_favorite, etc.) runs
    # For admin panel, is_favorite is usually false or irrelevant
    r_out = RecipeOut.model_validate(updated_recipe)
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

# Add these imports at the top of recipes.py
from pydantic import BaseModel, Field
from sqlalchemy import func
from app.models.review import Review # Import the new model

# NEW SCHEMAS FOR REVIEWS
class ReviewCreate(BaseModel):
    # Field(ge=1, le=5) ensures the user can only send numbers from 1 to 5
    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5")

class RecipeRatingOut(BaseModel):
    average_rating: float
    total_reviews: int

from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.receipe import Recipe

# POST: ADD / UPDATE REVIEW
@router.post("/{recipe_id}/reviews", response_model=RecipeRatingOut)
def submit_recipe_review(
    recipe_id: int,
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user)
):

    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if this user already rated
    existing_review = db.query(Review).filter(
        Review.recipe_id == recipe_id,
        Review.user_id == current_user_id
    ).first()

    if existing_review:
        existing_review.rating = review.rating
    else:
        new_review = Review(
            recipe_id=recipe_id,
            user_id=current_user_id,
            rating=review.rating
        )
        db.add(new_review)

    db.commit()

    # Calculate rating from ALL USERS
    avg_rating, total_reviews = db.query(
        func.avg(Review.rating),
        func.count(Review.id)
    ).filter(
        Review.recipe_id == recipe_id
    ).first()

    recipe.average_rating = float(avg_rating or 0)
    recipe.total_reviews = total_reviews or 0

    db.commit()
    db.refresh(recipe)

    return {
        "average_rating": round(recipe.average_rating, 1),
        "total_reviews": recipe.total_reviews
    }

# GET: FETCH RECIPE RATING
@router.get("/{recipe_id}/reviews", response_model=RecipeRatingOut)
def get_recipe_reviews(recipe_id: int, db: Session = Depends(get_db)):

    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    return {
        "average_rating": round(recipe.average_rating or 0, 1),
        "total_reviews": recipe.total_reviews or 0
    }