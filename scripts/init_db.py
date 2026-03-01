#!/usr/bin/env python3
"""
Database initialisation script.

Creates all SQL tables and indexes for every enabled backend.  MongoDB
collections are created lazily on first insert, so only the indexes are
ensured there.

Usage:
    # Initialise all backends (reads .env / environment variables)
    python -m scripts.init_db

    # Only specific backends
    python -m scripts.init_db --backends mongodb,postgresql

    # Or from the Makefile
    make init-db
"""

from __future__ import annotations

import argparse
import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(backends: set[str] | None = None) -> None:
    # ── Bootstrap logging + config ───────────────────────────────────────
    from app.configs import ConfigManager
    ConfigManager.load()
    cfg = ConfigManager.config

    from app.logs.log_handler import setup_logger, LogHandler

    for name in ("general",):
        setup_logger(
            log_folder=cfg.log_folder,
            logger_name=name,
            rotation=cfg.log_rotation,
            retention=cfg.log_retention,
        )
    logger = LogHandler.get_logger("general")

    # Determine which backends to initialise
    if backends is None:
        raw = cfg.enabled_backends.strip().lower()
        if raw == "all":
            backends = {"mongodb", "postgresql", "mysql", "mssql"}
        else:
            backends = {b.strip() for b in raw.split(",") if b.strip()}

    from app.db import register_manager

    # ── Connect databases ────────────────────────────────────────────────
    if "mongodb" in backends:
        from app.db.mongodb_manager import MongoDBManager
        mongo = MongoDBManager()
        mongo.connect(
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
        register_manager("default", mongo)
        logger.info("MongoDB connected")

    if "postgresql" in backends:
        from app.db.postgresql_manager import PostgreSQLManager
        pg = PostgreSQLManager()
        pg.connect(
            host=cfg.pg_host,
            port=cfg.pg_port,
            username=cfg.pg_username,
            password=cfg.pg_password,
            database=cfg.pg_database,
            pool_size=cfg.pg_pool_size,
            max_overflow=cfg.pg_max_overflow,
        )
        register_manager("postgres", pg)
        logger.info("PostgreSQL connected")

    if "mysql" in backends:
        from app.db.mysql_manager import MySQLManager
        my = MySQLManager()
        my.connect(
            host=cfg.mysql_host,
            port=cfg.mysql_port,
            username=cfg.mysql_username,
            password=cfg.mysql_password,
            database=cfg.mysql_database,
            pool_size=cfg.mysql_pool_size,
            max_overflow=cfg.mysql_max_overflow,
        )
        register_manager("mysql", my)
        logger.info("MySQL connected")

    if "mssql" in backends:
        from app.db.mssql_manager import MSSQLManager
        ms = MSSQLManager()
        ms.connect(
            host=cfg.mssql_host,
            port=cfg.mssql_port,
            username=cfg.mssql_username,
            password=cfg.mssql_password,
            database=cfg.mssql_database,
            pool_size=cfg.mssql_pool_size,
            max_overflow=cfg.mssql_max_overflow,
            driver=cfg.mssql_driver,
        )
        register_manager("mssql", ms)
        logger.info("MSSQL connected")

    # ── Ensure tables / indexes ──────────────────────────────────────────
    from app.modules.items.models import ItemMongo, ItemPg, ItemMySQL, ItemMSSQL
    from app.modules.tasks.models import TaskMongo, TaskPg, TaskMySQL, TaskMSSQL
    from app.modules.user.models import UserMongo, UserPg, UserMySQL, UserMSSQL
    from app.modules.demo.v1.models import DemoMongo, DemoPg, DemoMySQL, DemoMSSQL

    _BACKEND_MODELS = {
        "mongodb":    [ItemMongo, TaskMongo, UserMongo, DemoMongo],
        "postgresql": [ItemPg, TaskPg, UserPg, DemoPg],
        "mysql":      [ItemMySQL, TaskMySQL, UserMySQL, DemoMySQL],
        "mssql":      [ItemMSSQL, TaskMSSQL, UserMSSQL, DemoMSSQL],
    }

    ok = 0
    fail = 0
    for backend_name in sorted(backends):
        models = _BACKEND_MODELS.get(backend_name, [])
        for model_cls in models:
            try:
                model_cls.ensure_indexes()
                logger.info(f"  ✓ {model_cls.__name__}")
                ok += 1
            except Exception as exc:
                logger.error(f"  ✗ {model_cls.__name__}: {exc}")
                fail += 1

    # ── Disconnect ───────────────────────────────────────────────────────
    from app.db import disconnect_all
    disconnect_all()

    print(f"\nDone — {ok} models initialised, {fail} failures.")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialise database tables and indexes")
    parser.add_argument(
        "--backends",
        type=str,
        default=None,
        help="Comma-separated list of backends to init (e.g. mongodb,postgresql). Default: use enabled_backends from config.",
    )
    args = parser.parse_args()

    selected = None
    if args.backends:
        selected = {b.strip().lower() for b in args.backends.split(",") if b.strip()}

    main(selected)
