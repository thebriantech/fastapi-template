"""
Microsoft SQL Server connection manager.

Thin subclass of ``SQLManager`` — only provides the connection URL.

Install:
    pip install sqlalchemy pyodbc

Usage:
    from app.db.mssql_manager import MSSQLManager

    mssql = MSSQLManager()
    mssql.connect(
        host="localhost", port=1433,
        username="sa", password="secret",
        database="mydb",
        driver="ODBC Driver 18 for SQL Server",
    )

    # In main.py:
    register_manager("mssql", mssql)
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from app.db.sql_manager import SQLManager


class MSSQLManager(SQLManager):
    """Microsoft SQL Server backend via ``pyodbc``."""

    def _build_url(self, **kwargs: Any) -> str:
        user = kwargs["username"]
        pwd = kwargs["password"]
        host = kwargs["host"]
        port = kwargs["port"]
        db = kwargs["database"]
        driver = kwargs.get("driver", "ODBC Driver 18 for SQL Server")
        trust_cert = kwargs.get("trust_server_certificate", "yes")

        params = quote_plus(
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={db};"
            f"UID={user};"
            f"PWD={pwd};"
            f"TrustServerCertificate={trust_cert};"
        )
        return f"mssql+pyodbc:///?odbc_connect={params}"
