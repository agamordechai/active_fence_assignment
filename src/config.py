"""Configuration management for the Reddit Hate Speech Detection System"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration from environment variables"""

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_LEVEL_MAP = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    @classmethod
    def get_log_level(cls):
        """Get logging level as integer"""
        return cls.LOG_LEVEL_MAP.get(cls.LOG_LEVEL, logging.INFO)

    # Run Mode
    RUN_MODE = os.getenv('RUN_MODE', 'single').lower()  # single, scheduler, continuous

    # Web Scraping Settings
    RATE_LIMIT_DELAY = float(os.getenv('RATE_LIMIT_DELAY', '2.0'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))
    USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0')

    # Data Collection Settings
    TARGET_SUBREDDITS = [s.strip() for s in os.getenv('TARGET_SUBREDDITS',
                         'news,politics,unpopularopinion,racism,goodanimemes,RoastMe').split(',')]
    POSTS_PER_SUBREDDIT = int(os.getenv('POSTS_PER_SUBREDDIT', '10'))
    MAX_USERS_TO_ENRICH = int(os.getenv('MAX_USERS_TO_ENRICH', '20'))
    USER_HISTORY_DAYS = int(os.getenv('USER_HISTORY_DAYS', '60'))
    MAX_USER_CONTENT = int(os.getenv('MAX_USER_CONTENT', '100'))

    # Risk Score Configuration
    CRITICAL_RISK_THRESHOLD = int(os.getenv('CRITICAL_RISK_THRESHOLD', '70'))
    HIGH_RISK_THRESHOLD = int(os.getenv('HIGH_RISK_THRESHOLD', '50'))
    MEDIUM_RISK_THRESHOLD = int(os.getenv('MEDIUM_RISK_THRESHOLD', '30'))
    LOW_RISK_THRESHOLD = int(os.getenv('LOW_RISK_THRESHOLD', '10'))

    # Output Settings
    SAVE_RAW_DATA = os.getenv('SAVE_RAW_DATA', 'true').lower() == 'true'
    SAVE_PROCESSED_DATA = os.getenv('SAVE_PROCESSED_DATA', 'true').lower() == 'true'
    GENERATE_REPORTS = os.getenv('GENERATE_REPORTS', 'true').lower() == 'true'
    OUTPUT_FORMAT = os.getenv('OUTPUT_FORMAT', 'json').lower()

    # Performance & Resource Limits
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
    MAX_MEMORY_MB = int(os.getenv('MAX_MEMORY_MB', '2048'))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

    # Retry settings
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))

    # Content filtering
    MIN_POST_LENGTH = int(os.getenv('MIN_POST_LENGTH', '10'))
    FILTER_BOTS = os.getenv('FILTER_BOTS', 'true').lower() == 'true'
    FILTER_DELETED = os.getenv('FILTER_DELETED', 'true').lower() == 'true'

    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("\n" + "=" * 80)
        print("📋 CONFIGURATION")
        print("=" * 80)
        print(f"  Run Mode: {cls.RUN_MODE}")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print(f"  Target subreddits: {cls.TARGET_SUBREDDITS}")
        print(f"  Posts per subreddit: {cls.POSTS_PER_SUBREDDIT}")
        print(f"  Max users to enrich: {cls.MAX_USERS_TO_ENRICH}")
        print(f"  User history lookback: {cls.USER_HISTORY_DAYS} days")
        print(f"  Rate limit delay: {cls.RATE_LIMIT_DELAY}s")
        print("=" * 80)
        print("")


def setup_logging():
    """Setup logging configuration from environment variables"""
    log_level = Config.get_log_level()

    # Create logs directory
    Path("logs").mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/app.log', mode='a')
        ],
        force=True  # Force reconfiguration if already configured
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {Config.LOG_LEVEL}")

    return logger

