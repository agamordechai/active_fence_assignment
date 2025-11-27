"""Main entry point for the Reddit Hate Speech Detection System"""
import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

    # Load configuration from environment variables
    target_subreddits_str = os.getenv('TARGET_SUBREDDITS', 'news,worldnews,politics,unpopularopinion,TrueOffMyChest')
    target_subreddits = [s.strip() for s in target_subreddits_str.split(',')]

    posts_per_subreddit = int(os.getenv('POSTS_PER_SUBREDDIT', '25'))
    max_users_to_enrich = int(os.getenv('MAX_USERS_TO_ENRICH', '20'))

    # Print configuration (always visible)
    print("\n" + "=" * 80, flush=True)
    print("📋 CONFIGURATION", flush=True)
    print("=" * 80, flush=True)
    print(f"  Target subreddits: {target_subreddits}", flush=True)
    print(f"  Posts per subreddit: {posts_per_subreddit}", flush=True)
    print(f"  Max users to enrich: {max_users_to_enrich}", flush=True)
    print("=" * 80, flush=True)
    print("", flush=True)

    logger.info(f"Configuration loaded: {len(target_subreddits)} subreddits, {posts_per_subreddit} posts each")

    # Initialize and run pipeline
    pipeline = DataPipeline()

    try:
        results = pipeline.run_full_pipeline(
            subreddits=target_subreddits,
            posts_per_subreddit=posts_per_subreddit,
            max_users_to_enrich=max_users_to_enrich
        )

        print("\n" + "=" * 80, flush=True)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY!", flush=True)
        print("=" * 80, flush=True)
        logger.info("Generated files:")
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

