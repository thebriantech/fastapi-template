"""Database layer — backend-agnostic.

Public API:

    # Abstract interfaces
    from app.db import BaseDatabaseManager, BaseDocument

    # Concrete MongoDB
    from app.db import MongoDBManager, MongoDBDocument

    # Concrete SQL
    from app.db import SQLManager, SQLDocument
    from app.db import PostgreSQLManager, PostgreSQLDocument
    from app.db import MySQLManager, MySQLDocument
    from app.db import MSSQLManager, MSSQLDocument

    # Factory (auto-select backend from config)
    from app.db import create_db_from_config

    # Registry (multi-backend support)
    from app.db import register_manager, get_manager, disconnect_all
"""

from .base_manager import BaseDatabaseManager
from .base_document import BaseDocument
from .mongodb_manager import MongoDBManager
from .mongodb_document import MongoDBDocument, MongoDocument  # MongoDocument kept as alias
from .registry import register_manager, get_manager, disconnect_all, list_managers
from .factory import create_db_from_config

# SQL backends — guarded so the app still works without sqlalchemy installed
try:
    from .sql_manager import SQLManager
    from .sql_document import SQLDocument
    from .postgresql_manager import PostgreSQLManager
    from .postgresql_document import PostgreSQLDocument, PgDocument  # PgDocument kept as alias
    from .mysql_manager import MySQLManager
    from .mysql_document import MySQLDocument
    from .mssql_manager import MSSQLManager
    from .mssql_document import MSSQLDocument
except Exception:          # sqlalchemy or dialect driver not installed
    SQLManager = None       # type: ignore[assignment,misc]
    SQLDocument = None      # type: ignore[assignment,misc]
    PostgreSQLManager = None  # type: ignore[assignment,misc]
    PostgreSQLDocument = None  # type: ignore[assignment,misc]
    PgDocument = None       # type: ignore[assignment,misc]
    MySQLManager = None     # type: ignore[assignment,misc]
    MySQLDocument = None    # type: ignore[assignment,misc]
    MSSQLManager = None     # type: ignore[assignment,misc]
    MSSQLDocument = None    # type: ignore[assignment,misc]

__all__ = [
    # abstract
    "BaseDatabaseManager",
    "BaseDocument",
    # mongo concrete
    "MongoDBManager",
    "MongoDBDocument",
    "MongoDocument",        # backward-compat alias
    # sql shared
    "SQLManager",
    "SQLDocument",
    # sql concrete
    "PostgreSQLManager",
    "PostgreSQLDocument",
    "PgDocument",           # backward-compat alias
    "MySQLManager",
    "MySQLDocument",
    "MSSQLManager",
    "MSSQLDocument",
    # factory
    "create_db_from_config",
    # registry
    "register_manager",
    "get_manager",
    "disconnect_all",
    "list_managers",
]