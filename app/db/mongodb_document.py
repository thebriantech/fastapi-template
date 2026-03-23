"""
Async MongoDB document backed by Motor.
"""
from __future__ import annotations
import traceback
from typing import Any, List, Optional

from app.db.base_document import BaseDocument
from app.db.registry import get_manager

try:
    from pymongo import ASCENDING, DESCENDING
    from bson import ObjectId
except ImportError:
    pass


def _clean(doc: dict) -> dict:
    """Remove MongoDB internal _id field."""
    if isinstance(doc, dict):
        doc.pop("_id", None)
    return doc


class MongoDBDocument(BaseDocument):
    _collection_name: str = ""
    _database_name: str = ""
    _manager_alias: str = "default"

    @classmethod
    def _col(cls):
        mgr = get_manager(cls._manager_alias)
        return mgr.get_collection(cls._collection_name, cls._database_name or None)

    @classmethod
    async def insert_one(cls, document: dict) -> dict:
        try:
            await cls._col().insert_one(document)
            return {"status": True}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def insert_many(cls, documents: List[dict]) -> dict:
        if not documents:
            return {"status": True, "inserted": 0}
        try:
            result = await cls._col().insert_many(documents)
            return {"status": True, "inserted": len(result.inserted_ids)}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def find_one(cls, query: dict, **kwargs: Any) -> dict:
        try:
            doc = await cls._col().find_one(query)
            if doc:
                return {"status": True, "result": _clean(doc)}
            return {"status": False, "result": []}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def find(cls, query: dict, order_by: Optional[str] = None,
                   skip: int = 0, limit: int = 0, **kwargs: Any) -> dict:
        try:
            cursor = cls._col().find(query, {"_id": 0})
            if order_by:
                cursor = cursor.sort(order_by)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            docs = await cursor.to_list(length=None)
            return {"status": True, "result": docs}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def count(cls, query: Optional[dict] = None) -> dict:
        try:
            n = await cls._col().count_documents(query or {})
            return {"status": True, "count": n}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def get_all(cls, order_by: Optional[str] = None, **kwargs: Any) -> dict:
        return await cls.find({}, order_by=order_by)

    @classmethod
    async def update_one(cls, query: dict, update: dict, **kwargs: Any) -> dict:
        try:
            result = await cls._col().update_one(query, {"$set": update})
            return {"status": True, "affected": result.modified_count}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def update_many(cls, query: dict, update: dict, **kwargs: Any) -> dict:
        try:
            result = await cls._col().update_many(query, {"$set": update})
            return {"status": True, "affected": result.modified_count}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def upsert_one(cls, query: dict, document: dict) -> dict:
        try:
            result = await cls._col().update_one(query, {"$set": document}, upsert=True)
            return {"status": True, "affected": result.modified_count, "upserted": result.upserted_id is not None}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def delete_one(cls, query: dict) -> dict:
        try:
            result = await cls._col().delete_one(query)
            return {"status": True, "deleted": result.deleted_count}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def delete_many(cls, query: dict) -> dict:
        try:
            result = await cls._col().delete_many(query)
            return {"status": True, "deleted": result.deleted_count}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def execute_raw(cls, operation: Any, params: Optional[dict] = None, **kwargs: Any) -> dict:
        """Execute a raw pipeline (list) or command (dict) via motor."""
        try:
            db = get_manager(cls._manager_alias).get_database()
            if isinstance(operation, list):
                cursor = cls._col().aggregate(operation)
                result = await cursor.to_list(length=None)
                return {"status": True, "result": result}
            elif isinstance(operation, dict):
                result = await db.command(operation)
                return {"status": True, "result": result}
            return {"status": False, "error": "operation must be a list (pipeline) or dict (command)"}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def ensure_indexes(cls) -> None:
        """Override in subclass to create indexes. Called at startup (sync context)."""

    @classmethod
    def create_index(cls, keys, **kwargs):
        """Sync index creation via the sync registry manager for startup use."""
        pass
