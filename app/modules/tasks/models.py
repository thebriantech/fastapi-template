"""
Task models — one per database backend.

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


class TaskMongo(MongoDBDocument):
    """``tasks`` collection in MongoDB (alias ``default``)."""

    _collection_name: str = "tasks"
    _manager_alias: str = "default"

    @classmethod
    def ensure_indexes(cls) -> None:
        from pymongo import ASCENDING
        cls.create_index([("task_id", ASCENDING)], unique=True)


# ── PostgreSQL model ─────────────────────────────────────────────────────────


class TaskPg(PostgreSQLDocument):
    """``tasks`` table in PostgreSQL (alias ``postgres``)."""

    _table_name: str = "tasks"
    _manager_alias: str = "postgres"

    _DDL = """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id     VARCHAR(64) PRIMARY KEY,
            title       VARCHAR(255) NOT NULL,
            description TEXT,
            status      VARCHAR(32) NOT NULL DEFAULT 'todo',
            assignee    VARCHAR(255) NOT NULL
        )
    """

    @classmethod
    def ensure_table(cls) -> None:
        cls.execute_raw(cls._DDL)

    @classmethod
    def ensure_indexes(cls) -> None:
        cls.ensure_table()
        cls.execute_raw(
            "CREATE INDEX IF NOT EXISTS idx_tasks_pg_assignee ON tasks (assignee)"
        )


# ── MySQL model ──────────────────────────────────────────────────────────────


class TaskMySQL(MySQLDocument):
    """``tasks`` table in MySQL (alias ``mysql``)."""

    _table_name: str = "tasks"
    _manager_alias: str = "mysql"

    _DDL = """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id     VARCHAR(64) PRIMARY KEY,
            title       VARCHAR(255) NOT NULL,
            description TEXT,
            status      VARCHAR(32) NOT NULL DEFAULT 'todo',
            assignee    VARCHAR(255) NOT NULL
        )
    """

    @classmethod
    def ensure_table(cls) -> None:
        cls.execute_raw(cls._DDL)

    @classmethod
    def ensure_indexes(cls) -> None:
        cls.ensure_table()
        cls._create_index_if_not_exists("idx_tasks_my_assignee", "tasks", "assignee")

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


class TaskMSSQL(MSSQLDocument):
    """``tasks`` table in MSSQL (alias ``mssql``)."""

    _table_name: str = "tasks"
    _manager_alias: str = "mssql"

    _DDL = """
        IF OBJECT_ID(N'tasks', N'U') IS NULL
        CREATE TABLE tasks (
            task_id     NVARCHAR(64) PRIMARY KEY,
            title       NVARCHAR(255) NOT NULL,
            description NVARCHAR(MAX),
            status      NVARCHAR(32) NOT NULL DEFAULT 'todo',
            assignee    NVARCHAR(255) NOT NULL
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
                WHERE name = 'idx_tasks_ms_assignee' AND object_id = OBJECT_ID('tasks')
            )
            CREATE INDEX idx_tasks_ms_assignee ON tasks (assignee)
        """)
