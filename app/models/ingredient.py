from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base

class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    origin = Column(String, nullable=True)
    type = Column(String, nullable=True)  # Vegetable, Grain, etc.
    description = Column(Text, nullable=True)
    fun_facts = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    
    # Specific Nutrition Fields (from UI)
    protein = Column(String, nullable=True) # e.g., "10g"
    carbohydrates = Column(String, nullable=True)
    fats = Column(String, nullable=True)
    others = Column(String, nullable=True) # Vitamin B12 etc.

    # Relationship back to the association table
    recipe_links = relationship("RecipeIngredient", back_populates="ingredient")