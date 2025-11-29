"""Reddit web scraper using public JSON endpoints and Beautiful Soup"""
import requests
import json
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
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

    def get_user_posts(self, username: str, user_history_days: int = 60) -> List[Dict]:
        """
        Fetch all user's posts within the configured time window using pagination

        Args:
            username: Reddit username (without u/)
            user_history_days: Number of days to look back for posts (default: 60)

        Returns:
            List of post dictionaries from the last user_history_days
        """
        posts = []
        cutoff_time = (datetime.now() - timedelta(days=user_history_days)).timestamp()
        after = None
        should_continue = True
        page_count = 0

        logger.info(f"Fetching all posts from u/{username} (last {user_history_days} days)...")

        while should_continue:
            page_count += 1
            url = f"https://www.reddit.com/user/{username}/submitted.json?limit=100"
            if after:
                url += f"&after={after}"

            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                items = data['data']['children']
                if not items:
                    # No more items to fetch
                    break

                for post in items:
                    post_data = post['data']
                    created_utc = post_data['created_utc']

                    # Stop if we've gone past our time window
                    if created_utc < cutoff_time:
                        should_continue = False
                        break

                    posts.append({
                        'id': post_data['id'],
                        'title': post_data.get('title', ''),
                        'selftext': post_data.get('selftext', ''),
                        'subreddit': post_data['subreddit'],
                        'created_utc': created_utc,
                        'created_date': datetime.fromtimestamp(created_utc).isoformat(),
                        'score': post_data['score'],
                        'num_comments': post_data['num_comments'],
                        'permalink': post_data['permalink'],
                    })

                # Get pagination token for next page
                after = data['data'].get('after')
                if not after:
                    # No more pages
                    break

                logger.debug(f"Fetched page {page_count} for u/{username} posts (total: {len(posts)})")
                self._wait()

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"User u/{username} not found or deleted")
                elif e.response.status_code == 403:
                    logger.warning(f"User u/{username} has a private or suspended profile")
                else:
                    logger.error(f"HTTP error fetching posts from u/{username}: {e}")
                break
            except Exception as e:
                logger.error(f"Error fetching posts from u/{username}: {e}")
                break

        logger.info(f"Successfully fetched {len(posts)} posts from u/{username} ({page_count} pages)")
        return posts

    def get_user_comments(self, username: str, user_history_days: int = 60) -> List[Dict]:
        """
        Fetch all user's comments within the configured time window using pagination

        Args:
            username: Reddit username (without u/)
            user_history_days: Number of days to look back for comments (default: 60)

        Returns:
            List of comment dictionaries from the last user_history_days
        """
        comments = []
        cutoff_time = (datetime.now() - timedelta(days=user_history_days)).timestamp()
        after = None
        should_continue = True
        page_count = 0

        logger.info(f"Fetching all comments from u/{username} (last {user_history_days} days)...")

        while should_continue:
            page_count += 1
            url = f"https://www.reddit.com/user/{username}/comments.json?limit=100"
            if after:
                url += f"&after={after}"

            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                items = data['data']['children']
                if not items:
                    # No more items to fetch
                    break

                for comment in items:
                    comment_data = comment['data']
                    created_utc = comment_data['created_utc']

                    # Stop if we've gone past our time window
                    if created_utc < cutoff_time:
                        should_continue = False
                        break

                    comments.append({
                        'id': comment_data['id'],
                        'body': comment_data['body'],
                        'subreddit': comment_data['subreddit'],
                        'created_utc': created_utc,
                        'created_date': datetime.fromtimestamp(created_utc).isoformat(),
                        'score': comment_data['score'],
                        'permalink': comment_data['permalink'],
                        'link_title': comment_data.get('link_title', ''),
                    })

                # Get pagination token for next page
                after = data['data'].get('after')
                if not after:
                    # No more pages
                    break

                logger.debug(f"Fetched page {page_count} for u/{username} comments (total: {len(comments)})")
                self._wait()

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"User u/{username} not found or deleted")
                elif e.response.status_code == 403:
                    logger.warning(f"User u/{username} has a private or suspended profile")
                else:
                    logger.error(f"HTTP error fetching comments from u/{username}: {e}")
                break
            except Exception as e:
                logger.error(f"Error fetching comments from u/{username}: {e}")
                break

        logger.info(f"Successfully fetched {len(comments)} comments from u/{username} ({page_count} pages)")
        return comments

    def get_user_history(self, username: str, user_history_days: int = 60) -> Dict:
        """
        Fetch complete user history (posts and comments)

        Args:
            username: Reddit username (without u/)
            user_history_days: Number of days to look back for user content (default: 60)

        Returns:
            Dictionary containing username, posts, and comments
        """
        logger.info(f"Fetching complete history for u/{username}...")

        user_data = {
            'username': username,
            'posts': self.get_user_posts(username, user_history_days),
            'comments': self.get_user_comments(username, user_history_days),
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