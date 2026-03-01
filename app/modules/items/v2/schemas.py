"""
Items v2 schemas.

New in v2:
  - ``category`` field on create / response
  - ``tags`` list on create / response
  - ``is_active`` flag (defaults True on create, visible in response)
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    name: str
    description: str
    price: float
    quantity: int
    category: str = Field(default="general", description="Item category")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    is_active: bool = Field(default=True, description="Whether the item is active")


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ItemResponse(BaseModel):
    item_id: str
    name: str
    description: str
    price: float
    quantity: int
    category: str
    tags: List[str] = []
    is_active: bool = True
