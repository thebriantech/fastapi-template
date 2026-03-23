"""
MSSQL async document — wraps sync MSSQLDocument in a thread executor.
MSSQL has no mature native async Python driver, so we use
run_in_executor to avoid blocking the event loop.
"""
from __future__ import annotations
import asyncio
import functools
import traceback
from typing import Any, List, Optional

from app.db.base_document import BaseDocument
from app.db._mssql_sync_document import MSSQLDocument as _SyncMSSQLDocument


class MSSQLDocument(BaseDocument):
    """
    Async wrapper for the sync MSSQLDocument using thread-pool executor.
    All CRUD calls are forwarded to _SyncMSSQLDocument via run_in_executor.
    """
    _table_name: str = ""
    _database_name: str = ""
    _manager_alias: str = "mssql"
    _sync_cls = _SyncMSSQLDocument

    @classmethod
    async def _run(cls, method, *args, **kwargs):
        loop = asyncio.get_event_loop()
        fn = functools.partial(method, *args, **kwargs)
        return await loop.run_in_executor(None, fn)

    @classmethod
    async def insert_one(cls, document: dict) -> dict:
        return await cls._run(cls._sync_cls.insert_one, document)

    @classmethod
    async def insert_many(cls, documents: List[dict]) -> dict:
        return await cls._run(cls._sync_cls.insert_many, documents)

    @classmethod
    async def find_one(cls, query: dict, **kwargs: Any) -> dict:
        return await cls._run(cls._sync_cls.find_one, query, **kwargs)

    @classmethod
    async def find(cls, query: dict, order_by: Optional[str] = None,
                   skip: int = 0, limit: int = 0, **kwargs: Any) -> dict:
        return await cls._run(cls._sync_cls.find, query,
                               order_by=order_by, skip=skip, limit=limit, **kwargs)

    @classmethod
    async def count(cls, query: Optional[dict] = None) -> dict:
        return await cls._run(cls._sync_cls.count, query)

    @classmethod
    async def get_all(cls, order_by: Optional[str] = None, **kwargs: Any) -> dict:
        return await cls._run(cls._sync_cls.get_all, order_by=order_by, **kwargs)

    @classmethod
    async def update_one(cls, query: dict, update: dict, **kwargs: Any) -> dict:
        return await cls._run(cls._sync_cls.update_one, query, update, **kwargs)

    @classmethod
    async def update_many(cls, query: dict, update: dict, **kwargs: Any) -> dict:
        return await cls._run(cls._sync_cls.update_many, query, update, **kwargs)

    @classmethod
    async def upsert_one(cls, query: dict, document: dict) -> dict:
        return await cls._run(cls._sync_cls.upsert_one, query, document)

    @classmethod
    async def delete_one(cls, query: dict) -> dict:
        return await cls._run(cls._sync_cls.delete_one, query)

    @classmethod
    async def delete_many(cls, query: dict) -> dict:
        return await cls._run(cls._sync_cls.delete_many, query)

    @classmethod
    async def execute_raw(cls, operation: Any, params: Optional[dict] = None, **kwargs: Any) -> dict:
        return await cls._run(cls._sync_cls.execute_raw, operation, params, **kwargs)

    @classmethod
    def ensure_indexes(cls) -> None:
        """Override to create indexes at startup. Sync context is fine here."""
