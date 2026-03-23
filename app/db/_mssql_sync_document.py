"""
Internal sync MSSQL document implementation.
Used by mssql_document.py (async wrapper) via thread-pool executor.
Do not use this class directly in application code — use MSSQLDocument instead.
"""
from __future__ import annotations

import re
import traceback
from typing import Any, List, Optional

from app.db.registry import get_manager

try:
    from sqlalchemy import text
except ImportError:
    pass


class MSSQLDocument:
    """Sync MSSQL document backed by a sync SQLAlchemy engine (pyodbc)."""

    _table_name: str = ""
    _database_name: str = ""
    _manager_alias: str = "mssql"

    @classmethod
    def _engine(cls):
        return get_manager(cls._manager_alias).raw_client

    @classmethod
    def _log(cls):
        return get_manager(cls._manager_alias)._logger

    @classmethod
    def _qualified_table(cls) -> str:
        if cls._database_name:
            return f"{cls._database_name}.{cls._table_name}"
        return cls._table_name

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

    @classmethod
    def insert_one(cls, document: dict) -> dict:
        try:
            cols = ", ".join(document.keys())
            placeholders = ", ".join(f":{k}" for k in document)
            sql = f"INSERT INTO {cls._qualified_table()} ({cols}) VALUES ({placeholders})"
            with cls._engine().begin() as conn:
                conn.execute(text(sql), document)
            return {"status": True}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def insert_many(cls, documents: List[dict]) -> dict:
        if not documents:
            return {"status": True, "inserted": 0}
        try:
            cols = ", ".join(documents[0].keys())
            placeholders = ", ".join(f":{k}" for k in documents[0])
            sql = f"INSERT INTO {cls._qualified_table()} ({cols}) VALUES ({placeholders})"
            with cls._engine().begin() as conn:
                conn.execute(text(sql), documents)
            return {"status": True, "inserted": len(documents)}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def find_one(cls, query: dict, **kwargs) -> dict:
        """Uses SELECT TOP 1 instead of LIMIT 1 (not valid in MSSQL)."""
        try:
            where = cls._where_clause(query)
            sql = f"SELECT TOP 1 * FROM {cls._qualified_table()} WHERE {where}"
            with cls._engine().connect() as conn:
                row = conn.execute(text(sql), query).mappings().first()
            if row:
                return {"status": True, "result": dict(row)}
            return {"status": False, "result": []}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def find(cls, query: dict, order_by: Optional[str] = None,
             skip: int = 0, limit: int = 0, **kwargs) -> dict:
        try:
            if order_by and not re.match(r"^[\w\s,]+$", order_by):
                return {"status": False, "error": f"Invalid order_by value: {order_by!r}"}
            where = cls._where_clause(query)
            sql = f"SELECT * FROM {cls._qualified_table()} WHERE {where}"
            if order_by:
                sql += f" ORDER BY {order_by}"
            if limit:
                sql += f" FETCH NEXT {limit} ROWS ONLY"
            if skip:
                sql += f" OFFSET {skip} ROWS"
            with cls._engine().connect() as conn:
                rows = conn.execute(text(sql), query).mappings().all()
            return {"status": True, "result": [dict(r) for r in rows]}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def count(cls, query: Optional[dict] = None) -> dict:
        try:
            query = query or {}
            where = cls._where_clause(query)
            sql = f"SELECT COUNT(*) AS cnt FROM {cls._qualified_table()} WHERE {where}"
            with cls._engine().connect() as conn:
                row = conn.execute(text(sql), query).mappings().first()
            return {"status": True, "count": row["cnt"] if row else 0}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def get_all(cls, order_by: Optional[str] = None, **kwargs) -> dict:
        return cls.find({}, order_by=order_by)

    @classmethod
    def update_one(cls, query: dict, update: dict, **kwargs) -> dict:
        try:
            where = cls._where_clause(query)
            set_clause = cls._set_clause(update)
            sql = f"UPDATE {cls._qualified_table()} SET {set_clause} WHERE {where}"
            params = {**query, **cls._prefix_update_params(update)}
            with cls._engine().begin() as conn:
                result = conn.execute(text(sql), params)
            return {"status": True, "affected": result.rowcount}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def update_many(cls, query: dict, update: dict, **kwargs) -> dict:
        return cls.update_one(query, update, **kwargs)

    @classmethod
    def upsert_one(cls, query: dict, document: dict) -> dict:
        result = cls.update_one(query, document)
        if result.get("status") and result.get("affected", 0) == 0:
            merged = {**query, **document}
            return cls.insert_one(merged)
        return result

    @classmethod
    def delete_one(cls, query: dict) -> dict:
        try:
            where = cls._where_clause(query)
            sql = f"DELETE FROM {cls._qualified_table()} WHERE {where}"
            with cls._engine().begin() as conn:
                result = conn.execute(text(sql), query)
            return {"status": True, "deleted": result.rowcount}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def delete_many(cls, query: dict) -> dict:
        return cls.delete_one(query)

    @classmethod
    def execute_raw(cls, operation: Any, params: Optional[dict] = None, **kwargs) -> dict:
        try:
            with cls._engine().begin() as conn:
                result = conn.execute(text(str(operation)), params or {})
                if result.returns_rows:
                    rows = [dict(r) for r in result.mappings().all()]
                    return {"status": True, "result": rows}
                return {"status": True, "affected": result.rowcount}
        except Exception:
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def ensure_indexes(cls) -> None:
        pass
