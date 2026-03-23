"""
Async MongoDB manager using Motor (motor.motor_asyncio).
"""
from __future__ import annotations
from typing import Any, Optional

try:
    import motor.motor_asyncio
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
except ImportError:
    motor = None

from app.db.base_manager import BaseDatabaseManager
from app.logs.log_handler import LogHandler


class MongoDBManager(BaseDatabaseManager):
    def __init__(self) -> None:
        self._client: Optional["AsyncIOMotorClient"] = None
        self._default_db: Optional[str] = None
        self._logger = None

    @property
    def raw_client(self) -> "AsyncIOMotorClient":
        if self._client is None:
            raise RuntimeError("MongoDB not initialised. Call connect() first.")
        return self._client

    @property
    def default_database(self) -> str:
        return self._default_db or ""

    def connect(self, host, port, username, password, auth_source="admin",
                default_database="project_name", *, max_pool_size=50,
                min_pool_size=10, connect_timeout_ms=5000,
                server_selection_timeout_ms=5000, socket_timeout_ms=20000,
                retry_writes=True, retry_reads=True) -> None:
        if motor is None:
            raise ImportError("motor package is required for async MongoDB. Install: pip install motor")
        self._logger = LogHandler.get_logger("general")
        self._default_db = default_database
        kwargs = dict(host=host, port=port, username=username, password=password,
                      maxPoolSize=max_pool_size, minPoolSize=min_pool_size,
                      connectTimeoutMS=connect_timeout_ms,
                      serverSelectionTimeoutMS=server_selection_timeout_ms,
                      socketTimeoutMS=socket_timeout_ms,
                      retryWrites=retry_writes, retryReads=retry_reads)
        if auth_source:
            kwargs["authSource"] = auth_source
        self._client = motor.motor_asyncio.AsyncIOMotorClient(**kwargs)
        self._logger.success("MongoDB (Motor) client created")

    def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            if self._logger:
                self._logger.info("MongoDB connection closed")

    def is_connected(self) -> bool:
        return self._client is not None

    def get_database(self, db_name: str = None) -> "AsyncIOMotorDatabase":
        return self.raw_client[db_name or self._default_db]

    def get_collection(self, collection_name: str, db_name: str = None) -> "AsyncIOMotorCollection":
        return self.get_database(db_name)[collection_name]
