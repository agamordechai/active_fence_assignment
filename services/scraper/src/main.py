"""Main entry point for the Reddit Hate Speech Detection Scraper"""
import time
from pathlib import Path

from src.config import settings, setup_logging
from src.pipeline import DataPipeline

# Setup logging from config
logger = setup_logging()


def run():
    """Run pipeline continuously with minimal delay"""
    logger.info("Running pipeline continuously - will execute repeatedly")
    logger.info("Press Ctrl+C to stop")

    pipeline = DataPipeline()
    run_count = 0

    try:
        while True:
            run_count += 1
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Starting continuous run #{run_count}")
            logger.info(f"{'=' * 80}")

            try:
                pipeline.run_full_pipeline(
                    subreddits=settings.subreddits_list,
                    posts_per_subreddit=settings.posts_per_subreddit,
                    max_users_to_enrich=settings.max_users_to_enrich,
                    search_terms=settings.search_terms_list,
                    posts_per_search=settings.posts_per_search
                )
                logger.info(f"Continuous run #{run_count} completed successfully")

            except Exception as e:
                logger.error(f"Continuous run #{run_count} failed: {e}", exc_info=True)

            # Short delay before next run (5 minutes)
            wait_seconds = 5 * 60
            logger.info(f"Waiting 5 minutes before next run...")
            time.sleep(wait_seconds)

    except KeyboardInterrupt:
        logger.warning("\nContinuous mode stopped by user")
        logger.info(f"Total runs completed: {run_count}")


def main():
    """Main application entry point"""
    logger.info("Reddit Hate Speech Detection Scraper starting...")

    # Print configuration
    settings.print_config(logger)

    logger.info(f"Configuration loaded: {len(settings.subreddits_list)} subreddits, "
               f"{settings.posts_per_subreddit} posts each")

    # Run the pipeline
    run()


if __name__ == "__main__":
    # Create necessary directories
    Path("logs").mkdir(parents=True, exist_ok=True)

    main()
