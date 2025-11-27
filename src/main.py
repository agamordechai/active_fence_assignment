"""Main entry point for the Reddit Hate Speech Detection System"""
import logging
import sys
from pathlib import Path

from src.pipeline import DataPipeline

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

    # Define target subreddits for controversial/harmful content monitoring
    # These are public subreddits where controversial discussions happen
    target_subreddits = [
        'news',
        'worldnews',
        'politics',
        'unpopularopinion',
        'TrueOffMyChest',
    ]

    # Initialize and run pipeline
    pipeline = DataPipeline()

    try:
        results = pipeline.run_full_pipeline(
            subreddits=target_subreddits,
            posts_per_subreddit=25,  # 25 posts per subreddit = ~125 total
            max_users_to_enrich=20   # Enrich top 20 users
        )

        logger.info("\n✅ Pipeline completed successfully!")
        logger.info(f"Generated files:")
        for file_type, file_path in results['files'].items():
            logger.info(f"  - {file_type}: {file_path}")

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Create necessary directories
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)

    main()

