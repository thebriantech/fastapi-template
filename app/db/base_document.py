"""
Backend-agnostic abstract base document.

Defines the CRUD contract that every database backend document class must
implement.  Service code programs against *this* interface, so swapping
MongoDB for PostgreSQL (or anything else) only requires writing a new
subclass — zero changes in routes / services.

Usage:
    # In a MongoDB project:
    from app.db.mongodb_document import MongoDBDocument

    class Item(MongoDBDocument):
        _collection_name = "items"

    # In a PostgreSQL project:
    from app.db.postgresql_document import PostgreSQLDocument

    class Item(PostgreSQLDocument):
        _table_name = "items"
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseDocument(ABC):
    """
    Abstract base for all document / table model classes.

    Every concrete implementation (``MongoDocument``, ``PgDocument``, …)
    must implement these class-methods and return a **consistent** dict
    contract so the service layer never has to care about the backend.

    Return-value conventions
    ────────────────────────
    Success → ``{"status": True, ...backend-specific keys...}``
    Failure → ``{"status": False, "error": "<message>"}``
    """

    # ── Create ───────────────────────────────────────────────────

    @classmethod
    @abstractmethod
    def insert_one(cls, document: dict) -> dict:
        """Insert a single document / row."""

    @classmethod
    @abstractmethod
    def insert_many(cls, documents: List[dict]) -> dict:
        """Insert multiple documents / rows."""

    # ── Read ─────────────────────────────────────────────────────

    @classmethod
    @abstractmethod
    def find_one(cls, query: dict, **kwargs: Any) -> dict:
        """Find a single document / row matching *query*."""

    @classmethod
    @abstractmethod
    def find(cls, query: dict, **kwargs: Any) -> dict:
        """Find multiple documents / rows matching *query*."""

    @classmethod
    @abstractmethod
    def count(cls, query: Optional[dict] = None) -> dict:
        """Count documents / rows matching *query*."""

    @classmethod
    @abstractmethod
    def get_all(cls, **kwargs: Any) -> dict:
        """Return every document / row in the collection / table."""

    # ── Update ───────────────────────────────────────────────────

    @classmethod
    @abstractmethod
    def update_one(cls, query: dict, update: dict, **kwargs: Any) -> dict:
        """Update a single document / row matching *query*."""

    @classmethod
    @abstractmethod
    def update_many(cls, query: dict, update: dict, **kwargs: Any) -> dict:
        """Update multiple documents / rows matching *query*."""

    @classmethod
    @abstractmethod
    def upsert_one(cls, query: dict, document: dict) -> dict:
        """Update-or-insert."""

    # ── Delete ───────────────────────────────────────────────────

    @classmethod
    @abstractmethod
    def delete_one(cls, query: dict) -> dict:
        """Delete a single document / row matching *query*."""

    @classmethod
    @abstractmethod
    def delete_many(cls, query: dict) -> dict:
        """Delete all documents / rows matching *query*."""

    # ── Schema / index management ────────────────────────────────

    @classmethod
    def ensure_indexes(cls) -> None:
        """
        Override in subclasses to declare whatever indexes / constraints
        this collection / table needs.  Called once at startup.
        """

    # ── Custom query escape hatch ────────────────────────────────

    @classmethod
    @abstractmethod
    def execute_raw(cls, operation: Any, **kwargs: Any) -> dict:
        """
        Run an **arbitrary backend-specific** operation.

        For MongoDB this might be an aggregation pipeline; for SQL it
        might be a raw query string.  This is the escape hatch for
        queries that don't fit the CRUD helpers above.

        Returns:
            {"status": True,  "result": <anything>}
            {"status": False, "error": "<msg>"}
        """
