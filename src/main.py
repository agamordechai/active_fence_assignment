"""Main entry point for the Reddit Hate Speech Detection System"""
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/app.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main application entry point"""
    logger.info("Reddit Hate Speech Detection System starting...")
    logger.info("System initialized successfully")

    # TODO: Implement data collection, enrichment, and scoring
    logger.info("Ready to collect and analyze Reddit data")


if __name__ == "__main__":
    # Create necessary directories
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)

    main()

