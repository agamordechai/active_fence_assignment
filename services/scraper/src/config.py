"""Configuration management for the Scraper service"""
import logging
from enum import StrEnum
from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(StrEnum):
    """Log level options"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RunMode(StrEnum):
    """Run mode options"""
    SINGLE = "single"
    SCHEDULER = "scheduler"
    CONTINUOUS = "continuous"


class Settings(BaseSettings):
    """Scraper service settings from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Logging
    log_level: LogLevel = LogLevel.INFO

    # Run Mode
    run_mode: RunMode = RunMode.SINGLE

    # Web Scraping Settings
    rate_limit_delay: float = 2.0
    request_timeout: int = 10
    user_agent: str = "Mozilla/5.0"

    # Data Collection Settings (target_subreddits as comma-separated string)
    target_subreddits: str = "news,politics,unpopularopinion,racism,goodanimemes,RoastMe,conspiracy,controversialopinions,TrueOffMyChest,fightporn,ActualPublicFreakouts,rage,iamatotalpieceofshit,NoahGetTheBoat,awfuleverything,PoliticalDiscussion,TrueCrime"
    posts_per_subreddit: int = 10
    max_users_to_enrich: int = 20

    # Search terms for finding controversial/harmful content
    search_terms: str = "hate,violence,threat,kill,attack,racist,extremist"
    posts_per_search: int = 25

    user_history_days: int = 60

    @cached_property
    def subreddits_list(self) -> list[str]:
        """Get target subreddits as a list"""
        return [s.strip() for s in self.target_subreddits.split(",")]

    @cached_property
    def search_terms_list(self) -> list[str]:
        """Get search terms as a list"""
        return [s.strip() for s in self.search_terms.split(",")]

    # Risk Score Configuration
    critical_risk_threshold: int = 70
    high_risk_threshold: int = 50
    medium_risk_threshold: int = 30
    low_risk_threshold: int = 10

    # Output Settings
    save_raw_data: bool = True
    save_processed_data: bool = True
    generate_reports: bool = True
    output_format: str = "json"

    # Performance & Resource Limits
    max_concurrent_requests: int = 5
    max_memory_mb: int = 2048
    debug_mode: bool = False

    # Retry settings
    max_retries: int = 3
    retry_delay: int = 5

    # Content filtering
    min_post_length: int = 10
    filter_bots: bool = True
    filter_deleted: bool = True

    # API settings (for sending data to API service)
    api_url: str = "http://localhost:8000"
    api_timeout: int = 30

    def get_log_level_int(self) -> int:
        """Get logging level as integer"""
        return getattr(logging, self.log_level.value)

    def print_config(self, logger: logging.Logger) -> None:
        """Print current configuration"""
        logger.info("=" * 80)
        logger.info("SCRAPER CONFIGURATION")
        logger.info("=" * 80)
        logger.info(f"  Run Mode: {self.run_mode}")
        logger.info(f"  Log Level: {self.log_level}")
        logger.info(f"  Target subreddits: {self.subreddits_list}")
        logger.info(f"  Posts per subreddit: {self.posts_per_subreddit}")
        logger.info(f"  Max users to enrich: {self.max_users_to_enrich}")
        logger.info(f"  User history lookback: {self.user_history_days} days")
        logger.info(f"  Rate limit delay: {self.rate_limit_delay}s")
        logger.info(f"  API URL: {self.api_url}")
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
            logging.FileHandler("logs/scraper.log", mode="a"),
        ],
        force=True,
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {settings.log_level}")

    return logger
