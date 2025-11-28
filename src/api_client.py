"""API client for sending scraped data to the detection API"""
import os
import logging
import requests
from typing import Any, Dict, List, Union

from src.models import BulkResult, ScoredPost, ScoredUser, SendAllResult

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

    def _to_scored_post(self, data: Union[Dict[str, Any], ScoredPost]) -> ScoredPost:
        """Convert dict to ScoredPost if needed"""
        if isinstance(data, ScoredPost):
            return data
        return ScoredPost.from_dict(data)

    def _to_scored_user(self, data: Union[Dict[str, Any], ScoredUser]) -> ScoredUser:
        """Convert dict to ScoredUser if needed"""
        if isinstance(data, ScoredUser):
            return data
        return ScoredUser.from_dict(data)

    def send_posts(
        self, posts: List[Union[Dict[str, Any], ScoredPost]]
    ) -> BulkResult:
        """
        Send scored posts to the API using bulk endpoint

        Args:
            posts: List of ScoredPost models or dicts

        Returns:
            BulkResult with created, skipped, and errors counts
        """
        if not posts:
            return BulkResult()

        scored_posts = [self._to_scored_post(p) for p in posts]
        prepared = [p.model_dump(mode='json') for p in scored_posts]

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

    def send_users(
        self, users: List[Union[Dict[str, Any], ScoredUser]]
    ) -> BulkResult:
        """
        Send scored users to the API using bulk endpoint

        Args:
            users: List of ScoredUser models or dicts

        Returns:
            BulkResult with created, skipped, and errors counts
        """
        if not users:
            return BulkResult()

        scored_users = [self._to_scored_user(u) for u in users]
        prepared = [u.model_dump(mode='json') for u in scored_users]

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
        posts: List[Union[Dict[str, Any], ScoredPost]],
        users: List[Union[Dict[str, Any], ScoredUser]]
    ) -> SendAllResult:
        """
        Send both posts and users to the API

        Args:
            posts: List of ScoredPost models or dicts
            users: List of ScoredUser models or dicts

        Returns:
            SendAllResult with results for both posts and users
        """
        posts_result = self.send_posts(posts)
        users_result = self.send_users(users)

        return SendAllResult(posts=posts_result, users=users_result)
