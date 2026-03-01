"""
MySQL / MariaDB connection manager.

Thin subclass of ``SQLManager`` — only provides the connection URL.

Install:
    pip install sqlalchemy pymysql

Usage:
    from app.db.mysql_manager import MySQLManager

    mysql = MySQLManager()
    mysql.connect(host="localhost", port=3306, username="root", password="secret", database="mydb")

    # In main.py:
    register_manager("mysql", mysql)
"""

from __future__ import annotations

from typing import Any

from app.db.sql_manager import SQLManager


class MySQLManager(SQLManager):
    """MySQL / MariaDB backend via ``PyMySQL``."""

    def _build_url(self, **kwargs: Any) -> str:
        user = kwargs["username"]
        pwd = kwargs["password"]
        host = kwargs["host"]
        port = kwargs["port"]
        db = kwargs["database"]
        charset = kwargs.get("charset", "utf8mb4")
        return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?charset={charset}"
