"""Configuration management for the API service"""
import logging
from enum import StrEnum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(StrEnum):
    """Log level options"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """API service settings from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Logging
    log_level: LogLevel = LogLevel.INFO

    # Database Settings
    database_url: str = "sqlite:///./data/reddit_detection.db"

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Debug mode
    debug_mode: bool = False

    def get_log_level_int(self) -> int:
        """Get logging level as integer"""
        return getattr(logging, self.log_level.value)

    def print_config(self, logger: logging.Logger) -> None:
        """Print current configuration"""
        logger.info("=" * 80)
        logger.info("API CONFIGURATION")
        logger.info("=" * 80)
        logger.info(f"  Log Level: {self.log_level}")
        logger.info(f"  Database URL: {self.database_url}")
        logger.info(f"  Host: {self.host}")
        logger.info(f"  Port: {self.port}")
        logger.info("=" * 80)


# Global settings instance
settings = Settings()


def setup_logging() -> logging.Logger:
    """Setup logging configuration from settings"""
    log_level = settings.get_log_level_int()

    # Create logs directory
    Path("logs").mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/api.log", mode="a"),
        ],
        force=True,
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {settings.log_level}")

    return logger