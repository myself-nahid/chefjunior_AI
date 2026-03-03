from typing import Optional
from pydantic import BaseModel
from fastapi import Form

class IngredientBase(BaseModel):
    name: str
    origin: Optional[str] = None
    type: Optional[str] = None
    history: Optional[str] = None
    fun_facts: Optional[str] = None
    image_url: Optional[str] = None
    protein: Optional[str] = None
    carbohydrates: Optional[str] = None
    fun_facts: Optional[str] = None
    fats: Optional[str] = None
    others: Optional[str] = None

class IngredientCreate(IngredientBase):
    pass

class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    origin: Optional[str] = None
    type: Optional[str] = None
    history: Optional[str] = None
    protein: Optional[str] = None
    carbohydrates: Optional[str] = None
    fun_facts: Optional[str] = None
    fats: Optional[str] = None
    others: Optional[str] = None
    image_url: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        name: str = Form(None),
        origin: str = Form(None),
        type: str = Form(None),
        history: str = Form(None),
        protein: str = Form(None),
        carbohydrates: str = Form(None),
        fun_facts: str = Form(None),
        fats: str = Form(None),
        others: str = Form(None),
        image_url: str = Form(None),
    ):
        return cls(
            name=name,
            origin=origin,
            type=type,
            history=history,
            protein=protein,
            carbohydrates=carbohydrates,
            fun_facts=fun_facts,
            fats=fats,
            others=others,
            image_url=image_url,
        )

class Ingredient(IngredientBase):
    id: int

    class Config:
        from_attributes = True