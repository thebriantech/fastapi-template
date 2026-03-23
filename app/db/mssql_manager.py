"""
Microsoft SQL Server connection manager (sync, pyodbc-based).
Used by MSSQLDocument (async wrapper) via thread-pool executor.
"""
from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote_plus

from app.db.base_manager import BaseDatabaseManager
from app.logs.log_handler import LogHandler

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
    from sqlalchemy.pool import QueuePool
except ImportError:
    pass


class MSSQLManager(BaseDatabaseManager):
    """Microsoft SQL Server backend via pyodbc (sync)."""

    def __init__(self) -> None:
        self._engine: Optional["Engine"] = None
        self._default_db: Optional[str] = None
        self._logger = None

    @property
    def raw_client(self) -> "Engine":
        if self._engine is None:
            raise RuntimeError("MSSQL not initialised. Call connect() first.")
        return self._engine

    @property
    def default_database(self) -> str:
        return self._default_db or ""

    def _build_url(self, host, port, username, password, database,
                   driver="ODBC Driver 18 for SQL Server",
                   trust_server_certificate="yes") -> str:
        params = quote_plus(
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate={trust_server_certificate};"
        )
        return f"mssql+pyodbc:///?odbc_connect={params}"

    def connect(self, host: str, port: int, username: str, password: str,
                database: str, pool_size: int = 10, max_overflow: int = 20,
                driver: str = "ODBC Driver 18 for SQL Server", **kwargs) -> None:
        self._logger = LogHandler.get_logger("general")
        self._default_db = database
        url = self._build_url(host, port, username, password, database, driver)
        self._engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=False,
        )
        self._logger.success(f"MSSQL engine created for {host}:{port}/{database}")

    def disconnect(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            if self._logger:
                self._logger.info("MSSQL engine disposed")

    def is_connected(self) -> bool:
        if self._engine is None:
            return False
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
