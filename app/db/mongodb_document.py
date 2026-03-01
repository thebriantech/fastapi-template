"""
MongoDB-specific implementation of ``BaseDocument``.

Models that store data in MongoDB inherit from this class.  All the
pymongo-specific logic lives here — the rest of the app never sees it.

Usage:
    from app.db.mongodb_document import MongoDBDocument

    class Item(MongoDBDocument):
        _collection_name = "items"

        @classmethod
        def ensure_indexes(cls):
            cls.create_index([("item_id", 1)], unique=True)

        # ── Custom queries (escape hatch) ───────────────────
        @classmethod
        def find_expensive(cls, min_price: float):
            '''Example: a domain-specific query that goes beyond CRUD.'''
            return cls.execute_raw(
                [
                    {"$match": {"price": {"$gte": min_price}}},
                    {"$sort": {"price": -1}},
                ]
            )

        @classmethod
        def stats_by_status(cls):
            '''Example: aggregation pipeline as a custom query.'''
            return cls.execute_raw(
                [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
            )
"""

from __future__ import annotations

import traceback
from typing import Any, List, Optional

from pymongo.collection import Collection

from app.db.base_document import BaseDocument
from app.db.registry import get_manager


class MongoDBDocument(BaseDocument):
    """
    Concrete ``BaseDocument`` backed by MongoDB (pymongo).

    Class attributes (set in each subclass):
        _collection_name  (str, required)  – MongoDB collection name
        _database_name    (str, optional)  – overrides the default database
        _manager_alias    (str, optional)  – registry key if you run
                                             several Mongo clusters;
                                             defaults to ``"default"``
    """

    _collection_name: str = ""
    _database_name: str = ""
    _manager_alias: str = "default"

    # ── Internal helpers ─────────────────────────────────────────

    @classmethod
    def _mgr(cls):
        """Return the ``MongoDBManager`` from the registry."""
        return get_manager(cls._manager_alias)

    @classmethod
    def _col(cls) -> Collection:
        """Return the ``pymongo.Collection`` for this document class."""
        db_name = cls._database_name or cls._mgr().default_database
        return cls._mgr().get_collection(cls._collection_name, db_name)

    @classmethod
    def _log(cls):
        """Shortcut to the manager's logger."""
        return cls._mgr()._logger

    # ── Create ───────────────────────────────────────────────────

    @classmethod
    def insert_one(cls, document: dict) -> dict:
        try:
            result = cls._col().insert_one(document)
            return {"status": True, "inserted_id": str(result.inserted_id)}
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] insert_one failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def insert_many(cls, documents: List[dict]) -> dict:
        try:
            result = cls._col().insert_many(documents)
            return {
                "status": True,
                "inserted_ids": [str(i) for i in result.inserted_ids],
            }
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] insert_many failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    # ── Read ─────────────────────────────────────────────────────

    @classmethod
    def find_one(
        cls,
        query: dict,
        projection: Optional[dict] = None,
        **kwargs: Any,
    ) -> dict:
        try:
            result = cls._col().find_one(query, projection)
            if result:
                return {"status": True, "result": result}
            return {"status": False, "result": []}
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] find_one failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def find(
        cls,
        query: dict,
        projection: Optional[dict] = None,
        sort: Optional[list] = None,
        skip: int = 0,
        limit: int = 0,
        **kwargs: Any,
    ) -> dict:
        try:
            cursor = cls._col().find(query, projection or {"_id": 0})
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            return {"status": True, "result": list(cursor)}
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] find failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def count(cls, query: Optional[dict] = None) -> dict:
        try:
            n = cls._col().count_documents(query or {})
            return {"status": True, "count": n}
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] count failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def get_all(cls, projection: Optional[dict] = None, **kwargs: Any) -> dict:
        return cls.find({}, projection=projection)

    # ── Update ───────────────────────────────────────────────────

    @classmethod
    def update_one(
        cls,
        query: dict,
        update: dict,
        upsert: bool = False,
        **kwargs: Any,
    ) -> dict:
        try:
            if not any(k.startswith("$") for k in update):
                update = {"$set": update}
            result = cls._col().update_one(query, update, upsert=upsert)
            return {
                "status": True,
                "matched": result.matched_count,
                "modified": result.modified_count,
            }
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] update_one failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def update_many(
        cls,
        query: dict,
        update: dict,
        upsert: bool = False,
        **kwargs: Any,
    ) -> dict:
        try:
            if not any(k.startswith("$") for k in update):
                update = {"$set": update}
            result = cls._col().update_many(query, update, upsert=upsert)
            return {
                "status": True,
                "matched": result.matched_count,
                "modified": result.modified_count,
            }
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] update_many failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def upsert_one(cls, query: dict, document: dict) -> dict:
        return cls.update_one(query, document, upsert=True)

    # ── Delete ───────────────────────────────────────────────────

    @classmethod
    def delete_one(cls, query: dict) -> dict:
        try:
            result = cls._col().delete_one(query)
            return {"status": True, "deleted": result.deleted_count}
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] delete_one failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def delete_many(cls, query: dict) -> dict:
        try:
            result = cls._col().delete_many(query)
            return {"status": True, "deleted": result.deleted_count}
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] delete_many failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    # ── Collection-level ops ─────────────────────────────────────

    @classmethod
    def drop_collection(cls) -> dict:
        try:
            cls._col().drop()
            return {"status": True}
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] drop_collection failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    # ── Index management ─────────────────────────────────────────

    @classmethod
    def create_index(cls, keys, **kwargs) -> dict:
        try:
            name = cls._col().create_index(keys, **kwargs)
            return {"status": True, "index_name": name}
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] create_index failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    # ── Custom query escape hatch ────────────────────────────────

    @classmethod
    def execute_raw(cls, operation: Any, **kwargs: Any) -> dict:
        """
        Run an arbitrary MongoDB operation.

        If *operation* is a **list** it is treated as an aggregation pipeline.
        Otherwise it is forwarded to the underlying ``Collection`` as a
        ``command``.

        For even more control, grab the raw driver objects::

            col = cls._col()              # pymongo.Collection
            client = cls._mgr().raw_client  # pymongo.MongoClient

        Returns:
            {"status": True,  "result": [...]}
            {"status": False, "error": "<msg>"}
        """
        try:
            if isinstance(operation, list):
                # Aggregation pipeline
                result = list(cls._col().aggregate(operation, **kwargs))
            else:
                db = cls._mgr().get_database(
                    cls._database_name or cls._mgr().default_database
                )
                result = db.command(operation, **kwargs)
            return {"status": True, "result": result}
        except Exception:
            cls._log().error(
                f"[{cls._collection_name}] execute_raw failed: "
                f"{traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    # ── Direct collection access (for truly custom logic) ────────

    @classmethod
    def collection(cls) -> Collection:
        """
        Return the raw ``pymongo.Collection`` so callers can do
        anything pymongo supports::

            Item.collection().distinct("category")
            Item.collection().bulk_write([...])
        """
        return cls._col()


# Backward-compatible alias
MongoDocument = MongoDBDocument
