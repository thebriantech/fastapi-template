"""Database layer — async-native backend-agnostic interface.

Public API:

    from app.db import BaseDocument, BaseDatabaseManager
    from app.db import MongoDBManager, MongoDBDocument
    from app.db import PostgreSQLManager, PostgreSQLDocument
    from app.db import MySQLManager, MySQLDocument
    from app.db import MSSQLManager, MSSQLDocument
    from app.db import register_manager, get_manager, disconnect_all
"""

from .base_manager import BaseDatabaseManager
from .base_document import BaseDocument
from .mongodb_manager import MongoDBManager
from .mongodb_document import MongoDBDocument
from .registry import register_manager, get_manager, disconnect_all, list_managers
from .factory import create_db_from_config

try:
    from .sql_manager import SQLManager
    from .postgresql_manager import PostgreSQLManager
    from .postgresql_document import PostgreSQLDocument
    from .mysql_manager import MySQLManager
    from .mysql_document import MySQLDocument
    from .mssql_manager import MSSQLManager
    from .mssql_document import MSSQLDocument
except Exception:
    SQLManager = None
    PostgreSQLManager = None
    PostgreSQLDocument = None
    MySQLManager = None
    MySQLDocument = None
    MSSQLManager = None
    MSSQLDocument = None

__all__ = [
    "BaseDatabaseManager", "BaseDocument",
    "MongoDBManager", "MongoDBDocument",
    "SQLManager",
    "PostgreSQLManager", "PostgreSQLDocument",
    "MySQLManager", "MySQLDocument",
    "MSSQLManager", "MSSQLDocument",
    "create_db_from_config",
    "register_manager", "get_manager", "disconnect_all", "list_managers",
]