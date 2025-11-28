"""API client for sending scraped data to the detection API"""
import os
import logging
import requests
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class APIClient:
    """Client for communicating with the Reddit Hate Speech Detection API"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv('API_URL', 'http://localhost:8000')
        self.timeout = int(os.getenv('API_TIMEOUT', '30'))
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

    def _prepare_post_for_api(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform scored post data to match API schema"""
        risk = post_data.get('risk_assessment', {})

        # Convert datetime objects to ISO strings if needed
        created_date = post_data.get('created_date')
        if isinstance(created_date, datetime):
            created_date = created_date.isoformat()
        elif isinstance(created_date, str):
            pass  # Already a string
        else:
            created_date = datetime.utcnow().isoformat()

        scored_at = post_data.get('scored_at')
        if isinstance(scored_at, datetime):
            scored_at = scored_at.isoformat()

        return {
            'id': post_data.get('id'),
            'title': post_data.get('title', ''),
            'selftext': post_data.get('selftext', ''),
            'author': post_data.get('author', ''),
            'subreddit': post_data.get('subreddit', ''),
            'created_utc': post_data.get('created_utc', 0),
            'created_date': created_date,
            'score': post_data.get('score', 0),
            'upvote_ratio': post_data.get('upvote_ratio', 0.0),
            'num_comments': post_data.get('num_comments', 0),
            'permalink': post_data.get('permalink'),
            'url': post_data.get('url'),
            'is_self': post_data.get('is_self', False),
            'over_18': post_data.get('over_18', False),
            'spoiler': post_data.get('spoiler', False),
            'locked': post_data.get('locked', False),
            'link_flair_text': post_data.get('link_flair_text'),
            'risk_assessment': {
                'risk_score': risk.get('risk_score', 0),
                'risk_level': risk.get('risk_level', 'minimal'),
                'hate_score': risk.get('hate_score', 0),
                'violence_score': risk.get('violence_score', 0),
                'explanation': risk.get('explanation', ''),
                'flags': risk.get('flags', [])
            },
            'scored_at': scored_at
        }

    def _prepare_user_for_api(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform scored user data to match API schema"""
        risk = user_data.get('risk_assessment', {})

        # Convert datetime objects to ISO strings if needed
        account_created_date = user_data.get('account_created_date')
        if isinstance(account_created_date, datetime):
            account_created_date = account_created_date.isoformat()

        # scored_at can be in risk_assessment or at top level
        scored_at = risk.get('scored_at') or user_data.get('scored_at')
        if isinstance(scored_at, datetime):
            scored_at = scored_at.isoformat()

        # Map scorer field names to API schema field names
        # Scorer uses: average_hate_score, average_violence_score, overall_risk_score
        # API expects: hate_score, violence_score, risk_score
        hate_score = risk.get('average_hate_score', risk.get('hate_score', 0))
        violence_score = risk.get('average_violence_score', risk.get('violence_score', 0))
        risk_score = risk.get('overall_risk_score', risk.get('risk_score', 0))

        # Convert to int if they are floats
        hate_score = int(hate_score) if hate_score else 0
        violence_score = int(violence_score) if violence_score else 0
        risk_score = int(risk_score) if risk_score else 0

        return {
            'username': user_data.get('username'),
            'account_created_utc': user_data.get('account_created_utc'),
            'account_created_date': account_created_date,
            'link_karma': user_data.get('link_karma', 0),
            'comment_karma': user_data.get('comment_karma', 0),
            'is_gold': user_data.get('is_gold', False),
            'is_mod': user_data.get('is_mod', False),
            'has_verified_email': user_data.get('has_verified_email', False),
            'risk_assessment': {
                'risk_score': risk_score,
                'risk_level': risk.get('risk_level', 'minimal'),
                'hate_score': hate_score,
                'violence_score': violence_score,
                'explanation': risk.get('explanation', ''),
                'flags': risk.get('flags', [])
            },
            'statistics': {
                'total_posts_analyzed': risk.get('total_content_analyzed', user_data.get('total_posts_analyzed', 0)),
                'flagged_posts_count': risk.get('high_risk_content_count', user_data.get('flagged_posts_count', 0)),
                'flagged_comments_count': user_data.get('flagged_comments_count', 0),
                'avg_post_risk_score': float(risk_score),
                'avg_comment_risk_score': user_data.get('avg_comment_risk_score', 0.0),
                'max_risk_score_seen': int(risk_score)
            },
            'scored_at': scored_at
        }

    def send_posts(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Send scored posts to the API using bulk endpoint

        Returns:
            Dict with 'created', 'skipped', and 'errors' counts
        """
        if not posts:
            return {'created': 0, 'skipped': 0, 'errors': 0}

        prepared_posts = [self._prepare_post_for_api(p) for p in posts]

        try:
            response = self.session.post(
                f"{self.base_url}/bulk/posts",
                json=prepared_posts,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return {
                'created': result.get('created', 0),
                'skipped': result.get('skipped', 0),
                'errors': len(result.get('errors', []))
            }
        except requests.RequestException as e:
            logger.error(f"Failed to send posts to API: {e}")
            raise

    def send_users(self, users: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Send scored users to the API using bulk endpoint

        Returns:
            Dict with 'created', 'skipped', and 'errors' counts
        """
        if not users:
            return {'created': 0, 'skipped': 0, 'errors': 0}

        prepared_users = [self._prepare_user_for_api(u) for u in users]

        try:
            response = self.session.post(
                f"{self.base_url}/bulk/users",
                json=prepared_users,
                timeout=self.timeout
            )
            if response.status_code == 422:
                # Log validation error details
                logger.error(f"Validation error from API: {response.text}")
            response.raise_for_status()
            result = response.json()
            return {
                'created': result.get('created', 0),
                'skipped': result.get('skipped', 0),
                'errors': len(result.get('errors', []))
            }
        except requests.RequestException as e:
            logger.error(f"Failed to send users to API: {e}")
            raise

    def send_all(self, posts: List[Dict[str, Any]], users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send both posts and users to the API

        Returns:
            Dict with results for both posts and users
        """
        posts_result = self.send_posts(posts)
        users_result = self.send_users(users)

        return {
            'posts': posts_result,
            'users': users_result
        }
