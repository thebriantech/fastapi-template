"""
Database factory — creates the right manager + connects using config values.

The ``db_type`` config field determines which backend is used:

    db_type = "mongodb"     → MongoDBManager
    db_type = "postgresql"  → PostgreSQLManager
    db_type = "mysql"       → MySQLManager
    db_type = "mssql"       → MSSQLManager

Usage (in main.py lifespan):
    from app.db.factory import create_db_from_config

    manager = create_db_from_config(cfg)
    register_manager("default", manager)
"""

from __future__ import annotations

from typing import Any

from app.db.base_manager import BaseDatabaseManager


def create_db_from_config(cfg: Any, alias: str = "default") -> BaseDatabaseManager:
    """
    Instantiate and **connect** the database manager that matches
    ``cfg.db_type``.

    Args:
        cfg:   An ``AppConfig`` (or any object with the expected attributes).
        alias: Informational — not used here, but handy for logging.

    Returns:
        A connected ``BaseDatabaseManager`` instance.

    Raises:
        ValueError: if ``cfg.db_type`` is not a recognised backend.
    """
    db_type = cfg.db_type.lower().strip()

    if db_type == "mongodb":
        return _create_mongodb(cfg)

    if db_type in ("postgresql", "postgres", "pg"):
        return _create_postgresql(cfg)

    if db_type in ("mysql", "mariadb"):
        return _create_mysql(cfg)

    if db_type in ("mssql", "sqlserver", "mssqlserver"):
        return _create_mssql(cfg)

    raise ValueError(
        f"Unknown db_type '{cfg.db_type}'.  "
        f"Supported values: mongodb, postgresql, mysql, mssql"
    )


# ── Private helpers per backend ────────────────────────────────────────────


def _create_mongodb(cfg: Any) -> BaseDatabaseManager:
    from app.db.mongodb_manager import MongoDBManager

    mgr = MongoDBManager()
    mgr.connect(
        host=cfg.mongodb_host,
        port=cfg.mongodb_port,
        username=cfg.mongodb_username,
        password=cfg.mongodb_password,
        auth_source=cfg.mongodb_auth,
        default_database=cfg.mongodb_database,
        max_pool_size=cfg.mongodb_max_pool_size,
        min_pool_size=cfg.mongodb_min_pool_size,
        connect_timeout_ms=cfg.mongodb_connect_timeout_ms,
        server_selection_timeout_ms=cfg.mongodb_server_selection_timeout_ms,
        socket_timeout_ms=cfg.mongodb_socket_timeout_ms,
    )
    return mgr


def _create_postgresql(cfg: Any) -> BaseDatabaseManager:
    from app.db.postgresql_manager import PostgreSQLManager

    mgr = PostgreSQLManager()
    mgr.connect(
        host=cfg.pg_host,
        port=cfg.pg_port,
        username=cfg.pg_username,
        password=cfg.pg_password,
        database=cfg.pg_database,
        pool_size=cfg.pg_pool_size,
        max_overflow=cfg.pg_max_overflow,
    )
    return mgr


def _create_mysql(cfg: Any) -> BaseDatabaseManager:
    from app.db.mysql_manager import MySQLManager

    mgr = MySQLManager()
    mgr.connect(
        host=cfg.mysql_host,
        port=cfg.mysql_port,
        username=cfg.mysql_username,
        password=cfg.mysql_password,
        database=cfg.mysql_database,
        pool_size=cfg.mysql_pool_size,
        max_overflow=cfg.mysql_max_overflow,
    )
    return mgr


def _create_mssql(cfg: Any) -> BaseDatabaseManager:
    from app.db.mssql_manager import MSSQLManager

    mgr = MSSQLManager()
    mgr.connect(
        host=cfg.mssql_host,
        port=cfg.mssql_port,
        username=cfg.mssql_username,
        password=cfg.mssql_password,
        database=cfg.mssql_database,
        pool_size=cfg.mssql_pool_size,
        max_overflow=cfg.mssql_max_overflow,
        driver=cfg.mssql_driver,
    )
    return mgr
