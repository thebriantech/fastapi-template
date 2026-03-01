"""
SQL-specific implementation of ``BaseDocument``.

Shared by **all** SQL backends (PostgreSQL, MySQL, MSSQL, SQLite, …).
Uses SQLAlchemy Core so it works identically regardless of dialect.

Models inherit from this class and set ``_table_name``.  The CRUD helpers
translate the dict-based API into SQL statements so the service layer
keeps the same ``{"status": True/False, …}`` contract.

Usage:
    from app.db.sql_document import SQLDocument

    class Item(SQLDocument):
        _table_name = "items"
        _manager_alias = "postgres"        # matches register_manager() key

        @classmethod
        def ensure_indexes(cls):
            cls.execute_raw(
                "CREATE INDEX IF NOT EXISTS idx_item_id ON items (item_id)"
            )

        # Custom query:
        @classmethod
        def find_expensive(cls, min_price: float):
            return cls.execute_raw(
                "SELECT * FROM items WHERE price >= :min_price ORDER BY price DESC",
                params={"min_price": min_price},
            )
"""

from __future__ import annotations

import traceback
from typing import Any, List, Optional

from app.db.base_document import BaseDocument
from app.db.registry import get_manager

try:
    from sqlalchemy import text, inspect as sa_inspect
except ImportError:
    pass  # handled at manager level


