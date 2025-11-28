"""Reddit web scraper using public JSON endpoints and Beautiful Soup"""
import requests
import json
import time
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RedditScraper:
    """Scraper for Reddit data using public JSON endpoints"""

    def __init__(self, rate_limit_delay: float = 2.0):
        """
        Initialize the Reddit scraper

        Args:
            rate_limit_delay: Seconds to wait between requests (default: 2.0)
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.rate_limit_delay = rate_limit_delay

    def _wait(self):
        """Rate limiting delay between requests"""
        time.sleep(self.rate_limit_delay)

    def get_subreddit_posts(self, subreddit: str, limit: int = 100,
                           sort: str = 'new') -> List[Dict]:
        """
        Fetch posts from a subreddit using Reddit's JSON endpoint

        Args:
            subreddit: Name of the subreddit (without r/)
            limit: Maximum number of posts to fetch (up to 100 per request)
            sort: Sort method - 'new', 'hot', 'top', 'rising'

        Returns:
            List of post dictionaries with metadata
        """
        posts = []
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={min(limit, 100)}"

        try:
            logger.info(f"Fetching posts from r/{subreddit} ({sort})...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            for post in data['data']['children']:
                post_data = post['data']
                posts.append({
                    'id': post_data['id'],
                    'title': post_data['title'],
                    'selftext': post_data.get('selftext', ''),
                    'author': post_data['author'],
                    'subreddit': post_data['subreddit'],
                    'created_utc': post_data['created_utc'],
                    'created_date': datetime.fromtimestamp(post_data['created_utc']).isoformat(),
                    'score': post_data['score'],
                    'upvote_ratio': post_data.get('upvote_ratio', 0),
                    'num_comments': post_data['num_comments'],
                    'permalink': post_data['permalink'],
                    'url': post_data['url'],
                    'is_self': post_data['is_self'],
                    'over_18': post_data.get('over_18', False),
                    'spoiler': post_data.get('spoiler', False),
                    'locked': post_data.get('locked', False),
                    'link_flair_text': post_data.get('link_flair_text', ''),
                })

            logger.info(f"Successfully fetched {len(posts)} posts from r/{subreddit}")
            self._wait()

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching posts from r/{subreddit}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching posts from r/{subreddit}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from r/{subreddit}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching posts from r/{subreddit}: {e}")

        return posts

    def get_user_posts(self, username: str, limit: int = 100) -> List[Dict]:
        """
        Fetch a user's recent posts

        Args:
            username: Reddit username (without u/)
            limit: Maximum number of posts to fetch

        Returns:
            List of post dictionaries
        """
        posts = []
        url = f"https://www.reddit.com/user/{username}/submitted.json?limit={min(limit, 100)}"

        try:
            logger.info(f"Fetching posts from u/{username}...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            for post in data['data']['children']:
                post_data = post['data']
                posts.append({
                    'id': post_data['id'],
                    'title': post_data.get('title', ''),
                    'selftext': post_data.get('selftext', ''),
                    'subreddit': post_data['subreddit'],
                    'created_utc': post_data['created_utc'],
                    'created_date': datetime.fromtimestamp(post_data['created_utc']).isoformat(),
                    'score': post_data['score'],
                    'num_comments': post_data['num_comments'],
                    'permalink': post_data['permalink'],
                })

            logger.info(f"Successfully fetched {len(posts)} posts from u/{username}")
            self._wait()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"User u/{username} not found or has no posts")
            else:
                logger.error(f"HTTP error fetching posts from u/{username}: {e}")
        except Exception as e:
            logger.error(f"Error fetching posts from u/{username}: {e}")

        return posts

    def get_user_comments(self, username: str, limit: int = 100) -> List[Dict]:
        """
        Fetch a user's recent comments

        Args:
            username: Reddit username (without u/)
            limit: Maximum number of comments to fetch

        Returns:
            List of comment dictionaries
        """
        comments = []
        url = f"https://www.reddit.com/user/{username}/comments.json?limit={min(limit, 100)}"

        try:
            logger.info(f"Fetching comments from u/{username}...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            for comment in data['data']['children']:
                comment_data = comment['data']
                comments.append({
                    'id': comment_data['id'],
                    'body': comment_data['body'],
                    'subreddit': comment_data['subreddit'],
                    'created_utc': comment_data['created_utc'],
                    'created_date': datetime.fromtimestamp(comment_data['created_utc']).isoformat(),
                    'score': comment_data['score'],
                    'permalink': comment_data['permalink'],
                    'link_title': comment_data.get('link_title', ''),
                })

            logger.info(f"Successfully fetched {len(comments)} comments from u/{username}")
            self._wait()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"User u/{username} not found or has no comments")
            else:
                logger.error(f"HTTP error fetching comments from u/{username}: {e}")
        except Exception as e:
            logger.error(f"Error fetching comments from u/{username}: {e}")

        return comments

    def get_user_history(self, username: str, limit: int = 100) -> Dict:
        """
        Fetch complete user history (posts and comments)

        Args:
            username: Reddit username (without u/)
            limit: Maximum number of items to fetch per type

        Returns:
            Dictionary containing username, posts, and comments
        """
        logger.info(f"Fetching complete history for u/{username}...")

        user_data = {
            'username': username,
            'posts': self.get_user_posts(username, limit),
            'comments': self.get_user_comments(username, limit),
            'total_posts': 0,
            'total_comments': 0,
            'fetched_at': datetime.now().isoformat(),
        }

        user_data['total_posts'] = len(user_data['posts'])
        user_data['total_comments'] = len(user_data['comments'])

        logger.info(f"Fetched {user_data['total_posts']} posts and "
                   f"{user_data['total_comments']} comments for u/{username}")

        return user_data

    def search_posts(self, query: str, subreddit: Optional[str] = None,
                    limit: int = 100) -> List[Dict]:
        """
        Search for posts using Reddit's search

        Args:
            query: Search query
            subreddit: Optional subreddit to search in
            limit: Maximum number of posts to fetch

        Returns:
            List of post dictionaries matching the search
        """
        posts = []

        if subreddit:
            url = f"https://www.reddit.com/r/{subreddit}/search.json?q={query}&restrict_sr=1&limit={min(limit, 100)}&sort=new"
        else:
            url = f"https://www.reddit.com/search.json?q={query}&limit={min(limit, 100)}&sort=new"

        try:
            logger.info(f"Searching for: '{query}'" + (f" in r/{subreddit}" if subreddit else ""))
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            for post in data['data']['children']:
                post_data = post['data']
                posts.append({
                    'id': post_data['id'],
                    'title': post_data['title'],
                    'selftext': post_data.get('selftext', ''),
                    'author': post_data['author'],
                    'subreddit': post_data['subreddit'],
                    'created_utc': post_data['created_utc'],
                    'created_date': datetime.fromtimestamp(post_data['created_utc']).isoformat(),
                    'score': post_data['score'],
                    'num_comments': post_data['num_comments'],
                    'permalink': post_data['permalink'],
                    'url': post_data['url'],
                })

            logger.info(f"Found {len(posts)} posts matching '{query}'")
            self._wait()

        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")

        return posts

    def collect_from_multiple_subreddits(self, subreddits: List[str],
                                        posts_per_subreddit: int = 50) -> List[Dict]:
        """
        Collect posts from multiple subreddits

        Args:
            subreddits: List of subreddit names
            posts_per_subreddit: Number of posts to fetch per subreddit

        Returns:
            Combined list of posts from all subreddits
        """
        all_posts = []

        for subreddit in subreddits:
            posts = self.get_subreddit_posts(subreddit, limit=posts_per_subreddit)
            all_posts.extend(posts)
            logger.info(f"Progress: {len(all_posts)} total posts collected")

        return all_posts