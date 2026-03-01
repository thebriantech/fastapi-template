"""
User models — one per database backend.

Each model points at a different ``_manager_alias`` so they talk to the
database registered under that alias in ``main.py`` lifespan.

``get_user_model()`` remains available for the auth module (login / token
verification) which needs a single backend based on config.
"""

from __future__ import annotations
from typing import Type

from app.db.base_document import BaseDocument
from app.db.mongodb_document import MongoDBDocument
from app.db.postgresql_document import PostgreSQLDocument
from app.db.mysql_document import MySQLDocument
from app.db.mssql_document import MSSQLDocument


# ── MongoDB model ────────────────────────────────────────────────────────────


class UserMongo(MongoDBDocument):
    """``users`` collection in MongoDB (alias ``default``)."""

    _collection_name: str = "users"
    _manager_alias: str = "default"

    @classmethod
    def ensure_indexes(cls) -> None:
        from pymongo import ASCENDING
        cls.create_index([("username", ASCENDING)], unique=True)


# ── PostgreSQL model ─────────────────────────────────────────────────────────


class UserPg(PostgreSQLDocument):
    """``users`` table in PostgreSQL (alias ``postgres``)."""

    _table_name: str = "users"
    _manager_alias: str = "postgres"

    _DDL = """
        CREATE TABLE IF NOT EXISTS users (
            username        VARCHAR(255) PRIMARY KEY,
            user_group      VARCHAR(255) NOT NULL,
            email           VARCHAR(255) NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """

    @classmethod
    def ensure_table(cls) -> None:
        cls.execute_raw(cls._DDL)

    @classmethod
    def ensure_indexes(cls) -> None:
        cls.ensure_table()
        cls.execute_raw(
            "CREATE INDEX IF NOT EXISTS idx_users_pg_group ON users (user_group)"
        )


# ── MySQL model ──────────────────────────────────────────────────────────────


class UserMySQL(MySQLDocument):
    """``users`` table in MySQL (alias ``mysql``)."""

    _table_name: str = "users"
    _manager_alias: str = "mysql"

    _DDL = """
        CREATE TABLE IF NOT EXISTS users (
            username        VARCHAR(255) PRIMARY KEY,
            user_group      VARCHAR(255) NOT NULL,
            email           VARCHAR(255) NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """

    @classmethod
    def ensure_table(cls) -> None:
        cls.execute_raw(cls._DDL)

    @classmethod
    def ensure_indexes(cls) -> None:
        cls.ensure_table()
        cls._create_index_if_not_exists("idx_users_my_group", "users", "user_group")

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


class UserMSSQL(MSSQLDocument):
    """``users`` table in MSSQL (alias ``mssql``)."""

    _table_name: str = "users"
    _manager_alias: str = "mssql"

    _DDL = """
        IF OBJECT_ID(N'users', N'U') IS NULL
        CREATE TABLE users (
            username        NVARCHAR(255) PRIMARY KEY,
            user_group      NVARCHAR(255) NOT NULL,
            email           NVARCHAR(255) NOT NULL,
            hashed_password NVARCHAR(MAX) NOT NULL
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
                WHERE name = 'idx_users_ms_group' AND object_id = OBJECT_ID('users')
            )
            CREATE INDEX idx_users_ms_group ON users (user_group)
        """)


# ── Factory for auth module (config-based single backend) ────────────────────


def get_user_model() -> Type[BaseDocument]:
    """Return the right User model class for the configured DB backend.

    Used by the auth module (login / token verification) where a single
    backend is selected via ``db_type`` in the app config.
    """
    from app.configs import ConfigManager
    db = ConfigManager.config.db_type.lower()
    _MAP = {
        "mongodb": UserMongo,
        "postgresql": UserPg,
        "mysql": UserMySQL,
        "mssql": UserMSSQL,
    }
    return _MAP.get(db, UserMongo)