class SQLDocument(BaseDocument):
    """
    Concrete ``BaseDocument`` backed by any SQL database via SQLAlchemy Core.

    Class attributes (set in each subclass):
        _table_name       (str, required)  – SQL table name
        _database_name    (str, optional)  – schema / database override
        _manager_alias    (str, optional)  – registry key; defaults to "default"
    """

    _table_name: str = ""
    _database_name: str = ""
    _manager_alias: str = "default"

    # ── Internal helpers ─────────────────────────────────────────

    @classmethod
    def _mgr(cls):
        return get_manager(cls._manager_alias)

    @classmethod
    def _engine(cls):
        return cls._mgr().raw_client

    @classmethod
    def _log(cls):
        return cls._mgr()._logger

    @classmethod
    def _qualified_table(cls) -> str:
        """Return schema-qualified table name if a database/schema is set."""
        if cls._database_name:
            return f"{cls._database_name}.{cls._table_name}"
        return cls._table_name

    # ── Helpers to build WHERE clauses from dicts ────────────────

    @staticmethod
    def _where_clause(query: dict) -> str:
        """Build ``col = :col AND …`` from a dict."""
        if not query:
            return "1=1"
        return " AND ".join(f"{k} = :{k}" for k in query)

    @staticmethod
    def _set_clause(update: dict) -> str:
        """Build ``col = :_upd_col, …`` from a dict."""
        return ", ".join(f"{k} = :_upd_{k}" for k in update)

    @staticmethod
    def _prefix_update_params(update: dict) -> dict:
        """Prefix update params to avoid collision with WHERE params."""
        return {f"_upd_{k}": v for k, v in update.items()}

    # ── Create ───────────────────────────────────────────────────

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
            cls._log().error(
                f"[{cls._table_name}] insert_one failed: {traceback.format_exc()}"
            )
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
            cls._log().error(
                f"[{cls._table_name}] insert_many failed: {traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    # ── Read ─────────────────────────────────────────────────────

    @classmethod
    def find_one(cls, query: dict, **kwargs: Any) -> dict:
        try:
            where = cls._where_clause(query)
            sql = f"SELECT * FROM {cls._qualified_table()} WHERE {where} LIMIT 1"
            with cls._engine().connect() as conn:
                row = conn.execute(text(sql), query).mappings().first()
            if row:
                return {"status": True, "result": dict(row)}
            return {"status": False, "result": []}
        except Exception:
            cls._log().error(
                f"[{cls._table_name}] find_one failed: {traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def find(
        cls,
        query: dict,
        order_by: Optional[str] = None,
        skip: int = 0,
        limit: int = 0,
        **kwargs: Any,
    ) -> dict:
        try:
            where = cls._where_clause(query)
            sql = f"SELECT * FROM {cls._qualified_table()} WHERE {where}"
            if order_by:
                sql += f" ORDER BY {order_by}"
            if limit:
                sql += f" LIMIT {limit}"
            if skip:
                sql += f" OFFSET {skip}"
            with cls._engine().connect() as conn:
                rows = conn.execute(text(sql), query).mappings().all()
            return {"status": True, "result": [dict(r) for r in rows]}
        except Exception:
            cls._log().error(
                f"[{cls._table_name}] find failed: {traceback.format_exc()}"
            )
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
            cls._log().error(
                f"[{cls._table_name}] count failed: {traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def get_all(cls, order_by: Optional[str] = None, **kwargs: Any) -> dict:
        return cls.find({}, order_by=order_by)

    # ── Update ───────────────────────────────────────────────────

    @classmethod
    def update_one(cls, query: dict, update: dict, **kwargs: Any) -> dict:
        try:
            where = cls._where_clause(query)
            set_clause = cls._set_clause(update)
            sql = f"UPDATE {cls._qualified_table()} SET {set_clause} WHERE {where}"
            # Depending on dialect, LIMIT in UPDATE may not be supported.
            # We rely on the WHERE clause to narrow it down.
            params = {**query, **cls._prefix_update_params(update)}
            with cls._engine().begin() as conn:
                result = conn.execute(text(sql), params)
            return {"status": True, "affected": result.rowcount}
        except Exception:
            cls._log().error(
                f"[{cls._table_name}] update_one failed: {traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def update_many(cls, query: dict, update: dict, **kwargs: Any) -> dict:
        # For SQL, update_many is identical to update_one (no LIMIT).
        return cls.update_one(query, update, **kwargs)

    @classmethod
    def upsert_one(cls, query: dict, document: dict) -> dict:
        """
        Try to update first; if nothing matched, insert instead.

        For production use, consider dialect-specific UPSERT syntax
        (``INSERT … ON CONFLICT`` for Postgres, ``INSERT … ON DUPLICATE KEY``
        for MySQL, ``MERGE`` for MSSQL) via ``execute_raw``.
        """
        result = cls.update_one(query, document)
        if result.get("status") and result.get("affected", 0) == 0:
            merged = {**query, **document}
            return cls.insert_one(merged)
        return result

    # ── Delete ───────────────────────────────────────────────────

    @classmethod
    def delete_one(cls, query: dict) -> dict:
        try:
            where = cls._where_clause(query)
            sql = f"DELETE FROM {cls._qualified_table()} WHERE {where}"
            with cls._engine().begin() as conn:
                result = conn.execute(text(sql), query)
            return {"status": True, "deleted": result.rowcount}
        except Exception:
            cls._log().error(
                f"[{cls._table_name}] delete_one failed: {traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def delete_many(cls, query: dict) -> dict:
        return cls.delete_one(query)  # same SQL, no LIMIT

    # ── Schema / index management ────────────────────────────────

    @classmethod
    def drop_table(cls) -> dict:
        try:
            sql = f"DROP TABLE IF EXISTS {cls._qualified_table()}"
            with cls._engine().begin() as conn:
                conn.execute(text(sql))
            return {"status": True}
        except Exception:
            cls._log().error(
                f"[{cls._table_name}] drop_table failed: {traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}

    @classmethod
    def table_exists(cls) -> bool:
        """Check whether the table exists in the database."""
        try:
            insp = sa_inspect(cls._engine())
            return insp.has_table(cls._table_name, schema=cls._database_name or None)
        except Exception:
            return False

    # ── Custom query escape hatch ────────────────────────────────

    @classmethod
    def execute_raw(cls, operation: Any, params: Optional[dict] = None, **kwargs: Any) -> dict:
        """
        Execute an arbitrary SQL statement.

        *operation* is a SQL string.  Use ``:param`` placeholders and
        pass values via *params*.

        Examples::

            Item.execute_raw("SELECT * FROM items WHERE price > :p", params={"p": 100})
            Item.execute_raw("CREATE INDEX idx_name ON items (name)")

        Returns:
            {"status": True,  "result": [<row_dict>, ...]}
            {"status": False, "error": "<msg>"}
        """
        try:
            with cls._engine().begin() as conn:
                result = conn.execute(text(str(operation)), params or {})
                if result.returns_rows:
                    rows = [dict(r) for r in result.mappings().all()]
                    return {"status": True, "result": rows}
                return {"status": True, "affected": result.rowcount}
        except Exception:
            cls._log().error(
                f"[{cls._table_name}] execute_raw failed: {traceback.format_exc()}"
            )
            return {"status": False, "error": traceback.format_exc()}
