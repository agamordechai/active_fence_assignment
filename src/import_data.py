"""Utility script to import existing JSON data into the database"""
import json
import sys
from pathlib import Path
from datetime import datetime
import logging

from src.database.database import get_db_context, init_db
from src.database import crud

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_post_data(post_data: dict) -> dict:
    """Convert post data from JSON format to database format"""
    # Remove fields that don't exist in the model
    post_data.pop('enrichment_timestamp', None)

    # Convert created_date string to datetime if needed (skip if already datetime)
    created_date = post_data.get('created_date')
    if created_date and isinstance(created_date, str):
        post_data['created_date'] = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
    elif isinstance(created_date, (int, float)):
        # Handle unix timestamp
        post_data['created_date'] = datetime.fromtimestamp(created_date)

    # Convert scored_at string to datetime if needed
    scored_at = post_data.get('scored_at')
    if scored_at and isinstance(scored_at, str):
        post_data['scored_at'] = datetime.fromisoformat(scored_at.replace('Z', '+00:00'))

    # Convert collected_at string to datetime if needed
    collected_at = post_data.get('collected_at')
    if collected_at and isinstance(collected_at, str):
        post_data['collected_at'] = datetime.fromisoformat(collected_at.replace('Z', '+00:00'))

    return post_data


def convert_user_data(user_data: dict) -> dict:
    """Convert user data from JSON format to database format"""
    # Remove fields that don't exist in the model
    user_data.pop('enrichment_timestamp', None)
    user_data.pop('post_history', None)
    user_data.pop('comment_history', None)

    # Convert account_created_date string to datetime if needed
    account_created = user_data.get('account_created_date')
    if account_created and isinstance(account_created, str):
        user_data['account_created_date'] = datetime.fromisoformat(account_created.replace('Z', '+00:00'))
    elif isinstance(account_created, (int, float)):
        user_data['account_created_date'] = datetime.fromtimestamp(account_created)

    # Convert scored_at string to datetime if needed
    scored_at = user_data.get('scored_at')
    if scored_at and isinstance(scored_at, str):
        user_data['scored_at'] = datetime.fromisoformat(scored_at.replace('Z', '+00:00'))

    # Convert collected_at string to datetime if needed
    collected_at = user_data.get('collected_at')
    if collected_at and isinstance(collected_at, str):
        user_data['collected_at'] = datetime.fromisoformat(collected_at.replace('Z', '+00:00'))

    return user_data


def import_posts_from_json(json_file_path: str):
    """Import posts from JSON file into database"""
    logger.info(f"Importing posts from {json_file_path}")

    with open(json_file_path, 'r') as f:
        posts_data = json.load(f)

    with get_db_context() as db:
        created_count = 0
        skipped_count = 0

        for post_data in posts_data:
            try:
                post_id = post_data.get('id')
                existing_post = crud.get_post(db, post_id)

                if not existing_post:
                    converted_data = convert_post_data(post_data)
                    crud.create_post(db, converted_data)
                    created_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                logger.error(f"Error importing post {post_data.get('id')}: {e}")

        logger.info(f"Posts import complete: {created_count} created, {skipped_count} skipped")
        return created_count, skipped_count


def import_users_from_json(json_file_path: str):
    """Import users from JSON file into database"""
    logger.info(f"Importing users from {json_file_path}")

    with open(json_file_path, 'r') as f:
        users_data = json.load(f)

    with get_db_context() as db:
        created_count = 0
        skipped_count = 0

        for user_data in users_data:
            try:
                username = user_data.get('username')
                existing_user = crud.get_user(db, username)

                if not existing_user:
                    converted_data = convert_user_data(user_data)
                    crud.create_user(db, converted_data)
                    created_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                logger.error(f"Error importing user {user_data.get('username')}: {e}")

        logger.info(f"Users import complete: {created_count} created, {skipped_count} skipped")
        return created_count, skipped_count


def import_all_from_directory(directory_path: str = "data/processed", cleanup: bool = True):
    """Import all posts and users from the processed data directory

    Args:
        directory_path: Path to directory containing JSON files
        cleanup: If True, delete JSON files after successful import
    """
    logger.info(f"Importing all data from {directory_path}")

    data_dir = Path(directory_path)

    if not data_dir.exists():
        logger.error(f"Directory {directory_path} does not exist")
        return

    # Find the latest posts and users files
    posts_files = sorted(data_dir.glob("posts_scored_*.json"))
    users_files = sorted(data_dir.glob("users_scored_*.json"))

    imported_files = []
    posts_created = 0
    users_created = 0

    if not posts_files:
        logger.warning("No posts files found")
    else:
        latest_posts_file = posts_files[-1]
        logger.info(f"Using latest posts file: {latest_posts_file}")
        created, skipped = import_posts_from_json(str(latest_posts_file))
        posts_created = created
        if created > 0 or skipped > 0:
            imported_files.append(latest_posts_file)

    if not users_files:
        logger.warning("No users files found")
    else:
        latest_users_file = users_files[-1]
        logger.info(f"Using latest users file: {latest_users_file}")
        created, skipped = import_users_from_json(str(latest_users_file))
        users_created = created
        if created > 0 or skipped > 0:
            imported_files.append(latest_users_file)

    # Cleanup JSON files if requested and import was successful
    if cleanup and imported_files:
        logger.info("Cleaning up imported JSON files...")
        import os

        for json_file in imported_files:
            try:
                # Delete the processed file
                if os.path.exists(json_file):
                    os.remove(json_file)
                    logger.info(f"  Deleted {json_file.name}")

                # Delete corresponding raw file
                if 'posts_scored_' in str(json_file):
                    raw_file = str(json_file).replace('processed/posts_scored_', 'raw/posts_')
                    summary_file = str(json_file).replace('posts_scored_', 'summary_report_')
                elif 'users_scored_' in str(json_file):
                    raw_file = str(json_file).replace('processed/users_scored_', 'raw/users_')
                    summary_file = None

                if os.path.exists(raw_file):
                    os.remove(raw_file)
                    logger.info(f"  Deleted {os.path.basename(raw_file)}")

                if summary_file and os.path.exists(summary_file):
                    os.remove(summary_file)
                    logger.info(f"  Deleted {os.path.basename(summary_file)}")

            except Exception as e:
                logger.warning(f"Failed to delete {json_file}: {e}")

        logger.info(f"Cleanup complete. Imported {posts_created} posts and {users_created} users.")


def main():
    """Main entry point for the import script"""
    logger.info("Starting data import...")

    # Initialize database
    init_db()

    # Import data
    if len(sys.argv) > 1:
        # Import from specific files
        file_path = sys.argv[1]
        if "posts_scored" in file_path:
            import_posts_from_json(file_path)
        elif "users_scored" in file_path:
            import_users_from_json(file_path)
        else:
            logger.error("Unknown file type. File should contain 'posts_scored' or 'users_scored'")
    else:
        # Import all from directory
        import_all_from_directory()

    logger.info("Import complete!")


if __name__ == "__main__":
    main()

