"""
Microsoft SQL Server–specific document class.

Simply binds ``SQLDocument`` to a ``MSSQLManager`` alias.

Usage:
    from app.db.mssql_document import MSSQLDocument

    class Item(MSSQLDocument):
        _table_name = "items"
        _manager_alias = "mssql"        # must match register_manager() key

        @classmethod
        def ensure_indexes(cls):
            cls.execute_raw(
                "CREATE INDEX idx_item_id ON items (item_id)"
            )

        # MSSQL-specific custom query:
        @classmethod
        def top_items(cls, n: int = 10):
            return cls.execute_raw(
                f"SELECT TOP {n} * FROM items ORDER BY price DESC"
            )

        # Native UPSERT using MERGE:
        @classmethod
        def upsert_item(cls, item_id: str, data: dict):
            set_parts = ", ".join(f"T.{k} = :_upd_{k}" for k in data if k != "item_id")
            cols = ", ".join(data.keys())
            vals = ", ".join(f":{k}" for k in data)
            params = {**data, **{f"_upd_{k}": v for k, v in data.items()}, "_match_id": item_id}
            return cls.execute_raw(
                f"MERGE INTO items AS T "
                f"USING (SELECT :_match_id AS item_id) AS S ON T.item_id = S.item_id "
                f"WHEN MATCHED THEN UPDATE SET {set_parts} "
                f"WHEN NOT MATCHED THEN INSERT ({cols}) VALUES ({vals});",
                params=params,
            )
"""

from __future__ import annotations

from app.db.sql_document import SQLDocument


class MSSQLDocument(SQLDocument):
    """
    ``BaseDocument`` backed by Microsoft SQL Server.

    Set ``_manager_alias = "mssql"`` (or whatever alias you used
    when calling ``register_manager()``) in each subclass.
    """

    _manager_alias: str = "mssql"
