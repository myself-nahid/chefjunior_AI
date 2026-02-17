from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from app.models.user import favorites_table

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String)  # Easy, Medium, Hard
    cooking_time = Column(String) # e.g. "2 hrs"
    servings = Column(Integer)
    image_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    
    created_at = Column(String, default=datetime.utcnow().isoformat) # For analytics
    favorites_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)

    # Relationship to RecipeIngredient
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    favorited_by = relationship("User", secondary=favorites_table, back_populates="favorite_recipes")

class RecipeIngredient(Base):
    """Association table to store quantity of an ingredient in a recipe"""
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"))
    quantity = Column(String)  # e.g., "100gm", "1 Cup"

    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_links")