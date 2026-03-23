from app.db.sql_document import SQLDocument


class MySQLDocument(SQLDocument):
    _manager_alias: str = "mysql"
