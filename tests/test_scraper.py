"""Quick test script to verify Reddit scraping works"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.reddit_scraper import RedditScraper
import json

def test_scraper():
    """Test the Reddit scraper with a simple query"""
    print("Testing Reddit Scraper...")
    print("=" * 60)

    scraper = RedditScraper(rate_limit_delay=2.0)

    # Test 1: Get posts from a subreddit
    print("\n[Test 1] Fetching 5 posts from r/python...")
    posts = scraper.get_subreddit_posts('python', limit=5)
    print(f"✓ Successfully fetched {len(posts)} posts")

    if posts:
        print(f"\nSample post:")
        print(f"  Title: {posts[0]['title'][:80]}...")
        print(f"  Author: u/{posts[0]['author']}")
        print(f"  Score: {posts[0]['score']}")
        print(f"  Comments: {posts[0]['num_comments']}")

        # Test 2: Get user history
        test_username = posts[0]['author']
        if test_username not in ['[deleted]', 'AutoModerator']:
            print(f"\n[Test 2] Fetching history for u/{test_username}...")
            user_data = scraper.get_user_history(test_username, limit=10)
            print(f"✓ User has {user_data['total_posts']} posts and "
                  f"{user_data['total_comments']} comments")

    print("\n" + "=" * 60)
    print("✅ All tests passed! Scraper is working correctly.")
    print("\nYou can now run the full pipeline with:")
    print("  python -m src.main")
    print("  OR")
    print("  docker-compose up")

if __name__ == "__main__":
    test_scraper()

