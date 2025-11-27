"""Scheduler for periodic Reddit monitoring"""
import logging
import time

logger = logging.getLogger(__name__)


def main():
    """Scheduler entry point"""
    logger.info("Reddit monitoring scheduler starting...")

    # TODO: Implement scheduled monitoring
    while True:
        logger.info("Scheduler running...")
        time.sleep(60)  # Sleep for 60 seconds


if __name__ == "__main__":
    main()

