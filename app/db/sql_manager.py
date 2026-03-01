"""
SQLAlchemy-based database manager.

Shared implementation for **all** SQL backends (PostgreSQL, MySQL, MSSQL,
SQLite, …).  Each concrete subclass only needs to build the correct
connection URL — everything else is inherited.

Relies on ``sqlalchemy`` (Core, not ORM) so it stays lightweight and
consistent with the dict-in / dict-out contract used by ``BaseDocument``.

Install:
    pip install sqlalchemy

    # Plus the dialect driver you need:
    pip install psycopg2-binary   # PostgreSQL
    pip install pymysql            # MySQL
    pip install pyodbc             # MSSQL
"""

from __future__ import annotations

from typing import Any, Optional

from app.db.base_manager import BaseDatabaseManager
from app.logs.log_handler import LogHandler

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
    from sqlalchemy.pool import QueuePool

    _HAS_SQLALCHEMY = True
except ImportError:
    _HAS_SQLALCHEMY = False
    Engine = Any  # type: ignore


class SQLManager(BaseDatabaseManager):
    """
    Base manager for every SQL dialect.

    Subclasses override ``_build_url()`` to produce the right
    SQLAlchemy connection string.  Everything else — pooling,
    health checks, connect / disconnect — is handled here.
    """

    def __init__(self) -> None:
        if not _HAS_SQLALCHEMY:
            raise ImportError(
                "sqlalchemy is required for SQL backends.  "
                "Install it with:  pip install sqlalchemy"
            )
        self._engine: Optional[Engine] = None
        self._default_db: Optional[str] = None
        self._logger = None

    # ── Must be overridden by each dialect ───────────────────────

    def _build_url(self, **kwargs: Any) -> str:
        """
        Return a SQLAlchemy connection URL for this dialect.

        Override in subclass.  Example for PostgreSQL::

            return (
                f"postgresql+psycopg2://{user}:{password}"
                f"@{host}:{port}/{database}"
            )
        """
        raise NotImplementedError

    # ── BaseDatabaseManager interface ────────────────────────────

    @property
    def raw_client(self) -> Engine:
        """Return the underlying ``sqlalchemy.Engine``."""
        if self._engine is None:
            raise RuntimeError(
                "SQL database not initialised.  Call connect() first."
            )
        return self._engine

    @property
    def default_database(self) -> str:
        return self._default_db or ""

    # ── Lifecycle ────────────────────────────────────────────────

    def connect(
        self,
        host: str = "localhost",
        port: int = 5432,
        username: str = "",
        password: str = "",
        database: str = "",
        *,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
        echo: bool = False,
        connect_args: Optional[dict] = None,
        **extra: Any,
    ) -> None:
        """
        Create a ``sqlalchemy.Engine`` with a connection pool and
        verify reachability with a trivial query.
        """
        self._logger = LogHandler.get_logger("general")
        self._default_db = database

        url = self._build_url(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            **extra,
        )

        try:
            self._engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=pool_timeout,
                pool_recycle=pool_recycle,
                echo=echo,
                connect_args=connect_args or {},
            )
            # Fail-fast: verify the server is reachable
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self._logger.success(
                f"{self.__class__.__name__} connection established "
                f"({self._engine.url.get_backend_name()})"
            )
        except Exception as exc:
            self._logger.error(
                f"Failed to connect ({self.__class__.__name__}): {exc}"
            )
            raise

    def disconnect(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            if self._logger:
                self._logger.info(
                    f"{self.__class__.__name__} connection pool disposed"
                )

    def is_connected(self) -> bool:
        if self._engine is None:
            return False
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
