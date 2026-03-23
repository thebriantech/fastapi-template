from __future__ import annotations

from app.db.mongodb_document import MongoDBDocument
from app.db.postgresql_document import PostgreSQLDocument
from app.db.mysql_document import MySQLDocument
from app.db.mssql_document import MSSQLDocument


class UserMongo(MongoDBDocument):
    _collection_name = "users"
    _manager_alias = "default"

    @classmethod
    def ensure_indexes(cls) -> None:
        pass


class UserPg(PostgreSQLDocument):
    _table_name = "users"
    _manager_alias = "postgres"
    _DDL = """
        CREATE TABLE IF NOT EXISTS users (
            username        VARCHAR(255) PRIMARY KEY,
            user_group      VARCHAR(255) NOT NULL,
            email           VARCHAR(255) NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """

    @classmethod
    def ensure_indexes(cls) -> None:
        pass


class UserMySQL(MySQLDocument):
    _table_name = "users"
    _manager_alias = "mysql"
    _DDL = """
        CREATE TABLE IF NOT EXISTS users (
            username        VARCHAR(255) PRIMARY KEY,
            user_group      VARCHAR(255) NOT NULL,
            email           VARCHAR(255) NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """

    @classmethod
    def ensure_indexes(cls) -> None:
        pass


class UserMSSQL(MSSQLDocument):
    _table_name = "users"
    _manager_alias = "mssql"
    _DDL = """
        IF OBJECT_ID(N'users', N'U') IS NULL
        CREATE TABLE users (
            username        NVARCHAR(255) PRIMARY KEY,
            user_group      NVARCHAR(255) NOT NULL,
            email           NVARCHAR(255) NOT NULL,
            hashed_password NVARCHAR(MAX) NOT NULL
        )
    """

    @classmethod
    def ensure_indexes(cls) -> None:
        pass


def get_user_model():
    """Return the right User model class for the configured DB backend.

    Used by the auth module (login / token verification) where a single
    backend is selected via ``db_type`` in the app config.
    """
    from app.configs import ConfigManager
    db = ConfigManager.config.db_type.lower()
    return {
        "mongodb": UserMongo,
        "postgresql": UserPg,
        "postgres": UserPg,
        "pg": UserPg,
        "mysql": UserMySQL,
        "mariadb": UserMySQL,
        "mssql": UserMSSQL,
    }.get(db, UserMongo)
