from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.receipe import Recipe
from typing import Dict, Any

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns data for the admin dashboard cards and charts.
    """
    # 1. Top Cards Counts
    total_users = db.query(User).count()
    total_recipes = db.query(Recipe).count()
    # Assuming games logic is implemented or mocked for now
    total_games = db.query(func.sum(User.games_played)).scalar() or 0

    # 2. Top Performing Recipes (by favorites or views)
    top_recipes = db.query(Recipe).order_by(Recipe.favorites_count.desc()).limit(5).all()
    top_recipes_data = [
        {
            "id": r.id,
            "title": r.title,
            "views": r.views_count,
            "favorites": r.favorites_count
        } for r in top_recipes
    ]

    # 3. User Growth (Mocked logic for chart - typically grouping by month)
    # In a real app, you would perform a date_trunc query on 'joined_at'
    user_growth = {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "data": [10, 25, 40, 45, 80, total_users] 
    }

    return {
        "total_users": total_users,
        "total_recipes": total_recipes,
        "total_games": int(total_games),
        "top_recipes": top_recipes_data,
        "user_growth": user_growth
    }