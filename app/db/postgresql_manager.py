from app.db.sql_manager import SQLManager


class PostgreSQLManager(SQLManager):
    _dialect_driver = "postgresql+asyncpg"
