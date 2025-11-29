"""API client for sending scraped data to the detection API"""
import logging
import requests
from typing import Any, Dict, List, Union

from src.config import settings

logger = logging.getLogger(__name__)


class BulkResult:
    """Result from bulk API operations"""
    def __init__(self, created: int = 0, skipped: int = 0, errors: int = 0):
        self.created = created
        self.skipped = skipped
        self.errors = errors


class SendAllResult:
    """Result from sending both posts and users"""
    def __init__(self, posts: BulkResult, users: BulkResult):
        self.posts = posts
        self.users = users


class APIClient:
    """Client for communicating with the Reddit Hate Speech Detection API"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.api_url
        self.timeout = settings.api_timeout
        self.session = requests.Session()

    def health_check(self) -> bool:
        """Check if the API is available"""
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.RequestException as e:
            logger.warning(f"API health check failed: {e}")
            return False

    def _prepare_post(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare post data for API submission"""
        risk = post.get('risk_assessment', {})
        return {
            'id': post.get('id', ''),
            'title': post.get('title', ''),
            'selftext': post.get('selftext', ''),
            'author': post.get('author', ''),
            'subreddit': post.get('subreddit', ''),
            'created_utc': post.get('created_utc', 0),
            'created_date': post.get('created_date'),
            'score': post.get('score', 0),
            'upvote_ratio': post.get('upvote_ratio', 0.0),
            'num_comments': post.get('num_comments', 0),
            'permalink': post.get('permalink'),
            'url': post.get('url'),
            'is_self': post.get('is_self', False),
            'over_18': post.get('over_18', False),
            'spoiler': post.get('spoiler', False),
            'locked': post.get('locked', False),
            'link_flair_text': post.get('link_flair_text'),
            'risk_assessment': {
                'risk_score': int(risk.get('risk_score', 0)),
                'risk_level': risk.get('risk_level', 'minimal'),
                'hate_score': int(risk.get('hate_score', 0)),
                'violence_score': int(risk.get('violence_score', 0)),
                'explanation': risk.get('explanation', ''),
                'flags': risk.get('flags', [])
            },
            'scored_at': post.get('scored_at')
        }

    def _prepare_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare user data for API submission"""
        risk = user.get('risk_assessment', {})

        # Map scorer field names to API schema field names
        hate_score = risk.get('average_hate_score', risk.get('hate_score', 0))
        violence_score = risk.get('average_violence_score', risk.get('violence_score', 0))
        risk_score = risk.get('overall_risk_score', risk.get('risk_score', 0))

        return {
            'username': user.get('username', ''),
            'account_created_utc': user.get('account_created_utc'),
            'account_created_date': user.get('account_created_date'),
            'link_karma': user.get('link_karma', 0),
            'comment_karma': user.get('comment_karma', 0),
            'is_gold': user.get('is_gold', False),
            'is_mod': user.get('is_mod', False),
            'has_verified_email': user.get('has_verified_email', False),
            'risk_assessment': {
                'risk_score': int(risk_score) if risk_score else 0,
                'risk_level': risk.get('risk_level', 'minimal'),
                'hate_score': int(hate_score) if hate_score else 0,
                'violence_score': int(violence_score) if violence_score else 0,
                'explanation': risk.get('explanation', ''),
                'flags': risk.get('flags', [])
            },
            'statistics': {
                'total_posts_analyzed': risk.get(
                    'total_content_analyzed', user.get('total_posts_analyzed', 0)
                ),
                'flagged_posts_count': risk.get(
                    'high_risk_content_count', user.get('flagged_posts_count', 0)
                ),
                'flagged_comments_count': user.get('flagged_comments_count', 0),
                'avg_post_risk_score': float(risk_score) if risk_score else 0.0,
                'avg_comment_risk_score': user.get('avg_comment_risk_score', 0.0),
                'max_risk_score_seen': int(risk_score) if risk_score else 0
            },
            'scored_at': risk.get('scored_at') or user.get('scored_at')
        }

    def send_posts(self, posts: List[Dict[str, Any]]) -> BulkResult:
        """
        Send scored posts to the API using bulk endpoint

        Args:
            posts: List of scored post dictionaries

        Returns:
            BulkResult with created, skipped, and errors counts
        """
        if not posts:
            return BulkResult()

        prepared = [self._prepare_post(p) for p in posts]

        try:
            response = self.session.post(
                f"{self.base_url}/bulk/posts",
                json=prepared,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return BulkResult(
                created=result.get('created', 0),
                skipped=result.get('skipped', 0),
                errors=len(result.get('errors', []))
            )
        except requests.RequestException as e:
            logger.error(f"Failed to send posts to API: {e}")
            raise

    def send_users(self, users: List[Dict[str, Any]]) -> BulkResult:
        """
        Send scored users to the API using bulk endpoint

        Args:
            users: List of scored user dictionaries

        Returns:
            BulkResult with created, skipped, and errors counts
        """
        if not users:
            return BulkResult()

        prepared = [self._prepare_user(u) for u in users]

        try:
            response = self.session.post(
                f"{self.base_url}/bulk/users",
                json=prepared,
                timeout=self.timeout
            )
            if response.status_code == 422:
                logger.error(f"Validation error from API: {response.text}")
            response.raise_for_status()
            result = response.json()
            return BulkResult(
                created=result.get('created', 0),
                skipped=result.get('skipped', 0),
                errors=len(result.get('errors', []))
            )
        except requests.RequestException as e:
            logger.error(f"Failed to send users to API: {e}")
            raise

    def send_all(
        self,
        posts: List[Dict[str, Any]],
        users: List[Dict[str, Any]]
    ) -> SendAllResult:
        """
        Send both posts and users to the API

        Args:
            posts: List of scored post dictionaries
            users: List of scored user dictionaries

        Returns:
            SendAllResult with results for both posts and users
        """
        posts_result = self.send_posts(posts)
        users_result = self.send_users(users)

        return SendAllResult(posts=posts_result, users=users_result)

    def get_monitored_users(self) -> List[Dict[str, Any]]:
        """
        Get list of users marked for monitoring

        Returns:
            List of monitored user dictionaries
        """
        try:
            response = self.session.get(
                f"{self.base_url}/users",
                params={'is_monitored': True, 'limit': 1000},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get monitored users: {e}")
            return []

    def create_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new alert in the API

        Args:
            alert: Alert data dictionary

        Returns:
            Created alert data
        """
        try:
            response = self.session.post(
                f"{self.base_url}/alerts",
                json=alert,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to create alert: {e}")
            raise

    def create_monitoring_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a monitoring log entry in the API

        Args:
            log_entry: Monitoring log data dictionary

        Returns:
            Created log entry data
        """
        try:
            response = self.session.post(
                f"{self.base_url}/monitoring-logs",
                json=log_entry,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to create monitoring log: {e}")
            raise

    def set_user_monitored(self, username: str, is_monitored: bool = True) -> Dict[str, Any]:
        """
        Set a user's monitoring status

        Args:
            username: Reddit username
            is_monitored: Whether to monitor the user

        Returns:
            Updated user data
        """
        try:
            response = self.session.patch(
                f"{self.base_url}/users/{username}",
                json={'is_monitored': is_monitored},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to update user monitoring status: {e}")
            raise