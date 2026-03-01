"""
Item models — one per database backend.

Each model points at a different ``_manager_alias`` so they talk to the
database registered under that alias in ``main.py`` lifespan.

All four models expose the identical BaseDocument CRUD interface so the
service layer can treat them uniformly.
"""

from __future__ import annotations

from app.db.mongodb_document import MongoDBDocument
from app.db.postgresql_document import PostgreSQLDocument
from app.db.mysql_document import MySQLDocument
from app.db.mssql_document import MSSQLDocument


# ── MongoDB model ────────────────────────────────────────────────────────────


class ItemMongo(MongoDBDocument):
    """``items`` collection in MongoDB (alias ``default``)."""

    _collection_name: str = "items"
    _manager_alias: str = "default"

    @classmethod
    def ensure_indexes(cls) -> None:
        from pymongo import ASCENDING
        cls.create_index([("item_id", ASCENDING)], unique=True)


# ── PostgreSQL model ─────────────────────────────────────────────────────────


class ItemPg(PostgreSQLDocument):
    """``items`` table in PostgreSQL (alias ``postgres``)."""

    _table_name: str = "items"
    _manager_alias: str = "postgres"

    _DDL = """
        CREATE TABLE IF NOT EXISTS items (
            item_id     VARCHAR(64) PRIMARY KEY,
            name        VARCHAR(255) NOT NULL,
            description TEXT,
            price       DOUBLE PRECISION NOT NULL DEFAULT 0,
            quantity    INTEGER NOT NULL DEFAULT 0
        )
    """

    @classmethod
    def ensure_table(cls) -> None:
        cls.execute_raw(cls._DDL)

    @classmethod
    def ensure_indexes(cls) -> None:
        cls.ensure_table()
        cls.execute_raw(
            "CREATE INDEX IF NOT EXISTS idx_items_pg_name ON items (name)"
        )


# ── MySQL model ──────────────────────────────────────────────────────────────


class ItemMySQL(MySQLDocument):
    """``items`` table in MySQL (alias ``mysql``)."""

    _table_name: str = "items"
    _manager_alias: str = "mysql"

    _DDL = """
        CREATE TABLE IF NOT EXISTS items (
            item_id     VARCHAR(64) PRIMARY KEY,
            name        VARCHAR(255) NOT NULL,
            description TEXT,
            price       DOUBLE NOT NULL DEFAULT 0,
            quantity    INT NOT NULL DEFAULT 0
        )
    """

    @classmethod
    def ensure_table(cls) -> None:
        cls.execute_raw(cls._DDL)

    @classmethod
    def ensure_indexes(cls) -> None:
        cls.ensure_table()
        cls._create_index_if_not_exists("idx_items_my_name", "items", "name")

    @classmethod
    def _create_index_if_not_exists(cls, index_name: str, table: str, column: str) -> None:
        """MySQL doesn't support CREATE INDEX IF NOT EXISTS."""
        check = cls.execute_raw(
            "SELECT COUNT(*) AS cnt FROM information_schema.statistics "
            "WHERE table_schema = DATABASE() AND table_name = :tbl AND index_name = :idx",
            params={"tbl": table, "idx": index_name},
        )
        if check.get("status") and check.get("result", [{}])[0].get("cnt", 0) == 0:
            cls.execute_raw(f"CREATE INDEX {index_name} ON {table} ({column})")


# ── MSSQL model ──────────────────────────────────────────────────────────────


class ItemMSSQL(MSSQLDocument):
    """``items`` table in MSSQL (alias ``mssql``)."""

    _table_name: str = "items"
    _manager_alias: str = "mssql"

    _DDL = """
        IF OBJECT_ID(N'items', N'U') IS NULL
        CREATE TABLE items (
            item_id     NVARCHAR(64) PRIMARY KEY,
            name        NVARCHAR(255) NOT NULL,
            description NVARCHAR(MAX),
            price       FLOAT NOT NULL DEFAULT 0,
            quantity    INT NOT NULL DEFAULT 0
        )
    """

    @classmethod
    def ensure_table(cls) -> None:
        cls.execute_raw(cls._DDL)

    @classmethod
    def ensure_indexes(cls) -> None:
        cls.ensure_table()
        cls.execute_raw("""
            IF NOT EXISTS (
                SELECT 1 FROM sys.indexes
                WHERE name = 'idx_items_ms_name' AND object_id = OBJECT_ID('items')
            )
            CREATE INDEX idx_items_ms_name ON items (name)
        """)
