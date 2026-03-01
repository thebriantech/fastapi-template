"""
PostgreSQL-specific document class.

Simply binds ``SQLDocument`` to a ``PostgreSQLManager`` alias.

Usage:
    from app.db.postgresql_document import PostgreSQLDocument

    class Item(PostgreSQLDocument):
        _table_name = "items"
        _manager_alias = "postgres"     # must match register_manager() key

        @classmethod
        def ensure_indexes(cls):
            cls.execute_raw(
                "CREATE INDEX IF NOT EXISTS idx_item_id ON items (item_id)"
            )

        # PostgreSQL-specific custom query:
        @classmethod
        def search_by_name(cls, pattern: str):
            return cls.execute_raw(
                "SELECT * FROM items WHERE name ILIKE :pattern",
                params={"pattern": f"%{pattern}%"},
            )

        # Native UPSERT using ON CONFLICT:
        @classmethod
        def upsert_item(cls, item_id: str, data: dict):
            cols = ", ".join(data.keys())
            vals = ", ".join(f":{k}" for k in data)
            updates = ", ".join(f"{k} = EXCLUDED.{k}" for k in data if k != "item_id")
            return cls.execute_raw(
                f"INSERT INTO items ({cols}) VALUES ({vals}) "
                f"ON CONFLICT (item_id) DO UPDATE SET {updates}",
                params=data,
            )
"""

from __future__ import annotations

from app.db.sql_document import SQLDocument


class PostgreSQLDocument(SQLDocument):
    """
    ``BaseDocument`` backed by PostgreSQL.

    Set ``_manager_alias = "postgres"`` (or whatever alias you used
    when calling ``register_manager()``) in each subclass.
    """

    _manager_alias: str = "postgres"


# Backward-compatible alias
PgDocument = PostgreSQLDocument
