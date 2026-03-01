"""
Flat, typed configuration with full IDE autocompletion.

Uses pydantic-settings to:
  - load values from .env / environment variables
  - validate & cast types automatically
  - provide dot-access with IDE hints on every field

Usage anywhere in the app:
    from app.configs import ConfigManager

    ConfigManager.config.mongodb_host
    ConfigManager.config.auth_secret_key
    ConfigManager.config.redis_host
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_env_file() -> str | tuple[str, ...]:
    """Return the env file(s) to load based on the APP_ENV variable.

    Resolution order (highest priority first):
      1. ``.env.{APP_ENV}.local``  – machine-specific, never committed
      2. ``.env.{APP_ENV}``        – environment-specific
      3. ``.env``                  – shared defaults

    Only files that actually exist are included.
    """
    import os

    app_env = os.getenv("APP_ENV", "development").strip().lower()
    candidates = [
        f".env.{app_env}.local",
        f".env.{app_env}",
        ".env",
    ]
    # pydantic-settings loads files right-to-left (last = lowest priority),
    # so reverse so that .env is loaded first and overrides come after.
    found = tuple(f for f in reversed(candidates) if os.path.isfile(f))
    return found or ".env"


class AppConfig(BaseSettings):
    """
    Single flat config — every field maps 1-to-1 with an env var.

    IDE autocompletion works on every attribute:
        ConfigManager.config.mongodb_host   ← fully hinted
        ConfigManager.config.auth_algorithm ← fully hinted
    """

    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Environment ──────────────────────────────────────────────────────
    # "development", "staging", or "production"
    app_env: str = "development"

    # ── Application ──────────────────────────────────────────────────────
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_title: str = "FastAPI Template"
    app_description: str = "A modular FastAPI project template"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"

    # ── Logging ──────────────────────────────────────────────────────────
    # Set to false to disable writing log files (console output only).
    log_write_to_file: bool = True
    log_folder: str = "app/logs/logs_data"
    log_rotation: str = "200MB"
    log_retention: str = "7days"

    # ── Auth / Access control ────────────────────────────────────────────
    superuser_username: str = "aiss-admin"

    # ── Database backend ─────────────────────────────────────────────────
    # Which DB backend the auth module uses for login / token verification.
    db_type: str = "mongodb"

    # Comma-separated list of backends to connect on startup.
    # Valid values: mongodb, postgresql, mysql, mssql
    # Set to "all" to enable every backend.
    enabled_backends: str = "all"

    # ── MongoDB ──────────────────────────────────────────────────────────
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_username: str = "admin"
    mongodb_password: str = "password"
    mongodb_auth: str = "admin"
    mongodb_database: str = "project_name"
    mongodb_max_pool_size: int = 50
    mongodb_min_pool_size: int = 10
    mongodb_connect_timeout_ms: int = 5000
    mongodb_server_selection_timeout_ms: int = 5000
    mongodb_socket_timeout_ms: int = 20000

    # ── PostgreSQL ───────────────────────────────────────────────────────
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_username: str = "postgres"
    pg_password: str = "password"
    pg_database: str = "project_name"
    pg_pool_size: int = 10
    pg_max_overflow: int = 20

    # ── MySQL / MariaDB ──────────────────────────────────────────────────
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_username: str = "root"
    mysql_password: str = "password"
    mysql_database: str = "project_name"
    mysql_pool_size: int = 10
    mysql_max_overflow: int = 20

    # ── MSSQL (SQL Server) ───────────────────────────────────────────────
    mssql_host: str = "localhost"
    mssql_port: int = 1433
    mssql_username: str = "sa"
    mssql_password: str = "password"
    mssql_database: str = "project_name"
    mssql_pool_size: int = 10
    mssql_max_overflow: int = 20
    mssql_driver: str = "ODBC Driver 18 for SQL Server"

    # ── Auth / JWT ───────────────────────────────────────────────────────
    auth_secret_key: str = "change-me"
    auth_algorithm: str = "HS256"
    auth_expire_seconds: int = 3600

    # ── Redis ────────────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""

    # ── S3 / MinIO storage (optional) ────────────────────────────────────
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_endpoint: str = ""
    s3_bucket: str = ""

    # ── OpenTelemetry tracing (optional) ─────────────────────────────────
    trace_endpoint: str = ""
    trace_service_name: str = "fastapi-template"

    # ── Encryption key files (optional) ──────────────────────────────────
    crypt_aes_key_file: str = ""
    crypt_hmac_key_file: str = ""


# ─── Singleton holder ───────────────────────────────────────────────────────


class ConfigManager:
    """
    Singleton config holder.

    Call ``ConfigManager.load()`` once during startup, then import anywhere:

        from app.configs import ConfigManager
        ConfigManager.config.mongodb_host
    """

    config: AppConfig  # ← type hint gives IDE completion on .config

    @classmethod
    def load(cls) -> AppConfig:
        """Parse environment / .env and store the config singleton."""
        cls.config = AppConfig()
        return cls.config

    @classmethod
    def reload(cls) -> AppConfig:
        """Re-read env vars (useful in tests)."""
        return cls.load()


# Backward-compatible helper
def load_configs(config_folder: str = "app/configs") -> AppConfig:
    """Entry-point called at startup to initialise configuration."""
    return ConfigManager.load()
