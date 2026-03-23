from app.db.sql_manager import SQLManager


class MySQLManager(SQLManager):
    _dialect_driver = "mysql+aiomysql"
