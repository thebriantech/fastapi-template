from typing import Optional
from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    name: str
    description: str
    price: float
    quantity: int


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None


class ItemResponse(BaseModel):
    item_id: str
    name: str
    description: str
    price: float
    quantity: int
