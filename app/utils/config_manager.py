"""
Config manager — YAML-first, env-var override.

Single config file: app/configs/config.yaml
The active section is chosen by the APP_ENV environment variable (default: development).

Load order (highest priority first):
  1. Environment variables              (secrets, CI/CD overrides)
  2. config.yaml[APP_ENV] section       (environment-specific values)

Usage anywhere in the app:
    from app.configs import ConfigManager
    from app.utils.config_manager import ConfigManager  # direct import

    ConfigManager.config.mongodb_host
    ConfigManager.config.auth_secret_key
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type

import yaml
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


# ── YAML settings source ─────────────────────────────────────────────────────

class YamlConfigSource(PydanticBaseSettingsSource):
    """
    Reads the section matching APP_ENV from app/configs/config.yaml.
    Keys must match pydantic field names exactly.
    """

    def __init__(
        self,
        settings_cls: Type[BaseSettings],
        yaml_file: str | Path,
        env: str,
    ) -> None:
        super().__init__(settings_cls)
        self._data: Dict[str, Any] = {}
        path = Path(yaml_file)
        if path.is_file():
            with path.open("r", encoding="utf-8") as f:
                all_sections = yaml.safe_load(f) or {}
            section = all_sections.get(env, {})
            if isinstance(section, dict):
                # Strip private/anchor keys (prefixed with _)
                self._data = {k: v for k, v in section.items() if not k.startswith("_")}

    def get_field_value(self, field: FieldInfo, field_name: str) -> Tuple[Any, str, bool]:
        return self._data.get(field_name), field_name, False

    def __call__(self) -> Dict[str, Any]:
        # Return all keys from YAML — declared fields are validated/typed by
        # pydantic; any extra keys are stored in model_extra (extra="allow").
        return dict(self._data)


# ── Locate config.yaml ───────────────────────────────────────────────────────

def _config_file() -> Path:
    candidate = Path(__file__).parent.parent / "configs" / "config.yaml"
    if candidate.is_file():
        return candidate
    return Path("app/configs/config.yaml")


# ── AppConfig ─────────────────────────────────────────────────────────────────

class AppConfig(BaseSettings):
    """
    Typed schema for application configuration.

    No hardcoded defaults — all values are loaded from config.yaml (by
    environment section) and can be overridden by environment variables.

    Extra keys in config.yaml that are not declared as fields are accepted
    and accessible via:
        ConfigManager.config.get("my_custom_key")
        ConfigManager.config.my_custom_key       # direct attribute access
    """

    model_config = SettingsConfigDict(extra="allow")

    # ── Environment ──────────────────────────────────────────────────────
    app_env: str

    # ── Application ──────────────────────────────────────────────────────
    app_host: str
    app_port: int
    app_title: str
    app_description: str
    app_version: str
    api_prefix: str

    # ── Logging ──────────────────────────────────────────────────────────
    log_write_to_file: bool
    log_folder: str
    log_rotation: str
    log_retention: str

    # ── Auth / Access control ────────────────────────────────────────────
    superuser_username: str

    # ── Database backend ─────────────────────────────────────────────────
    db_type: str
    enabled_backends: str

    # ── MongoDB ──────────────────────────────────────────────────────────
    mongodb_host: str
    mongodb_port: int
    mongodb_username: str
    mongodb_password: str
    mongodb_auth: str
    mongodb_database: str
    mongodb_max_pool_size: int
    mongodb_min_pool_size: int
    mongodb_connect_timeout_ms: int
    mongodb_server_selection_timeout_ms: int
    mongodb_socket_timeout_ms: int

    # ── PostgreSQL ───────────────────────────────────────────────────────
    pg_host: str
    pg_port: int
    pg_username: str
    pg_password: str
    pg_database: str
    pg_pool_size: int
    pg_max_overflow: int

    # ── MySQL / MariaDB ──────────────────────────────────────────────────
    mysql_host: str
    mysql_port: int
    mysql_username: str
    mysql_password: str
    mysql_database: str
    mysql_pool_size: int
    mysql_max_overflow: int

    # ── MSSQL (SQL Server) ───────────────────────────────────────────────
    mssql_host: str
    mssql_port: int
    mssql_username: str
    mssql_password: str
    mssql_database: str
    mssql_pool_size: int
    mssql_max_overflow: int
    mssql_driver: str

    # ── Auth / JWT ───────────────────────────────────────────────────────
    auth_secret_key: str
    auth_algorithm: str
    auth_expire_seconds: int

    # ── Redis ────────────────────────────────────────────────────────────
    redis_host: str
    redis_port: int
    redis_password: str

    # ── Optional integrations (empty string = disabled) ──────────────────
    s3_access_key_id: Optional[str] = ""
    s3_secret_access_key: Optional[str] = ""
    s3_endpoint: Optional[str] = ""
    s3_bucket: Optional[str] = ""

    trace_endpoint: Optional[str] = ""
    trace_service_name: Optional[str] = ""

    crypt_aes_key_file: Optional[str] = ""
    crypt_hmac_key_file: Optional[str] = ""

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve any config value by name — including keys not declared as
        fields in this class (extra keys from config.yaml or env vars).

        Examples:
            cfg.get("mongodb_host")
            cfg.get("my_custom_key", "fallback")
        """
        return getattr(self, key, default)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple:
        """
        Load order (highest priority first):
          1. Environment variables
          2. config.yaml[APP_ENV] section
        """
        app_env = os.getenv("APP_ENV", "development").strip().lower()
        return (
            env_settings,
            YamlConfigSource(settings_cls, _config_file(), app_env),
        )


# ── ConfigManager ─────────────────────────────────────────────────────────────

class ConfigManager:
    """
    Singleton config holder.

    Call ``ConfigManager.load()`` once during startup, then import anywhere:

        from app.configs import ConfigManager
        ConfigManager.config.mongodb_host
    """

    config: AppConfig

    @classmethod
    def load(cls) -> AppConfig:
        """Load config.yaml[APP_ENV] + env vars and store the singleton."""
        cls.config = AppConfig()
        return cls.config

    @classmethod
    def reload(cls) -> AppConfig:
        """Re-read config (useful in tests or after env var changes)."""
        return cls.load()


# Backward-compatible helper
def load_configs(config_folder: str = "app/configs") -> AppConfig:
    return ConfigManager.load()
