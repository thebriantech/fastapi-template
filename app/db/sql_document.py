"""
Async SQL document backed by SQLAlchemy asyncio extension.
All CRUD methods are async. Use with PostgreSQLManager or MySQLManager.
"""
from __future__ import annotations

import re
import traceback
from typing import Any, List, Optional

from app.db.base_document import BaseDocument
from app.db.registry import get_manager

try:
    from sqlalchemy import text
except ImportError:
    pass


class SQLDocument(BaseDocument):
    """
    Concrete BaseDocument backed by any async SQL database via SQLAlchemy.

    Class attributes (set in each subclass):
        _table_name       (str, required)  – SQL table name
        _database_name    (str, optional)  – schema / database override
        _manager_alias    (str, optional)  – registry key
    """

    _table_name: str = ""
    _database_name: str = ""
    _manager_alias: str = "default"

    # ── Internal helpers ─────────────────────────────────────────

    @classmethod
    def _engine(cls):
        return get_manager(cls._manager_alias).raw_client

    @classmethod
    def _qualified_table(cls) -> str:
        if cls._database_name:
            return f"{cls._database_name}.{cls._table_name}"
        return cls._table_name

    # ── Helpers to build WHERE/SET clauses ───────────────────────

    @staticmethod
    def _where_clause(query: dict) -> str:
        if not query:
            return "1=1"
        return " AND ".join(f"{k} = :{k}" for k in query)

    @staticmethod
    def _set_clause(update: dict) -> str:
        return ", ".join(f"{k} = :_upd_{k}" for k in update)

    @staticmethod
    def _prefix_update_params(update: dict) -> dict:
        return {f"_upd_{k}": v for k, v in update.items()}

    # ── Create ───────────────────────────────────────────────────

    @classmethod
    async def insert_one(cls, document: dict) -> dict:
        try:
            cols = ", ".join(document.keys())
            placeholders = ", ".join(f":{k}" for k in document)
            sql = f"INSERT INTO {cls._qualified_table()} ({cols}) VALUES ({placeholders})"
            async with cls._engine().begin() as conn:
                await conn.execute(text(sql), document)
            return {"status": True}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def insert_many(cls, documents: List[dict]) -> dict:
        if not documents:
            return {"status": True, "inserted": 0}
        try:
            cols = ", ".join(documents[0].keys())
            placeholders = ", ".join(f":{k}" for k in documents[0])
            sql = f"INSERT INTO {cls._qualified_table()} ({cols}) VALUES ({placeholders})"
            async with cls._engine().begin() as conn:
                await conn.execute(text(sql), documents)
            return {"status": True, "inserted": len(documents)}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    # ── Read ─────────────────────────────────────────────────────

    @classmethod
    async def find_one(cls, query: dict, **kwargs: Any) -> dict:
        try:
            where = cls._where_clause(query)
            sql = f"SELECT * FROM {cls._qualified_table()} WHERE {where} LIMIT 1"
            async with cls._engine().connect() as conn:
                result = await conn.execute(text(sql), query)
                row = result.mappings().first()
            if row:
                return {"status": True, "result": dict(row)}
            return {"status": False, "result": []}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def find(cls, query: dict, order_by: Optional[str] = None,
                   skip: int = 0, limit: int = 0, **kwargs: Any) -> dict:
        try:
            if order_by and not re.match(r"^[\w\s,]+$", order_by):
                return {"status": False, "error": f"Invalid order_by value: {order_by!r}"}
            where = cls._where_clause(query)
            sql = f"SELECT * FROM {cls._qualified_table()} WHERE {where}"
            if order_by:
                sql += f" ORDER BY {order_by}"
            if limit:
                sql += f" LIMIT {limit}"
            if skip:
                sql += f" OFFSET {skip}"
            async with cls._engine().connect() as conn:
                result = await conn.execute(text(sql), query)
                rows = result.mappings().all()
            return {"status": True, "result": [dict(r) for r in rows]}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def count(cls, query: Optional[dict] = None) -> dict:
        try:
            query = query or {}
            where = cls._where_clause(query)
            sql = f"SELECT COUNT(*) AS cnt FROM {cls._qualified_table()} WHERE {where}"
            async with cls._engine().connect() as conn:
                result = await conn.execute(text(sql), query)
                row = result.mappings().first()
            return {"status": True, "count": row["cnt"] if row else 0}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def get_all(cls, order_by: Optional[str] = None, **kwargs: Any) -> dict:
        return await cls.find({}, order_by=order_by)

    # ── Update ───────────────────────────────────────────────────

    @classmethod
    async def update_one(cls, query: dict, update: dict, **kwargs: Any) -> dict:
        try:
            where = cls._where_clause(query)
            set_clause = cls._set_clause(update)
            sql = f"UPDATE {cls._qualified_table()} SET {set_clause} WHERE {where}"
            params = {**query, **cls._prefix_update_params(update)}
            async with cls._engine().begin() as conn:
                result = await conn.execute(text(sql), params)
            return {"status": True, "affected": result.rowcount}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def update_many(cls, query: dict, update: dict, **kwargs: Any) -> dict:
        return await cls.update_one(query, update, **kwargs)

    @classmethod
    async def upsert_one(cls, query: dict, document: dict) -> dict:
        result = await cls.update_one(query, document)
        if result.get("status") and result.get("affected", 0) == 0:
            merged = {**query, **document}
            return await cls.insert_one(merged)
        return result

    # ── Delete ───────────────────────────────────────────────────

    @classmethod
    async def delete_one(cls, query: dict) -> dict:
        try:
            where = cls._where_clause(query)
            sql = f"DELETE FROM {cls._qualified_table()} WHERE {where}"
            async with cls._engine().begin() as conn:
                result = await conn.execute(text(sql), query)
            return {"status": True, "deleted": result.rowcount}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def delete_many(cls, query: dict) -> dict:
        return await cls.delete_one(query)

    # ── Schema / index management ────────────────────────────────

    @classmethod
    async def drop_table(cls) -> dict:
        try:
            sql = f"DROP TABLE IF EXISTS {cls._qualified_table()}"
            async with cls._engine().begin() as conn:
                await conn.execute(text(sql))
            return {"status": True}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    async def table_exists(cls) -> bool:
        try:
            sql = f"SELECT 1 FROM information_schema.tables WHERE table_name = :tbl"
            async with cls._engine().connect() as conn:
                result = await conn.execute(text(sql), {"tbl": cls._table_name})
                row = result.first()
            return row is not None
        except Exception:
            return False

    # ── Custom query escape hatch ────────────────────────────────

    @classmethod
    async def execute_raw(cls, operation: Any, params: Optional[dict] = None, **kwargs: Any) -> dict:
        """
        Execute an arbitrary SQL statement asynchronously.

        Returns:
            {"status": True,  "result": [<row_dict>, ...]}
            {"status": False, "error": "<msg>"}
        """
        try:
            async with cls._engine().begin() as conn:
                result = await conn.execute(text(str(operation)), params or {})
                if result.returns_rows:
                    rows = [dict(r) for r in result.mappings().all()]
                    return {"status": True, "result": rows}
                return {"status": True, "affected": result.rowcount}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}
