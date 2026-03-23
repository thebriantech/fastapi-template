from app.db.mongodb_document import MongoDBDocument
from app.db.postgresql_document import PostgreSQLDocument
from app.db.mysql_document import MySQLDocument
from app.db.mssql_document import MSSQLDocument


class TaskMongo(MongoDBDocument):
    _collection_name = "tasks"
    _manager_alias = "default"

    @classmethod
    def ensure_indexes(cls) -> None:
        pass


class TaskPg(PostgreSQLDocument):
    _table_name = "tasks"
    _manager_alias = "postgres"
    _DDL = """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id     VARCHAR(64) PRIMARY KEY,
            title       VARCHAR(255) NOT NULL,
            description TEXT,
            status      VARCHAR(32) NOT NULL DEFAULT 'todo',
            assignee    VARCHAR(255) NOT NULL
        )
    """

    @classmethod
    def ensure_indexes(cls) -> None:
        pass


class TaskMySQL(MySQLDocument):
    _table_name = "tasks"
    _manager_alias = "mysql"
    _DDL = """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id     VARCHAR(64) PRIMARY KEY,
            title       VARCHAR(255) NOT NULL,
            description TEXT,
            status      VARCHAR(32) NOT NULL DEFAULT 'todo',
            assignee    VARCHAR(255) NOT NULL
        )
    """

    @classmethod
    def ensure_indexes(cls) -> None:
        pass


class TaskMSSQL(MSSQLDocument):
    _table_name = "tasks"
    _manager_alias = "mssql"
    _DDL = """
        IF OBJECT_ID(N'tasks', N'U') IS NULL
        CREATE TABLE tasks (
            task_id     NVARCHAR(64) PRIMARY KEY,
            title       NVARCHAR(255) NOT NULL,
            description NVARCHAR(MAX),
            status      NVARCHAR(32) NOT NULL DEFAULT 'todo',
            assignee    NVARCHAR(255) NOT NULL
        )
    """

    @classmethod
    def ensure_indexes(cls) -> None:
        pass
