from app.db.mongodb_document import MongoDBDocument
from app.db.postgresql_document import PostgreSQLDocument
from app.db.mysql_document import MySQLDocument
from app.db.mssql_document import MSSQLDocument


class ItemMongo(MongoDBDocument):
    _collection_name = "items"
    _manager_alias = "default"

    @classmethod
    def ensure_indexes(cls) -> None:
        pass


class ItemPg(PostgreSQLDocument):
    _table_name = "items"
    _manager_alias = "postgres"
    _DDL = """
        CREATE TABLE IF NOT EXISTS items (
            item_id     VARCHAR(64) PRIMARY KEY,
            name        VARCHAR(255) NOT NULL,
            description TEXT,
            price       DOUBLE PRECISION NOT NULL DEFAULT 0,
            quantity    INTEGER NOT NULL DEFAULT 0
        )
    """

    @classmethod
    def ensure_indexes(cls) -> None:
        pass


class ItemMySQL(MySQLDocument):
    _table_name = "items"
    _manager_alias = "mysql"
    _DDL = """
        CREATE TABLE IF NOT EXISTS items (
            item_id     VARCHAR(64) PRIMARY KEY,
            name        VARCHAR(255) NOT NULL,
            description TEXT,
            price       DOUBLE NOT NULL DEFAULT 0,
            quantity    INT NOT NULL DEFAULT 0
        )
    """

    @classmethod
    def ensure_indexes(cls) -> None:
        pass


class ItemMSSQL(MSSQLDocument):
    _table_name = "items"
    _manager_alias = "mssql"
    _DDL = """
        IF OBJECT_ID(N'items', N'U') IS NULL
        CREATE TABLE items (
            item_id     NVARCHAR(64) PRIMARY KEY,
            name        NVARCHAR(255) NOT NULL,
            description NVARCHAR(MAX),
            price       FLOAT NOT NULL DEFAULT 0,
            quantity    INT NOT NULL DEFAULT 0
        )
    """

    @classmethod
    def ensure_indexes(cls) -> None:
        pass
