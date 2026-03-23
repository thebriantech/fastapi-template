from app.db.sql_document import SQLDocument


class PostgreSQLDocument(SQLDocument):
    _manager_alias: str = "postgres"
