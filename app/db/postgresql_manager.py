"""
PostgreSQL connection manager.

Thin subclass of ``SQLManager`` — only provides the connection URL.

Install:
    pip install sqlalchemy psycopg2-binary

Usage:
    from app.db.postgresql_manager import PostgreSQLManager

    pg = PostgreSQLManager()
    pg.connect(host="localhost", port=5432, username="app", password="secret", database="mydb")

    # In main.py:
    register_manager("postgres", pg)
"""

from __future__ import annotations

from typing import Any

from app.db.sql_manager import SQLManager


class PostgreSQLManager(SQLManager):
    """PostgreSQL backend via ``psycopg2``."""

    def _build_url(self, **kwargs: Any) -> str:
        user = kwargs["username"]
        pwd = kwargs["password"]
        host = kwargs["host"]
        port = kwargs["port"]
        db = kwargs["database"]
        return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
