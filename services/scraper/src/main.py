"""Main entry point for the Reddit Hate Speech Detection Scraper"""
import sys
import time
from pathlib import Path

from src.config import Config, setup_logging
from src.pipeline import DataPipeline

# Setup logging from config
logger = setup_logging()


def run_single():
    """Run pipeline once and exit"""
    logger.info("Running in SINGLE mode - will execute once and exit")

    pipeline = DataPipeline()

    try:
        results = pipeline.run_full_pipeline(
            subreddits=Config.TARGET_SUBREDDITS,
            posts_per_subreddit=Config.POSTS_PER_SUBREDDIT,
            max_users_to_enrich=Config.MAX_USERS_TO_ENRICH,
            search_terms=Config.SEARCH_TERMS,
            posts_per_search=Config.POSTS_PER_SEARCH
        )

        logger.info("=" * 80)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)

        return results

    except KeyboardInterrupt:
        logger.warning("\nPipeline interrupted by user")
    except Exception as e:
        logger.error(f"\nPipeline failed: {e}", exc_info=True)
        raise


def run_scheduler():
    """Run pipeline on a schedule (every 2 hours)"""
    logger.info("Running in SCHEDULER mode - will execute every 2 hours")
    logger.info("Press Ctrl+C to stop")

    pipeline = DataPipeline()
    run_count = 0

    try:
        while True:
            run_count += 1
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Starting scheduled run #{run_count}")
            logger.info(f"{'=' * 80}")

            try:
                results = pipeline.run_full_pipeline(
                    subreddits=Config.TARGET_SUBREDDITS,
                    posts_per_subreddit=Config.POSTS_PER_SUBREDDIT,
                    max_users_to_enrich=Config.MAX_USERS_TO_ENRICH,
                    search_terms=Config.SEARCH_TERMS,
                    posts_per_search=Config.POSTS_PER_SEARCH
                )
                logger.info(f"Scheduled run #{run_count} completed successfully")

            except Exception as e:
                logger.error(f"Scheduled run #{run_count} failed: {e}", exc_info=True)

            # Wait 2 hours before next run
            wait_seconds = 2 * 60 * 60  # 2 hours
            logger.info(f"Waiting 2 hours until next run...")
            logger.info(f"Next run scheduled at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + wait_seconds))}")
            time.sleep(wait_seconds)

    except KeyboardInterrupt:
        logger.warning("\nScheduler stopped by user")
        logger.info(f"Total runs completed: {run_count}")


def run_continuous():
    """Run pipeline continuously with minimal delay"""
    logger.info("Running in CONTINUOUS mode - will execute repeatedly")
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
                results = pipeline.run_full_pipeline(
                    subreddits=Config.TARGET_SUBREDDITS,
                    posts_per_subreddit=Config.POSTS_PER_SUBREDDIT,
                    max_users_to_enrich=Config.MAX_USERS_TO_ENRICH,
                    search_terms=Config.SEARCH_TERMS,
                    posts_per_search=Config.POSTS_PER_SEARCH
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
    Config.print_config()

    logger.info(f"Configuration loaded: {len(Config.TARGET_SUBREDDITS)} subreddits, "
               f"{Config.POSTS_PER_SUBREDDIT} posts each")

    # Execute based on RUN_MODE
    if Config.RUN_MODE == 'single':
        run_single()
    elif Config.RUN_MODE == 'scheduler':
        run_scheduler()
    elif Config.RUN_MODE == 'continuous':
        run_continuous()
    else:
        logger.error(f"Invalid RUN_MODE: {Config.RUN_MODE}. Must be 'single', 'scheduler', or 'continuous'")
        sys.exit(1)


if __name__ == "__main__":
    # Create necessary directories
    Path("logs").mkdir(parents=True, exist_ok=True)

    main()