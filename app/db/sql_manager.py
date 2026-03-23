"""
Async SQL manager using SQLAlchemy asyncio extension.
Supports: PostgreSQL (asyncpg), MySQL (aiomysql).
"""
from __future__ import annotations
from typing import Any, Optional

from app.db.base_manager import BaseDatabaseManager
from app.logs.log_handler import LogHandler

try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
except ImportError:
    pass


class SQLManager(BaseDatabaseManager):
    """
    Base async SQLAlchemy manager. Subclass for each dialect.
    Dialect-specific subclasses override _build_url().
    """

    _dialect_driver: str = ""   # e.g. "postgresql+asyncpg", "mysql+aiomysql"

    def __init__(self) -> None:
        self._engine: Optional["AsyncEngine"] = None
        self._default_db: Optional[str] = None
        self._logger = None

    def _build_url(self, host, port, username, password, database) -> str:
        return f"{self._dialect_driver}://{username}:{password}@{host}:{port}/{database}"

    @property
    def raw_client(self) -> "AsyncEngine":
        if self._engine is None:
            raise RuntimeError(f"Async DB not initialised. Call connect() first.")
        return self._engine

    @property
    def default_database(self) -> str:
        return self._default_db or ""

    def connect(self, host: str, port: int, username: str, password: str,
                database: str, pool_size: int = 10, max_overflow: int = 20) -> None:
        self._logger = LogHandler.get_logger("general")
        self._default_db = database
        url = self._build_url(host, port, username, password, database)
        self._engine = create_async_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=False,
        )
        self._logger.success(f"Async {self.__class__.__name__} engine created for {host}:{port}/{database}")

    def disconnect(self) -> None:
        # async dispose needs to be called in async context
        if self._engine is not None:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._engine.dispose())
                else:
                    loop.run_until_complete(self._engine.dispose())
            except Exception:
                pass
            self._engine = None
            if self._logger:
                self._logger.info(f"{self.__class__.__name__} async engine disposed")

    def is_connected(self) -> bool:
        return self._engine is not None
