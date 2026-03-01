"""
Application entry-point.

Startup / shutdown logic lives in the ``lifespan`` async context manager
(the modern replacement for @app.on_event("startup") / ("shutdown")).

Order of operations at startup:
  1. Loggers are registered
  2. ConfigManager loads .env / environment variables
  3. MongoDB connection is established (inside lifespan)
  4. Module routers are included

Because routers access LogHandler and ConfigManager at *class-body* time
(import time), steps 1-2 MUST happen before the router modules are imported.
"""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

# ── Step 1 & 2: bootstrap config + logging before any module import ──────────
from app.configs import ConfigManager

ConfigManager.load()

from app.logs.log_handler import setup_logger, LogHandler

# Apply log_write_to_file config before registering any logger
LogHandler.set_write_to_file(ConfigManager.config.log_write_to_file)

_LOGGERS = [
    "general",
    "auth",
    "user_management",
    # add more logger names here as you add modules
]

for _name in _LOGGERS:
    setup_logger(
        log_folder=ConfigManager.config.log_folder,
        logger_name=_name,
        rotation=ConfigManager.config.log_rotation,
        retention=ConfigManager.config.log_retention,
    )

# ── Now safe to import module routers (they read config / loggers) ───────────
from app.modules import (
    auth_router,
    user_management_router,
    items_router,
    items_v2_router,
    tasks_router,
)


# ── Lifespan: heavy I/O init (DB, Redis …) on startup, cleanup on shutdown ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once when the server starts, yields while the server is running,
    then runs the shutdown block when the server stops.
    """
    logger = LogHandler.get_logger("general")

    # --- startup -----------------------------------------------------------
    logger.info(f"Starting server – environment: {ConfigManager.config.app_env}")
    logger.info("Initializing resources …")

    # ── Database(s) ────────────────────────────────────────────────────────
    from app.db import register_manager, disconnect_all
    from app.db.mongodb_manager import MongoDBManager
    from app.db.postgresql_manager import PostgreSQLManager
    from app.db.mysql_manager import MySQLManager
    from app.db.mssql_manager import MSSQLManager

    cfg = ConfigManager.config

    # Parse enabled backends from config
    _raw = cfg.enabled_backends.strip().lower()
    if _raw == "all":
        _enabled = {"mongodb", "postgresql", "mysql", "mssql"}
    else:
        _enabled = {b.strip() for b in _raw.split(",") if b.strip()}

    # 1. MongoDB — primary / default
    if "mongodb" in _enabled:
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

    # 2. PostgreSQL
    if "postgresql" in _enabled:
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

    # 3. MySQL
    if "mysql" in _enabled:
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

    # 4. MSSQL
    if "mssql" in _enabled:
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

    # ── Ensure indexes / tables for all models ─────────────────────────────
    from app.modules.items.models import ItemMongo, ItemPg, ItemMySQL, ItemMSSQL
    from app.modules.tasks.models import TaskMongo, TaskPg, TaskMySQL, TaskMSSQL
    from app.modules.user.models import UserMongo, UserPg, UserMySQL, UserMSSQL

    # All per-backend model classes that need ensure_indexes
    _ALL_MODELS = [
        # Items
        ItemMongo, ItemPg, ItemMySQL, ItemMSSQL,
        # Tasks
        TaskMongo, TaskPg, TaskMySQL, TaskMSSQL,
        # Users
        UserMongo, UserPg, UserMySQL, UserMSSQL,
    ]

    for model_cls in _ALL_MODELS:
        try:
            model_cls.ensure_indexes()
        except Exception as exc:
            logger.warning(f"ensure_indexes failed for {model_cls.__name__}: {exc}")

    logger.success("Server startup complete")

    yield  # ← server is running and accepting requests

    # --- shutdown ----------------------------------------------------------
    logger.info("Shutting down – releasing resources …")
    disconnect_all()


# ── App factory ──────────────────────────────────────────────────────────────
server = FastAPI(
    title=ConfigManager.config.app_title,
    description=ConfigManager.config.app_description,
    version=ConfigManager.config.app_version,
    lifespan=lifespan,
)

# Register module routers
_prefix = ConfigManager.config.api_prefix
server.include_router(auth_router, prefix=_prefix)
server.include_router(user_management_router, prefix=_prefix)
server.include_router(items_router, prefix=_prefix)
server.include_router(items_v2_router, prefix=_prefix.replace("/v1", "/v2"))
server.include_router(tasks_router, prefix=_prefix)


@server.get("/health", tags=["Health"])
def health_check():
    from app.db import list_managers

    db_status = {
        alias: mgr.is_connected() for alias, mgr in list_managers().items()
    }
    return {"status": "ok", "databases": db_status}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:server",
        host=ConfigManager.config.app_host,
        port=ConfigManager.config.app_port,
        reload=True,
    )
