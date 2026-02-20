from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, recipes, chat, ingredients, analytics, games, notifications

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
api_router.include_router(ingredients.router, prefix="/ingredients", tags=["ingredients"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(games.router, prefix="/games", tags=["games"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])