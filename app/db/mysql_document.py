"""
MySQL / MariaDB–specific document class.

Simply binds ``SQLDocument`` to a ``MySQLManager`` alias.

Usage:
    from app.db.mysql_document import MySQLDocument

    class Item(MySQLDocument):
        _table_name = "items"
        _manager_alias = "mysql"        # must match register_manager() key

        @classmethod
        def ensure_indexes(cls):
            cls.execute_raw(
                "CREATE INDEX idx_item_id ON items (item_id)"
            )

        # MySQL-specific custom query:
        @classmethod
        def fulltext_search(cls, keyword: str):
            return cls.execute_raw(
                "SELECT * FROM items WHERE MATCH(name, description) AGAINST(:kw IN BOOLEAN MODE)",
                params={"kw": keyword},
            )

        # Native UPSERT using ON DUPLICATE KEY:
        @classmethod
        def upsert_item(cls, data: dict):
            cols = ", ".join(data.keys())
            vals = ", ".join(f":{k}" for k in data)
            updates = ", ".join(f"{k} = VALUES({k})" for k in data if k != "item_id")
            return cls.execute_raw(
                f"INSERT INTO items ({cols}) VALUES ({vals}) "
                f"ON DUPLICATE KEY UPDATE {updates}",
                params=data,
            )
"""

from __future__ import annotations

from app.db.sql_document import SQLDocument


class MySQLDocument(SQLDocument):
    """
    ``BaseDocument`` backed by MySQL / MariaDB.

    Set ``_manager_alias = "mysql"`` (or whatever alias you used
    when calling ``register_manager()``) in each subclass.
    """

    _manager_alias: str = "mysql"
