from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4 # Para generar UUIDs si es necesario y para tipado
from datetime import datetime

# --- Theme Models ---
class ThemeBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, examples=["Fútbol Clásico"])

class ThemeCreate(ThemeBase):
    pass

class Theme(ThemeBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True # Permite que Pydantic lea datos desde atributos de objeto (ORM mode)

# --- Category Models ---
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, examples=["Nombre Jugador"])
    theme_id: UUID
    order: Optional[int] = 0

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True # Permite que Pydantic lea datos desde atributos de objeto (ORM mode)