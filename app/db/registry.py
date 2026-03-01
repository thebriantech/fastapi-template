"""
Database manager registry.

Holds named ``BaseDatabaseManager`` instances so that:
  - Multiple backends can coexist (Mongo + Postgres, two Mongo clusters, …)
  - Models look up their manager by alias at runtime
  - The service layer never imports a concrete manager

Usage:
    # At startup (main.py lifespan)
    from app.db.registry import register_manager, get_manager

    mongo = MongoDBManager()
    mongo.connect(...)
    register_manager("default", mongo)

    # In a model / anywhere
    mgr = get_manager("default")   # or just get_manager()
"""

from __future__ import annotations

from typing import Dict

from app.db.base_manager import BaseDatabaseManager

_managers: Dict[str, BaseDatabaseManager] = {}


def register_manager(alias: str, manager: BaseDatabaseManager) -> None:
    """
    Register a database manager under *alias*.

    The first registered manager also becomes the ``"default"`` if that
    alias hasn't been taken yet.
    """
    _managers[alias] = manager
    if "default" not in _managers:
        _managers["default"] = manager


def get_manager(alias: str = "default") -> BaseDatabaseManager:
    """
    Retrieve a previously registered manager.

    Raises ``KeyError`` with a helpful message if not found.
    """
    try:
        return _managers[alias]
    except KeyError:
        available = ", ".join(_managers) or "(none)"
        raise KeyError(
            f"No database manager registered under '{alias}'. "
            f"Available: {available}.  "
            f"Did you call register_manager() in your lifespan?"
        )


def disconnect_all() -> None:
    """Disconnect every registered manager (call at shutdown)."""
    for mgr in _managers.values():
        mgr.disconnect()
    _managers.clear()


def list_managers() -> Dict[str, BaseDatabaseManager]:
    """Return a copy of all registered managers (for health checks, etc.)."""
    return dict(_managers)
