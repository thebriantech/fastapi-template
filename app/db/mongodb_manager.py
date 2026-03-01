"""
Production-ready MongoDB connection manager.

Implements ``BaseDatabaseManager`` so it can be swapped with any other
backend (PostgreSQL, SQLite, …) without changing service / model code.

Features:
- Connection pooling with configurable pool size
- Health checks (ping)
- Proper connection lifecycle (connect / disconnect)
- Retry-aware writes and reads
- Configurable timeouts
- ``raw_client`` property for custom / advanced queries

Usage:
    from app.db.mongodb_manager import MongoDBManager

    mgr = MongoDBManager()
    mgr.connect(host=..., port=..., ...)
    col = mgr.get_collection("items")
    mgr.disconnect()
"""

from typing import Any, Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.db.base_manager import BaseDatabaseManager
from app.logs.log_handler import LogHandler


class MongoDBManager(BaseDatabaseManager):
    """
    Manages a single ``MongoClient`` instance with production-grade
    connection-pool settings, health checks, and clean shutdown.
    """

    def __init__(self) -> None:
        self._client: Optional[MongoClient] = None
        self._default_db: Optional[str] = None
        self._logger = None

    # ── BaseDatabaseManager interface ────────────────────────────

    @property
    def raw_client(self) -> MongoClient:
        """
        Return the underlying ``MongoClient``.

        Use this for custom queries that go beyond the CRUD helpers::

            pipeline = [{"$group": {"_id": "$status", "n": {"$sum": 1}}}]
            result = db_manager.raw_client["mydb"]["col"].aggregate(pipeline)
        """
        if self._client is None:
            raise RuntimeError(
                "MongoDB not initialised.  Call connect() first."
            )
        return self._client

    @property
    def default_database(self) -> str:
        """The database name used when models don't specify one."""
        return self._default_db or ""

    # ── Lifecycle ────────────────────────────────────────────────

    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        auth_source: str = "admin",
        default_database: str = "project_name",
        *,
        max_pool_size: int = 50,
        min_pool_size: int = 10,
        max_idle_time_ms: int = 30_000,
        connect_timeout_ms: int = 5_000,
        server_selection_timeout_ms: int = 5_000,
        socket_timeout_ms: int = 20_000,
        retry_writes: bool = True,
        retry_reads: bool = True,
    ) -> None:
        """
        Create the ``MongoClient``, verify the connection with a ping,
        and store the default database name.

        Raises ``ConnectionFailure`` / ``ServerSelectionTimeoutError``
        if the server is unreachable — fail-fast on startup.
        """
        self._logger = LogHandler.get_logger("general")
        self._default_db = default_database

        kwargs = dict(
            host=host,
            port=port,
            username=username,
            password=password,
            maxPoolSize=max_pool_size,
            minPoolSize=min_pool_size,
            maxIdleTimeMS=max_idle_time_ms,
            connectTimeoutMS=connect_timeout_ms,
            serverSelectionTimeoutMS=server_selection_timeout_ms,
            socketTimeoutMS=socket_timeout_ms,
            retryWrites=retry_writes,
            retryReads=retry_reads,
        )

        if auth_source:
            kwargs["authSource"] = auth_source

        try:
            self._client = MongoClient(**kwargs)
            # Fail-fast: verify the server is reachable
            self._client.admin.command("ping")
            self._logger.success("MongoDB connection established successfully")
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            self._logger.error(f"Failed to connect to MongoDB: {exc}")
            raise

    def disconnect(self) -> None:
        """Close the client and release all pooled connections."""
        if self._client is not None:
            self._client.close()
            self._client = None
            if self._logger:
                self._logger.info("MongoDB connection closed")

    def is_connected(self) -> bool:
        """Return ``True`` if the client can successfully ping the server."""
        if self._client is None:
            return False
        try:
            self._client.admin.command("ping")
            return True
        except Exception:
            return False

    # ── Convenience accessors ────────────────────────────────────

    def get_database(self, db_name: str = None) -> Database:
        """Return a ``Database`` handle (defaults to ``default_database``)."""
        return self.raw_client[db_name or self._default_db]

    def get_collection(
        self, collection_name: str, db_name: str = None
    ) -> Collection:
        """Return a ``Collection`` handle."""
        return self.get_database(db_name)[collection_name]
