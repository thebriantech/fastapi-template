"""
Abstract database manager interface.

Every database backend (MongoDB, PostgreSQL, SQLite, …) implements this
contract so the rest of the application never imports driver-specific code
directly.

Usage:
    from app.db.base_manager import BaseDatabaseManager

    class MongoDBManager(BaseDatabaseManager):
        ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseDatabaseManager(ABC):
    """
    Abstract base class that every database backend must implement.

    Subclasses are responsible for:
      - establishing / closing the connection
      - health checks
      - exposing a ``raw_client`` for advanced / custom queries
    """

    # ── Lifecycle ────────────────────────────────────────────────

    @abstractmethod
    def connect(self, **kwargs: Any) -> None:
        """
        Open the connection (or connection pool) using backend-specific
        keyword arguments.

        Must raise on failure (fail-fast).
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection and release pooled resources."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Return ``True`` if the backend is reachable right now."""

    # ── Raw access ───────────────────────────────────────────────

    @property
    @abstractmethod
    def raw_client(self) -> Any:
        """
        Return the underlying driver client (``MongoClient``,
        ``asyncpg.Pool``, ``sqlalchemy.Engine``, …) so that callers
        can run arbitrary backend-specific operations when the CRUD
        helpers are not enough.
        """

    @property
    @abstractmethod
    def default_database(self) -> str:
        """The default database / schema name for this backend."""
