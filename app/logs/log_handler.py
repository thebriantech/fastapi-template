from loguru import logger
from typing import Dict
import os


class LogHandler:
    loggers_data: Dict = {}
    _write_to_file: bool = True  # default; overridden by config

    @classmethod
    def set_write_to_file(cls, enabled: bool) -> None:
        """Enable or disable file logging globally.

        Call **before** :func:`setup_logger` so that subsequent
        ``register()`` calls respect the setting.
        """
        cls._write_to_file = enabled

    @classmethod
    def register(
            cls,
            log_folder: str = None,
            logger_name: str = None,
            rotation: str = "200MB",
            retention: str = "7days",
            write_to_file: bool | None = None,
        ):
        assert logger_name is not None, "You must specify logger_name!"
        assert logger_name not in cls.loggers_data.keys(), (
            f"Logger name {logger_name} already existed"
        )

        # Per-call override > class-level default
        should_write = write_to_file if write_to_file is not None else cls._write_to_file

        if should_write:
            assert os.path.exists(log_folder), (
                f"Log folder {log_folder} does not exist"
            )
            log_path = os.path.join(log_folder, f"{logger_name}.txt")
            logger.add(
                log_path,
                filter=lambda record: record["extra"]["logger_name"] == logger_name,
                enqueue=False,
                rotation=rotation,
                retention=retention,
            )

        cls.loggers_data[logger_name] = {
            "logger": logger.bind(logger_name=logger_name),
            "log_folder": log_folder,
            "rotation": rotation,
            "retention": retention,
            "write_to_file": should_write,
        }

    @classmethod
    def get_logger(
            cls,
            logger_name: str,
        ) -> logger:
        assert logger_name in cls.loggers_data.keys(), (
            f"Logger name {logger_name} does not existed"
        )
        return cls.loggers_data[logger_name]["logger"]


def setup_logger(
        log_folder: str = "app/logs/logs_data",
        logger_name: str = "general",
        rotation: str = "200MB",
        retention: str = "7days",
        write_to_file: bool | None = None,
    ):
    """Register a named logger.

    Args:
        log_folder: Directory for log files.
        logger_name: Unique logger identifier.
        rotation: Log file rotation size/interval (e.g. "200MB", "1 day").
        retention: How long to keep old log files (e.g. "7days", "1 month").
        write_to_file: Override the global ``LogHandler._write_to_file``
            setting for this specific logger.  ``None`` means use the
            global default.
    """
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    LogHandler.register(
        log_folder=log_folder,
        logger_name=logger_name,
        rotation=rotation,
        retention=retention,
        write_to_file=write_to_file,
    )


if __name__ == "__main__":
    LogHandler.register(log_folder="./logs_data", logger_name="test")
    test_logger = LogHandler.get_logger("test")
    test_logger.error("Test")
