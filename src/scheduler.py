"""Scheduler for periodic Reddit monitoring"""
from src.config import setup_logging

logger = setup_logging()


def main():
    """Scheduler entry point - delegates to main.py run_scheduler()"""
    logger.info("Reddit monitoring scheduler starting...")
    logger.info("Use RUN_MODE=scheduler in .env and run main.py instead")
    logger.info("This module is deprecated in favor of main.py with RUN_MODE configuration")

    # Import and run scheduler mode from main
    from src.main import run_scheduler
    run_scheduler()


if __name__ == "__main__":
    main()

