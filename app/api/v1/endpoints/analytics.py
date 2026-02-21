from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.receipe import Recipe
from app.models.game import Game
from app.models.activity import ActivityLog
from app.core import security
from app.schemas.recipe import RecipeOut

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(security.get_current_user) 
):
    # 1. TOP CARDS (Counts + Growth Logic)
    total_recipes = db.query(Recipe).count()
    total_users = db.query(User).count()
    total_games = db.query(Game).count()

    # Calculate "Growth %" (Simple logic: Users joined in last 30 days)
    last_month = datetime.utcnow() - timedelta(days=30)
    new_users = db.query(User).filter(User.joined_at >= last_month).count()
    
    # Avoid division by zero
    previous_users = total_users - new_users
    user_growth_pct = round((new_users / previous_users * 100), 1) if previous_users > 0 else 100

    previous_recipes = total_recipes - db.query(Recipe).filter(Recipe.created_at >= last_month).count()
    recipe_growth_pct = round((new_users / previous_recipes * 100), 1) if previous_recipes > 0 else 100
    
    previous_games = total_games - db.query(Game).filter(Game.created_at >= last_month).count()
    game_growth_pct = round((new_users / previous_games * 100), 1) if previous_games > 0 else 100

    # 2. RECENT ACTIVITY FEED
    activities = db.query(ActivityLog)\
        .order_by(ActivityLog.timestamp.desc())\
        .limit(5)\
        .all()
    
    recent_activity_data = []
    for log in activities:
        recent_activity_data.append({
            "message": f"User '{log.user.full_name}' {log.action} {log.target}",
            "time": log.timestamp.strftime("%H:%M") # Or "5 min ago" logic
        })

    # 3. USER GROWTH CHART (Jan - Dec)
    # This SQL query groups users by month number
    # Format: [(1, 50), (2, 35)...] where 1=Jan, 50=Count
    stats = db.query(
        extract('month', User.joined_at).label('month'), 
        func.count(User.id).label('count')
    ).group_by('month').all()

    # Initialize 12 months with 0
    chart_data = [0] * 12 
    for month_num, count in stats:
        # month_num is 1-12, array index is 0-11
        chart_data[int(month_num) - 1] = count

    # 4. TOP PERFORMING RECIPES (Table)
    top_recipes = db.query(Recipe)\
        .order_by(Recipe.views_count.desc())\
        .limit(5)\
        .all()

    top_recipes_data = []
    for r in top_recipes:
        top_recipes_data.append({
            "id": r.id,
            "name": r.title,
            "views": r.views_count,
            "favorites": r.favorites_count,
            # If you add Reviews later, calculate average rating here
            "rating": 4.5, 
            "completions": r.favorites_count # Using favorites as proxy for completions
        })

    # FINAL JSON RESPONSE
    return {
        "cards": {
            "total_recipes": total_recipes,
            "total_users": total_users,
            "total_games": total_games,
            "user_growth_pct": user_growth_pct,
            "recipe_growth_pct": recipe_growth_pct,
            "game_growth_pct": game_growth_pct
        },
        "recent_activity": recent_activity_data,
        "user_growth_chart": chart_data, # [10, 20, 5, ...]
        "top_recipes": top_recipes_data
    }
# analytics
# Helper function to calculate growth
def calculate_growth(db: Session, model, date_column):
    # 1. Get Total Count
    total_count = db.query(model).count()
    
    # 2. Get Count from 30 days ago
    last_month_date = datetime.utcnow() - timedelta(days=30)
    
    # Note: This assumes your models have a date column (joined_at, created_at)
    # If a model doesn't have one, return 0 growth
    if not hasattr(model, date_column):
        return total_count, 0.0

    previous_count = db.query(model).filter(getattr(model, date_column) < last_month_date).count()

    if previous_count == 0:
        growth = 100.0 if total_count > 0 else 0.0
    else:
        growth = ((total_count - previous_count) / previous_count) * 100
        
    return total_count, round(growth, 1)


@router.get("/page-view", response_model=dict)
def get_analytics_page(db: Session = Depends(get_db)):
    """
    Returns data specifically for the 'Analytics' sidebar page.
    """
    
    # 1. Calculate Stats & Growth
    # Users (uses 'joined_at')
    user_count, user_growth = calculate_growth(db, User, "joined_at")
    
    # Recipes (uses 'created_at' - ensure your Recipe model has this, otherwise add it)
    recipe_count, recipe_growth = calculate_growth(db, Recipe, "created_at")
    
    # Games (Assuming Game model doesn't store created_at, we might mock this or add the column)
    game_count = db.query(Game).count()
    game_growth = 0.0 # Placeholder if no date column exists

    # 2. Get Most Popular Recipes
    # Ordered by views_count (Descending)
    popular_recipes = db.query(Recipe)\
        .order_by(Recipe.views_count.desc())\
        .limit(10)\
        .all()

    # 3. Construct JSON
    return {
        "stats": {
            "recipes": {
                "total": recipe_count,
                "growth": recipe_growth,
                "label": "Up from last month" if recipe_growth >= 0 else "Down from last month"
            },
            "users": {
                "total": user_count,
                "growth": user_growth,
                "label": "Up from last month" if user_growth >= 0 else "Down from last month"
            },
            "games": {
                "total": game_count,
                "growth": game_growth,
                "label": "Up from last month"
            }
        },
        "popular_recipes": [RecipeOut.model_validate(r) for r in popular_recipes]
    }