"""
Abstract async document CRUD interface.
All methods are async — use this base class with async-native drivers (motor, asyncpg, aiomysql).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Optional


class BaseDocument(ABC):
    @classmethod
    @abstractmethod
    async def insert_one(cls, document: dict) -> dict: ...

    @classmethod
    @abstractmethod
    async def insert_many(cls, documents: List[dict]) -> dict: ...

    @classmethod
    @abstractmethod
    async def find_one(cls, query: dict, **kwargs: Any) -> dict: ...

    @classmethod
    @abstractmethod
    async def find(cls, query: dict, order_by: Optional[str] = None,
                   skip: int = 0, limit: int = 0, **kwargs: Any) -> dict: ...

    @classmethod
    @abstractmethod
    async def count(cls, query: Optional[dict] = None) -> dict: ...

    @classmethod
    @abstractmethod
    async def get_all(cls, order_by: Optional[str] = None, **kwargs: Any) -> dict: ...

    @classmethod
    @abstractmethod
    async def update_one(cls, query: dict, update: dict, **kwargs: Any) -> dict: ...

    @classmethod
    @abstractmethod
    async def update_many(cls, query: dict, update: dict, **kwargs: Any) -> dict: ...

    @classmethod
    @abstractmethod
    async def upsert_one(cls, query: dict, document: dict) -> dict: ...

    @classmethod
    @abstractmethod
    async def delete_one(cls, query: dict) -> dict: ...

    @classmethod
    @abstractmethod
    async def delete_many(cls, query: dict) -> dict: ...

    @classmethod
    @abstractmethod
    async def execute_raw(cls, operation: Any, params: Optional[dict] = None, **kwargs: Any) -> dict: ...

    @classmethod
    def ensure_indexes(cls) -> None:
        """Override to create indexes/tables at startup. Sync is fine here."""
