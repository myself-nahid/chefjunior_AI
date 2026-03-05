from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.database import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    rating = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "recipe_id", name="unique_user_recipe_review"),
    )